# Retrieval functionality for Django RAG backend
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import AzureChatOpenAI
from langchain.schema import Document
from .vectorstore import vector_store
from .config import config
import logging
from rank_bm25 import BM25Okapi
import numpy as np

# Cross-encoder for reranking
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

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


class HybridRetriever:
    """Hybrid retriever combining semantic search (embeddings) and keyword search (BM25)"""

    def __init__(self):
        self.vector_store = vector_store
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=200
        )

        # Initialize cross-encoder for reranking
        self.cross_encoder = None
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("Cross-encoder initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize cross-encoder: {e}")

        # Cache for BM25 index
        self.bm25_index = None
        self.bm25_documents = []

    def _build_bm25_index(self, documents: List[Document]) -> None:
        """Build BM25 index from documents

        Args:
            documents: List of documents to index
        """
        # Tokenize documents for BM25
        tokenized_docs = [doc.page_content.lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.bm25_documents = documents
        logger.info(f"BM25 index built with {len(documents)} documents")

    def keyword_search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """Perform keyword-based search using BM25

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if not self.bm25_index or not self.bm25_documents:
            logger.warning("BM25 index not built, building now...")
            # Get all documents from vector store
            all_docs = self._get_all_documents_from_vectorstore()
            if not all_docs:
                return []
            self._build_bm25_index(all_docs)

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)

        # Get top k indices
        k = min(k, len(scores))
        top_indices = np.argsort(scores)[-k:][::-1]

        # Return documents with scores
        results = [(self.bm25_documents[idx], float(scores[idx]))
                   for idx in top_indices if scores[idx] > 0]

        return results

    def semantic_search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """Perform semantic search using embeddings

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
            threshold=0.0  # No threshold for hybrid search
        )
        return results

    def reciprocal_rank_fusion(self,
                               semantic_results: List[Tuple[Document, float]],
                               keyword_results: List[Tuple[Document, float]],
                               k: int = 10,
                               semantic_weight: float = 0.6) -> List[Document]:
        """Combine results using Reciprocal Rank Fusion (RRF)

        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            k: Number of final results
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            Fused and ranked documents
        """
        keyword_weight = 1.0 - semantic_weight
        rrf_constant = 60  # Standard RRF constant

        # Build score dictionary
        doc_scores = {}

        # Add semantic search scores
        for rank, (doc, score) in enumerate(semantic_results):
            doc_id = id(doc)
            rrf_score = semantic_weight / (rrf_constant + rank + 1)
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {'doc': doc, 'score': 0}
            doc_scores[doc_id]['score'] += rrf_score
            doc_scores[doc_id]['doc'].metadata['semantic_score'] = score

        # Add keyword search scores
        for rank, (doc, score) in enumerate(keyword_results):
            doc_id = id(doc)
            rrf_score = keyword_weight / (rrf_constant + rank + 1)
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {'doc': doc, 'score': 0}
            doc_scores[doc_id]['score'] += rrf_score
            doc_scores[doc_id]['doc'].metadata['bm25_score'] = score

        # Sort by combined score
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)

        # Add RRF score to metadata
        for item in sorted_docs:
            item['doc'].metadata['rrf_score'] = item['score']

        return [item['doc'] for item in sorted_docs[:k]]

    def cross_encoder_rerank(self, query: str, documents: List[Document], top_n: int = 5) -> List[Document]:
        """Rerank documents using cross-encoder model

        Args:
            query: Search query
            documents: Documents to rerank
            top_n: Number of top documents to return

        Returns:
            Reranked documents
        """
        if not self.cross_encoder or not documents:
            return documents[:top_n]

        try:
            # Prepare query-document pairs
            pairs = [[query, doc.page_content[:512]] for doc in documents]

            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs)

            # Sort by score
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

            # Add cross-encoder scores to metadata
            reranked_docs = []
            for doc, score in doc_score_pairs[:top_n]:
                doc.metadata['cross_encoder_score'] = float(score)
                reranked_docs.append(doc)

            logger.info(f"Cross-encoder reranked {len(documents)} documents to top {top_n}")
            return reranked_docs

        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return documents[:top_n]

    def hybrid_search(self,
                     query: str,
                     k: int = 10,
                     semantic_weight: float = 0.6,
                     use_cross_encoder: bool = True) -> List[Document]:
        """Perform hybrid search combining semantic and keyword search

        Args:
            query: Search query
            k: Number of results to return
            semantic_weight: Weight for semantic results (0-1)
            use_cross_encoder: Whether to use cross-encoder reranking

        Returns:
            List of ranked documents
        """
        # Perform semantic search
        semantic_results = self.semantic_search(query, k=k*2)
        logger.info(f"Semantic search returned {len(semantic_results)} results")

        # Perform keyword search
        keyword_results = self.keyword_search(query, k=k*2)
        logger.info(f"Keyword search returned {len(keyword_results)} results")

        # Fuse results
        fused_docs = self.reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            k=k*2,
            semantic_weight=semantic_weight
        )

        # Rerank with cross-encoder if available
        if use_cross_encoder and self.cross_encoder:
            final_docs = self.cross_encoder_rerank(query, fused_docs, top_n=k)
        else:
            final_docs = fused_docs[:k]

        return final_docs

    def _get_all_documents_from_vectorstore(self) -> List[Document]:
        """Retrieve all documents from vector store for BM25 indexing

        Returns:
            List of all documents
        """
        try:
            # Get documents from child store
            child_collection = self.vector_store.child_store._collection
            all_docs = child_collection.get()

            documents = []
            if all_docs and all_docs['documents']:
                for i, content in enumerate(all_docs['documents']):
                    metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
                    doc = Document(page_content=content, metadata=metadata)
                    documents.append(doc)

            logger.info(f"Retrieved {len(documents)} documents from vector store")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents from vector store: {e}")
            return []

    def rebuild_bm25_index(self) -> bool:
        """Rebuild BM25 index from vector store

        Returns:
            True if successful
        """
        try:
            documents = self._get_all_documents_from_vectorstore()
            if documents:
                self._build_bm25_index(documents)
                return True
            return False
        except Exception as e:
            logger.error(f"Error rebuilding BM25 index: {e}")
            return False


# Singleton instances
retriever = IntelligentRetriever()
hybrid_retriever = HybridRetriever()
