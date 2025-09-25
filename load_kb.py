#!/usr/bin/env python
import os
import sys
import django

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authapi.settings')
django.setup()

from rag.utils import document_processor
from rag.config import config
from rag.agent import rag_agent

def load_knowledge_base():
    print("Loading knowledge base...")
    
    # Load documents from PDFs folder
    kb_documents = document_processor.load_knowledge_base(config.KNOWLEDGE_BASE_PATH)
    
    if kb_documents:
        print(f"Loaded {len(kb_documents)} documents from PDFs folder")
        
        # Add to vector store
        success = rag_agent.add_documents(kb_documents)
        
        if success:
            print("✅ Knowledge base loaded successfully!")
            return True
        else:
            print("❌ Failed to add documents to vector store")
            return False
    else:
        print("❌ No documents found in PDFs folder")
        return False

if __name__ == "__main__":
    load_knowledge_base()
