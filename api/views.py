# Django REST API views for RAG backend
import os
import time
import tempfile
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import (
    QueryRequest, QueryResponse, DocumentUpload, SystemMetrics,
    KnowledgeBaseStatus, ConversationSession, ChatMessage
)
from .serializers import (
    QueryRequestInputSerializer, QueryResponseOutputSerializer,
    DocumentUploadInputSerializer, DocumentUploadResponseSerializer,
    MemoryContextSerializer, SessionsListSerializer, HealthCheckSerializer,
    KnowledgeBaseReloadSerializer, VectorStoreClearSerializer,
    SystemMetricsSerializer, KnowledgeBaseStatusSerializer
)
from .agent import rag_agent
from .agent_v2 import get_agent_v2  # NEW: Enhanced agent
from .memory import memory_manager
from .utils import document_processor, metrics_collector, response_formatter
from .config import config
from .vectorstore import vector_store

logger = logging.getLogger(__name__)


def index_view(request):
    """Serve the main frontend page"""
    return render(request, 'index.html')


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "RAG Pipeline API",
            "version": "1.0.0",
            "data_source": "PDFs folder (./pdfs/)",
            "features": {
                "knowledge_base": "Active",
                "web_search": "Active",
                "data_location": "pdfs/ folder"
            }
        })


class QueryProcessView(APIView):
    """Process a user query through the RAG pipeline"""
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    
    def post(self, request):
        serializer = QueryRequestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = time.time()
        
        try:
            # Check if we should use the new agent (v2) or fallback to old agent
            use_v2 = serializer.validated_data.get('use_v2_agent', True)

            if use_v2:
                # Use new enhanced agent with query routing
                agent_v2 = get_agent_v2()
                result = agent_v2.process_query(
                    query=serializer.validated_data['query'],
                    session_id=serializer.validated_data.get('session_id', 'default')
                )
            else:
                # Fallback to old RAG agent
                result = rag_agent.process_query(
                    query=serializer.validated_data['query'],
                    session_id=serializer.validated_data.get('session_id'),
                    use_web_search=serializer.validated_data.get('use_web_search', True),
                    enhance_formatting=serializer.validated_data.get('enhance_formatting', True)
                )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record metrics in background
            metrics_collector.record_query(
                response_time,
                len(result.get("sources", [])) > 0,
                result.get("web_search_used", False)
            )
            
            # Format response
            response_data = {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "confidence_score": result.get("confidence_score", 0.5),
                "web_search_used": result.get("web_search_used", False),
                "session_id": result.get("session_id", serializer.validated_data.get('session_id', 'default')),
                "metadata": result.get("metadata", {})
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            metrics_collector.record_error()
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentUploadView(APIView):
    """Upload and process a document"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uploaded_file = request.FILES['file']

            # Ensure pdfs directory exists
            os.makedirs(config.KNOWLEDGE_BASE_PATH, exist_ok=True)

            # Save file to pdfs folder
            file_path = os.path.join(config.KNOWLEDGE_BASE_PATH, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Process document
            documents = document_processor.load_document(file_path)

            # Add to vector store
            success = rag_agent.add_documents(documents)

            if success:
                return Response({
                    "status": "success",
                    "message": f"Document {uploaded_file.name} saved to pdfs/ and embedded successfully",
                    "chunks_created": len(documents),
                    "file_path": file_path
                })
            else:
                return Response(
                    {"error": "Failed to add documents to vector store"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TextUploadView(APIView):
    """Upload raw text content"""
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    
    def post(self, request):
        serializer = DocumentUploadInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Process text
            doc = document_processor.process_text(
                serializer.validated_data['content'],
                serializer.validated_data.get('metadata', {})
            )
            
            # Add to vector store
            success = rag_agent.add_documents([doc])
            
            if success:
                return Response({
                    "status": "success",
                    "message": "Text content processed successfully"
                })
            else:
                return Response(
                    {"error": "Failed to add content to vector store"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error uploading text: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryView(APIView):
    """Get conversation memory for a session"""
    permission_classes = [AllowAny]
    
    def get(self, request, session_id):
        try:
            context = memory_manager.get_conversation_context(session_id)
            memory_vars = memory_manager.get_memory_variables(session_id)
            
            return Response({
                "session_id": session_id,
                "context": context,
                "memory": memory_vars
            })
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, session_id):
        """Clear conversation memory for a session"""
        try:
            memory_manager.clear_session(session_id)
            return Response({
                "status": "success", 
                "message": f"Memory cleared for session {session_id}"
            })
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionsListView(APIView):
    """List all active sessions"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            sessions = memory_manager.get_all_sessions()
            return Response({
                "sessions": sessions, 
                "count": len(sessions)
            })
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MetricsView(APIView):
    """Get system metrics"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            metrics = metrics_collector.get_metrics()
            return Response(metrics)
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Reset system metrics"""
        try:
            metrics_collector.reset_metrics()
            return Response({
                "status": "success", 
                "message": "Metrics reset successfully"
            })
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeBaseStatusView(APIView):
    """Get knowledge base status and statistics"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get collection info
            parent_count = vector_store.parent_store._collection.count()
            child_count = vector_store.child_store._collection.count()
            
            return Response({
                "status": "active",
                "parent_chunks": parent_count,
                "child_chunks": child_count,
                "total_documents": parent_count + child_count,
                "knowledge_base_path": config.KNOWLEDGE_BASE_PATH,
                "data_source": "PDFs folder (./pdfs/)"
            })
        except Exception as e:
            logger.error(f"Error getting knowledge base status: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeBaseReloadView(APIView):
    """Reload knowledge base from PDFs folder"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Clear existing vector store
            vector_store.delete_collection()
            
            # Reload documents from PDFs folder
            kb_documents = document_processor.load_knowledge_base(config.KNOWLEDGE_BASE_PATH)
            if kb_documents:
                success = rag_agent.add_documents(kb_documents)
                if success:
                    return Response({
                        "status": "success",
                        "message": f"Knowledge base reloaded with {len(kb_documents)} documents from PDFs folder"
                    })
                else:
                    return Response(
                        {"error": "Failed to add documents to vector store"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response({
                    "status": "success",
                    "message": "No documents found in PDFs folder"
                })
        except Exception as e:
            logger.error(f"Error reloading knowledge base: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VectorStoreClearView(APIView):
    """Clear the entire vector store (use with caution)"""
    permission_classes = [AllowAny]
    
    def delete(self, request):
        try:
            vector_store.delete_collection()
            return Response({
                "status": "success", 
                "message": "Vector store cleared successfully"
            })
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )