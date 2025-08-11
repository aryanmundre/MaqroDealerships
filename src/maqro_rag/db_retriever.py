"""
Database-aware RAG retriever using pgvector for vehicle search.
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Config
from .embedding import get_embedding_provider
from .db_vector_store import DatabaseVectorStore
from .inventory import VehicleData
from .entity_parser import VehicleQuery


class DatabaseRAGRetriever:
    """RAG retriever that uses database-stored embeddings for vehicle search."""
    
    def __init__(self, config: Config):
        """Initialize database RAG retriever."""
        self.config = config
        self.embedding_provider = get_embedding_provider(config)
        self.vector_store = DatabaseVectorStore()
        self.is_initialized = True  # Always ready since we use database
        
        logger.info("Initialized DatabaseRAGRetriever")
    
    async def build_embeddings_for_dealership(
        self,
        session: AsyncSession,
        dealership_id: str,
        force_rebuild: bool = False
    ) -> int:
        """Build embeddings for all inventory items in a dealership."""
        try:
            logger.info(f"Building embeddings for dealership: {dealership_id}")
            
            if force_rebuild:
                # Delete existing embeddings
                await self.vector_store.delete_embeddings_for_dealership(session, dealership_id)
                logger.info("Deleted existing embeddings for rebuild")
            
            # Get inventory items missing embeddings
            missing_items = await self.vector_store.get_missing_embeddings(session, dealership_id)
            
            if not missing_items:
                logger.info("No missing embeddings found")
                return 0
            
            logger.info(f"Processing {len(missing_items)} inventory items")
            
            # Prepare embeddings data
            embeddings_data = []
            formatted_texts = []
            
            for item in missing_items:
                # Create vehicle object for consistent formatting
                vehicle_data = VehicleData({
                    'year': item['year'],
                    'make': item['make'],
                    'model': item['model'],
                    'price': self._parse_price(item['price']),
                    'mileage': item.get('mileage', 0),
                    'description': item.get('description', ''),
                    'features': item.get('features', ''),
                    'condition': item.get('condition', ''),
                    # Default values
                    'color': '',
                    'fuel_type': '',
                    'transmission': '',
                    'doors': 0,
                    'seats': 0,
                    'engine': '',
                    'drivetrain': ''
                })
                
                # Format text for embedding
                formatted_text = vehicle_data.format_for_embedding()
                formatted_texts.append(formatted_text)
                
                embeddings_data.append({
                    'inventory_id': item['id'],
                    'formatted_text': formatted_text,
                    'dealership_id': dealership_id
                })
            
            # Generate embeddings in batch
            logger.info("Generating embeddings...")
            embeddings = self.embedding_provider.embed_texts(formatted_texts)
            
            # Add embeddings to data
            for i, embedding in enumerate(embeddings):
                embeddings_data[i]['embedding'] = embedding
            
            # Store embeddings in database
            logger.info("Storing embeddings in database...")
            embedding_ids = await self.vector_store.store_embeddings_batch(session, embeddings_data)
            
            logger.info(f"Successfully built {len(embedding_ids)} embeddings for dealership {dealership_id}")
            return len(embedding_ids)
            
        except Exception as e:
            logger.error(f"Error building embeddings: {e}")
            raise
    
    async def search_vehicles(
        self,
        session: AsyncSession,
        query: str,
        dealership_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search vehicles using database vector similarity."""
        try:
            if not query.strip():
                raise ValueError("Search query cannot be empty")
            
            logger.info(f"Searching vehicles for: '{query}' in dealership {dealership_id}")
            
            # Generate query embedding
            query_embedding = self.embedding_provider.embed_text(query)
            
            # Search similar vehicles in database
            results = await self.vector_store.similarity_search(
                session=session,
                query_embedding=query_embedding,
                dealership_id=dealership_id,
                limit=top_k,
                similarity_threshold=similarity_threshold
            )
            
            logger.info(f"Found {len(results)} vehicles matching query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            raise
    
    async def search_vehicles_hybrid(
        self,
        session: AsyncSession,
        query: str,
        vehicle_query: VehicleQuery,
        dealership_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Hybrid search using both metadata filters and vector similarity."""
        try:
            logger.info(f"Hybrid search for: '{query}' with filters")
            
            # For now, use the standard vector search
            # TODO: Implement metadata filtering in SQL query
            results = await self.search_vehicles(
                session=session,
                query=query,
                dealership_id=dealership_id,
                top_k=top_k * 2,  # Get more results to filter
                similarity_threshold=0.2  # Lower threshold for filtering
            )
            
            # Apply entity-based filtering
            if vehicle_query.has_strong_signals:
                filtered_results = self._apply_entity_filters(results, vehicle_query)
                logger.info(f"Filtered to {len(filtered_results)} results using entity filters")
                return filtered_results[:top_k]
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to regular search
            return await self.search_vehicles(session, query, dealership_id, top_k)
    
    def _apply_entity_filters(
        self,
        results: List[Dict[str, Any]],
        vehicle_query: VehicleQuery
    ) -> List[Dict[str, Any]]:
        """Apply entity-based filters to search results."""
        filtered_results = []
        
        for result in results:
            vehicle = result['vehicle']
            match = True
            
            # Make filter
            if vehicle_query.make and match:
                vehicle_make = vehicle.get('make', '').lower()
                query_make = vehicle_query.make.lower()
                if query_make not in vehicle_make:
                    match = False
            
            # Model filter
            if vehicle_query.model and match:
                vehicle_model = vehicle.get('model', '').lower()
                query_model = vehicle_query.model.lower()
                if query_model not in vehicle_model:
                    match = False
            
            # Year range filter
            if (vehicle_query.year_min or vehicle_query.year_max) and match:
                vehicle_year = vehicle.get('year', 0)
                if isinstance(vehicle_year, int):
                    if vehicle_query.year_min and vehicle_year < vehicle_query.year_min:
                        match = False
                    if vehicle_query.year_max and vehicle_year > vehicle_query.year_max:
                        match = False
            
            # Budget filter
            if vehicle_query.budget_max and match:
                vehicle_price = vehicle.get('price', 0)
                if isinstance(vehicle_price, (int, float)) and vehicle_price > vehicle_query.budget_max:
                    match = False
            
            # Color filter
            if vehicle_query.color and match:
                vehicle_desc = vehicle.get('description', '').lower()
                vehicle_features = vehicle.get('features', '').lower()
                query_color = vehicle_query.color.lower()
                if query_color not in vehicle_desc and query_color not in vehicle_features:
                    match = False
            
            if match:
                # Boost similarity score for exact matches
                if vehicle_query.make and vehicle_query.make.lower() == vehicle.get('make', '').lower():
                    result['similarity_score'] = min(1.0, result['similarity_score'] + 0.2)
                filtered_results.append(result)
        
        # Re-sort by similarity score
        return sorted(filtered_results, key=lambda x: x['similarity_score'], reverse=True)
    
    async def refresh_embeddings_for_inventory(
        self,
        session: AsyncSession,
        inventory_id: str,
        dealership_id: str
    ) -> bool:
        """Refresh embeddings for a specific inventory item."""
        try:
            # Delete existing embedding
            await self.vector_store.delete_embeddings_for_inventory(session, inventory_id)
            
            # Get the specific inventory item and rebuild its embedding
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT i.id, i.make, i.model, i.year, i.price, i.mileage, 
                       i.description, i.features, i.condition
                FROM inventory i
                WHERE i.id = :inventory_id AND i.dealership_id = :dealership_id
                """),
                {"inventory_id": inventory_id, "dealership_id": dealership_id}
            )
            
            row = result.fetchone()
            if not row:
                logger.warning(f"Inventory item {inventory_id} not found")
                return False
            
            # Create vehicle object and format text
            vehicle_data = VehicleData({
                'year': row.year,
                'make': row.make,
                'model': row.model,
                'price': self._parse_price(row.price),
                'mileage': row.mileage or 0,
                'description': row.description or '',
                'features': row.features or '',
                'condition': row.condition or '',
                # Default values
                'color': '',
                'fuel_type': '',
                'transmission': '',
                'doors': 0,
                'seats': 0,
                'engine': '',
                'drivetrain': ''
            })
            
            formatted_text = vehicle_data.format_for_embedding()
            
            # Generate embedding
            embedding = self.embedding_provider.embed_text(formatted_text)
            
            # Store embedding
            await self.vector_store.store_embedding(
                session=session,
                inventory_id=inventory_id,
                embedding=embedding,
                formatted_text=formatted_text,
                dealership_id=dealership_id
            )
            
            logger.info(f"Refreshed embedding for inventory {inventory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing embeddings for inventory {inventory_id}: {e}")
            return False
    
    async def get_retriever_stats(
        self,
        session: AsyncSession,
        dealership_id: str
    ) -> Dict[str, Any]:
        """Get retriever statistics."""
        try:
            # Get embedding count
            embedding_count = await self.vector_store.get_embedding_count(session, dealership_id)
            
            # Get missing embeddings count
            missing_items = await self.vector_store.get_missing_embeddings(session, dealership_id)
            missing_count = len(missing_items)
            
            return {
                "total_embeddings": embedding_count,
                "missing_embeddings": missing_count,
                "retriever_type": "DatabaseRAGRetriever",
                "dealership_id": dealership_id,
                "is_ready": embedding_count > 0,
                "embedding_dimension": self.vector_store.embedding_dimension
            }
            
        except Exception as e:
            logger.error(f"Error getting retriever stats: {e}")
            return {"error": str(e)}
    
    def _parse_price(self, price_str: str) -> int:
        """Parse price string to integer."""
        if not price_str:
            return 0
        
        try:
            clean_price = price_str.replace('$', '').replace(',', '').strip()
            return int(float(clean_price))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse price: {price_str}")
            return 0