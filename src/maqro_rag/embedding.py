"""
Embedding providers for converting text to vectors.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from loguru import logger

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import openai
except ImportError:
    openai = None

try:
    import cohere
except ImportError:
    cohere = None

from .config import Config


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts into vectors."""
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text into a vector."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-ada-002."""
    
    def __init__(self, config: Config):
        """Initialize OpenAI embedding provider."""
        if openai is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.config = config
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = config.embedding.model
        self.batch_size = config.embedding.batch_size
        self.max_retries = config.embedding.max_retries
        
        logger.info(f"Initialized OpenAI embedding provider with model: {self.model}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using OpenAI API."""
        if not texts:
            return np.array([])
        
        embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [embedding.embedding for embedding in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error embedding batch {batch_num}: {e}")
                raise
        
        return np.array(embeddings, dtype=np.float32)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text using OpenAI API."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider."""
    
    def __init__(self, config: Config):
        """Initialize Cohere embedding provider."""
        if cohere is None:
            raise ImportError("Cohere package not installed. Run: pip install cohere")
        
        self.config = config
        self.api_key = os.getenv("COHERE_API_KEY")
        
        if not self.api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")
        
        self.client = cohere.Client(self.api_key)
        self.model = config.embedding.cohere_model or "embed-english-v3.0"
        self.batch_size = config.embedding.batch_size
        self.max_retries = config.embedding.max_retries
        
        logger.info(f"Initialized Cohere embedding provider with model: {self.model}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using Cohere API."""
        if not texts:
            return np.array([])
        
        embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                response = self.client.embed(
                    texts=batch,
                    model=self.model
                )
                batch_embeddings = response.embeddings
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error embedding batch {batch_num}: {e}")
                raise
        
        return np.array(embeddings, dtype=np.float32)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text using Cohere API."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model
            )
            embedding = response.embeddings[0]
            return np.array([embedding], dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise


def get_embedding_provider(config: Config) -> EmbeddingProvider:
    """Factory function to get the appropriate embedding provider."""
    provider = config.embedding.provider.lower()
    
    if provider == "openai":
        return OpenAIEmbeddingProvider(config)
    elif provider == "cohere":
        return CohereEmbeddingProvider(config)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


class EmbeddingManager:
    """Manager class for handling embedding operations with caching and error handling."""
    
    def __init__(self, config: Config):
        """Initialize embedding manager."""
        self.config = config
        self.provider = get_embedding_provider(config)
        self._cache = {}
    
    def embed_texts(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """Embed texts with optional caching."""
        if not texts:
            return np.array([])
        
        # Check cache if enabled
        if use_cache:
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                if text in self._cache:
                    cached_embeddings.append(self._cache[text])
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Get embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.provider.embed_texts(uncached_texts)
                
                # Cache new embeddings
                for text, embedding in zip(uncached_texts, new_embeddings):
                    self._cache[text] = embedding
                
                # Combine cached and new embeddings
                all_embeddings = []
                cache_idx = 0
                new_idx = 0
                
                for i in range(len(texts)):
                    if i in uncached_indices:
                        all_embeddings.append(new_embeddings[new_idx])
                        new_idx += 1
                    else:
                        all_embeddings.append(cached_embeddings[cache_idx])
                        cache_idx += 1
                
                return np.array(all_embeddings)
            else:
                return np.array(cached_embeddings)
        else:
            return self.provider.embed_texts(texts)
    
    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Embed single text with optional caching."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if use_cache and text in self._cache:
            return np.array([self._cache[text]])
        
        embedding = self.provider.embed_text(text)
        
        if use_cache:
            self._cache[text] = embedding[0]
        
        return embedding
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        import sys
        return {
            "cached_texts": len(self._cache),
            "cache_size_mb": sum(sys.getsizeof(emb) for emb in self._cache.values()) / 1024 / 1024
        } 