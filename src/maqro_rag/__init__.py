# RAG package for Maqro Dealership vehicle inventory processing
"""
Maqro RAG (Retrieval-Augmented Generation) package for processing
vehicle inventory and providing intelligent search capabilities.
"""

__version__ = "0.1.0"

# Core components
from .config import Config
from .embedding import EmbeddingProvider, get_embedding_provider, EmbeddingManager
from .vector_store import VectorStore, get_vector_store
from .inventory import InventoryProcessor, VehicleData
from .retrieval import VehicleRetriever
from .rag_enhanced import EnhancedRAGService, ConversationContext, ResponseQuality, ResponseTemplate
from .entity_parser import EntityParser, VehicleQuery
from .prompt_builder import PromptBuilder, AgentConfig

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
    "ResponseTemplate",
    "EntityParser",
    "VehicleQuery",
    "PromptBuilder",
    "AgentConfig"
] 