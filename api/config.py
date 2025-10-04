# Configuration settings for Django RAG backend
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the RAG pipeline"""
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    
    # Model Deployments
    CHAT_MODEL_DEPLOYMENT: str = os.getenv("CHAT_MODEL_DEPLOYMENT", "chat-heavy")
    EMBEDDING_MODEL_DEPLOYMENT: str = os.getenv("EMBEDDING_MODEL_DEPLOYMENT", "embed-large")
    
    # Tavily Web Search
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")
    
    # Vector Store
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vector_store")
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./pdfs")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    PARENT_CHUNK_SIZE: int = int(os.getenv("PARENT_CHUNK_SIZE", "1500"))
    
    # Memory
    MAX_MEMORY_TOKENS: int = int(os.getenv("MAX_MEMORY_TOKENS", "2000"))
    CONVERSATION_BUFFER_SIZE: int = int(os.getenv("CONVERSATION_BUFFER_SIZE", "10"))
    
    # Django API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Search Parameters
    RETRIEVER_K: int = 5  # Number of documents to retrieve
    RERANK_TOP_N: int = 3  # Number of documents after reranking
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score

    # NEW: Hybrid Retrieval Parameters
    BM25_K1: float = 1.5  # BM25 k1 parameter
    BM25_B: float = 0.75  # BM25 b parameter
    SEMANTIC_WEIGHT: float = 0.6  # Weight for semantic search in hybrid (0-1)
    USE_CROSS_ENCODER: bool = True  # Enable cross-encoder reranking
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # NEW: Query Enhancement Parameters
    ENABLE_QUERY_ENHANCEMENT: bool = True  # Enable query enhancement
    ENABLE_QUERY_CLASSIFICATION: bool = True  # Enable query classification
    MAX_QUERY_VARIATIONS: int = 3  # Number of query variations to generate

    # NEW: SQL Engine Parameters
    SQL_QUERY_LIMIT: int = 100  # Default limit for SQL queries
    ENABLE_SQL_CACHE: bool = False  # Cache SQL query results (future feature)

    # NEW: Analytics Parameters
    ENABLE_ANALYTICS: bool = True  # Track query analytics
    ANALYTICS_RETENTION_DAYS: int = 30  # Keep analytics for 30 days

config = Config()
