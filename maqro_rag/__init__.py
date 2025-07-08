"""
Maqro RAG Module - Inventory Embedding & Retrieval System

This module provides a complete RAG pipeline for auto dealership inventory:
- Ingests dealership inventory (CSV/JSON)
- Creates semantic embeddings using OpenAI/Cohere
- Stores embeddings in FAISS/Pinecone/Weaviate
- Retrieves top-k matching vehicles for lead queries
"""

from .config import Config
from .embedding import EmbeddingProvider
from .vector_store import VectorStore
from .inventory import InventoryProcessor
from .retrieval import VehicleRetriever

__version__ = "1.0.0"
__all__ = ["Config", "EmbeddingProvider", "VectorStore", "InventoryProcessor", "VehicleRetriever"] 