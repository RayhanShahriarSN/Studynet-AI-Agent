# RAG Pipeline API

A production-ready Retrieval Augmented Generation (RAG) system that combines knowledge base search with web search capabilities, featuring intelligent document retrieval, conversational memory, and agent-based architecture.

## API Endpoints

### Core Query Processing

#### `POST /query`

Process user queries through the RAG pipeline

```json
{
  "query": "How do I add a lead?",
  "session_id": "optional-session-id",
  "use_web_search": true
}
```

#### `GET /`

Health check and system status

```json
{
  "status": "healthy",
  "service": "RAG Pipeline API",
  "version": "1.0.0"
}
```

### Document Management

#### `POST /upload/document`

Upload and process documents (PDF, TXT, DOCX, CSV, JSON)

- **Content-Type**: `multipart/form-data`
- **File**: Document file to process

#### `POST /upload/text`

Add raw text content to knowledge base

```json
{
  "content": "Text content to add",
  "metadata": { "source": "manual_entry" }
}
```

### Memory Management

#### `GET /memory/{session_id}`

Retrieve conversation history for a session

#### `DELETE /memory/{session_id}`

Clear conversation memory for a specific session

#### `GET /sessions`

List all active conversation sessions

### System Monitoring

#### `GET /metrics`

Get system performance metrics

```json
{
  "queries_processed": 150,
  "avg_response_time": 2.3,
  "kb_hits": 120,
  "web_searches": 30,
  "errors": 2
}
```

#### `POST /metrics/reset`

Reset system metrics to zero

### Knowledge Base Management

#### `GET /knowledge-base/status`

Get knowledge base statistics and status

```json
{
  "status": "active",
  "parent_chunks": 245,
  "child_chunks": 1230,
  "total_documents": 1475
}
```

#### `POST /knowledge-base/reload`

Reload knowledge base from PDFs folder

#### `DELETE /vectorstore/clear`

Clear entire vector store (destructive operation)

## Features

- **Hierarchical Vector Storage**: Parent-child chunking for better context preservation
- **Intelligent Retrieval**: Query reformulation and LLM-based reranking
- **Conversational Memory**: Token-aware conversation management with summarization
- **Hybrid Search**: Knowledge base + web search fallback
- **Agent-based Architecture**: ReAct agent with tool selection
- **Multi-format Support**: PDF, TXT, DOCX, CSV, JSON document processing

## Quick Start

### Prerequisites

- Python 3.8+
- Azure OpenAI account with deployed models
- Tavily API key for web search

### Installation

1. **Clone and setup environment**:

```bash
git clone <repository>
cd rag-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
   Create `.env` file:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CHAT_MODEL_DEPLOYMENT=gpt-4
EMBEDDING_MODEL_DEPLOYMENT=text-embedding-ada-002
TAVILY_API_KEY=your_tavily_api_key
```

3. **Setup knowledge base**:

```bash
mkdir pdfs
# Copy your PDF documents to the pdfs folder
```

4. **Run the application**:

```bash
python main.py
```

API will be available at `http://localhost:8000`

### Interactive Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Basic Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I reset my password?"}'
```

### Upload Document

```bash
curl -X POST "http://localhost:8000/upload/document" \
  -F "file=@manual.pdf"
```

### Session Management

```python
import requests

# Start conversation
response1 = requests.post("http://localhost:8000/query", json={
    "query": "What is RAG?"
})
session_id = response1.json()["session_id"]

# Continue conversation with context
response2 = requests.post("http://localhost:8000/query", json={
    "query": "How does it work?",
    "session_id": session_id
})
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   RAG Agent     │
│   (Streamlit)   │◄──►│   Backend       │◄──►│   (LangChain)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                               ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │    │   Vector Store  │    │   Memory        │
│   Processor     │◄──►│   (Chroma)      │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDFs Folder   │    │   Azure OpenAI  │    │   Tavily Web    │
│   Knowledge     │    │   Embeddings    │    │   Search        │
│   Base          │    │   + Chat        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Components

### RAG Techniques

- **Hierarchical Chunking**: Parent chunks (1500 chars) for context, child chunks (500 chars) for precision
- **Query Enhancement**: LLM-based query reformulation and multiple query variations
- **Advanced Retrieval**: Semantic similarity search with hybrid search capabilities
- **Intelligent Reranking**: LLM-based semantic reranking for relevance
- **Memory Management**: Conversation context preservation with token-aware summarization

### Technology Stack

- **LangChain**: Agent framework and RAG orchestration
- **Azure OpenAI**: LLM (chat) and embeddings
- **Chroma**: Vector database for document storage
- **Tavily**: Web search API for real-time information
- **FastAPI**: RESTful API framework
- **Pydantic**: Data validation and serialization

## Configuration

### Key Parameters

```python
# Chunking Strategy
CHUNK_SIZE = 500                # Child chunk size
CHUNK_OVERLAP = 100            # Overlap between chunks
PARENT_CHUNK_SIZE = 1500       # Parent chunk size

# Retrieval Parameters
RETRIEVER_K = 5                # Documents to retrieve
SIMILARITY_THRESHOLD = 0.7     # Minimum similarity score

# Memory Management
MAX_MEMORY_TOKENS = 2000       # Maximum tokens in memory
CONVERSATION_BUFFER_SIZE = 10  # Message buffer size
```

## File Structure

```
rag-pipeline/
├── agent.py              # Main RAG agent with ReAct pattern
├── config.py             # Configuration management
├── embeddings.py         # Azure OpenAI embedding service
├── main.py               # FastAPI application server
├── memory.py             # Conversation memory management
├── models.py             # Pydantic data models
├── retriever.py          # Intelligent retrieval system
├── utils.py              # Document processing utilities
├── vectorstore.py        # Hierarchical vector storage
├── streamlit_app.py      # Streamlit frontend interface
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration
├── pdfs/                 # Knowledge base documents
└── vector_store/         # Vector database storage
    ├── parent/           # Parent chunk storage
    └── child/            # Child chunk storage
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### API Documentation

The API automatically generates interactive documentation:

- **Swagger UI**: Navigate to `/docs` for interactive API testing
- **ReDoc**: Navigate to `/redoc` for detailed API documentation

### Environment Variables

All configuration is managed through environment variables. See `config.py` for complete list of available settings.

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security Considerations

- Configure CORS appropriately for production
- Implement authentication mechanisms
- Use environment-specific configurations
- Monitor and log API usage
- Set up rate limiting

### Monitoring

The system includes built-in metrics collection:

- Query processing statistics
- Response time monitoring
- Knowledge base hit rates
- Error tracking

Access metrics via `/metrics` endpoint or integrate with monitoring solutions like Prometheus.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

- Check the documentation
- Review API endpoints at `/docs`
- Create an issue in the repository
