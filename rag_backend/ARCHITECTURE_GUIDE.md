# 🏗️ Architecture Guide - RAG AI Agent

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (HTML/CSS/JS)  │  Mobile Browser  │  API Client     │
│  - Chat Interface        │  - Responsive    │  - Postman      │
│  - File Upload          │  - Touch UI      │  - curl         │
│  - Real-time Updates    │  - Mobile Apps   │  - Python SDK   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO REST API LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  URL Routing          │  API Views           │  Serializers    │
│  - /api/query/        │  - QueryProcessView  │  - Input/Output │
│  - /api/upload/       │  - DocumentUpload    │  - Validation   │
│  - /api/memory/       │  - MemoryView        │  - Formatting   │
│  - /api/health/       │  - HealthCheck       │  - Error Handle │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  RAG Agent            │  Memory Manager      │  Document Proc  │
│  - Query Processing   │  - Session Mgmt      │  - PDF Parser   │
│  - AI Integration     │  - Context Storage   │  - Text Split   │
│  - Tool Creation      │  - Summarization     │  - Metadata Ext │
│  - Response Format    │  - Token Counting    │  - ID Generation│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA STORAGE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Vector Database      │  SQLite Database     │  File System    │
│  - Chroma DB          │  - User Sessions     │  - PDF Files    │
│  - Embeddings         │  - Chat History      │  - Static Files │
│  - Similarity Search  │  - System Metrics    │  - Logs         │
│  - Hierarchical Chunk │  - Configuration     │  - Temp Files   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                         │
├─────────────────────────────────────────────────────────────────┤
│  Azure OpenAI         │  Tavily Search       │  Other APIs     │
│  - GPT-4 Chat         │  - Web Search        │  - Future:      │
│  - Text Embeddings    │  - Real-time Info    │  - Email        │
│  - Model Management   │  - News Articles     │  - SMS          │
│  - Token Management   │  - Social Media      │  - Notifications│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

### 1. User Query Flow
```
User Input → Frontend → API → RAG Agent → Vector Search → AI Processing → Response
     │           │        │        │            │              │           │
     │           │        │        │            │              │           │
     ▼           ▼        ▼        ▼            ▼              ▼           ▼
"Question" → JavaScript → Django → Agent.py → VectorStore → OpenAI → "Answer"
```

### 2. Document Upload Flow
```
PDF Upload → Frontend → API → Document Processor → Vector Store → Embeddings
     │           │        │           │               │             │
     │           │        │           │               │             │
     ▼           ▼        ▼           ▼               ▼             ▼
"file.pdf" → FormData → UploadView → Utils.py → ChromaDB → Azure OpenAI
```

### 3. Memory Management Flow
```
Chat Message → Memory Manager → Database → Context Retrieval → AI Context
      │              │              │            │              │
      │              │              │            │              │
      ▼              ▼              ▼            ▼              ▼
"User: Hi" → MemoryManager → SQLite → "Previous context" → "Enhanced query"
```

---

## 📁 File Structure Deep Dive

### Django Project Structure
```
rag_backend/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables
├── db.sqlite3                  # SQLite database
├── vector_store/               # Chroma vector database
│   ├── parent/                 # Parent document chunks
│   └── child/                  # Child document chunks
├── pdfs/                       # PDF documents folder
├── static/                     # Static files (CSS, JS, images)
│   ├── css/style.css           # Main stylesheet
│   ├── js/app.js               # Frontend JavaScript
│   └── images/                 # Images and icons
├── templates/                  # Django templates
├── config/                     # Django project settings
│   ├── __init__.py
│   ├── settings.py             # Main settings
│   ├── urls.py                 # Main URL routing
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
└── api/                        # Main API application
    ├── __init__.py
    ├── admin.py                # Django admin
    ├── apps.py                 # App configuration
    ├── models.py               # Database models
    ├── views.py                # API views/endpoints
    ├── urls.py                 # API URL routing
    ├── serializers.py          # Data serialization
    ├── agent.py                # RAG agent logic
    ├── memory.py               # Conversation memory
    ├── vectorstore.py          # Vector database operations
    ├── retriever.py            # Document retrieval
    ├── embeddings.py           # Text embeddings
    ├── utils.py                # Utility functions
    ├── config.py               # Configuration management
    └── templates/              # API-specific templates
        └── index.html          # Frontend template
```

---

## 🔌 API Endpoint Architecture

### URL Routing Structure
```
Main URLs (rag_backend/urls.py)
├── /api/ → api.urls
└── /admin/ → Django admin

API URLs (api/urls.py)
├── / → Frontend (index.html)
├── /health/ → HealthCheckView
├── /query/ → QueryProcessView
├── /upload/document/ → DocumentUploadView
├── /upload/text/ → TextUploadView
├── /memory/<session_id>/ → MemoryView
├── /sessions/ → SessionsListView
├── /metrics/ → MetricsView
├── /knowledge-base/status/ → KnowledgeBaseStatusView
├── /knowledge-base/reload/ → KnowledgeBaseReloadView
└── /vectorstore/clear/ → VectorStoreClearView
```

