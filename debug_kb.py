#!/usr/bin/env python
import os
import sys
import django

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_backend.settings')
django.setup()

from rag.utils import document_processor
from rag.config import config
from rag.vectorstore import vector_store
from rag.agent import rag_agent

def test_knowledge_base_loading():
    print("Testing knowledge base loading...")
    
    # Check if PDFs folder exists
    kb_path = config.KNOWLEDGE_BASE_PATH
    print(f"Knowledge base path: {kb_path}")
    print(f"Path exists: {os.path.exists(kb_path)}")
    
    if os.path.exists(kb_path):
        files = os.listdir(kb_path)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        print(f"PDF files found: {pdf_files}")
    
    # Test document loading
    try:
        print("\nLoading documents from PDFs folder...")
        documents = document_processor.load_knowledge_base(kb_path)
        print(f"Documents loaded: {len(documents)}")
        
        if documents:
            print(f"First document preview: {documents[0].page_content[:200]}...")
            print(f"First document metadata: {documents[0].metadata}")
        
        # Test adding to vector store
        if documents:
            print("\nTesting vector store addition...")
            success = rag_agent.add_documents(documents)
            print(f"Vector store addition successful: {success}")
            
            if success:
                # Test search
                print("\nTesting search...")
                results = vector_store.similarity_search_with_score("test query", k=3)
                print(f"Search results: {len(results)}")
                for i, (doc, score) in enumerate(results):
                    print(f"Result {i+1}: Score {score:.3f} - {doc.page_content[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_base_loading()
