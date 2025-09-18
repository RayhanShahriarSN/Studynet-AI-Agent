import os
import re
import json
import PyPDF2
from django.shortcuts import render
from django.views import View
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from openai import AzureOpenAI
from rag.forms import QuestionForm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path
import hashlib
from datetime import datetime

SESSION_KEY = "chat_history"

# Azure OpenAI settings
ENDPOINT = os.getenv("ENDPOINT_URL", "https://studynet-ai-agent.openai.azure.com/")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "chat-heavy")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "EZFRKMlQvMguHWxd4ymVjQdb5JVds9OhN5PXD3zS3dWIhfFCBpk0JQQJ99BIACL93NaXJ3w3AAAAACOGovff")

# PDF storage settings
PDF_FOLDER = "media/pdfs"
EMBEDDINGS_FILE = "media/pdf_embeddings.json"

class PDFRAGSystem:
    def __init__(self):
        self.vectorizer = None
        self.document_chunks = []
        self.document_metadata = []
        self.tfidf_matrix = None
        self.load_or_create_embeddings()
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n[Page {page_num + 1}]\n{page_text}"
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text, filename, chunk_size=500, overlap=50):
        """Split text into chunks for better retrieval"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append({
                    'text': chunk.strip(),
                    'filename': filename,
                    'chunk_id': len(chunks)
                })
        
        return chunks
    
    def process_pdfs(self):
        """Process all PDFs in the PDF folder"""
        if not os.path.exists(PDF_FOLDER):
            os.makedirs(PDF_FOLDER)
            return
        
        all_chunks = []
        all_texts = []
        
        pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(PDF_FOLDER, pdf_file)
            print(f"Processing {pdf_file}...")
            
            text = self.extract_text_from_pdf(pdf_path)
            if text:
                chunks = self.chunk_text(text, pdf_file)
                all_chunks.extend(chunks)
                all_texts.extend([chunk['text'] for chunk in chunks])
        
        if all_texts:
            # Create TF-IDF vectorizer and matrix
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                max_df=0.8,
                min_df=2
            )
            
            self.tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            self.document_chunks = all_chunks
            
            # Save embeddings
            self.save_embeddings()
            print(f"Processed {len(pdf_files)} PDFs into {len(all_chunks)} chunks")
        else:
            print("No text extracted from PDFs")
    
    def save_embeddings(self):
        """Save embeddings and metadata to file"""
        try:
            # Ensure media directory exists
            os.makedirs(os.path.dirname(EMBEDDINGS_FILE), exist_ok=True)
            
            data = {
                'chunks': self.document_chunks,
                'vectorizer_vocab': self.vectorizer.vocabulary_ if self.vectorizer else {},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Embeddings saved to {EMBEDDINGS_FILE}")
        except Exception as e:
            print(f"Error saving embeddings: {e}")
    
    def load_or_create_embeddings(self):
        """Load existing embeddings or create new ones"""
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.document_chunks = data.get('chunks', [])
                vocab = data.get('vectorizer_vocab', {})
                
                if self.document_chunks and vocab:
                    # Recreate vectorizer and TF-IDF matrix
                    all_texts = [chunk['text'] for chunk in self.document_chunks]
                    self.vectorizer = TfidfVectorizer(
                        max_features=5000,
                        stop_words='english',
                        ngram_range=(1, 2),
                        vocabulary=vocab
                    )
                    self.tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                    print(f"Loaded {len(self.document_chunks)} chunks from saved embeddings")
                    return
            except Exception as e:
                print(f"Error loading embeddings: {e}")
        
        # If loading failed or no embeddings exist, process PDFs
        print("Creating new embeddings...")
        self.process_pdfs()
    
    def search_documents(self, query, top_k=5):
        """Search for relevant document chunks"""
        if not self.vectorizer or not self.document_chunks:
            return []
        
        try:
            # Transform query using the same vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top-k most similar documents
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Only include if similarity is above threshold
                    chunk = self.document_chunks[idx].copy()
                    chunk['similarity'] = float(similarities[idx])
                    results.append(chunk)
            
            return results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

# Global RAG system instance
rag_system = PDFRAGSystem()

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
        """Clean text while preserving line breaks for lists and structure"""
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
        
        # Fix numbered lists - ensure they have line breaks
        text = re.sub(r'(\d+\.)\s*', r'\n\1 ', text)
        
        # Fix bullet points
        text = re.sub(r'([.!?])\s*[-•*]\s*', r'\1\n• ', text)
        
        # Clean up extra spaces but preserve line structure
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n +', r'\n', text)  # Remove spaces after line breaks
        text = re.sub(r' +\n', r'\n', text)  # Remove spaces before line breaks
        
        # Convert line breaks to HTML <br> tags for proper display
        text = text.replace('\n', '<br>')
        
        # Clean up any leading/trailing whitespace
        text = text.strip()
        
        return text

    def get_context_from_pdfs(self, query):
        """Get relevant context from PDFs"""
        relevant_chunks = rag_system.search_documents(query, top_k=3)
        
        if not relevant_chunks:
            return "No relevant information found in uploaded PDFs."
        
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['filename']}]\n{chunk['text'][:800]}..."
            )
        
        return "\n\n".join(context_parts)

    def get(self, request):
        ask_form = QuestionForm()
        chat = request.session.get(SESSION_KEY, [])
        
        # Get PDF info for display
        pdf_files = []
        if os.path.exists(PDF_FOLDER):
            pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
        
        return render(request, self.template_name, {
            "ask_form": ask_form,
            "chat": chat,
            "status_msg": f"Backend ready - {len(pdf_files)} PDFs loaded",
            "pdf_count": len(pdf_files)
        })

    def post(self, request):
        # Handle PDF upload
        if 'pdf_file' in request.FILES:
            return self.handle_pdf_upload(request)
        
        # Handle chat message
        ask_form = QuestionForm(request.POST)
        chat = request.session.get(SESSION_KEY, [])

        if ask_form.is_valid():
            question = ask_form.cleaned_data["question"]
            chat.append({"who": "user", "text": question})

            try:
                if not self.azure_client:
                    self._initialize_azure_client()
                    if not self.azure_client:
                        raise Exception("Failed to initialize Azure OpenAI client")

                # Get relevant context from PDFs
                pdf_context = self.get_context_from_pdfs(question)
                
                # Create enhanced system prompt with PDF context
                system_prompt = f"""You are a helpful AI assistant. Answer questions based on the provided context from PDF documents.