### Request/Response Flow
```
HTTP Request → URL Router → View Class → Serializer → Business Logic → Response
     │              │           │           │            │              │
     │              │           │           │            │              │
     ▼              ▼           ▼           ▼            ▼              ▼
POST /query/ → urls.py → QueryProcessView → Serializer → RAG Agent → JSON Response
```

---

## 🧠 AI Processing Architecture

### RAG Pipeline Components
```
User Query
    │
    ▼
Query Optimizer (utils.py)
    │
    ▼
Document Retriever (retriever.py)
    │
    ▼
Vector Store Search (vectorstore.py)
    │
    ▼
Context Assembly
    │
    ▼
AI Agent (agent.py)
    │
    ▼
Azure OpenAI Processing
    │
    ▼
Response Formatter (utils.py)
    │
    ▼
Final Answer
```

### Memory Management Flow
```
Chat Message
    │
    ▼
Memory Manager (memory.py)
    │
    ├── Store in Database (models.py)
    ├── Check Token Limits
    ├── Summarize if Needed
    └── Retrieve Context
    │
    ▼
Enhanced Query Context
```

---

## 🗄️ Database Schema

### SQLite Tables
```sql
-- Chat Messages
CREATE TABLE api_chatmessage (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(100),
    role VARCHAR(20),
    content TEXT,
    timestamp DATETIME
);

-- Conversation Sessions
CREATE TABLE api_conversationsession (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    created_at DATETIME,
    last_activity DATETIME
);

-- Query Requests
CREATE TABLE api_queryrequest (
    id INTEGER PRIMARY KEY,
    query TEXT,
    session_id VARCHAR(100),
    use_web_search BOOLEAN,
    timestamp DATETIME
);
```

### Vector Database Structure
```
Chroma Collections:
├── parent_chunks
│   ├── Document ID
│   ├── Content (full document)
│   ├── Metadata
│   └── Embedding Vector
└── child_chunks
    ├── Document ID
    ├── Content (chunk)
    ├── Parent ID
    ├── Metadata
    └── Embedding Vector
```

---

## 🔧 Configuration Architecture

### Environment Variables Flow
```
.env File → config.py → Django Settings → Application Code
    │           │             │                │
    │           │             │                │
    ▼           ▼             ▼                ▼
API Keys → Config Class → settings.py → agent.py, embeddings.py
```

### Settings Hierarchy
```
1. Environment Variables (.env)
2. Django Settings (settings.py)
3. Default Values (config.py)
4. Hardcoded Values (code)
```

---

## 🚀 Deployment Architecture

### Development Environment
```
Local Machine
├── Python Virtual Environment
├── SQLite Database
├── Local Vector Store
├── Development Server (Django)
└── Local File System
```

### Production Environment
```
Web Server (Nginx/Apache)
├── WSGI Server (Gunicorn)
├── Django Application
├── PostgreSQL Database
├── Persistent Vector Store
├── Static File Server
└── Load Balancer (optional)
```

---

## 🔒 Security Architecture

### Authentication & Authorization
```
Request → CORS Middleware → CSRF Protection → View Permission → Business Logic
    │            │              │                │              │
    │            │              │                │              │
    ▼            ▼              ▼                ▼              ▼
HTTP → CORS Check → CSRF Token → AllowAny → Process Request
```

### Data Protection
```
Sensitive Data → Encryption → Database → Decryption → Application
      │              │           │           │            │
      │              │           │           │            │
      ▼              ▼           ▼           ▼            ▼
API Keys → Environment → .env → Secure Storage → Runtime Use
```

---

## 📊 Monitoring & Logging

### Logging Architecture
```
Application Code → Logger → Log Handler → Log File/Console
       │              │          │            │
       │              │          │            │
       ▼              ▼          ▼            ▼
Error/Info → Python Logger → Console Handler → Terminal Output
```

### Metrics Collection
```
User Actions → Metrics Collector → Database → Analytics Dashboard
      │              │                │            │
      │              │                │            │
      ▼              ▼                ▼            ▼
Query Count → Utils.py → SQLite → /api/metrics/
```

---

## 🔄 Error Handling Architecture

### Error Flow
```
Exception → Try/Catch → Logger → Error Response → User Notification
     │           │         │         │              │
     │           │         │         │              │
     ▼           ▼         ▼         ▼              ▼
Error → views.py → Log → JSON Error → Frontend Alert
```

### Error Types
```
1. Validation Errors (400) - Invalid input
2. Authentication Errors (401) - Unauthorized
3. Permission Errors (403) - Forbidden
4. Not Found Errors (404) - Resource missing
5. Server Errors (500) - Internal issues
6. AI Service Errors (502) - External service down
```

---

## 🎯 Performance Optimization

### Caching Strategy
```
Frequent Data → Cache Layer → Memory/Disk → Fast Retrieval
      │              │           │            │
      │              │           │            │
      ▼              ▼           ▼            ▼
Vector Results → Redis Cache → Memory → Sub-second Response
```

### Database Optimization
```
Query → Query Optimizer → Index Usage → Efficient Retrieval
  │           │              │              │
  │           │              │              │
  ▼           ▼              ▼              ▼
SQL Query → Django ORM → Database Index → Fast Result
```

---

This architecture provides a robust, scalable foundation for your RAG AI Agent that can be easily extended and customized for various use cases! 🚀
