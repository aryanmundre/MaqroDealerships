import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from maqro_rag import Config, VehicleRetriever, EnhancedRAGService
from maqro_backend.core.config import settings
from maqro_backend.services.ai_services import analyze_conversation_context
# from maqro_backend.db.session import create_tables  # Removed - tables managed by Supabase


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
    logger.info("Starting up Maqro API...")
    
    # 1. Load RAG system for vehicle search
    config = Config.from_yaml(settings.rag_config_path)
    retriever = VehicleRetriever(config)
    
    # Initialize RAG retriever with proper error handling
    index_path = settings.rag_index_name
    inventory_file = "sample_inventory.csv"  # Default inventory file
    
    # Check if the FAISS index and metadata files exist
    if not (os.path.exists(f"{index_path}.faiss") and os.path.exists(f"{index_path}.metadata")):
        logger.warning(
            f"Index '{index_path}.faiss' not found. Building it from '{inventory_file}'..."
        )
        if not os.path.exists(inventory_file):
            logger.error(
                f"Inventory file '{inventory_file}' not found. Cannot build index."
            )
            raise FileNotFoundError(f"Required inventory file '{inventory_file}' not found")
        else:
            try:
                retriever.build_index(
                    inventory_file=inventory_file, save_path=index_path
                )
                logger.info(f"Successfully built and saved index to '{index_path}'")
            except Exception as e:
                logger.error(f"Failed to build RAG index: {e}")
                raise
    else:
        try:
            retriever.load_index(index_path)
            logger.info(f"Successfully loaded RAG index from '{index_path}'")
        except Exception as e:
            logger.error(f"Failed to load RAG index: {e}")
            raise
    
    # 2. Load Enhanced RAG service
    enhanced_rag_service = EnhancedRAGService(
        retriever=retriever, 
        analyze_conversation_context_func=analyze_conversation_context
    )
    logger.info("Enhanced RAG service loaded")

    # 3. Database tables are managed by Supabase
    logger.info("Database connection ready (tables managed by Supabase)")
    
    yield
    
    logger.info("Shutting down...")


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