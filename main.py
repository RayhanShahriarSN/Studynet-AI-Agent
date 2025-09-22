# Main application entry point
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
import time
import os
import tempfile
from contextlib import asynccontextmanager

from models import QueryRequest, QueryResponse, DocumentUpload, MemoryContext
from agent import rag_agent
from memory import memory_manager
from utils import document_processor, metrics_collector, response_formatter
from config import config
from langchain.schema import Document

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting RAG Pipeline API...")
    logger.info(f"Azure Endpoint: {config.AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Vector DB Path: {config.VECTOR_DB_PATH}")
    logger.info(f"Knowledge Base Path: {config.KNOWLEDGE_BASE_PATH}")
    
    # Create necessary directories
    os.makedirs(config.VECTOR_DB_PATH, exist_ok=True)
    os.makedirs(f"{config.VECTOR_DB_PATH}/parent", exist_ok=True)
    os.makedirs(f"{config.VECTOR_DB_PATH}/child", exist_ok=True)
    os.makedirs(config.KNOWLEDGE_BASE_PATH, exist_ok=True)
    
    # Load knowledge base documents from PDFs folder
    logger.info("Loading knowledge base documents from PDFs folder...")
    try:
        kb_documents = document_processor.load_knowledge_base(config.KNOWLEDGE_BASE_PATH)
        if kb_documents:
            success = rag_agent.add_documents(kb_documents)
            if success:
                logger.info(f"Successfully loaded {len(kb_documents)} documents from PDFs folder")
            else:
                logger.warning("Failed to add some documents to vector store")
        else:
            logger.info("No documents found in PDFs folder")
    except Exception as e:
        logger.error(f"Error loading knowledge base from PDFs folder: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Pipeline API...")

# Initialize FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="Intelligent RAG system with memory context and web search",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RAG Pipeline API",
        "version": "1.0.0",
        "data_source": "PDFs folder (./pdfs/)",
        "features": {
            "knowledge_base": "Active",
            "web_search": "Active",
            "data_location": "pdfs/ folder"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a user query through the RAG pipeline"""
    start_time = time.time()
    
    try:
        # Process query through RAG agent with enhanced formatting
        result = rag_agent.process_query(
            query=request.query,
            session_id=request.session_id,
            use_web_search=request.use_web_search,
            enhance_formatting=request.enhance_formatting
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record metrics in background
        background_tasks.add_task(
            metrics_collector.record_query,
            response_time,
            len(result.get("sources", [])) > 0,
            result.get("web_search_used", False)
        )
        
        # Format response
        response = QueryResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            confidence_score=result.get("confidence_score", 0.5),
            web_search_used=result.get("web_search_used", False),
            session_id=result["session_id"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        metrics_collector.record_error()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process document
        documents = document_processor.load_document(tmp_file_path)
        
        # Add to vector store
        success = rag_agent.add_documents(documents)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Document {file.filename} processed successfully",
                "chunks_created": len(documents)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add documents to vector store")
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/text")
async def upload_text(upload: DocumentUpload):
    """Upload raw text content"""
    try:
        # Process text
        doc = document_processor.process_text(upload.content, upload.metadata)
        
        # Add to vector store
        success = rag_agent.add_documents([doc])
        
        if success:
            return {
                "status": "success",
                "message": "Text content processed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add content to vector store")
            
    except Exception as e:
        logger.error(f"Error uploading text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{session_id}")
async def get_memory(session_id: str):
    """Get conversation memory for a session"""
    try:
        context = memory_manager.get_conversation_context(session_id)
        memory_vars = memory_manager.get_memory_variables(session_id)
        
        return {
            "session_id": session_id,
            "context": context,
            "memory": memory_vars
        }
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Clear conversation memory for a session"""
    try:
        memory_manager.clear_session(session_id)
        return {"status": "success", "message": f"Memory cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        sessions = memory_manager.get_all_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        metrics = metrics_collector.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metrics/reset")
async def reset_metrics():
    """Reset system metrics"""
    try:
        metrics_collector.reset_metrics()
        return {"status": "success", "message": "Metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-base/status")
async def get_knowledge_base_status():
    """Get knowledge base status and statistics"""
    try:
        from vectorstore import vector_store
        
        # Get collection info
        parent_count = vector_store.parent_store._collection.count()
        child_count = vector_store.child_store._collection.count()
        
        return {
            "status": "active",
            "parent_chunks": parent_count,
            "child_chunks": child_count,
            "total_documents": parent_count + child_count,
            "knowledge_base_path": config.KNOWLEDGE_BASE_PATH,
            "data_source": "PDFs folder (./pdfs/)"
        }
    except Exception as e:
        logger.error(f"Error getting knowledge base status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge-base/reload")
async def reload_knowledge_base():
    """Reload knowledge base from PDFs folder"""
    try:
        # Clear existing vector store
        from vectorstore import vector_store
        vector_store.delete_collection()
        
        # Reload documents from PDFs folder
        kb_documents = document_processor.load_knowledge_base(config.KNOWLEDGE_BASE_PATH)
        if kb_documents:
            success = rag_agent.add_documents(kb_documents)
            if success:
                return {
                    "status": "success",
                    "message": f"Knowledge base reloaded with {len(kb_documents)} documents from PDFs folder"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to add documents to vector store")
        else:
            return {
                "status": "success",
                "message": "No documents found in PDFs folder"
            }
    except Exception as e:
        logger.error(f"Error reloading knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/vectorstore/clear")
async def clear_vectorstore():
    """Clear the entire vector store (use with caution)"""
    try:
        from vectorstore import vector_store
        vector_store.delete_collection()
        return {"status": "success", "message": "Vector store cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing vector store: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )