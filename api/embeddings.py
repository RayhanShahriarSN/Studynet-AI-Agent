# Embeddings functionality for Django RAG backend
from typing import List
from langchain_openai import AzureOpenAIEmbeddings
from .config import config

class EmbeddingService:
    """Service for handling text embeddings using Azure OpenAI"""

    def __init__(self):
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=config.EMBEDDING_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            model="text-embedding-3-large",
            dimensions=3072
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self.embeddings.embed_query(text)

# Singleton instance
embedding_service = EmbeddingService()
