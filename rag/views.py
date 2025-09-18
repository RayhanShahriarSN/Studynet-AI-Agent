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



FASTAPI_URL = "http://127.0.0.1:8000"  # FastAPI backend URL
SESSION_KEY = "rag_chat_history"
PDF_DIR = settings.MEDIA_ROOT / "pdfs"


class QnAPage(View):
    template_name = "QnA.html"

    def get(self, request):
        try:
            resp = requests.get(f"{FASTAPI_URL}/llm-options/")
            options = resp.json()
        except Exception as e:
            options = {"providers": {}, "current": {}}
            messages.warning(request, f"Could not reach backend: {e}")

        providers_list = []
        for key, val in options.get("providers", {}).items():
            providers_list.append({"name": key, "models": val.get("models", ["default-model"])})

        current_provider = request.session.get("current_provider") or options.get("current", {}).get("provider")
        if not current_provider or current_provider not in [p["name"] for p in providers_list]:
            current_provider = providers_list[0]["name"] if providers_list else "openai"

        provider_models = next((p["models"] for p in providers_list if p["name"] == current_provider), ["default-model"])
        current_model = request.session.get("current_model") or options.get("current", {}).get("model")
        if current_model not in provider_models:
            current_model = provider_models[0]

        llm_form = LLMConfigForm(initial={"llm_provider": current_provider, "model_name": current_model})
        ask_form = QuestionForm()
        chat = request.session.get(SESSION_KEY, [])

        return render(request, self.template_name, {
            "providers": providers_list,
            "current_provider": current_provider,
            "provider_models": provider_models,
            "default_model": current_model,
            "llm_form": llm_form,
            "ask_form": ask_form,
            "chat": chat,
            "status_msg": "Backend ready"
        })

    def post(self, request):
        ask_form = QuestionForm(request.POST)
        if not ask_form.is_valid():
            messages.error(request, "Invalid question.")
            return redirect("rag_qna_page")

        question = ask_form.cleaned_data["question"]

        provider = request.session.get("current_provider", "openai")
        model_name = request.session.get("current_model", "gpt-4o-mini")

        try:
            resp = requests.post(f"{FASTAPI_URL}/ask/", json={
                "question": question,
                "llm_provider": provider,
                "model_name": model_name
            })
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer", "No answer")
            llm_used = data.get("llm_used", "")

            # ✅ Convert Markdown to HTML
            answer_html = markdown.markdown(answer)

        except Exception as e:
            messages.error(request, f"Backend error: {e}")
            return redirect("rag_qna_page")

        chat = request.session.get(SESSION_KEY, [])
        chat.append({"who": "user", "text": question})
        chat.append({"who": "bot", "text": answer_html, "llm": llm_used})
        request.session[SESSION_KEY] = chat
        request.session.modified = True

        return redirect("rag_qna_page")


# -----------------------------
# Admin QnA Page
# -----------------------------
class QnAPage_admin(View):
    template_name = "QnA_admin.html"

    def get(self, request):
        try:
            resp = requests.get(f"{FASTAPI_URL}/llm-options/")
            options = resp.json()
        except Exception as e:
            options = {"providers": {}, "current": {}}
            messages.warning(request, f"Could not reach backend: {e}")

        providers_list = []
        for key, val in options.get("providers", {}).items():
            providers_list.append({"name": key, "models": val.get("models", ["default-model"])})

        current_provider = request.session.get("current_provider") or options.get("current", {}).get("provider")
        if not current_provider or current_provider not in [p["name"] for p in providers_list]:
            current_provider = providers_list[0]["name"] if providers_list else "openai"

        provider_models = next((p["models"] for p in providers_list if p["name"] == current_provider), ["default-model"])
        current_model = request.session.get("current_model") or options.get("current", {}).get("model")
        if current_model not in provider_models:
            current_model = provider_models[0]

        llm_form = LLMConfigForm(initial={"llm_provider": current_provider, "model_name": current_model})
        ask_form = QuestionForm()
        chat = request.session.get(SESSION_KEY, [])

        return render(request, self.template_name, {
            "providers": providers_list,
            "current_provider": current_provider,
            "provider_models": provider_models,
            "default_model": current_model,
            "llm_form": llm_form,
            "ask_form": ask_form,
            "chat": chat,
            "status_msg": "Backend ready"
        })

    def post(self, request):
        ask_form = QuestionForm(request.POST)
        if not ask_form.is_valid():
            messages.error(request, "Invalid question.")
            return redirect("rag_qna_page_admin")

        question = ask_form.cleaned_data["question"]

        provider = request.session.get("current_provider", "openai")
        model_name = request.session.get("current_model", "gpt-4o-mini")

        try:
            resp = requests.post(f"{FASTAPI_URL}/ask/", json={
                "question": question,
                "llm_provider": provider,
                "model_name": model_name
            })
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer", "No answer")
            llm_used = data.get("llm_used", "")

            # ✅ Convert Markdown to HTML
            answer_html = markdown.markdown(answer)

        except Exception as e:
            messages.error(request, f"Backend error: {e}")
            return redirect("rag_qna_page_admin")

        chat = request.session.get(SESSION_KEY, [])
        chat.append({"who": "user", "text": question})
        chat.append({"who": "bot", "text": answer_html, "llm": llm_used})
        request.session[SESSION_KEY] = chat
        request.session.modified = True

        return redirect("rag_qna_page_admin")





