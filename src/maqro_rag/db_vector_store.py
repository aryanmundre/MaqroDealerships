"""
Database vector store using Supabase pgvector for similarity search.
"""

import uuid
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam, String, Float, Integer


class DatabaseVectorStore:
    """Vector store that uses Supabase pgvector for embeddings storage and similarity search."""
    
    def __init__(self):
        """Initialize database vector store."""
        self.embedding_dimension = 1536  # OpenAI ada-002 embedding size
        logger.info("Initialized DatabaseVectorStore")
    
    async def store_embedding(
        self, 
        session: AsyncSession,
        inventory_id: str,
        embedding: List[float],
        formatted_text: str,
        dealership_id: str
    ) -> str:
        """Store a single embedding in the database."""
        try:
            # Convert embedding to pgvector format (handle numpy arrays)
            if hasattr(embedding, 'tolist'):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)
            embedding_str = f"[{','.join(map(str, embedding_list))}]"
            
            # Insert embedding into database
            result = await session.execute(
                text(f"""
                INSERT INTO vehicle_embeddings (inventory_id, embedding, formatted_text, dealership_id)
                VALUES (:inventory_id, '{embedding_str}'::vector, :formatted_text, :dealership_id)
                RETURNING id
                """),
                {
                    "inventory_id": inventory_id,
                    "formatted_text": formatted_text,
                    "dealership_id": dealership_id
                }
            )
            
            embedding_id = result.scalar()
            await session.commit()
            
            logger.debug(f"Stored embedding for inventory {inventory_id}")
            return str(embedding_id)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing embedding: {e}")
            raise
    
    async def store_embeddings_batch(
        self,
        session: AsyncSession, 
        embeddings_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Store multiple embeddings in a single transaction."""
        try:
            embedding_ids = []
            
            for data in embeddings_data:
                # Convert embedding to pgvector format (handle numpy arrays)
                embedding = data['embedding']
                if hasattr(embedding, 'tolist'):
                    embedding_list = embedding.tolist()
                else:
                    embedding_list = list(embedding)
                embedding_str = f"[{','.join(map(str, embedding_list))}]"
                
                result = await session.execute(
                    text(f"""
                    INSERT INTO vehicle_embeddings (inventory_id, embedding, formatted_text, dealership_id)
                    VALUES (:inventory_id, '{embedding_str}'::vector, :formatted_text, :dealership_id)
                    RETURNING id
                    """),
                    {
                        "inventory_id": data["inventory_id"],
                        "formatted_text": data["formatted_text"],
                        "dealership_id": data["dealership_id"]
                    }
                )
                
                embedding_id = result.scalar()
                embedding_ids.append(str(embedding_id))
            
            await session.commit()
            logger.info(f"Stored {len(embedding_ids)} embeddings in batch")
            return embedding_ids
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing embeddings batch: {e}")
            raise
    
    async def similarity_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        dealership_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search for similar vehicles using cosine similarity."""
        try:
            # Convert query embedding to pgvector format (handle numpy arrays)
            if hasattr(query_embedding, 'tolist'):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = list(query_embedding)
            query_embedding_str = f"[{','.join(map(str, embedding_list))}]"
            
            # Perform similarity search with inventory join  
            # Use direct string formatting for vector (safe since it's generated internally)
            # and named parameters for user inputs
            sql_query = f"""
                SELECT 
                    i.id,
                    i.make,
                    i.model,
                    i.year,
                    i.price,
                    i.mileage,
                    i.description,
                    i.features,
                    i.condition,
                    i.status,
                    ve.formatted_text,
                    ve.embedding <=> '{query_embedding_str}'::vector as distance,
                    (1 - (ve.embedding <=> '{query_embedding_str}'::vector)) as similarity_score
                FROM inventory i
                JOIN vehicle_embeddings ve ON i.id = ve.inventory_id
                WHERE ve.dealership_id = :dealership_id
                  AND i.status = 'active'
                  AND (1 - (ve.embedding <=> '{query_embedding_str}'::vector)) >= :similarity_threshold
                ORDER BY distance ASC
                LIMIT :limit_val
            """
            
            result = await session.execute(
                text(sql_query),
                {
                    "dealership_id": dealership_id, 
                    "similarity_threshold": similarity_threshold,
                    "limit_val": limit
                }
            )
            
            rows = result.fetchall()
            
            # Format results to match existing RAG system expectations
            results = []
            for row in rows:
                vehicle_data = {
                    'id': str(row.id),
                    'year': row.year,
                    'make': row.make,
                    'model': row.model,
                    'price': self._parse_price(row.price),
                    'mileage': row.mileage or 0,
                    'description': row.description or '',
                    'features': row.features or '',
                    'condition': row.condition or '',
                    'status': row.status or 'active',
                    # Default values for missing fields
                    'color': '',
                    'fuel_type': '',
                    'transmission': '',
                    'doors': 0,
                    'seats': 0,
                    'engine': '',
                    'drivetrain': ''
                }
                
                result_item = {
                    'vehicle': vehicle_data,
                    'similarity_score': float(row.similarity_score),
                    'metadata': {
                        'database_id': str(row.id),
                        'formatted_text': row.formatted_text,
                        'vehicle': vehicle_data
                    }
                }
                results.append(result_item)
            
            logger.info(f"Found {len(results)} vehicles with similarity >= {similarity_threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            # Rollback the transaction to clear any error state
            try:
                await session.rollback()
            except:
                pass  # Ignore rollback errors
            return []
    
    async def delete_embeddings_for_inventory(
        self, 
        session: AsyncSession, 
        inventory_id: str
    ) -> bool:
        """Delete embeddings for a specific inventory item."""
        try:
            result = await session.execute(
                text("DELETE FROM vehicle_embeddings WHERE inventory_id = :inventory_id"),
                {"inventory_id": inventory_id}
            )
            
            await session.commit()
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} embeddings for inventory {inventory_id}")
            return deleted_count > 0
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting embeddings: {e}")
            raise
    
    async def delete_embeddings_for_dealership(
        self,
        session: AsyncSession,
        dealership_id: str
    ) -> int:
        """Delete all embeddings for a dealership."""
        try:
            result = await session.execute(
                text("DELETE FROM vehicle_embeddings WHERE dealership_id = :dealership_id"),
                {"dealership_id": dealership_id}
            )
            
            await session.commit()
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} embeddings for dealership {dealership_id}")
            return deleted_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting dealership embeddings: {e}")
            raise
    
    async def get_embedding_count(
        self, 
        session: AsyncSession, 
        dealership_id: str
    ) -> int:
        """Get count of embeddings for a dealership."""
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM vehicle_embeddings WHERE dealership_id = :dealership_id"),
                {"dealership_id": dealership_id}
            )
            
            count = result.scalar()
            logger.debug(f"Found {count} embeddings for dealership {dealership_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error getting embedding count: {e}")
            return 0
    
    async def check_embedding_exists(
        self,
        session: AsyncSession,
        inventory_id: str
    ) -> bool:
        """Check if embedding exists for an inventory item."""
        try:
            result = await session.execute(
                text("SELECT 1 FROM vehicle_embeddings WHERE inventory_id = :inventory_id LIMIT 1"),
                {"inventory_id": inventory_id}
            )
            
            exists = result.scalar() is not None
            return exists
            
        except Exception as e:
            logger.error(f"Error checking embedding existence: {e}")
            return False
    
    async def get_missing_embeddings(
        self,
        session: AsyncSession,
        dealership_id: str
    ) -> List[Dict[str, Any]]:
        """Get inventory items that don't have embeddings yet."""
        try:
            result = await session.execute(
                text("""
                SELECT i.id, i.make, i.model, i.year, i.price, i.mileage, 
                       i.description, i.features, i.condition
                FROM inventory i
                LEFT JOIN vehicle_embeddings ve ON i.id = ve.inventory_id
                WHERE i.dealership_id = :dealership_id
                  AND i.status = 'active'
                  AND ve.id IS NULL
                """),
                {"dealership_id": dealership_id}
            )
            
            rows = result.fetchall()
            missing_items = []
            
            for row in rows:
                item = {
                    'id': str(row.id),
                    'make': row.make,
                    'model': row.model,
                    'year': row.year,
                    'price': row.price,
                    'mileage': row.mileage,
                    'description': row.description,
                    'features': row.features,
                    'condition': row.condition
                }
                missing_items.append(item)
            
            logger.info(f"Found {len(missing_items)} inventory items missing embeddings")
            return missing_items
            
        except Exception as e:
            logger.error(f"Error finding missing embeddings: {e}")
            return []
    
    def _parse_price(self, price_str: str) -> int:
        """Parse price string to integer."""
        if not price_str:
            return 0
        
        try:
            # Remove currency symbols and commas
            clean_price = price_str.replace('$', '').replace(',', '').strip()
            return int(float(clean_price))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse price: {price_str}")
            return 0