# Embeddings functionality
from typing import List
from langchain_openai import AzureOpenAIEmbeddings
from config import config
import numpy as np

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
    
    def similarity_search(self, query_embedding: List[float], 
                         document_embeddings: List[List[float]], 
                         k: int = 5) -> List[tuple]:
        """Calculate cosine similarity and return top k results"""
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(document_embeddings)
        
        # Calculate cosine similarity
        similarities = np.dot(doc_vecs, query_vec) / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
        )
        
        # Get top k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        return [(idx, similarities[idx]) for idx in top_k_indices]

# Singleton instance
embedding_service = EmbeddingService()