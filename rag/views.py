import os
import re
import time
import json
import uuid
import logging
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime

import requests
import numpy as np
import PyPDF2
import markdown
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rag.utils import ResponseEnhancer
 
from openai import AzureOpenAI, OpenAI
from .utils import (
    document_processor,
    query_optimizer,
    response_formatter,
    metrics_collector,
    response_enhancer
)
from .forms import QuestionForm, LLMConfigForm, PDFUploadForm
from .agent import rag_agent
from .memory import memory_manager
from .utils import document_processor, metrics_collector, response_formatter
from .vectorstore import vector_store
from .config import config
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


SESSION_KEY = "rag_chat_history"
PDF_DIR = settings.MEDIA_ROOT / "pdfs"
RAG_PDF_DIR = settings.RAG_PDF_DIR



def clean_response_text(text: str) -> str:
    """Enhanced clean AI response text for display in template with beautiful formatting."""
    if not text:
        return ""

    # Headings
    text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

    # Blockquotes
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)

    # Bold, Italic, Code
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    # Lists
    text = re.sub(r'^[-*•]\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    text = re.sub(r'^(\d+)\.\s+(.+)$', r'<li>\2</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>)', r'<ol>\1</ol>', text, flags=re.DOTALL)

    # Split into paragraphs for long answers
    paragraphs = re.split(r'\n\n+', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    text = ''.join([f'<p>{p.replace('\n', '<br>')}</p>' for p in paragraphs])

    return text

MAX_TOKENS = 6000
RAG_PDF_DIR = settings.RAG_PDF_DIR
SESSION_KEY = "chat_history"


# -------------------------
# PDF Upload View
# -------------------------
class UploadPDF(View):
    template_name = "uploadPDF.html"

    def get(self, request):
        form = PDFUploadForm()
        RAG_PDF_DIR.mkdir(parents=True, exist_ok=True)

        allowed_files = ["*.pdf", "*.csv"]
        uploaded_files = []
        for pattern in allowed_files:
            for file_path in RAG_PDF_DIR.glob(pattern):
                relative_url = f"{settings.MEDIA_URL}pdfs/{file_path.name}"
                uploaded_files.append({
                    "name": file_path.name,
                    "url": relative_url,
                    "abs_url": request.build_absolute_uri(relative_url)
                })
        return render(request, self.template_name, {"form": form, "pdf_files": uploaded_files})
        
    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        uploaded_file = form.cleaned_data["pdf_file"]
        RAG_PDF_DIR.mkdir(parents=True, exist_ok=True)

        base_name, ext = os.path.splitext(uploaded_file.name)
        base_name = get_valid_filename(base_name) or "document"
        ext = ext.lower()
        candidate = RAG_PDF_DIR / f"{base_name}{ext}"
        i = 1
        while candidate.exists():
            candidate = RAG_PDF_DIR / f"{base_name}_{i}{ext}"
            i += 1

        # Save file
        with open(candidate, "wb+") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        messages.success(request, f"File uploaded: {candidate.name}")

        # Process file and add to RAG vector store
        try:
            documents = document_processor.load_document(str(candidate))
            if not documents:
                messages.warning(request, f"{candidate.name} uploaded but could not extract content.")
            else:
                success = rag_agent.add_documents(documents)
                if success:
                    messages.success(request, f"{candidate.name} content added to knowledge base successfully!")
                else:
                    messages.error(request, f"Failed to add {candidate.name} content to vector store.")
        except Exception as e:
            messages.error(request, f"Error processing {candidate.name}: {str(e)}")

        return redirect("upload_pdf")


# -------------------------
# Admin QnA View
# -------------------------
@method_decorator(user_passes_test(lambda u: u.is_admin, login_url='forbidden'), name='dispatch')
class QnAAdmin(View):
    template_name = "QnA_admin.html"

    def get(self, request):
        # Ensure admin session
        if "session_id" not in request.session:
            request.session["session_id"] = str(uuid.uuid4())
        session_id = request.session["session_id"]

        memory_vars = memory_manager.get_memory_variables(session_id)
        chat_history = memory_vars.get("chat_history", [])

        chat = []
        for msg in chat_history:
            if msg is None or not hasattr(msg, "content"):
                continue
            if msg.__class__.__name__ == "HumanMessage":
                chat.append({"who": "user", "text": msg.content})
            elif msg.__class__.__name__ == "AIMessage":
                chat.append({"who": "bot", "text": clean_response_text(msg.content)})

        user_messages = [m["text"] for m in chat if m["who"] == "user"]
        recent_queries = user_messages[-10:] if len(user_messages) > 10 else user_messages

        context = {
            "chat": chat,
            "ask_form": QuestionForm(),
            "llm_form": LLMConfigForm(),
            "session_id": session_id,
            "recent_queries": recent_queries,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to use the chat service.")
            return redirect("login_page")

        ask_form = QuestionForm(request.POST)
        if ask_form.is_valid():
            question = ask_form.cleaned_data["question"]
            last_processed_question = request.session.get("last_processed_question")
            if last_processed_question == question:
                return redirect("rag_admin")
            request.session["last_processed_question"] = question

            session_id = request.session.get("session_id", str(uuid.uuid4()))
            request.session["session_id"] = session_id

            answer, sources, confidence, web_search_used, tokens_used = self.query_rag_backend(
                question, session_id
            )

            if tokens_used and tokens_used > 0:
                request.user.tokens_used += tokens_used
                request.user.save()

            if "last_processed_question" in request.session:
                del request.session["last_processed_question"]

            return redirect("rag_admin")

        return self.get(request)

    def query_rag_backend(self, question, session_id):
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
                    data.get("tokens_used", 0),
                )
            return f"Error: {response.text}", [], None, False, 0
        except Exception as e:
            return f"Error: {str(e)}", [], None, False, 0


@method_decorator(csrf_protect, name="dispatch")
class ClearChatAdmin(View):
    def post(self, request):
        try:
            session_id = request.session.get("session_id")
            if session_id:
                memory_manager.clear_session(session_id)

            if SESSION_KEY in request.session:
                request.session[SESSION_KEY] = []
                request.session.modified = True

            if "chat_history" in request.session:
                request.session["chat_history"] = []
                request.session.modified = True
        except Exception as e:
            print(f"Error clearing chat: {e}")

        return redirect("rag_admin")


# -------------------------
# User QnA View
# -------------------------


def index_view(request):
    """Serve the main frontend page"""
    return render(request, 'index.html')

import uuid
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.conf import settings
import requests

from .forms import QuestionForm, LLMConfigForm
from .memory import memory_manager
from rag.utils import ResponseEnhancer

MAX_TOKENS = 20000

@method_decorator([csrf_protect], name="dispatch")
class QnAUser(View):
    template_name = "QnA_user.html"

    # -----------------------------
    # Helper Methods
    # -----------------------------
    def get_system_status(self):
        try:
            # API health
            url = f"{settings.RAG_API_BASE_URL}/rag/health/"
            response = requests.get(url, timeout=5)
            api_status = "Online" if response.ok else "Offline"
            api_status_class = "online" if response.ok else "offline"

            # KB status
            kb_url = f"{settings.RAG_API_BASE_URL}/rag/knowledge-base/status/"
            kb_response = requests.get(kb_url, timeout=5)
            kb_documents = kb_response.json().get("total_documents", 0) if kb_response.ok else 0

        except Exception as e:
            print(f"System status error: {e}")
            api_status, api_status_class, kb_documents = "Offline", "offline", 0

        return {
            "api_status": api_status,
            "api_status_class": api_status_class,
            "kb_documents": kb_documents,
        }

    # def get_recent_queries(self, session_id):
    #     try:
    #         memory_vars = memory_manager.get_memory_variables(session_id)
    #         chat_history = memory_vars.get("chat_history", [])
    #         user_queries = [
    #             msg.content for msg in chat_history
    #             if hasattr(msg, "content") and msg.__class__.__name__ == "HumanMessage"
    #         ]
    #         return user_queries[-5:] if len(user_queries) > 5 else user_queries
    #     except Exception as e:
    #         print(f"Recent queries error: {e}")
    #         return []

 

    def query_rag_backend(self, question, session_id, use_web_search=True, enhance_formatting=True):
        try:
            url = f"{settings.RAG_API_BASE_URL}/rag/query/"
            payload = {
                "query": question,
                "session_id": session_id,
                "use_web_search": use_web_search,
                "enhance_formatting": enhance_formatting

            }
            response = requests.post(url, json=payload, timeout=30)
            print(response.json())
            if response.ok:
                data = response.json()
                return (
                    data.get("answer", "No response received."),
                    data.get("sources", []),
                    data.get("confidence_score", None),
                    data.get("web_search_used", False),
                    data.get("tokens_used", 0),
                )
            return f"Backend error: {response.status_code}", [], None, False, 0
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again.", [], None, False, 0
        except requests.exceptions.ConnectionError:
            return "Cannot connect to backend service.", [], None, False, 0
        except Exception as e:
            print(f"RAG backend exception: {e}")
            return f"Error: {str(e)}", [], None, False, 0

    # -----------------------------
    # GET Method
    # -----------------------------
    def get(self, request):
        session_id = request.session.get("session_id", str(uuid.uuid4())) #Checking If already has a session id, otherwise create 1
        request.session["session_id"] = session_id #Saving it into the Django session


#   memory_vars → this is usually a dictionary with things like:

# {
#     "chat_history": [
#         HumanMessage(content="Hello"),
#         AIMessage(content="Hi there, how can I help?"),
#         ...
#     ],
#     "some_other_var": ...
# }

        # Load chat
        memory_vars = memory_manager.get_memory_variables(session_id) #Retrieving the memory variables for the given session_id
        chat_history = memory_vars.get("chat_history", [])
        chat = []
        seen_messages = set() #To avoid duplicates

        for msg in chat_history: #Iterating through the chat history messages
            if msg is None or not hasattr(msg, "content"):  #Skip if message is None or has no content
                continue
            msg_id = f"{msg.content}_{msg.__class__.__name__}" #Creating a unique ID for each message based on its content and type
             #Skip if this message has already been processed (to avoid duplicates)
            if msg_id in seen_messages: 
                continue
            seen_messages.add(msg_id) #Mark this message as seen

            if msg.__class__.__name__ == "HumanMessage":
                chat.append({"who": "user", "text": msg.content, "timestamp": getattr(msg, "timestamp", None)}) #If it's a user message, add to chat as user
            elif msg.__class__.__name__ == "AIMessage":
                chat.append({
                    "who": "bot",
                    "text": getattr(msg, "content", ""),
                    "sources": getattr(msg, "sources", []) or [],
                    "llm": getattr(msg, "model", "StudyNet AI") or "StudyNet AI",
                    "confidence": getattr(msg, "confidence", 0) or 0,
                    "web_search": getattr(msg, "web_search_used", False),
                    "timestamp": getattr(msg, "timestamp", None),
                })

        # System status and recent queries
        system_status = self.get_system_status()
       

        tokens_used = getattr(request.user, "tokens_used", 0)
        tokens_remaining = MAX_TOKENS - tokens_used
        status_msg = f"Backend ready - Tokens remaining: {max(0, tokens_remaining)}"

        context = {
            "chat": chat,
            "ask_form": QuestionForm(),
            "llm_form": LLMConfigForm(),
            "status_msg": status_msg,
            "session_id": session_id,
           
            "tokens_remaining": max(0, tokens_remaining),
            "max_tokens": MAX_TOKENS,
            "api_status": system_status["api_status"],
            "api_status_class": system_status["api_status_class"],
            "kb_documents": system_status["kb_documents"],
        }
        return render(request, self.template_name, context)

    # -----------------------------
    # POST Method
    # -----------------------------
    def post(self, request):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to use the chat service.")
            return redirect("login_page")

        ask_form = QuestionForm(request.POST) #Binding the form with the POST data
        if not ask_form.is_valid():
            return self.get(request) #If form invalid, re-render page with errors

        question = ask_form.cleaned_data["question"] #Extracting the cleaned question from the form
        use_web_search = ask_form.cleaned_data.get("use_web_search", True) #Extracting web search preference
        enhance_formatting = ask_form.cleaned_data.get("enhance_formatting", True) #Extracting formatting preference

        session_id = request.session.get("session_id", str(uuid.uuid4())) #Get or create session ID
        request.session["session_id"] = session_id

        # Token check
        tokens_used = getattr(request.user, "tokens_used", 0) #Get user's used tokens
        if tokens_used >= MAX_TOKENS: #If user has exceeded max tokens
            memory_manager.add_message(session_id, "user", question) #Log user's question
            memory_manager.add_message(session_id, "assistant", f"Maximum tokens reached. You have used all {MAX_TOKENS} tokens.")
            messages.warning(request, f"Token limit reached: {MAX_TOKENS} tokens.")
            return redirect("rag_user")

        # Prevent duplicate submissions
        last_question = request.session.get("last_question") #Get last question from session
        if last_question == question:
            return redirect("rag_user")
        request.session["last_question"] = question

        # Query backend
        answer, sources, confidence, web_search_used, tokens_consumed = self.query_rag_backend(
            question, session_id, use_web_search, enhance_formatting
        )

        # Convert markdown to HTML
        answer_html = ResponseEnhancer._convert_markdown_to_html(answer)

        # Update tokens
        if tokens_consumed > 0:
            request.user.tokens_used = tokens_used + tokens_consumed
            request.user.save()

        # Save messages in memory
        memory_vars = memory_manager.get_memory_variables(session_id)
        chat_history = memory_vars.get("chat_history", [])
        print(chat_history)

        if not (chat_history and hasattr(chat_history[-1], "content") and
                chat_history[-1].__class__.__name__ == "HumanMessage" and
                chat_history[-1].content == question):
            memory_manager.add_message(session_id, "user", question)

        if not (chat_history and hasattr(chat_history[-1], "content") and
                chat_history[-1].__class__.__name__ == "AIMessage" and
                chat_history[-1].content == answer_html):
            ai_message = memory_manager.add_message(session_id, "assistant", answer_html)
            if hasattr(ai_message, "__dict__"):
                ai_message.sources = sources
                ai_message.model = "StudyNet AI"
                ai_message.confidence = confidence * 100 if confidence else None
                ai_message.web_search_used = web_search_used

        # Remove last_question to allow new submissions
        request.session.pop("last_question", None)
        messages.success(request, f"Response generated successfully. Tokens used: {tokens_consumed}")
        return redirect("rag_user")



@method_decorator(csrf_protect, name="dispatch")
class ClearChatUser(View):
    def post(self, request):
        try:
            session_id = request.session.get("session_id")
            if session_id:
                memory_manager.clear_session(session_id)

            if SESSION_KEY in request.session:
                request.session[SESSION_KEY] = []
                request.session.modified = True

            if "chat_history" in request.session:
                request.session["chat_history"] = []
                request.session.modified = True
        except Exception as e:
            print(f"Error clearing chat: {e}")
            messages.error(request, f"Error clearing chat: {str(e)}")

        return redirect("rag_user")







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