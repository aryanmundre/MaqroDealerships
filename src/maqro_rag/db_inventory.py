"""
Database inventory processor for RAG system.
Fetches inventory data from Supabase database instead of CSV files.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Config
from .inventory import VehicleData

logger = logging.getLogger(__name__)


class DatabaseInventoryProcessor:
    """Process vehicle inventory data from database for RAG system."""
    
    def __init__(self, config: Config):
        """Initialize database inventory processor."""
        self.config = config
        self._processed_data = []
    
    async def process_database_inventory(self, session: AsyncSession, dealership_id: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process inventory from database and return formatted texts and metadata."""
        # Import here to avoid circular imports
        from maqro_backend.crud import get_inventory_by_dealership
        
        try:
            # Get inventory from database
            logger.info(f"Fetching inventory from database for dealership: {dealership_id}")
            inventory_items = await get_inventory_by_dealership(session=session, dealership_id=dealership_id)
            logger.info(f"Retrieved {len(inventory_items)} vehicles from database")
            
            formatted_texts = []
            metadata = []
            
            for i, inventory_item in enumerate(inventory_items):
                try:
                    # Convert database model to dict
                    vehicle_data = {
                        'year': inventory_item.year,
                        'make': inventory_item.make,
                        'model': inventory_item.model,
                        'price': self._parse_price(inventory_item.price),
                        'mileage': inventory_item.mileage or 0,
                        'description': inventory_item.description or '',
                        'features': inventory_item.features or '',
                        'condition': inventory_item.condition or '',
                        'status': inventory_item.status or 'active',
                        # Default values for fields not in database
                        'color': '',
                        'fuel_type': '',
                        'transmission': '',
                        'doors': 0,
                        'seats': 0,
                        'engine': '',
                        'drivetrain': ''
                    }
                    
                    # Create vehicle object for formatting
                    vehicle = VehicleData(vehicle_data)
                    
                    # Format for embedding
                    formatted_text = vehicle.format_for_embedding()
                    formatted_texts.append(formatted_text)
                    
                    # Create metadata with vehicle data nested (for compatibility)
                    meta = {
                        'index': i,
                        'vehicle': vehicle.to_dict(),
                        'formatted_text': formatted_text,
                        'database_id': str(inventory_item.id),
                        'dealership_id': str(inventory_item.dealership_id),
                        # Backward compatibility fields
                        'year': vehicle.year,
                        'make': vehicle.make,
                        'model': vehicle.model,
                        'price': vehicle.price,
                        'features': vehicle.features,
                        'description': vehicle.description
                    }
                    metadata.append(meta)
                    
                except Exception as e:
                    logger.warning(f"Error processing vehicle {i} from database: {e}")
                    continue
            
            self._processed_data = metadata
            logger.info(f"Successfully processed {len(formatted_texts)} vehicles from database")
            
            return formatted_texts, metadata
            
        except Exception as e:
            logger.error(f"Error fetching inventory from database: {e}")
            raise
    
    def _parse_price(self, price_str: str) -> int:
        """Parse price string from database to integer."""
        if not price_str:
            return 0
        
        try:
            # Remove currency symbols, commas, and convert to int
            clean_price = price_str.replace('$', '').replace(',', '').strip()
            return int(float(clean_price))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse price: {price_str}")
            return 0
    
    def get_vehicle_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get vehicle data by index."""
        if 0 <= index < len(self._processed_data):
            return self._processed_data[index]
        return None
    
    def get_vehicles_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get vehicles matching specific criteria."""
        matches = []
        
        for vehicle_data in self._processed_data:
            vehicle = vehicle_data['vehicle']
            match = True
            
            for key, value in criteria.items():
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
                matches.append(vehicle_data)
        
        return matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get inventory statistics."""
        if not self._processed_data:
            return {}
        
        vehicles = [data['vehicle'] for data in self._processed_data]
        
        # Price statistics
        prices = [v['price'] for v in vehicles if v['price'] > 0]
        price_stats = {
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'total_vehicles': len(vehicles)
        }
        
        # Make statistics
        makes = [v['make'] for v in vehicles if v['make']]
        make_counts = {}
        for make in makes:
            make_counts[make] = make_counts.get(make, 0) + 1
        
        # Year statistics
        years = [v['year'] for v in vehicles if v['year']]
        year_stats = {
            'min_year': min(years) if years else 0,
            'max_year': max(years) if years else 0,
            'avg_year': sum(years) / len(years) if years else 0
        }
        
        return {
            'price_statistics': price_stats,
            'make_distribution': make_counts,
            'year_statistics': year_stats,
            'total_vehicles': len(vehicles),
            'source': 'database'
        }