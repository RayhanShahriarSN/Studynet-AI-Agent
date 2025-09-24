from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.contrib import messages as django_messages
from .forms import LLMConfigForm, QuestionForm, PDFUploadForm
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from openai import AzureOpenAI
import requests
from django.utils.text import get_valid_filename
import os
from pathlib import Path
import markdown
from openai import OpenAI
import re
import json
import PyPDF2
from .forms import QuestionForm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator




SESSION_KEY = "rag_chat_history"
PDF_DIR = settings.MEDIA_ROOT / "pdfs"

class ClearChat_admin(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_admin")


RAG_PDF_DIR = settings.RAG_PDF_DIR

class UploadPDF(View):
    template_name = "uploadPDF2.html"
   

    def get(self, request):
        form = PDFUploadForm()
        RAG_PDF_DIR.mkdir(parents=True, exist_ok=True)

        pdf_files = []
        for pdf_path in RAG_PDF_DIR.glob("*.pdf"):
            pdf_files.append({
                "name": pdf_path.name,
                "url": f"{settings.MEDIA_URL}pdfs/{pdf_path.name}"
            })

        return render(request, self.template_name, {
            "form": form,
            "pdf_files": pdf_files
        })

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        pdf_file = form.cleaned_data["pdf_file"]
        
        RAG_PDF_DIR.mkdir(parents=True, exist_ok=True)

        base_name, ext = os.path.splitext(pdf_file.name)
        base_name = get_valid_filename(base_name) or "document"
        ext = ".pdf"
        candidate = RAG_PDF_DIR / f"{base_name}{ext}"
        i = 1
        while candidate.exists():
            candidate = RAG_PDF_DIR / f"{base_name}_{i}{ext}"
            i += 1

        with open(candidate, "wb+") as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)

        messages.success(request, f"PDF uploaded: {candidate.name}")
        return redirect("upload_pdf")


SESSION_KEY = "chat_history"
load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_API_KEY"] = API_KEY

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT

DEPLOYMENT = os.getenv("CHAT_MODEL_DEPLOYMENT")
os.environ["CHAT_MODEL_DEPLOYMENT"] = DEPLOYMENT

if not API_KEY or not ENDPOINT or not DEPLOYMENT:
    raise ValueError(
        "Azure OpenAI configuration missing. Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT in your environment or .env file."
    )
    

