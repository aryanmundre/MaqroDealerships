"""
Vehicle retrieval system using vector similarity search.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from loguru import logger

from .config import Config
from .embedding import get_embedding_provider
from .vector_store import get_vector_store
from .inventory import InventoryProcessor


class VehicleRetriever:
    """Retrieves vehicles using vector similarity search."""
    
    def __init__(self, config: Config):
        """Initialize vehicle retriever."""
        self.config = config
        self.embedding_provider = get_embedding_provider(config)
        self.vector_store = get_vector_store(config)
        self.inventory_processor = InventoryProcessor(config)
        self.is_initialized = False
        
        logger.info("Initialized VehicleRetriever")
    
    def build_index(self, inventory_file: str, index_path: str) -> None:
        """Build vector index from inventory file."""
        try:
            logger.info(f"Building index from inventory file: {inventory_file}")
            
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
            
            # Save index
            self.vector_store.save(index_path)
            logger.info(f"Saved vector index to {index_path}")
            
            # Update initialization status
            self.is_initialized = True
            logger.info(f"Successfully built index with {len(formatted_texts)} vehicles")
            
        except Exception as e:
            logger.error(f"Error building index: {e}")
            raise
    
    def load_index(self, index_path: str) -> None:
        """Load existing vector index."""
        try:
            self.vector_store.load(index_path)
            self.is_initialized = True
            logger.info(f"Loaded vector index from {index_path}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def search_vehicles(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for vehicles using semantic similarity."""
        if not self.is_initialized:
            raise RuntimeError("Vector index not initialized. Call build_index() or load_index() first.")
        
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        try:
            # Use configured top_k if not specified
            if top_k is None:
                top_k = self.config.retrieval.top_k
            
            # Create query embedding
            query_embedding = self.embedding_provider.embed_text(query)
            
            # Search vector store
            scores, metadata = self.vector_store.search(query_embedding, top_k)
            
            # Format results
            results = []
            for i, (score, meta) in enumerate(zip(scores, metadata)):
                result = {
                    'vehicle': meta['vehicle'],
                    'similarity_score': float(score),
                    'metadata': meta
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} vehicles matching query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise
    
    def search_vehicles_with_filters(
        self, 
        query: str, 
        filters: Dict[str, Any], 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for vehicles with additional filters."""
        # Get initial results
        results = self.search_vehicles(query, top_k)
        
        # Apply filters
        filtered_results = []
        for result in results:
            vehicle = result['vehicle']
            match = True
            
            for key, value in filters.items():
                if key in vehicle:
                    if isinstance(value, (list, tuple)):
                        if vehicle[key] not in value:
                            match = False
                            break
                    else:
                        if vehicle[key] != value:
                            match = False
                            break
                else:
                    match = False
                    break
            
            if match:
                filtered_results.append(result)
        
        logger.info(f"Applied filters, found {len(filtered_results)} matching vehicles")
        return filtered_results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index."""
        if not self.is_initialized:
            return {"error": "Index not initialized"}
        
        try:
            # Get basic stats
            stats = {
                "total_vehicles": len(self.vector_store.metadata) if hasattr(self.vector_store, 'metadata') else 0,
                "index_type": self.config.vector_store.type,
                "embedding_dimension": self.config.vector_store.dimension,
                "is_initialized": self.is_initialized
            }
            
            # Add inventory statistics if available
            if hasattr(self.inventory_processor, '_processed_data'):
                inventory_stats = self.inventory_processor.get_statistics()
                stats.update(inventory_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}
    
    def update_index(self, inventory_file: str, index_path: str) -> None:
        """Update existing index with new inventory data."""
        try:
            logger.info(f"Updating index with new inventory: {inventory_file}")
            
            # Rebuild index
            self.build_index(inventory_file, index_path)
            
            logger.info("Index updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating index: {e}")
            raise
    
    def get_similar_vehicles(self, vehicle_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find vehicles similar to a specific vehicle."""
        if not self.is_initialized:
            raise RuntimeError("Vector index not initialized")
        
        try:
            # Get vehicle data
            vehicle_data = self.inventory_processor.get_vehicle_by_index(vehicle_id)
            if not vehicle_data:
                raise ValueError(f"Vehicle with index {vehicle_id} not found")
            
            # Use vehicle description as query
            query = vehicle_data['formatted_text']
            
            # Search for similar vehicles (exclude the vehicle itself)
            results = self.search_vehicles(query, top_k + 1)
            
            # Filter out the vehicle itself
            similar_vehicles = [
                result for result in results 
                if result['metadata']['index'] != vehicle_id
            ][:top_k]
            
            logger.info(f"Found {len(similar_vehicles)} vehicles similar to vehicle {vehicle_id}")
            return similar_vehicles
            
        except Exception as e:
            logger.error(f"Error finding similar vehicles: {e}")
            raise
    
    def batch_search(self, queries: List[str], top_k: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """Perform batch search for multiple queries."""
        if not queries:
            return []
        
        results = []
        for query in queries:
            try:
                query_results = self.search_vehicles(query, top_k)
                results.append(query_results)
            except Exception as e:
                logger.warning(f"Error searching for query '{query}': {e}")
                results.append([])
        
        logger.info(f"Completed batch search for {len(queries)} queries")
        return results
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query."""
        if not partial_query.strip():
            return []
        
        try:
            # Get all vehicle data
            if hasattr(self.inventory_processor, '_processed_data'):
                vehicles = self.inventory_processor._processed_data
            else:
                return []
            
            # Create suggestions based on make, model, and features
            suggestions = set()
            partial_lower = partial_query.lower()
            
            for vehicle_data in vehicles:
                vehicle = vehicle_data['vehicle']
                
                # Check make
                if vehicle.get('make', '').lower().startswith(partial_lower):
                    suggestions.add(f"{vehicle['make']} vehicles")
                
                # Check model
                if vehicle.get('model', '').lower().startswith(partial_lower):
                    suggestions.add(f"{vehicle['model']} cars")
                
                # Check features
                features = vehicle.get('features', '').lower()
                if partial_lower in features:
                    # Extract relevant feature
                    feature_words = features.split(',')
                    for word in feature_words:
                        if partial_lower in word.strip():
                            suggestions.add(word.strip())
                            break
            
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {e}")
            return []
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate and analyze a search query."""
        if not query.strip():
            return {"valid": False, "error": "Query cannot be empty"}
        
        analysis = {
            "valid": True,
            "query": query,
            "length": len(query),
            "word_count": len(query.split()),
            "has_price_range": any(word in query.lower() for word in ['under', 'over', '$', 'price']),
            "has_vehicle_type": any(word in query.lower() for word in ['sedan', 'suv', 'truck', 'car', 'vehicle']),
            "has_brand": any(word in query.lower() for word in ['toyota', 'honda', 'ford', 'bmw', 'mercedes'])
        }
        
        return analysis 