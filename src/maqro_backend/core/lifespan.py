import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from maqro_rag import Config, VehicleRetriever, EnhancedRAGService
from maqro_rag.db_retriever import DatabaseRAGRetriever
from maqro_backend.core.config import settings
from maqro_backend.services.ai_services import analyze_conversation_context
from maqro_backend.db.session import get_db
from maqro_backend.crud import ensure_embeddings_for_dealership, get_rag_stats
# from maqro_backend.db.session import create_tables  # Removed - tables managed by Supabase


# Global variables to store RAG components
retriever = None
db_retriever = None
enhanced_rag_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs when the app starts up and shuts down
    - Startup: Load database-aware RAG system
    - Shutdown: Cleanup (if needed)
    """

    global retriever, db_retriever, enhanced_rag_service
    logger.info("Starting up Maqro API with Database RAG...")
    
    # 1. Load RAG configuration
    config = Config.from_yaml(settings.rag_config_path)
    
    # 2. Initialize database RAG retriever (no file dependencies)
    db_retriever = DatabaseRAGRetriever(config)
    logger.info("Database RAG retriever initialized")
    
    # 3. Keep legacy retriever for backward compatibility (if needed)
    retriever = VehicleRetriever(config) 
    
    # Try to load legacy index if it exists (fallback)
    index_path = settings.rag_index_name
    if os.path.exists(f"{index_path}.faiss") and os.path.exists(f"{index_path}.metadata"):
        try:
            retriever.load_index(index_path)
            logger.info("Legacy FAISS index loaded as fallback")
        except Exception as e:
            logger.warning(f"Could not load legacy index: {e}")
    
    # 4. Initialize Enhanced RAG service with database retriever
    enhanced_rag_service = EnhancedRAGService(
        retriever=db_retriever,  # Use database retriever
        analyze_conversation_context_func=analyze_conversation_context
    )
    logger.info("Enhanced RAG service loaded with database backend")

    # 5. Ensure embeddings exist for all dealerships on startup
    async for db_session in get_db():
        try:
            # For now, use default dealership ID for testing
            # TODO: In production, iterate through all dealerships
            default_dealership_id = "d660c7d6-99e2-4fa8-b99b-d221def53d20"
            
            logger.info("Checking RAG embeddings on startup...")
            embed_stats = await ensure_embeddings_for_dealership(
                session=db_session,
                dealership_id=default_dealership_id
            )
            
            if embed_stats.get("error"):
                logger.error(f"RAG embedding error: {embed_stats['error']}")
            else:
                logger.info(f"RAG ready: {embed_stats['total_embeddings']} embeddings, built {embed_stats['built_count']} new ones")
            
            break  # Exit after first session
        except Exception as e:
            logger.error(f"Error ensuring RAG embeddings on startup: {e}")
            # Continue startup even if embeddings fail
    
    # 6. Database tables are managed by Supabase
    logger.info("Database connection ready (tables managed by Supabase)")
    logger.info("🚀 Maqro API startup complete with Database RAG")
    
    yield
    
    logger.info("Shutting down...")


def get_retriever() -> VehicleRetriever:
    """Dependency to get the legacy RAG retriever (fallback)"""
    if retriever is None:
        raise RuntimeError("Legacy RAG system not initialized")
    return retriever

def get_db_retriever() -> DatabaseRAGRetriever:
    """Dependency to get the database RAG retriever"""
    if db_retriever is None:
        raise RuntimeError("Database RAG system not initialized")
    return db_retriever

def get_enhanced_rag_service() -> EnhancedRAGService:
    """Dependency to get the Enhanced RAG service"""
    if enhanced_rag_service is None:
        raise RuntimeError("Enhanced RAG service not initialized")
    return enhanced_rag_service