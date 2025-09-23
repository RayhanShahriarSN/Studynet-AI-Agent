# RAG AI Agent - Complete Developer Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Workflow](#architecture--workflow)
3. [File Structure & Purpose](#file-structure--purpose)
4. [Setup & Installation](#setup--installation)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [Frontend Customization](#frontend-customization)
7. [Backend Customization](#backend-customization)
8. [Database & Models](#database--models)
9. [Configuration Guide](#configuration-guide)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Features](#advanced-features)
12. [Deployment Guide](#deployment-guide)

---

## 🎯 Project Overview

This is a **RAG (Retrieval-Augmented Generation) AI Agent** built with Django REST Framework. It allows users to:
- Ask questions about documents (PDFs)
- Get AI-powered answers using Azure OpenAI
- Upload and process new documents
- Search the web for additional information
- Maintain conversation history

### Key Technologies
- **Backend**: Django + Django REST Framework
- **AI**: Azure OpenAI (GPT-4) + Embeddings
- **Vector Database**: Chroma
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Document Processing**: PyPDF2, LangChain

---

## 🏗️ Architecture & Workflow

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   AI Services   │
│   (HTML/CSS/JS) │◄──►│   (REST API)    │◄──►│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Vector Store   │
                       │   (Chroma)      │
                       └─────────────────┘
```

### Complete Workflow
1. **User Input**: User types a question in the frontend
2. **API Request**: Frontend sends POST request to `/api/query/`
3. **Query Processing**: Django processes the request
4. **Document Retrieval**: System searches vector store for relevant documents
5. **AI Processing**: Query + documents sent to Azure OpenAI
6. **Response Generation**: AI generates answer with sources
7. **Response Return**: Answer sent back to frontend
8. **Display**: Frontend shows answer with sources and metadata

---

## 📁 File Structure & Purpose

### Root Directory
```
Studynet-AI-Agent/
├── rag_backend/                    # Main Django project
│   ├── manage.py                   # Django management script
│   ├── requirements.txt            # Python dependencies
│   ├── start_server.py            # Server startup script
│   ├── load_kb.py                 # Knowledge base loader
│   ├── debug_kb.py                # Debug script
│   ├── .env                       # Environment variables (create this)
│   ├── db.sqlite3                 # SQLite database (auto-created)
│   ├── vector_store/              # Chroma vector database
│   ├── pdfs/                      # PDF documents folder
│   ├── static/                    # Static files (CSS, JS, images)
│   ├── templates/                 # Django templates
│   ├── rag_backend/               # Django project settings
│   └── api/                       # Main API application
```

### Django Project Structure (`rag_backend/`)
```
rag_backend/
├── rag_backend/                   # Project configuration
│   ├── __init__.py
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Main URL routing
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
└── api/                          # API application
    ├── __init__.py
    ├── admin.py                   # Django admin
    ├── apps.py                    # App configuration
    ├── models.py                  # Database models
    ├── views.py                   # API views/endpoints
    ├── urls.py                    # API URL routing
    ├── serializers.py             # Data serialization
    ├── agent.py                   # RAG agent logic
    ├── memory.py                  # Conversation memory
    ├── vectorstore.py             # Vector database operations
    ├── retriever.py               # Document retrieval
    ├── embeddings.py              # Text embeddings
    ├── utils.py                   # Utility functions
    ├── config.py                  # Configuration management
    └── templates/                 # API-specific templates
        └── index.html             # Frontend template
```

### Static Files Structure
```
static/
├── css/
│   └── style.css                  # Main stylesheet
├── js/
│   └── app.js                     # Frontend JavaScript
└── images/
    └── favicon.ico                # Website icon
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8+ installed
- Git installed
- Azure OpenAI account (for AI functionality)

### Step 1: Clone and Navigate
```bash
git clone <your-repo-url>
cd Studynet-AI-Agent/rag_backend
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Environment Configuration
Create a `.env` file in the `rag_backend` directory:
```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Model Deployments
CHAT_MODEL_DEPLOYMENT=chat-heavy
EMBEDDING_MODEL_DEPLOYMENT=embed-large

# Tavily Web Search
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: Override default paths
VECTOR_DB_PATH=./vector_store
KNOWLEDGE_BASE_PATH=./pdfs
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 4: Database Setup
```bash
python manage.py migrate
```

### Step 5: Load Knowledge Base
```bash
python load_kb.py
```

### Step 6: Start Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Step 7: Access Application
Open your browser and go to: `http://localhost:8000/api/`

---

## 🔌 API Endpoints Reference

### Base URL
All API endpoints are prefixed with: `http://localhost:8000/api/`

### 1. Frontend Interface
- **URL**: `/`
- **Method**: GET
- **Purpose**: Serves the main web interface
- **Response**: HTML page

### 2. Health Check
- **URL**: `/health/`
- **Method**: GET
- **Purpose**: Check if API is running
- **Response**:
```json
{
    "status": "healthy",
    "service": "RAG Pipeline API",
    "version": "1.0.0"
}
```

### 3. Query Processing
- **URL**: `/query/`
- **Method**: POST
- **Purpose**: Process user questions
- **Request Body**:
```json
{
    "query": "What is the application process?",
    "session_id": "optional_session_id",
    "use_web_search": true,
    "enhance_formatting": true
}
```
- **Response**:
```json
{
    "answer": "The application process involves...",
    "sources": [
        {
            "type": "knowledge_base",
            "content": "Document content..."
        }
    ],
    "confidence_score": 0.85,
    "web_search_used": false,
    "session_id": "session_123"
}
```

### 4. Document Upload
- **URL**: `/upload/document/`
- **Method**: POST
- **Purpose**: Upload and process PDF documents
- **Request**: Multipart form data with `file` field
- **Response**:
```json
{
    "status": "success",
    "message": "Document processed successfully",
    "chunks_created": 15
}
```

### 5. Text Upload
- **URL**: `/upload/text/`
- **Method**: POST
- **Purpose**: Upload raw text content
- **Request Body**:
```json
{
    "content": "Your text content here",
    "metadata": {
        "title": "Document Title",
        "author": "Author Name"
    }
}
```

### 6. Memory Management
- **URL**: `/memory/{session_id}/`
- **Method**: GET/DELETE
- **Purpose**: Get or clear conversation memory
- **GET Response**:
```json
{
    "session_id": "session_123",
    "context": "Previous conversation...",
    "memory": {...}
}
```

### 7. Sessions List
- **URL**: `/sessions/`
- **Method**: GET
- **Purpose**: List all active sessions
- **Response**:
```json
{
    "sessions": ["session_1", "session_2"],
    "count": 2
}
```

### 8. System Metrics
- **URL**: `/metrics/`
- **Method**: GET/POST
- **Purpose**: Get or reset system metrics
- **GET Response**:
```json
{
    "total_queries": 150,
    "successful_queries": 145,
    "failed_queries": 5,
    "average_response_time": 2.3
}
```

### 9. Knowledge Base Status
- **URL**: `/knowledge-base/status/`
- **Method**: GET
- **Purpose**: Check knowledge base status
- **Response**:
```json
{
    "status": "active",
    "parent_chunks": 25,
    "child_chunks": 150,
    "total_documents": 175
}
```

### 10. Knowledge Base Reload
- **URL**: `/knowledge-base/reload/`
- **Method**: POST
- **Purpose**: Reload all documents from PDFs folder
- **Response**:
```json
{
    "status": "success",
    "message": "Knowledge base reloaded with 62 documents"
}
```

### 11. Vector Store Clear
- **URL**: `/vectorstore/clear/`
- **Method**: DELETE
- **Purpose**: Clear all vector store data
- **Response**:
```json
{
    "status": "success",
    "message": "Vector store cleared successfully"
}
```

---

## 🎨 Frontend Customization

### File Locations
- **Main Template**: `api/templates/index.html`
- **CSS**: `static/css/style.css`
- **JavaScript**: `static/js/app.js`

### Key Frontend Components

#### 1. HTML Structure (`api/templates/index.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <!-- Meta tags, CSS links -->
</head>
<body>
    <div class="container">
        <header class="header">
            <!-- Logo and navigation -->
        </header>
        <main class="main-content">
            <div class="chat-container">
                <!-- Chat messages area -->
            </div>
            <aside class="sidebar">
                <!-- System status and settings -->
            </aside>
        </main>
    </div>
</body>
</html>
```

#### 2. CSS Styling (`static/css/style.css`)
- **Main Classes**:
  - `.container`: Main layout container
  - `.chat-container`: Chat interface
  - `.message`: Individual messages
  - `.sidebar`: Right sidebar
  - `.btn`: Button styles
  - `.modal`: Modal dialogs

#### 3. JavaScript Logic (`static/js/app.js`)
- **Main Class**: `RAGAgent`
- **Key Methods**:
  - `sendMessage()`: Send user queries
  - `addMessage()`: Add messages to chat
  - `loadSystemStatus()`: Update system status
  - `handleFileUpload()`: Process file uploads

### Customizing the Frontend

#### Adding New Features
1. **New UI Elements**: Add HTML in `index.html`
2. **Styling**: Add CSS in `style.css`
3. **Functionality**: Add JavaScript in `app.js`

#### Example: Adding a Dark Mode Toggle
```html
<!-- In index.html -->
<button id="darkModeToggle" class="btn btn-secondary">
    <i class="fas fa-moon"></i> Dark Mode
</button>
```

```css
/* In style.css */
.dark-mode {
    background: #1a1a1a;
    color: #ffffff;
}

.dark-mode .message-bubble {
    background: #2d2d2d;
    color: #ffffff;
}
```

```javascript
// In app.js
document.getElementById('darkModeToggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
});
```

---

## ⚙️ Backend Customization

### Core Files and Their Purposes

#### 1. API Views (`api/views.py`)
Contains all API endpoint logic:
- `HealthCheckView`: System health
- `QueryProcessView`: Main query processing
- `DocumentUploadView`: File upload handling
- `MemoryView`: Conversation memory
- `MetricsView`: System metrics

#### 2. RAG Agent (`api/agent.py`)
Main AI logic:
- `RAGAgent` class: Core agent functionality
- `process_query()`: Process user queries
- `add_documents()`: Add documents to knowledge base

#### 3. Vector Store (`api/vectorstore.py`)
Document storage and retrieval:
- `HierarchicalVectorStore` class
- `add_documents()`: Store documents
- `similarity_search_with_score()`: Search documents

#### 4. Memory Management (`api/memory.py`)
Conversation history:
- `ConversationMemoryManager` class
- `add_message()`: Store messages
- `get_conversation_context()`: Retrieve context

### Adding New API Endpoints

#### Step 1: Add View in `api/views.py`
```python
class NewFeatureView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Your logic here
        return Response({"message": "New feature working!"})
```

#### Step 2: Add URL in `api/urls.py`
```python
urlpatterns = [
    # ... existing patterns
    path('new-feature/', views.NewFeatureView.as_view(), name='new_feature'),
]
```

#### Step 3: Test the Endpoint
```bash
curl http://localhost:8000/api/new-feature/
```

### Adding New AI Features

#### Example: Adding Sentiment Analysis
1. **Create new utility** in `api/utils.py`:
```python
class SentimentAnalyzer:
    def analyze_sentiment(self, text):
        # Your sentiment analysis logic
        return {"sentiment": "positive", "score": 0.8}
```

2. **Integrate in agent** (`api/agent.py`):
```python
def process_query(self, query, ...):
    # ... existing logic
    
    # Add sentiment analysis
    from .utils import SentimentAnalyzer
    sentiment = SentimentAnalyzer().analyze_sentiment(query)
    
    return {
        "answer": answer,
        "sentiment": sentiment,
        # ... other fields
    }
```

---

## 🗄️ Database & Models

### Models (`api/models.py`)

#### 1. ChatMessage
```python
class ChatMessage(models.Model):
    session_id = models.CharField(max_length=100)
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

#### 2. ConversationSession
```python
class ConversationSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
```

#### 3. QueryRequest/QueryResponse
```python
class QueryRequest(models.Model):
    query = models.TextField()
    session_id = models.CharField(max_length=100)
    use_web_search = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

### Database Operations

#### Creating New Models
1. **Define model** in `api/models.py`
2. **Create migration**: `python manage.py makemigrations`
3. **Apply migration**: `python manage.py migrate`

#### Example: Adding User Preferences
```python
class UserPreferences(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    preferred_language = models.CharField(max_length=10, default='en')
    response_length = models.CharField(max_length=20, default='medium')
    enable_notifications = models.BooleanField(default=True)
```

---

## ⚙️ Configuration Guide

### Environment Variables (`.env`)

#### Required Variables
```env
# Azure OpenAI (Required for AI functionality)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
CHAT_MODEL_DEPLOYMENT=your_chat_model
EMBEDDING_MODEL_DEPLOYMENT=your_embedding_model

# Tavily Search (Required for web search)
TAVILY_API_KEY=your_tavily_key
```

#### Optional Variables
```env
# Paths
VECTOR_DB_PATH=./vector_store
KNOWLEDGE_BASE_PATH=./pdfs

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AI Settings
SIMILARITY_THRESHOLD=0.7
MAX_MEMORY_MESSAGES=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Django Settings (`rag_backend/settings.py`)

#### Key Settings
```python
# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',  # Your main app
]

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Static Files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "No knowledge base connected"
**Problem**: Frontend shows 0 documents
**Solution**:
```bash
# Load the knowledge base
python load_kb.py

# Or use the API
curl -X POST http://localhost:8000/api/knowledge-base/reload/
```

#### 2. "Negative indexing is not supported"
**Problem**: Error when processing queries
**Solution**: This has been fixed in the code. If you see this error, restart the server.

#### 3. "TemplateDoesNotExist"
**Problem**: Frontend not loading
**Solution**: Ensure the template is in the correct location:
```bash
# Check if template exists
ls api/templates/index.html
```

#### 4. "Failed to add documents to vector store"
**Problem**: Document upload failing
**Solution**:
```bash
# Clear and recreate vector store
curl -X DELETE http://localhost:8000/api/vectorstore/clear/
python load_kb.py
```

#### 5. "Azure OpenAI API Error"
**Problem**: AI responses not working
**Solution**: Check your `.env` file:
```env
AZURE_OPENAI_API_KEY=your_correct_key
AZURE_OPENAI_ENDPOINT=https://your-correct-resource.openai.azure.com/
```

### Debug Mode

#### Enable Debug Logging
Add to `rag_backend/settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

#### Debug Script
Use the provided debug script:
```bash
python debug_kb.py
```

---

## 🚀 Advanced Features

### 1. Custom Document Processors

#### Adding Support for New File Types
```python
# In api/utils.py
def load_document(self, file_path: str) -> List[Document]:
    if file_path.endswith('.docx'):
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        return loader.load()
    elif file_path.endswith('.txt'):
        # Existing logic
        pass
```

### 2. Custom AI Models

#### Adding Different AI Providers
```python
# In api/agent.py
def __init__(self):
    # Use different model
    self.llm = AzureChatOpenAI(
        azure_deployment="gpt-4-turbo",  # Different model
        temperature=0.1,  # Different temperature
    )
```

### 3. Advanced Memory Management

#### Custom Memory Strategies
```python
# In api/memory.py
def get_conversation_context(self, session_id: str, strategy: str = "recent"):
    if strategy == "recent":
        return self.get_recent_messages(session_id)
    elif strategy == "summarized":
        return self.get_summarized_context(session_id)
    elif strategy == "relevant":
        return self.get_relevant_context(session_id)
```

### 4. Custom Retrieval Strategies

#### Adding New Retrieval Methods
```python
# In api/retriever.py
def hybrid_search(self, query: str, k: int = 5) -> List[Document]:
    # Combine multiple search strategies
    semantic_results = self.semantic_search(query, k)
    keyword_results = self.keyword_search(query, k)
    return self.merge_results(semantic_results, keyword_results)
```

---

## 🌐 Deployment Guide

### Production Deployment

#### 1. Environment Setup
```bash
# Install production dependencies
pip install gunicorn psycopg2-binary

# Set production environment
export DJANGO_SETTINGS_MODULE=config.settings_production
```

#### 2. Database Configuration
```python
# In settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rag_agent_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 3. Static Files
```bash
# Collect static files
python manage.py collectstatic

# Serve with nginx or Apache
```

#### 4. WSGI Configuration
```python
# In wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
application = get_wsgi_application()
```

#### 5. Run with Gunicorn
```bash
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
    volumes:
      - ./pdfs:/app/pdfs
      - ./vector_store:/app/vector_store
```

---

## 📚 Additional Resources

### Useful Commands
```bash
# Start development server
python manage.py runserver

# Load knowledge base
python load_kb.py

# Debug knowledge base
python debug_kb.py

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### File Locations Summary
- **Main Settings**: `rag_backend/settings.py`
- **URL Routing**: `rag_backend/urls.py` and `api/urls.py`
- **API Logic**: `api/views.py`
- **Database Models**: `api/models.py`
- **AI Agent**: `api/agent.py`
- **Frontend**: `api/templates/index.html`
- **Static Files**: `static/` directory
- **Configuration**: `api/config.py`
- **Environment**: `.env` file

### Support and Community
- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **LangChain Documentation**: https://python.langchain.com/
- **Azure OpenAI**: https://docs.microsoft.com/en-us/azure/cognitive-services/openai/

---

## 🎉 Conclusion

This RAG AI Agent is a powerful, customizable system that can be adapted for various use cases. The modular architecture makes it easy to:

- Add new document types
- Integrate different AI models
- Customize the frontend
- Extend functionality
- Deploy to production

Whether you're a beginner or an experienced developer, this documentation provides everything you need to understand, customize, and deploy the system successfully.

**Happy coding!** 🚀
