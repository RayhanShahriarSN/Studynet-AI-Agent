# Retrieval functionality for Django RAG backend
from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain.schema import Document
from .vectorstore import vector_store
from .config import config
import logging

logger = logging.getLogger(__name__)

class IntelligentRetriever:
    """Advanced retriever with query reformulation and reranking"""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=200
        )
        
        self.vector_store = vector_store
    
    def reformulate_query(self, query: str, context: Optional[str] = None) -> List[str]:
        """Use LLM to reformulate query for better retrieval"""
        prompt = f"""Given the user query, generate 3 alternative search queries that would help find relevant information.
        These should capture different aspects or phrasings of the original query.
        
        Original Query: {query}
        """
        
        if context:
            prompt += f"\n\nConversation Context:\n{context}"
        
        prompt += "\n\nGenerate 3 alternative queries (one per line):"
        
        try:
            response = self.llm.invoke(prompt)
            alternatives = response.content.strip().split('\n')
            # Clean and filter alternatives
            alternatives = [q.strip().lstrip('123.-) ') for q in alternatives if q.strip()][:3]
            return [query] + alternatives
        except Exception as e:
            logger.error(f"Query reformulation failed: {e}")
            return [query]
    
    def rerank_results(self, query: str, documents: List[Document], 
                      top_n: int = 3) -> List[Document]:
        """Use LLM to rerank search results based on relevance"""
        if not documents or len(documents) <= top_n:
            return documents[:top_n] if documents else []
        
        # Prepare documents for reranking
        doc_texts = []
        for i, doc in enumerate(documents[:10]):  # Limit to top 10 for reranking
            doc_texts.append(f"[{i}] {doc.page_content[:500]}")
        
        prompt = f"""Given the query and the following documents, rank them by relevance to the query.
        Return only the indices of the top {top_n} most relevant documents in order, separated by commas.
        
        Query: {query}
        
        Documents:
        {chr(10).join(doc_texts)}
        
        Top {top_n} indices (comma-separated):"""
        
        try:
            response = self.llm.invoke(prompt)
            indices_str = response.content.strip()
            indices = [int(idx.strip()) for idx in indices_str.split(',') if idx.strip().isdigit()]
            
            # Return reranked documents
            reranked = []
            for idx in indices[:top_n]:
                if 0 <= idx < len(documents):
                    reranked.append(documents[idx])
            
            # Fill with original order if reranking didn't work perfectly
            if len(reranked) < top_n:
                for doc in documents:
                    if doc not in reranked and len(reranked) < top_n:
                        reranked.append(doc)
            
            return reranked
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents[:top_n]
    
    def retrieve(self, query: str, k: int = 5, 
                use_reformulation: bool = True,
                use_reranking: bool = True,
                context: Optional[str] = None) -> List[Document]:
        """Main retrieval pipeline with all enhancements"""
        
        # Ensure k is positive
        k = max(1, k)
        
        # Step 1: Query reformulation
        queries = [query]
        if use_reformulation:
            queries = self.reformulate_query(query, context)
            logger.info(f"Reformulated queries: {queries}")
        
        # Step 2: Retrieve documents for all queries
        all_documents = []
        seen_contents = set()
        
        for q in queries:
            results = self.vector_store.similarity_search_with_score(
                q, 
                k=k * 2,  # Get more initially for better reranking
                threshold=config.SIMILARITY_THRESHOLD
            )
            
            for doc, score in results:
                # Deduplicate based on content
                if doc.page_content not in seen_contents:
                    seen_contents.add(doc.page_content)
                    doc.metadata['retrieval_score'] = score
                    all_documents.append(doc)
        
        # Step 3: Sort by score
        all_documents.sort(key=lambda x: x.metadata.get('retrieval_score', 0), reverse=True)
        
        # Step 4: Rerank if enabled
        if use_reranking and len(all_documents) > 0:
            all_documents = self.rerank_results(query, all_documents, top_n=k)
        else:
            all_documents = all_documents[:k]
        
        return all_documents
    
    def retrieve_with_metadata_filter(self, query: str, 
                                     metadata_filters: Dict[str, Any],
                                     k: int = 5) -> List[Document]:
        """Retrieve with metadata filtering (hybrid search)"""
        return self.vector_store.hybrid_search(
            query=query,
            k=k,
            metadata_filters=metadata_filters
        )

# Singleton instance
retriever = IntelligentRetriever()