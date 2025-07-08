"""
Vehicle retrieval module for the RAG pipeline.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from loguru import logger
from .config import Config
from .embedding import get_embedding_provider, EmbeddingProvider
from .vector_store import get_vector_store, VectorStore
from .inventory import InventoryProcessor


class VehicleRetriever:
    """Main class for vehicle retrieval using RAG."""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_provider = get_embedding_provider(config)
        self.vector_store = get_vector_store(config)
        self.inventory_processor = InventoryProcessor(config)
        self.is_initialized = False
        
        logger.info("Initialized VehicleRetriever")
    
    def build_index(self, inventory_file: str, save_path: Optional[str] = None) -> None:
        """Build the vector index from inventory data."""
        logger.info(f"Building index from inventory file: {inventory_file}")
        
        try:
            # Process inventory
            formatted_texts, metadata = self.inventory_processor.process_inventory(inventory_file)
            
            if not formatted_texts:
                raise ValueError("No vehicles found in inventory file")
            
            # Create embeddings
            logger.info("Creating embeddings for vehicles...")
            embeddings = self.embedding_provider.embed_texts(formatted_texts)
            
            # Add to vector store
            logger.info("Adding embeddings to vector store...")
            self.vector_store.add_vectors(embeddings, metadata)
            
            # Save if path provided
            if save_path:
                self.vector_store.save(save_path)
                logger.info(f"Saved vector index to {save_path}")
            
            self.is_initialized = True
            logger.info(f"Successfully built index with {len(formatted_texts)} vehicles")
            
        except Exception as e:
            logger.error(f"Error building index: {e}")
            raise
    
    def load_index(self, load_path: str) -> None:
        """Load an existing vector index."""
        try:
            self.vector_store.load(load_path)
            self.is_initialized = True
            logger.info(f"Loaded vector index from {load_path}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def search_vehicles(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for vehicles matching the query."""
        if not self.is_initialized:
            raise ValueError("Vector index not initialized. Call build_index() or load_index() first.")
        
        # Use config default if top_k not specified
        if top_k is None:
            top_k = self.config.retrieval.top_k
        
        try:
            # Create query embedding
            query_embedding = self.embedding_provider.embed_text(query)
            
            # Search vector store
            scores, metadata = self.vector_store.search(query_embedding, top_k)
            
            # Filter by similarity threshold
            threshold = self.config.retrieval.similarity_threshold
            filtered_results = []
            
            for i, (score, vehicle_meta) in enumerate(zip(scores, metadata)):
                if score >= threshold:
                    result = {
                        'rank': i + 1,
                        'similarity_score': float(score),
                        'vehicle': vehicle_meta
                    }
                    filtered_results.append(result)
            
            logger.info(f"Found {len(filtered_results)} vehicles matching query: '{query}'")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise
    
    def get_vehicle_details(self, vehicle_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a vehicle."""
        return {
            'year': vehicle_metadata.get('year'),
            'make': vehicle_metadata.get('make'),
            'model': vehicle_metadata.get('model'),
            'price': vehicle_metadata.get('price'),
            'features': vehicle_metadata.get('features'),
            'description': vehicle_metadata.get('description'),
            'formatted_text': vehicle_metadata.get('formatted_text')
        }
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into a readable string."""
        if not results:
            return "No vehicles found matching your criteria."
        
        formatted_results = []
        for result in results:
            vehicle = result['vehicle']
            score = result['similarity_score']
            
            vehicle_info = f"{result['rank']}. {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}"
            price_info = f"Price: ${vehicle.get('price', 'N/A'):,}" if vehicle.get('price') else "Price: N/A"
            score_info = f"Match: {score:.2%}"
            
            formatted_results.append(f"{vehicle_info} | {price_info} | {score_info}")
        
        return "\n".join(formatted_results)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        if not self.is_initialized:
            return {"error": "Index not initialized"}
        
        try:
            # For FAISS, we can get some basic stats
            if hasattr(self.vector_store, 'index') and self.vector_store.index is not None:
                return {
                    "total_vehicles": len(self.vector_store.metadata),
                    "index_type": "FAISS",
                    "dimension": self.vector_store.dimension
                }
            else:
                return {
                    "total_vehicles": len(self.vector_store.metadata),
                    "index_type": "Unknown"
                }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)} 