"""
Configuration management for Maqro RAG module.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingConfig(BaseModel):
    """Configuration for embedding providers."""
    provider: str = Field(default="openai", description="Embedding provider: 'openai' or 'cohere'")
    model: str = Field(default="text-embedding-ada-002", description="OpenAI model name")
    cohere_model: Optional[str] = Field(default=None, description="Cohere model name")
    batch_size: int = Field(default=100, description="Batch size for embedding requests")
    max_retries: int = Field(default=3, description="Maximum retries for API calls")


class VectorStoreConfig(BaseModel):
    """Configuration for vector store."""
    type: str = Field(default="faiss", description="Vector store type: 'faiss', 'pinecone', 'weaviate'")
    dimension: int = Field(default=1536, description="Embedding dimension")
    pinecone: Optional[Dict[str, str]] = Field(default=None, description="Pinecone configuration")
    weaviate: Optional[Dict[str, str]] = Field(default=None, description="Weaviate configuration")


class RetrievalConfig(BaseModel):
    """Configuration for retrieval settings."""
    top_k: int = Field(default=3, description="Number of top results to return")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}")


class Config(BaseModel):
    """Main configuration class."""
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            embedding=EmbeddingConfig(
                provider=os.getenv("EMBEDDING_PROVIDER", "openai"),
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
                cohere_model=os.getenv("COHERE_MODEL"),
                batch_size=int(os.getenv("BATCH_SIZE", "100")),
                max_retries=int(os.getenv("MAX_RETRIES", "3"))
            ),
            vector_store=VectorStoreConfig(
                type=os.getenv("VECTOR_STORE_TYPE", "faiss"),
                dimension=int(os.getenv("VECTOR_DIMENSION", "1536"))
            ),
            retrieval=RetrievalConfig(
                top_k=int(os.getenv("TOP_K", "3")),
                similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv("LOG_FORMAT", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}")
            )
        ) 