class ConfigureLLM(View):
    def post(self, request):
        form = LLMConfigForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid configuration.")
            return redirect("rag_qna_page")

        provider = form.cleaned_data["llm_provider"]
        model_name = form.cleaned_data["model_name"]

        try:
            headers = {"Authorization": "Bearer admin_secret_token_2024"}
            resp = requests.post(
                f"{FASTAPI_URL}/configure-llm/",
                json={"llm_provider": provider, "model_name": model_name},
                headers=headers,
                timeout=5
            )
            resp.raise_for_status()
            messages.success(request, f"LLM configured: {provider.title()} ({model_name})")

            # Save in session
            request.session["current_provider"] = provider
            request.session["current_model"] = model_name
            request.session.modified = True

        except requests.RequestException as e:
            messages.warning(request, f"Could not configure LLM: {e}")

        return redirect("rag_qna_page")
    
    
class ConfigureLLM_admin(View):
    def post(self, request):
        form = LLMConfigForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid configuration.")
            return redirect("rag_qna_page")

        provider = form.cleaned_data["llm_provider"]
        model_name = form.cleaned_data["model_name"]

        try:
            headers = {"Authorization": "Bearer admin_secret_token_2024"}
            resp = requests.post(
                f"{FASTAPI_URL}/configure-llm/",
                json={"llm_provider": provider, "model_name": model_name},
                headers=headers,
                timeout=5
            )
            resp.raise_for_status()
            messages.success(request, f"LLM configured: {provider.title()} ({model_name})")

            # Save in session
            request.session["current_provider"] = provider
            request.session["current_model"] = model_name
            request.session.modified = True

        except requests.RequestException as e:
            messages.warning(request, f"Could not configure LLM: {e}")

        return redirect("rag_qna_page_admin")


