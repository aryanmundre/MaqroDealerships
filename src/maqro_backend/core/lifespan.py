from contextlib import asynccontextmanager
from fastapi import FastAPI
from maqro_rag import Config, VehicleRetriever, EnhancedRAGService
from maqro_backend.core.config import settings
from maqro_backend.db.session import create_tables


# Global variable to store retriever  
retriever = None
enhanced_rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs when the app starts up and shuts down
    - Startup: Load RAG system + Create database tables
    - Shutdown: Cleanup (if needed)
    """

    global retriever, enhanced_rag_service
    print("Starting up Maqro API...")
    
    # 1. Load RAG system for vehicle search
    config = Config.from_yaml(settings.rag_config_path)
    retriever = VehicleRetriever(config)
    retriever.load_index(settings.rag_index_name)
    
    # 2. Load Enhanced RAG service
    enhanced_rag_service = EnhancedRAGService(retriever)
    print("Enhanced RAG service loaded")

    # 3. Create database tables if they don't exist
    await create_tables()
    print("Database tables ready")
    
    yield
    
    print("Shutting down...")


def get_retriever() -> VehicleRetriever:
    """Dependency to get the RAG retriever"""
    if retriever is None:
        raise RuntimeError("RAG system not initialized")
    return retriever

def get_enhanced_rag_service() -> EnhancedRAGService:
    """Dependency to get the Enhanced RAG service"""
    if enhanced_rag_service is None:
        raise RuntimeError("Enhanced RAG service not initialized")
    return enhanced_rag_service