# Django REST API views for RAG backend
import os
import csv
import json
import time
import tempfile
import logging
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Count, Avg, Sum, Q
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from account.authentication import BearerTokenAuthentication
from rest_framework.permissions import IsAuthenticated as isAuthenticated
from rest_framework.permissions import IsAdminUser as isAdminUser

from .models import (
    QueryRequest, QueryResponse, DocumentUpload, SystemMetrics,
    KnowledgeBaseStatus, ConversationSession, ChatMessage,
    QueryAnalytics, DataSourceStats, CSVUpload, AgentInteraction
)
from .serializers import (
    QueryRequestInputSerializer, QueryResponseOutputSerializer,
    DocumentUploadInputSerializer, DocumentUploadResponseSerializer,
    MemoryContextSerializer, SessionsListSerializer, HealthCheckSerializer,
    KnowledgeBaseReloadSerializer, VectorStoreClearSerializer,
    SystemMetricsSerializer, KnowledgeBaseStatusSerializer,
    CSVUploadInputSerializer, CSVUploadResponseSerializer,
    AnalyticsQueryStatsSerializer, AnalyticsSourceStatsSerializer,
    SystemReportSerializer, UsageReportSerializer,
    SQLExportInputSerializer, SQLExportResponseSerializer,
    QueryAnalyticsSerializer, DataSourceStatsSerializer
)
from .agent import rag_agent, master_orchestrator
from .memory import memory_manager
from .utils import document_processor, metrics_collector, response_formatter
from .config import config
from .vectorstore import vector_store
from .sql_engine import sql_engine
from .retriever import hybrid_retriever
from .token_tracker import token_tracker
from .query_logger import query_logger
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


logger = logging.getLogger(__name__)



# ============================================================================
# Token Tracking Serializers
# ============================================================================

class TokenUsageStatsSerializer(serializers.Serializer):
    """Token usage statistics"""
    total_tokens = serializers.IntegerField()
    total_prompt_tokens = serializers.IntegerField()
    total_completion_tokens = serializers.IntegerField()
    total_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=6)
    avg_tokens_per_query = serializers.FloatField()
    avg_cost_per_query = serializers.DecimalField(max_digits=10, decimal_places=6)
    queries_count = serializers.IntegerField()


class DeveloperDashboardSerializer(serializers.Serializer):
    """Complete developer dashboard data"""
    # Token metrics
    token_usage = TokenUsageStatsSerializer()

    # Query metrics
    total_queries = serializers.IntegerField()
    successful_queries = serializers.IntegerField()
    failed_queries = serializers.IntegerField()
    success_rate = serializers.FloatField()

    # Performance metrics
    avg_response_time_ms = serializers.FloatField()
    avg_confidence_score = serializers.FloatField()

    # Query type breakdown
    sql_queries_count = serializers.IntegerField()
    rag_queries_count = serializers.IntegerField()
    hybrid_queries_count = serializers.IntegerField()

    # Data source metrics
    total_data_sources = serializers.IntegerField()
    csv_tables = serializers.IntegerField()
    documents = serializers.IntegerField()

    # Session metrics
    total_sessions = serializers.IntegerField()
    active_sessions_24h = serializers.IntegerField()


class QueryCostBreakdownSerializer(serializers.Serializer):
    """Individual query cost breakdown"""
    query_id = serializers.IntegerField()
    query_text = serializers.CharField()
    prompt_tokens = serializers.IntegerField()
    completion_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    cost_usd = serializers.DecimalField(max_digits=10, decimal_places=6)
    query_type = serializers.CharField()
    created_at = serializers.DateTimeField()


# ============================================================================
# Frontend & Core Views
# ============================================================================
from django.contrib.auth.decorators import login_required
@never_cache
def index_view(request):
    """Serve the main frontend page"""
    token = request.session.get("token", "")
    return render(request, "index.html", {"token": token})

@never_cache
def user_view(request):
    """Serve the main frontend page"""
    token = request.session.get("token", "")
    return render(request, "User_page.html", {"token": token})

@never_cache
def developer_dashboard_view(request):
    """Serve the developer dashboard page"""
    return render(request, 'developer_dashboard.html')