class ClearChatPhi(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_phi")
    


    





@method_decorator(csrf_protect, name='dispatch')
class QnAPagePhi_admin(View):
    template_name = "QnA_admin2.html"

    def __init__(self):
        super().__init__()
        self.pdf_texts = self._load_all_pdfs()

    def _load_all_pdfs(self):
        
        texts = []
        if not PDF_DIR.exists():
            return texts

        for pdf_file in PDF_DIR.glob("*.pdf"):
            try:
                with open(pdf_file, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pdf_text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            pdf_text += page_text + "\n"
                    texts.append({"filename": pdf_file.name, "content": pdf_text})
            except Exception as e:
                print(f"Failed to read {pdf_file.name}: {e}")
        return texts


    def clean_response_text(self, text):
        """Clean AI response: remove markdown, HTML, tables, preserve bullets and numbered lists."""
        if not text:
            return text

        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)

        # Remove headers
        text = re.sub(r'#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)

        # Remove inline code and code blocks
        text = re.sub(r'`{3}[\s\S]*?`{3}', '', text)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove Markdown tables
        text = re.sub(r'\|.*?\|', '', text)  # Remove table rows
        text = re.sub(r'-{3,}', '', text)    # Remove table separators

        # Replace bullets with simple •
        text = re.sub(r'^[-•*]\s*', r'• ', text, flags=re.MULTILINE)

        # Ensure numbered lists are on new lines
        text = re.sub(r'(\d+)\.\s*', r'\n\1. ', text)

        # Collapse multiple blank lines into one
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # Strip leading/trailing spaces
        text = text.strip()

        return text




    def _ask_azure_openai(self, question, context):
        
        if not ENDPOINT or not DEPLOYMENT or not API_KEY:
            raise ValueError("Azure OpenAI configuration missing. Check ENDPOINT, DEPLOYMENT, and API_KEY.")

       
        url = f"{ENDPOINT.rstrip('/')}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview"
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Answer based on the provided PDF content. Provide the output in plain text only, do not use tables or Markdown tables. Use bullets or numbered lists instead."},
                {"role": "user", "content": f"PDF Content:\n{context}\n\nQuestion: {question}"}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }

        print(f"Sending request to Azure OpenAI at {url} ...")
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f"Azure OpenAI error {response.status_code}: {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        total_tokens_used = result.get("usage", {}).get("total_tokens", 0) #if missing, 0 will be set
        return content, total_tokens_used
    

    

    def get(self, request):
        ask_form = QuestionForm()
        chat = request.session.get(SESSION_KEY, [])
        return render(request, self.template_name, {
            "ask_form": ask_form,
            "chat": chat,
            "status_msg": "Backend ready" if API_KEY else "Azure API key missing"
        })

    def post(self, request):
        ask_form = QuestionForm(request.POST)
        chat = request.session.get(SESSION_KEY, [])

        if ask_form.is_valid():
            question = ask_form.cleaned_data["question"]
            chat.append({"who": "user", "text": question})

            
            try:
                
                    relevant_texts = []
                    for pdf in self.pdf_texts:
                        if any(word.lower() in pdf['content'].lower() for word in question.split()):
                            relevant_texts.append(f"{pdf['filename']}:\n{pdf['content']}")

                    context = "\n\n".join(relevant_texts) or "No relevant content found in PDFs."

                    
                    # Step 2: Ask Azure OpenAI via REST API
                    answer, new_tokens = self._ask_azure_openai(question, context)

                    request.user.tokens_used = request.user.tokens_used + new_tokens
                    print(request.user.tokens_used)
                    request.user.save()

    
                    answer_clean = self.clean_response_text(answer)
                    chat.append({"who": "bot", "text": answer_clean})

            except Exception as e:
                    error_msg = f"Azure OpenAI error: {e}"
                    chat.append({"who": "bot", "text": error_msg})
                    django_messages.error(request, error_msg)

                # Save chat session
            request.session[SESSION_KEY] = chat
            request.session.modified = True

        return render(request, self.template_name, {
                "ask_form": QuestionForm(),
                "chat": chat,
                "status_msg": "Backend ready" if API_KEY else "Azure API key missing"
        })
    


    
class ClearChatPhiAdmin(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_phi_admin")
    




import uuid
import time
import requests
from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.contrib import messages

from .forms import  QuestionForm, PDFUploadForm

SESSION_KEY = "chat_history"

import re

import time
import uuid
import requests
from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .forms import QuestionForm, LLMConfigForm
from .memory import memory_manager


SESSION_KEY = "chat_history"
import uuid
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views import View
from .forms import QuestionForm, LLMConfigForm
from .memory import memory_manager  # adjust import if needed


# Define clean_response_text function
def clean_response_text(text: str) -> str:
    """Clean AI response text for display."""
    if not text:
        return ""
    # Remove extra whitespace and line breaks
    return " ".join(text.split())


@method_decorator(csrf_protect, name='dispatch')
class QnAPagePhi(View):
    template_name = "QnA_user.html"

    def get(self, request):
        # Ensure session_id exists
        if "session_id" not in request.session:
            request.session["session_id"] = str(uuid.uuid4())

        session_id = request.session["session_id"]

        # Load memory messages
        memory_vars = memory_manager.get_memory_variables(session_id)
        chat_history = memory_vars.get("chat_history", [])

        # Convert LangChain BaseMessage objects to template-friendly dict
        chat = []
        for msg in chat_history:
            if msg is None:
                continue
            if hasattr(msg, "content"):
                if msg.__class__.__name__ == "HumanMessage":
                    chat.append({"who": "user", "text": msg.content})
                elif msg.__class__.__name__ == "AIMessage":
                    chat.append({"who": "bot", "text": clean_response_text(msg.content)})

        # Last 10 user queries safely
        user_messages = [m["text"] for m in chat if m["who"] == "user"]
        user_messages = list(user_messages)  # Ensure it's a list
        recent_queries = user_messages[-10:] if len(user_messages) >= 10 else user_messages

        context = {
            "chat": chat,
            "ask_form": QuestionForm(),
            "llm_form": LLMConfigForm(),
            "status_msg": "Backend ready",
            "session_id": session_id,
            "recent_queries": recent_queries,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        session_id = request.session.get("session_id", str(uuid.uuid4()))
        ask_form = QuestionForm(request.POST)

        if ask_form.is_valid():
            question = ask_form.cleaned_data["question"]

            # Add user message to memory
            memory_manager.add_message(session_id, "user", question)

            # Call RAG backend
            answer, sources, confidence, web_search_used = self.query_rag_backend(
                question, session_id
            )

            # Clean AI response
            answer_clean = clean_response_text(answer)

            # Add AI message to memory
            memory_manager.add_message(session_id, "assistant", answer_clean)

            # Redirect to avoid form resubmission
            return redirect("rag_qna_page_phi")

        return self.get(request)

    def query_rag_backend(self, question, session_id):
        """Send question to RAG API backend"""
        try:
            url = f"{settings.RAG_API_BASE_URL}/rag/query/"
            payload = {
                "query": question,
                "session_id": session_id,
                "use_web_search": True,
                "enhance_formatting": True,
            }
            response = requests.post(url, json=payload, timeout=30)
            if response.ok:
                data = response.json()
                return (
                    data.get("answer", ""),
                    data.get("sources", []),
                    data.get("confidence_score", None),
                    data.get("web_search_used", False),
                )
            return f"Error: {response.text}", [], None, False
        except Exception as e:
            return f"Error: {str(e)}", [], None, False

                  

class ClearChatAPI(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        #messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_api")





# Django REST API views for RAG backend
import os
import time
import tempfile
import logging
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from templates import *
from django.contrib import messages

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
from .memory import memory_manager
from .utils import document_processor, metrics_collector, response_formatter
from .config import config
from .vectorstore import vector_store

logger = logging.getLogger(__name__)

# Define the session key for chat messages
SESSION_KEY = "chat_messages"


def index_view(request):
    """Serve the main frontend page"""
    return render(request, 'QnA_user.html')


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
            # Process query through RAG agent with enhanced formatting
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
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "confidence_score": result.get("confidence_score", 0.5),
                "web_search_used": result.get("web_search_used", False),
                "session_id": result["session_id"]
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
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Process document
            documents = document_processor.load_document(tmp_file_path)
            
            # Add to vector store
            success = rag_agent.add_documents(documents)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            if success:
                return Response({
                    "status": "success",
                    "message": f"Document {uploaded_file.name} processed successfully",
                    "chunks_created": len(documents)
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



class ClearChatAPI(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_phi")