class ClearChat(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page")

class ClearChat_admin(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_admin")


RAG_PDF_DIR = settings.RAG_PDF_DIR

class UploadPDF(View):
    template_name = "uploadPDF.html"
   

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

API_KEY = os.getenv("AZURE_API_KEY")
os.environ["AZURE_API_KEY"] = API_KEY

ENDPOINT = os.getenv("AZURE_ENDPOINT")
os.environ["AZURE_ENDPOINT"] = ENDPOINT

DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
os.environ["AZURE_DEPLOYMENT"] = DEPLOYMENT

class QnAPage2(View):
    template_name = "QnA2.html"
    
    def __init__(self):
        super().__init__()
        self.azure_client = None
        self._initialize_azure_client()
    
    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client with API key authentication"""
        try:
            self.azure_client = AzureOpenAI(
                azure_endpoint=ENDPOINT,
                api_key=API_KEY,
                api_version="2024-02-15-preview"
            )
            print("Azure OpenAI client initialized successfully with API key")
            
        except Exception as e:
            print(f"Failed to initialize Azure OpenAI client: {e}")
            self.azure_client = None

    def clean_response_text(self, text):
        """Remove markdown formatting and HTML tags from response while preserving structure"""
        if not text:
            return text
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
        text = re.sub(r'#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)  # headers
        text = re.sub(r'`(.*?)`', r'\1', text)        # inline code
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # code blocks
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Preserve line breaks for numbered lists and bullet points
        text = re.sub(r'(\d+\.)\s*', r'\n\1 ', text)  # Add line break before numbered items
        text = re.sub(r'^[-•*]\s*', r'\n• ', text, flags=re.MULTILINE)  # Add line break before bullet points
        
        # Clean up excessive whitespace but preserve single line breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Replace multiple line breaks with double line break
        text = re.sub(r'^\s+', '', text)  # Remove leading whitespace
        text = re.sub(r'\s+$', '', text)  # Remove trailing whitespace
        
        return text

    def get(self, request):
        ask_form = QuestionForm()
        chat = request.session.get(SESSION_KEY, [])
        return render(request, self.template_name, {
            "ask_form": ask_form,
            "chat": chat,
            "status_msg": "Backend ready" if self.azure_client else "Azure client not initialized"
        })

    def post(self, request):
        ask_form = QuestionForm(request.POST)
        chat = request.session.get(SESSION_KEY, [])

        if ask_form.is_valid():
            question = ask_form.cleaned_data["question"]
            chat.append({"who": "user", "text": question})

            try:
                # Check if Azure client is initialized
                if not self.azure_client:
                    self._initialize_azure_client()
                    if not self.azure_client:
                        raise Exception("Failed to initialize Azure OpenAI client")

                # Prepare messages
                messages_payload = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. Provide clear, concise responses without using markdown formatting or HTML tags."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]

                print(f"Sending request to Azure OpenAI...")
                print(f"Endpoint: {ENDPOINT}")
                print(f"Deployment: {DEPLOYMENT}")
                print(f"Question: {question}")

                # Make the API call using Azure OpenAI SDK
                completion = self.azure_client.chat.completions.create(
                    model=DEPLOYMENT,
                    messages=messages_payload,
                    max_tokens=1000,
                    temperature=0.7,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False
                )

                print(f"Response received from Azure OpenAI")

                # Extract the response
                if completion.choices and len(completion.choices) > 0:
                    choice = completion.choices[0]
                    answer = choice.message.content
                    
                    # Check if answer is empty
                    if not answer or answer.strip() == "":
                        finish_reason = choice.finish_reason
                        if finish_reason == "content_filter":
                            answer = "Response was filtered due to content policy."
                        elif finish_reason == "length":
                            answer = "Response was cut off due to length limit."
                        else:
                            answer = f"Empty response received (finish_reason: {finish_reason})"
                    
                    # Clean the response text
                    answer_clean = self.clean_response_text(answer)
                    
                    # Add token usage info
                    usage = completion.usage
                    total_tokens = usage.total_tokens if usage else "unknown"
                    llm_info = f"Azure OpenAI - {DEPLOYMENT} (tokens: {total_tokens})"
                    
                    chat.append({
                        "who": "bot", 
                        "text": answer_clean, 
                        "llm": llm_info
                    })
                    
                    print(f"Successfully processed response: {answer_clean[:100]}...")
                    
                else:
                    error_msg = "No response choices returned from Azure OpenAI"
                    chat.append({"who": "bot", "text": error_msg})
                    django_messages.error(request, error_msg)

            except Exception as e:
                error_msg = f"Azure OpenAI error: {str(e)}"
                print(f"Error details: {e}")
                
                chat.append({"who": "bot", "text": error_msg})
                django_messages.error(request, error_msg)

            # Save chat in session
            request.session[SESSION_KEY] = chat
            request.session.modified = True

        return render(request, self.template_name, {
            "ask_form": QuestionForm(),
            "chat": chat,
            "status_msg": "Backend ready" if self.azure_client else "Azure client error"
        })

# Test function
def test_azure_api_key_connection():
    """Test Azure OpenAI with API key"""
    try:
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
            api_version="2024-02-15-preview"
        )
        
        completion = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=50
        )
        
        if completion.choices:
            print(f"✓ API Key test successful: {completion.choices[0].message.content}")
            return True
        else:
            print("✗ No response")
            return False
            
    except Exception as e:
        print(f"✗ API Key test failed: {e}")
        return False

# Uncomment to test:
# test_azure_api_key_connection()

class ClearChat2(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page2")
    

class ClearChatPhi(View):
    def post(self, request):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        messages.info(request, "Conversation cleared.")
        return redirect("rag_qna_page_phi")
    


    



SESSION_KEY = "chat_history"

# Azure OpenAI settings
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")

class QnAPagePhi(View):
    template_name = "QnA_phi.html"

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
        return result["choices"][0]["message"]["content"]

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
                answer = self._ask_azure_openai(question, context)
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
    


    