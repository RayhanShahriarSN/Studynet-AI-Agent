# Data models
import os
from dotenv import load_dotenv
from typing import Optional

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
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    PARENT_CHUNK_SIZE: int = int(os.getenv("PARENT_CHUNK_SIZE", "1500"))
    
    # Memory
    MAX_MEMORY_TOKENS: int = int(os.getenv("MAX_MEMORY_TOKENS", "2000"))
    CONVERSATION_BUFFER_SIZE: int = int(os.getenv("CONVERSATION_BUFFER_SIZE", "10"))
    
    # FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Search Parameters
    RETRIEVER_K: int = 5  # Number of documents to retrieve
    RERANK_TOP_N: int = 3  # Number of documents after reranking
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score

config = Config()

# Pydantic models for API
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class MemoryContext(BaseModel):
    """Conversation memory context"""
    session_id: str
    messages: List[ChatMessage] = []
    total_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class QueryRequest(BaseModel):
    """Request model for query processing"""
    query: str = Field(..., description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    use_web_search: bool = Field(True, description="Whether to use web search as fallback")
    enhance_formatting: bool = Field(True, description="Whether to enhance response formatting")

class QueryResponse(BaseModel):
    """Response model for query processing"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(default=[], description="Source documents used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    web_search_used: bool = Field(False, description="Whether web search was used")
    session_id: str = Field(..., description="Session ID")

class DocumentUpload(BaseModel):
    """Model for text document upload"""
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")