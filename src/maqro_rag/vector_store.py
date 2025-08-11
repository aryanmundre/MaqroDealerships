"""
Vector store module for storing and retrieving embeddings.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import faiss
from loguru import logger
from .config import Config


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to the store with metadata."""
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save the vector store to disk."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load the vector store from disk."""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS vector store implementation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.dimension = config.vector_store.dimension
        self.index = None
        self.metadata = []
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        logger.info(f"Initialized FAISS index with dimension {self.dimension}")
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to FAISS index."""
        if self.index is None:
            raise ValueError("FAISS index not initialized")
        
        # Ensure vectors are in the correct format for FAISS
        vectors = np.array(vectors, dtype=np.float32)
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)
        
        # Add to index
        self.index.add(vectors)
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(vectors)} vectors to FAISS index")
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Search for similar vectors in FAISS index."""
        if self.index is None:
            raise ValueError("FAISS index not initialized")
        
        # Ensure query vector is in the correct format for FAISS (2D array)
        query_vector = np.array(query_vector, dtype=np.float32)
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Normalize query vector
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.index.search(query_vector, top_k)
        
        # Get metadata for results
        results_metadata = [self.metadata[i] for i in indices[0] if i < len(self.metadata)]
        
        return scores[0], results_metadata
    
    def save(self, path: str) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            raise ValueError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.faiss")
        
        # Save metadata
        import pickle
        with open(f"{path}.metadata", 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"Saved FAISS index and metadata to {path}")
    
    def load(self, path: str) -> None:
        """Load FAISS index and metadata from disk."""
        # Load FAISS index
        self.index = faiss.read_index(f"{path}.faiss")
        
        # Load metadata
        import pickle
        with open(f"{path}.metadata", 'rb') as f:
            self.metadata = pickle.load(f)
        
        logger.info(f"Loaded FAISS index and metadata from {path}")


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation (placeholder for future implementation)."""
    
    def __init__(self, config: Config):
        self.config = config
        # TODO: Implement Pinecone integration
        raise NotImplementedError("Pinecone integration not yet implemented")
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to Pinecone index."""
        raise NotImplementedError("Pinecone integration not yet implemented")
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Search for similar vectors in Pinecone index."""
        raise NotImplementedError("Pinecone integration not yet implemented")
    
    def save(self, path: str) -> None:
        """Save Pinecone index (not applicable for cloud service)."""
        raise NotImplementedError("Pinecone is a cloud service, no local save needed")
    
    def load(self, path: str) -> None:
        """Load Pinecone index (not applicable for cloud service)."""
        raise NotImplementedError("Pinecone is a cloud service, no local load needed")


class WeaviateVectorStore(VectorStore):
    """Weaviate vector store implementation (placeholder for future implementation)."""
    
    def __init__(self, config: Config):
        self.config = config
        # TODO: Implement Weaviate integration
        raise NotImplementedError("Weaviate integration not yet implemented")
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to Weaviate index."""
        raise NotImplementedError("Weaviate integration not yet implemented")
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Search for similar vectors in Weaviate index."""
        raise NotImplementedError("Weaviate integration not yet implemented")
    
    def save(self, path: str) -> None:
        """Save Weaviate index (not applicable for cloud service)."""
        raise NotImplementedError("Weaviate is a cloud service, no local save needed")
    
    def load(self, path: str) -> None:
        """Load Weaviate index (not applicable for cloud service)."""
        raise NotImplementedError("Weaviate is a cloud service, no local load needed")


def get_vector_store(config: Config) -> VectorStore:
    """Factory function to get the appropriate vector store."""
    store_type = config.vector_store.type.lower()
    
    if store_type == "faiss":
        return FAISSVectorStore(config)
    elif store_type == "pinecone":
        return PineconeVectorStore(config)
    elif store_type == "weaviate":
        return WeaviateVectorStore(config)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}") 