class HealthCheckView(APIView):
    """Health check endpoint"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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


# ============================================================================
# Query Processing
# ============================================================================

class QueryProcessView(APIView):
    """Process a user query through the RAG pipeline"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = QueryRequestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start_time = time.time()
        query_text = serializer.validated_data['query']
        session_id = serializer.validated_data.get('session_id')

        try:
            # Process query through Master Orchestrator (supports SQL + RAG + Hybrid)
            result = master_orchestrator.process_query(
                query=query_text,
                session_id=session_id,
                use_classification=True,  # Enable query classification
                use_enhancement=True  # Enable query enhancement
            )

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Record metrics in background
            metrics_collector.record_query(
                response_time_ms / 1000,
                len(result.get("sources", [])) > 0,
                result.get("web_search_used", False)
            )

            # Determine query type
            classification = result.get("classification", {})
            sql_used = result.get("sql_used", False)
            rag_used = result.get("rag_used", False)

            if sql_used and rag_used:
                query_type = QueryAnalytics.QueryTypeChoices.HYBRID
            elif sql_used:
                query_type = QueryAnalytics.QueryTypeChoices.STRUCTURED_SQL
            elif rag_used:
                query_type = QueryAnalytics.QueryTypeChoices.SEMANTIC_RAG
            else:
                query_type = QueryAnalytics.QueryTypeChoices.UNKNOWN

            # Extract token usage from result (if available in metadata)
            # For now, we'll estimate based on query/response length
            # In production, you should extract this from LLM response metadata
            prompt_tokens = len(query_text.split()) * 2  # Rough estimate
            completion_tokens = len(result.get("answer", "").split()) * 2  # Rough estimate
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            cost_usd = token_tracker.calculate_cost(
                prompt_tokens,
                completion_tokens,
                model='gpt-4-turbo'
            )

            # Create QueryAnalytics record
            QueryAnalytics.objects.create(
                session_id=result["session_id"],
                query_text=query_text,
                query_type=query_type,
                classification_method=classification.get('method', 'keyword') if classification else 'keyword',
                response_time_ms=response_time_ms,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost_usd=cost_usd,
                tools_used=result.get("tools_used", []),
                sql_used=sql_used,
                rag_used=rag_used,
                web_search_used=result.get("web_search_used", False),
                sources_count=len(result.get("sources", [])),
                confidence_score=result.get("confidence_score", 0.5),
                success=True,
                error_message=None
            )

            # Log to JSON file
            query_logger.log_query(
                query_text=query_text,
                query_type=query_type,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                response_time_ms=response_time_ms,
                success=True,
                sql_used=sql_used,
                rag_used=rag_used,
                confidence_score=result.get("confidence_score", 0.5)
            )

            # Format response
            response_data = {
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "confidence_score": result.get("confidence_score", 0.5),
                "web_search_used": result.get("web_search_used", False),
                "session_id": result["session_id"],
                "query_type": query_type,
                "tokens_used": total_tokens,
                "cost_usd": str(cost_usd)
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            metrics_collector.record_error()

            # Record failed query analytics
            response_time_ms = int((time.time() - start_time) * 1000)
            QueryAnalytics.objects.create(
                session_id=session_id or 'unknown',
                query_text=query_text,
                query_type=QueryAnalytics.QueryTypeChoices.UNKNOWN,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )

            # Log failed query to JSON file
            query_logger.log_query(
                query_text=query_text,
                query_type='unknown',
                tokens_used=0,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=Decimal('0.0'),
                response_time_ms=response_time_ms,
                success=False,
                sql_used=False,
                rag_used=False,
                confidence_score=0.0
            )

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Document Upload
# ============================================================================

class DocumentUploadView(APIView):
    """Upload and process a document"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from pathlib import Path
            from .vectorstore import vector_store
            from .models import DataSourceStats

            uploaded_file = request.FILES['file']

            # Create uploaded_docs folder if it doesn't exist
            upload_dir = Path("./uploaded_docs")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Save file permanently to uploaded_docs/
            file_path = upload_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Process document with Docling
            documents = document_processor.load_document(str(file_path), use_docling=True)

            # Add metadata
            for doc in documents:
                doc.metadata['hard_kb'] = False
                doc.metadata['source_folder'] = str(upload_dir)
                doc.metadata['original_filename'] = uploaded_file.name

            # Add to vector store
            vector_store.add_documents(documents)

            # Track in database
            ext = file_path.suffix.lower()
            source_type_map = {
                '.pdf': 'pdf_document',
                '.docx': 'docx_document',
                '.doc': 'docx_document',
                '.txt': 'text_document',
                '.html': 'html_document'
            }
            source_type = source_type_map.get(ext, 'text_document')

            DataSourceStats.objects.update_or_create(
                source_name=uploaded_file.name,
                defaults={
                    'source_type': source_type,
                    'chunk_count': len(documents),
                    'file_size_kb': uploaded_file.size // 1024,
                    'metadata': {
                        'hard_kb': False,
                        'file_path': str(file_path)
                    }
                }
            )

            return Response({
                "status": "success",
                "message": f"Document {uploaded_file.name} uploaded and embedded successfully",
                "chunks_created": len(documents),
                "file_path": str(file_path)
            })

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TextUploadView(APIView):
    """Upload raw text content"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]
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


class CSVUploadView(APIView):
    """Upload CSV files and make them queryable via SQL"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from pathlib import Path

            uploaded_file = request.FILES['file']
            table_name = request.data.get('table_name', '')
            uploaded_by = request.data.get('uploaded_by', 'anonymous')

            # Validate CSV file
            if not uploaded_file.name.endswith('.csv'):
                return Response(
                    {"error": "File must be a CSV"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create uploaded_docs folder if it doesn't exist
            upload_dir = Path("./uploaded_docs")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Save file permanently to uploaded_docs/
            file_path = upload_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Generate table name
            final_table_name = table_name or sql_engine._sanitize_table_name(file_path.stem)

            # Add to SQL engine
            success = sql_engine.add_csv_file(str(file_path), final_table_name)

            if not success:
                return Response(
                    {"error": "Failed to load CSV into SQL engine"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Get table info
            schema = sql_engine.get_table_schema(final_table_name)

            # Save to database
            csv_upload = CSVUpload.objects.create(
                original_filename=uploaded_file.name,
                table_name=final_table_name,
                file_size_bytes=uploaded_file.size,
                row_count=schema['row_count'],
                column_count=len(schema['columns']),
                columns=[col['column_name'] for col in schema['columns']],
                uploaded_by=uploaded_by
            )

            # Update data source stats
            DataSourceStats.objects.update_or_create(
                source_name=final_table_name,
                defaults={
                    'source_type': 'csv_table',
                    'row_count': schema['row_count'],
                    'file_size_kb': uploaded_file.size // 1024,
                    'columns': [col['column_name'] for col in schema['columns']],
                    'metadata': {
                        'hard_kb': False,
                        'file_path': str(file_path),
                        'original_filename': uploaded_file.name
                    }
                }
            )

            return Response({
                "status": "success",
                "message": f"CSV uploaded and available as table '{final_table_name}'",
                "table_name": final_table_name,
                "row_count": schema['row_count'],
                "column_count": len(schema['columns']),
                "columns": [col['column_name'] for col in schema['columns']],
                "file_path": str(file_path)
            })

        except Exception as e:
            logger.error(f"CSV upload error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Memory & Sessions
# ============================================================================

class MemoryView(APIView):
    """Get conversation memory for a session"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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


# ============================================================================
# Metrics & System Status
# ============================================================================

class MetricsView(APIView):
    """Get system metrics"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

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


# ============================================================================
# Analytics Endpoints
# ============================================================================

class AnalyticsQueryStatsView(APIView):
    """Get query analytics and statistics"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

    def get(self, request):
        try:
            # Get time filter (default: last 7 days)
            days = int(request.query_params.get('days', 7))
            since = timezone.now() - timedelta(days=days)

            # Get analytics
            analytics = QueryAnalytics.objects.filter(created_at__gte=since)

            total_queries = analytics.count()
            sql_queries = analytics.filter(sql_used=True).count()
            rag_queries = analytics.filter(rag_used=True).count()
            hybrid_queries = analytics.filter(sql_used=True, rag_used=True).count()

            # Averages
            avg_response_time = analytics.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0
            avg_confidence = analytics.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0

            # Success rate
            successful = analytics.filter(success=True).count()
            success_rate = (successful / total_queries * 100) if total_queries > 0 else 0

            # Tool usage
            total_tools = sum(len(a.tools_used) for a in analytics)

            data = {
                'total_queries': total_queries,
                'sql_queries': sql_queries,
                'rag_queries': rag_queries,
                'hybrid_queries': hybrid_queries,
                'avg_response_time_ms': round(avg_response_time, 2),
                'avg_confidence_score': round(avg_confidence, 3),
                'success_rate': round(success_rate, 2),
                'total_tools_used': total_tools
            }

            serializer = AnalyticsQueryStatsSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsSourceStatsView(APIView):
    """Get data source statistics"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

    def get(self, request):
        try:
            sources = DataSourceStats.objects.all()

            total_sources = sources.count()
            csv_tables = sources.filter(source_type='csv_table').count()
            documents = sources.exclude(source_type='csv_table').count()
            total_rows = sources.aggregate(Sum('row_count'))['row_count__sum'] or 0
            total_chunks = sources.aggregate(Sum('chunk_count'))['chunk_count__sum'] or 0

            serializer = AnalyticsSourceStatsSerializer({
                'total_sources': total_sources,
                'csv_tables': csv_tables,
                'documents': documents,
                'total_rows': total_rows,
                'total_chunks': total_chunks,
                'sources': DataSourceStatsSerializer(sources, many=True).data
            })

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Source stats error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Reporting Endpoints
# ============================================================================

class SystemReportView(APIView):
    """Generate system health report"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

    def get(self, request):
        try:
            # Database stats
            db_stats = {
                'total_sessions': ConversationSession.objects.count(),
                'total_messages': ChatMessage.objects.count(),
                'total_analytics_records': QueryAnalytics.objects.count()
            }

            # Vector store stats
            try:
                parent_count = vector_store.parent_store._collection.count()
                child_count = vector_store.child_store._collection.count()
                vector_stats = {
                    'parent_chunks': parent_count,
                    'child_chunks': child_count,
                    'total_chunks': parent_count + child_count
                }
            except:
                vector_stats = {'error': 'Unable to get vector store stats'}

            # SQL engine stats
            sql_stats = {
                'available_tables': len(sql_engine.get_available_tables()),
                'tables': sql_engine.get_available_tables()
            }

            # Memory usage (placeholder - can be enhanced)
            memory_stats = {
                'active_sessions': ConversationSession.objects.count(),
                'recent_sessions': ConversationSession.objects.filter(
                    updated_at__gte=timezone.now() - timedelta(hours=24)
                ).count()
            }

            # Recent errors
            recent_errors = list(QueryAnalytics.objects.filter(
                success=False
            ).order_by('-created_at')[:10].values('error_message', 'created_at'))

            report = {
                'system_status': 'healthy',
                'uptime_info': {'checked_at': timezone.now().isoformat()},
                'database_stats': db_stats,
                'vector_store_stats': vector_stats,
                'sql_engine_stats': sql_stats,
                'memory_usage': memory_stats,
                'recent_errors': recent_errors
            }

            serializer = SystemReportSerializer(report)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"System report error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsageReportView(APIView):
    """Generate usage report"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]

    def get(self, request):
        try:
            # Get time period (default: 7 days)
            days = int(request.query_params.get('days', 7))
            since = timezone.now() - timedelta(days=days)

            analytics = QueryAnalytics.objects.filter(created_at__gte=since)

            # Query breakdown
            query_breakdown = {
                'sql': analytics.filter(query_type='structured_sql').count(),
                'rag': analytics.filter(query_type='semantic_rag').count(),
                'hybrid': analytics.filter(query_type='hybrid').count(),
                'unknown': analytics.filter(query_type='unknown').count()
            }

            # Tool usage
            tool_usage = {}
            for analytic in analytics:
                for tool in analytic.tools_used:
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1

            # Top queries (by frequency)
            top_queries_data = analytics.values('query_text').annotate(
                count=Count('query_text')
            ).order_by('-count')[:10]

            top_queries = [
                {'query': q['query_text'][:100], 'count': q['count']}
                for q in top_queries_data
            ]

            # Performance metrics
            performance = {
                'avg_response_time': analytics.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0,
                'max_response_time': analytics.aggregate(Avg('response_time_ms'))['response_time_ms__max'] or 0,
                'min_response_time': analytics.aggregate(Avg('response_time_ms'))['response_time_ms__min'] or 0
            }

            report = {
                'time_period': f'Last {days} days',
                'total_queries': analytics.count(),
                'unique_sessions': analytics.values('session_id').distinct().count(),
                'query_breakdown': query_breakdown,
                'tool_usage': tool_usage,
                'top_queries': top_queries,
                'performance_metrics': performance
            }

            serializer = UsageReportSerializer(report)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Usage report error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# SQL Export Endpoint
# ============================================================================

class SQLExportView(APIView):
    """Export SQL query results to CSV or JSON"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = SQLExportInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            query = serializer.validated_data['query']
            export_format = serializer.validated_data.get('format', 'csv')
            filename = serializer.validated_data.get('filename', f'export_{int(time.time())}')

            # Execute query
            result = sql_engine.execute_query(query, limit=10000)

            if not result['success']:
                return Response(
                    {"error": result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Export based on format
            if export_format == 'csv':
                return self._export_csv(result, filename)
            else:
                return self._export_json(result, filename)

        except Exception as e:
            logger.error(f"SQL export error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _export_csv(self, result, filename):
        """Export to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

        writer = csv.DictWriter(response, fieldnames=result['columns'])
        writer.writeheader()
        writer.writerows(result['data'])

        return response

    def _export_json(self, result, filename):
        """Export to JSON"""
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'

        json.dump(result['data'], response, indent=2)
        return response


# ============================================================================
# Developer Dashboard - Token Tracking
# ============================================================================
from rest_framework.permissions import IsAdminUser as isAdminUser

class TokenUsageView(APIView):
    """Get detailed token usage and cost statistics"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAdminUser]

    def get(self, request):
        """Get token usage statistics

        Query params:
            - days: Number of days to analyze (default: 7)
            - session_id: Filter by session (optional)
        """
        try:
            # Get time filter
            days = int(request.query_params.get('days', 7))
            since = timezone.now() - timedelta(days=days)

            # Get session filter
            session_id = request.query_params.get('session_id')

            # Build query
            analytics = QueryAnalytics.objects.filter(created_at__gte=since)
            if session_id:
                analytics = analytics.filter(session_id=session_id)

            # Aggregate token usage
            aggregates = analytics.aggregate(
                total_tokens=Sum('tokens_used'),
                total_prompt_tokens=Sum('prompt_tokens'),
                total_completion_tokens=Sum('completion_tokens'),
                total_cost=Sum('total_cost_usd'),
                queries_count=Count('id')
            )

            total_tokens = aggregates['total_tokens'] or 0
            total_prompt_tokens = aggregates['total_prompt_tokens'] or 0
            total_completion_tokens = aggregates['total_completion_tokens'] or 0
            total_cost = aggregates['total_cost'] or Decimal('0.0')
            queries_count = aggregates['queries_count'] or 0

            avg_tokens = (total_tokens / queries_count) if queries_count > 0 else 0
            avg_cost = (total_cost / queries_count) if queries_count > 0 else Decimal('0.0')

            data = {
                'total_tokens': total_tokens,
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'total_cost_usd': total_cost,
                'avg_tokens_per_query': round(avg_tokens, 2),
                'avg_cost_per_query': round(avg_cost, 6),
                'queries_count': queries_count
            }

            serializer = TokenUsageStatsSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Token usage error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeveloperDashboardView(APIView):
    """Comprehensive developer dashboard with all metrics"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAdminUser]

    def get(self, request):
        """Get comprehensive dashboard data

        Query params:
            - days: Number of days to analyze (default: 7)
        """
        try:
            # Get time filter
            days = int(request.query_params.get('days', 7))
            since = timezone.now() - timedelta(days=days)

            # Get analytics
            analytics = QueryAnalytics.objects.filter(created_at__gte=since)

            # Token metrics
            token_aggregates = analytics.aggregate(
                total_tokens=Sum('tokens_used'),
                total_prompt_tokens=Sum('prompt_tokens'),
                total_completion_tokens=Sum('completion_tokens'),
                total_cost=Sum('total_cost_usd'),
                queries_count=Count('id')
            )

            total_tokens = token_aggregates['total_tokens'] or 0
            total_prompt_tokens = token_aggregates['total_prompt_tokens'] or 0
            total_completion_tokens = token_aggregates['total_completion_tokens'] or 0
            total_cost = token_aggregates['total_cost'] or Decimal('0.0')
            queries_count = token_aggregates['queries_count'] or 0

            avg_tokens = (total_tokens / queries_count) if queries_count > 0 else 0
            avg_cost = (total_cost / queries_count) if queries_count > 0 else Decimal('0.0')

            # Query metrics
            total_queries = analytics.count()
            successful_queries = analytics.filter(success=True).count()
            failed_queries = analytics.filter(success=False).count()
            success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

            # Performance metrics
            avg_response_time = analytics.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0
            avg_confidence = analytics.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0

            # Query type breakdown
            sql_count = analytics.filter(sql_used=True, rag_used=False).count()
            rag_count = analytics.filter(rag_used=True, sql_used=False).count()
            hybrid_count = analytics.filter(sql_used=True, rag_used=True).count()

            # Data source metrics
            sources = DataSourceStats.objects.all()
            total_sources = sources.count()
            csv_tables = sources.filter(source_type='csv_table').count()
            documents = sources.exclude(source_type='csv_table').count()

            # Session metrics
            sessions = ConversationSession.objects.all()
            total_sessions = sessions.count()
            active_24h = sessions.filter(updated_at__gte=timezone.now() - timedelta(hours=24)).count()

            data = {
                'token_usage': {
                    'total_tokens': total_tokens,
                    'total_prompt_tokens': total_prompt_tokens,
                    'total_completion_tokens': total_completion_tokens,
                    'total_cost_usd': total_cost,
                    'avg_tokens_per_query': round(avg_tokens, 2),
                    'avg_cost_per_query': round(avg_cost, 6),
                    'queries_count': queries_count
                },
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'failed_queries': failed_queries,
                'success_rate': round(success_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'avg_confidence_score': round(avg_confidence, 3),
                'sql_queries_count': sql_count,
                'rag_queries_count': rag_count,
                'hybrid_queries_count': hybrid_count,
                'total_data_sources': total_sources,
                'csv_tables': csv_tables,
                'documents': documents,
                'total_sessions': total_sessions,
                'active_sessions_24h': active_24h
            }

            serializer = DeveloperDashboardSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueryCostBreakdownView(APIView):
    """Get cost breakdown for individual queries"""
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [isAdminUser]

    def get(self, request):
        """Get detailed cost breakdown per query

        Query params:
            - days: Number of days to analyze (default: 7)
            - limit: Max number of queries to return (default: 50)
            - order: Order by 'cost' or 'date' (default: cost)
        """
        try:
            # Get filters
            days = int(request.query_params.get('days', 7))
            limit = int(request.query_params.get('limit', 50))
            order = request.query_params.get('order', 'cost')

            since = timezone.now() - timedelta(days=days)

            # Get queries
            analytics = QueryAnalytics.objects.filter(created_at__gte=since)

            # Order
            if order == 'cost':
                analytics = analytics.order_by('-total_cost_usd')
            else:
                analytics = analytics.order_by('-created_at')

            # Limit
            analytics = analytics[:limit]

            # Build response
            breakdown = []
            for query in analytics:
                breakdown.append({
                    'query_id': query.id,
                    'query_text': query.query_text[:100],  # Truncate for display
                    'prompt_tokens': query.prompt_tokens,
                    'completion_tokens': query.completion_tokens,
                    'total_tokens': query.tokens_used,
                    'cost_usd': query.total_cost_usd,
                    'query_type': query.query_type,
                    'created_at': query.created_at
                })

            serializer = QueryCostBreakdownSerializer(breakdown, many=True)
            return Response({
                'queries': serializer.data,
                'total_queries': len(breakdown)
            })

        except Exception as e:
            logger.error(f"Cost breakdown error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
