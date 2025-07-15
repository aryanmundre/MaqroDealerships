"""
Embedding provider module for creating semantic embeddings.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from loguru import logger
import openai
import cohere
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
    """OpenAI embedding provider."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = config.embedding.model
        self.batch_size = config.embedding.batch_size
        self.max_retries = config.embedding.max_retries
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using OpenAI API."""
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            logger.info(f"Embedding batch {i//self.batch_size + 1}/{(len(texts) + self.batch_size - 1)//self.batch_size}")
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [embedding.embedding for embedding in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error embedding batch: {e}")
                raise
        
        return np.array(embeddings)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            return np.array([response.data[0].embedding])
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.model = config.embedding.cohere_model or "embed-english-v3.0"
        self.batch_size = config.embedding.batch_size
        self.max_retries = config.embedding.max_retries
        
        if not os.getenv("COHERE_API_KEY"):
            raise ValueError("COHERE_API_KEY environment variable is required")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using Cohere API."""
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            logger.info(f"Embedding batch {i//self.batch_size + 1}/{(len(texts) + self.batch_size - 1)//self.batch_size}")
            
            try:
                response = self.client.embed(
                    texts=batch,
                    model=self.model
                )
                batch_embeddings = response.embeddings
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error embedding batch: {e}")
                raise
        
        return np.array(embeddings)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text using Cohere API."""
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model
            )
            return np.array([response.embeddings[0]])
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