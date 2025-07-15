# RAG package for Maqro Dealership vehicle inventory processing
"""
Maqro RAG (Retrieval-Augmented Generation) package for processing
vehicle inventory and providing intelligent search capabilities.
"""

__version__ = "0.1.0"

# Core components
from maqro_rag.config import Config
from maqro_rag.embedding import EmbeddingProvider
from maqro_rag.vector_store import VectorStore
from maqro_rag.inventory import InventoryProcessor
from maqro_rag.retrieval import VehicleRetriever

__all__ = [
    "Config",
    "EmbeddingProvider", 
    "VectorStore",
    "InventoryProcessor",
    "VehicleRetriever"
] 