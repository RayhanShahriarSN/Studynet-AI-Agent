# Vector store implementation for Django RAG backend
import os
from typing import List, Dict, Any, Optional, Tuple
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from .embeddings import embedding_service
from .config import config
import uuid

class HierarchicalVectorStore:
    """Hierarchical vector store with parent-child chunking"""
    
    def __init__(self):
        self.embedding_function = embedding_service.embeddings
        
        # Initialize parent and child vector stores
        self.parent_store = Chroma(
            collection_name="parent_chunks",
            embedding_function=self.embedding_function,
            persist_directory=f"{config.VECTOR_DB_PATH}/parent"
        )
        
        self.child_store = Chroma(
            collection_name="child_chunks",
            embedding_function=self.embedding_function,
            persist_directory=f"{config.VECTOR_DB_PATH}/child"
        )
        
        # Text splitters for hierarchical chunking
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.PARENT_CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP * 2,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Mapping between parent and child chunks
        self.parent_child_map: Dict[str, List[str]] = {}
        
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents with hierarchical chunking"""
        all_parent_ids = []

        for doc in documents:
            # Skip empty documents
            if not doc.page_content or len(doc.page_content.strip()) == 0:
                continue

            # Create parent chunks
            try:
                parent_chunks = self.parent_splitter.split_text(doc.page_content)
            except Exception as e:
                # If chunking fails, use entire content as one chunk
                parent_chunks = [doc.page_content]

            for parent_chunk in parent_chunks:
                # Skip empty chunks
                if not parent_chunk or len(parent_chunk.strip()) == 0:
                    continue

                parent_id = str(uuid.uuid4())

                # Create child chunks from parent
                try:
                    child_chunks = self.child_splitter.split_text(parent_chunk)
                except Exception as e:
                    # If chunking fails, use entire parent as one child
                    child_chunks = [parent_chunk]

                child_ids = []

                # Add child chunks
                for i, child_chunk in enumerate(child_chunks):
                    if not child_chunk or len(child_chunk.strip()) == 0:
                        continue

                    child_id = f"{parent_id}_child_{i}"
                    child_doc = Document(
                        page_content=child_chunk,
                        metadata={
                            **doc.metadata,
                            "parent_id": parent_id,
                            "chunk_index": i,
                            "chunk_type": "child"
                        }
                    )
                    self.child_store.add_documents([child_doc], ids=[child_id])
                    child_ids.append(child_id)

                # Only add parent if we have children
                if child_ids:
                    # Add parent chunk
                    parent_doc = Document(
                        page_content=parent_chunk,
                        metadata={
                            **doc.metadata,
                            "chunk_type": "parent",
                            "num_children": len(child_ids)
                        }
                    )
                    self.parent_store.add_documents([parent_doc], ids=[parent_id])

                    # Store mapping
                    self.parent_child_map[parent_id] = child_ids
                    all_parent_ids.append(parent_id)

        return all_parent_ids
    
    def similarity_search_with_score(self, query: str, k: int = 5, 
                                    threshold: float = 0.7) -> List[Tuple[Document, float]]:
        """Search with hierarchical retrieval"""
        # Ensure k is positive
        k = max(1, k)
        
        # Search in child chunks
        child_results = self.child_store.similarity_search_with_score(query, k=k*2)
        
        # Filter by threshold
        filtered_results = [(doc, score) for doc, score in child_results if score >= threshold]
        
        # Get unique parent IDs
        parent_ids = list(set([doc.metadata.get("parent_id") for doc, _ in filtered_results 
                              if doc.metadata.get("parent_id")]))
        
        # Retrieve parent documents for context
        enriched_results = []
        for doc, score in filtered_results[:k]:
            parent_id = doc.metadata.get("parent_id")
            if parent_id:
                parent_docs = self.parent_store.get(ids=[parent_id])
                if parent_docs and parent_docs["documents"]:
                    doc.metadata["parent_context"] = parent_docs["documents"][0]
            enriched_results.append((doc, score))
        
        return enriched_results
    
    def hybrid_search(self, query: str, k: int = 5, 
                     metadata_filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Hybrid search combining semantic and keyword search"""
        # Ensure k is positive
        k = max(1, k)
        
        # Semantic search
        semantic_results = self.similarity_search_with_score(query, k=k)
        
        # Keyword search (using metadata if provided)
        if metadata_filters:
            keyword_results = self.child_store.get(
                where=metadata_filters,
                limit=k
            )
            # Combine and deduplicate results
            combined = semantic_results + [(Document(page_content=doc, metadata={}), 0.5) 
                                          for doc in keyword_results.get("documents", [])]
            # Sort by score and deduplicate
            seen = set()
            final_results = []
            for doc, score in sorted(combined, key=lambda x: x[1], reverse=True):
                if doc.page_content not in seen:
                    seen.add(doc.page_content)
                    final_results.append(doc)
                    if len(final_results) >= k:
                        break
            return final_results
        
        return [doc for doc, _ in semantic_results]
    
    def delete_collection(self):
        """Clear the vector stores"""
        try:
            self.parent_store.delete_collection()
        except:
            pass
        try:
            self.child_store.delete_collection()
        except:
            pass
        self.parent_child_map.clear()
        
        # Reinitialize the stores
        self.parent_store = Chroma(
            collection_name="parent_chunks",
            embedding_function=self.embedding_function,
            persist_directory=f"{config.VECTOR_DB_PATH}/parent"
        )
        
        self.child_store = Chroma(
            collection_name="child_chunks",
            embedding_function=self.embedding_function,
            persist_directory=f"{config.VECTOR_DB_PATH}/child"
        )

# Singleton instance
vector_store = HierarchicalVectorStore()
