# RAG package for Maqro Dealership vehicle inventory processing
"""
Maqro RAG (Retrieval-Augmented Generation) package for processing
vehicle inventory and providing intelligent search capabilities.
"""

__version__ = "0.1.0"

# Core components
from maqro_rag.config import Config
from maqro_rag.embedding import EmbeddingProvider, get_embedding_provider, EmbeddingManager
from maqro_rag.vector_store import VectorStore, get_vector_store
from maqro_rag.inventory import InventoryProcessor, VehicleData
from maqro_rag.retrieval import VehicleRetriever
from maqro_rag.rag_enhanced import EnhancedRAGService, ConversationContext, ResponseQuality, ResponseTemplate

__all__ = [
    "Config",
    "EmbeddingProvider", 
    "get_embedding_provider",
    "EmbeddingManager",
    "VectorStore",
    "get_vector_store",
    "InventoryProcessor",
    "VehicleData",
    "VehicleRetriever",
    "EnhancedRAGService",
    "ConversationContext",
    "ResponseQuality",
    "ResponseTemplate"
] 