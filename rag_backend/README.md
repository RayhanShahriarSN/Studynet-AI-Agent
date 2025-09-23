# Django RAG Backend

A Django REST API backend for the RAG (Retrieval Augmented Generation) pipeline, migrated from FastAPI.

## Features

- **Django REST Framework**: Modern API endpoints with automatic documentation
- **RAG Pipeline**: Intelligent document retrieval and generation
- **Memory Management**: Conversation context preservation
- **Document Processing**: Support for PDF, TXT, DOCX, CSV, JSON files
- **Web Search Integration**: Tavily search for real-time information
- **Vector Database**: Hierarchical chunking with ChromaDB
- **Azure OpenAI**: Integration with Azure OpenAI services

## API Endpoints

### Core Query Processing
- `GET /api/` - Health check and system status
- `POST /api/query/` - Process user queries through RAG pipeline

### Document Management
- `POST /api/upload/document/` - Upload and process documents
- `POST /api/upload/text/` - Add raw text content

### Memory Management
- `GET /api/memory/{session_id}/` - Get conversation memory
- `DELETE /api/memory/{session_id}/` - Clear conversation memory
- `GET /api/sessions/` - List all active sessions

### System Monitoring
- `GET /api/metrics/` - Get system performance metrics
- `POST /api/metrics/` - Reset system metrics

### Knowledge Base Management
- `GET /api/knowledge-base/status/` - Get knowledge base statistics
- `POST /api/knowledge-base/reload/` - Reload knowledge base from PDFs
- `DELETE /api/vectorstore/clear/` - Clear vector store

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Create `.env` file in the project root:
   ```env
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   CHAT_MODEL_DEPLOYMENT=chat-heavy
   EMBEDDING_MODEL_DEPLOYMENT=embed-large
   TAVILY_API_KEY=your_tavily_api_key
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the server**:
   ```bash
   python manage.py runserver
   ```

## Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I add a lead?"}'
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/upload/document/" \
  -F "file=@manual.pdf"
```

### Session Management
```python
import requests

# Start conversation
response1 = requests.post("http://localhost:8000/api/query/", json={
    "query": "What is RAG?"
})
session_id = response1.json()["session_id"]

# Continue conversation with context
response2 = requests.post("http://localhost:8000/api/query/", json={
    "query": "How does it work?",
    "session_id": session_id
})
```

## Migration from FastAPI

This Django backend is a complete migration from the original FastAPI project. All functionality has been preserved:

- **FastAPI → Django REST Framework**: All endpoints converted to DRF APIViews
- **Pydantic Models → Django Models**: Data models converted to Django ORM
- **FastAPI Dependencies → Django Apps**: Modular structure with Django apps
- **Uvicorn → Django Dev Server**: Development server replaced
- **FastAPI Middleware → Django Middleware**: CORS and other middleware configured

## API Documentation

- **Django Admin**: `http://localhost:8000/admin/`
- **API Root**: `http://localhost:8000/api/`
- **Browsable API**: Available at all endpoints when using a web browser

## Project Structure

```
rag_backend/
├── api/                    # Main API app
│   ├── models.py          # Django models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # URL routing
│   ├── agent.py           # RAG agent
│   ├── memory.py          # Memory management
│   ├── utils.py           # Utility functions
│   ├── config.py          # Configuration
│   ├── embeddings.py      # Embedding service
│   ├── vectorstore.py     # Vector database
│   └── retriever.py       # Document retrieval
├── rag_backend/           # Django project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI configuration
├── pdfs/                  # Knowledge base documents
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── start_server.py        # Startup script
```

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Production Deployment

### Using Gunicorn
```bash
gunicorn rag_backend.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables
All configuration is managed through environment variables. See `api/config.py` for the complete list.

## License

This project is licensed under the MIT License.