Context from PDFs:
{pdf_context}

Instructions:
- Answer questions using ONLY the information provided in the context above
- If the context doesn't contain relevant information, say "I don't have information about this in the uploaded PDFs"
- Be specific and cite which document your information comes from
- Provide clear, concise responses without using markdown formatting
- If asked about multiple topics, organize your response with numbered points"""

                messages_payload = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]

                print(f"Sending request with PDF context...")
                print(f"Context length: {len(pdf_context)} characters")

                completion = self.azure_client.chat.completions.create(
                    model=DEPLOYMENT,
                    messages=messages_payload,
                    max_tokens=1000,
                    temperature=0.3,  # Lower temperature for more factual responses
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False
                )

                if completion.choices and len(completion.choices) > 0:
                    choice = completion.choices[0]
                    answer = choice.message.content
                    
                    if not answer or answer.strip() == "":
                        finish_reason = choice.finish_reason
                        if finish_reason == "content_filter":
                            answer = "Response was filtered due to content policy."
                        else:
                            answer = f"Empty response received (finish_reason: {finish_reason})"
                    
                    answer_clean = self.clean_response_text(answer)
                    
                    usage = completion.usage
                    total_tokens = usage.total_tokens if usage else "unknown"
                    llm_info = f"Azure OpenAI + PDF RAG - {DEPLOYMENT} (tokens: {total_tokens})"
                    
                    chat.append({
                        "who": "bot", 
                        "text": answer_clean, 
                        "llm": llm_info
                    })
                    
                else:
                    error_msg = "No response choices returned from Azure OpenAI"
                    chat.append({"who": "bot", "text": error_msg})
                    django_messages.error(request, error_msg)

            except Exception as e:
                error_msg = f"Azure OpenAI error: {str(e)}"
                print(f"Error details: {e}")
                chat.append({"who": "bot", "text": error_msg})
                django_messages.error(request, error_msg)

            request.session[SESSION_KEY] = chat
            request.session.modified = True

        return render(request, self.template_name, {
            "ask_form": QuestionForm(),
            "chat": chat,
            "status_msg": "Backend ready with PDF RAG"
        })
    
    def handle_pdf_upload(self, request):
        """Handle PDF file upload"""
        try:
            pdf_file = request.FILES['pdf_file']
            
            # Validate file type
            if not pdf_file.name.lower().endswith('.pdf'):
                django_messages.error(request, "Only PDF files are allowed")
                return self.get(request)
            
            # Save file to PDF folder
            os.makedirs(PDF_FOLDER, exist_ok=True)
            file_path = os.path.join(PDF_FOLDER, pdf_file.name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            
            # Reprocess all PDFs to include the new one
            global rag_system
            rag_system.process_pdfs()
            
            django_messages.success(request, f"PDF '{pdf_file.name}' uploaded and processed successfully!")
            
        except Exception as e:
            django_messages.error(request, f"Error uploading PDF: {str(e)}")
        
        return self.get(request)