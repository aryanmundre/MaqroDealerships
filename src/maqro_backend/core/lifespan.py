from contextlib import asynccontextmanager
from fastapi import FastAPI
from maqro_rag import Config, VehicleRetriever
from maqro_backend.core.config import settings
from maqro_backend.db.session import create_tables


# Global variable to store retriever  
retriever = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs when the app starts up and shuts down
    - Startup: Load RAG system + Create database tables
    - Shutdown: Cleanup (if needed)
    """

    global retriever
    print("Starting up Maqro API...")
    
    # 1. Load RAG system for vehicle search
    config = Config.from_yaml(settings.rag_config_path)
    retriever = VehicleRetriever(config)
    retriever.load_index(settings.rag_index_name)
    print("RAG system loaded")
    
    # 2. Create database tables if they don't exist
    await create_tables()
    print("Database tables ready")
    
    yield
    
    print("Shutting down...")


def get_retriever() -> VehicleRetriever:
    """Dependency to get the RAG retriever"""
    if retriever is None:
        raise RuntimeError("RAG system not initialized")
    return retriever
