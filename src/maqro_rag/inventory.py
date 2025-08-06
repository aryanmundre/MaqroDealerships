"""
Inventory processing for vehicle data.
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

from .config import Config


class VehicleData:
    """Data class for vehicle information."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize vehicle data from dictionary."""
        self.year = data.get('year', '')
        self.make = data.get('make', '')
        self.model = data.get('model', '')
        self.price = data.get('price', 0)
        self.features = data.get('features', '')
        self.description = data.get('description', '')
        self.mileage = data.get('mileage', 0)
        self.color = data.get('color', '')
        self.condition = data.get('condition', '')
        self.fuel_type = data.get('fuel_type', '')
        self.transmission = data.get('transmission', '')
        self.doors = data.get('doors', 0)
        self.seats = data.get('seats', 0)
        self.engine = data.get('engine', '')
        self.drivetrain = data.get('drivetrain', '')
        
        # Validate required fields
        if not all([self.year, self.make, self.model]):
            raise ValueError("Year, make, and model are required fields")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'year': self.year,
            'make': self.make,
            'model': self.model,
            'price': self.price,
            'features': self.features,
            'description': self.description,
            'mileage': self.mileage,
            'color': self.color,
            'condition': self.condition,
            'fuel_type': self.fuel_type,
            'transmission': self.transmission,
            'doors': self.doors,
            'seats': self.seats,
            'engine': self.engine,
            'drivetrain': self.drivetrain
        }
    
    def format_for_embedding(self) -> str:
        """Format vehicle data for embedding generation."""
        parts = [
            f"{self.year} {self.make} {self.model}",
            f"${self.price:,}" if self.price else "Price available upon request"
        ]
        
        if self.features:
            parts.append(self.features)
        
        if self.description:
            parts.append(self.description)
        
        if self.mileage:
            parts.append(f"{self.mileage:,} miles")
        
        if self.color:
            parts.append(f"Color: {self.color}")
        
        if self.condition:
            parts.append(f"Condition: {self.condition}")
        
        if self.fuel_type:
            parts.append(f"Fuel: {self.fuel_type}")
        
        if self.transmission:
            parts.append(f"Transmission: {self.transmission}")
        
        if self.engine:
            parts.append(f"Engine: {self.engine}")
        
        if self.drivetrain:
            parts.append(f"Drivetrain: {self.drivetrain}")
        
        return ". ".join(parts)


class InventoryProcessor:
    """Process vehicle inventory data for RAG system."""
    
    def __init__(self, config: Config):
        """Initialize inventory processor."""
        self.config = config
        self._processed_data = []
    
    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load vehicle data from CSV file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Inventory file not found: {file_path}")
        
        vehicles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Clean and validate data
                        cleaned_row = self._clean_row_data(row)
                        vehicles.append(cleaned_row)
                        
                    except Exception as e:
                        logger.warning(f"Error processing row {row_num}: {e}")
                        continue
            
            logger.info(f"Loaded {len(vehicles)} vehicles from {file_path}")
            return vehicles
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise
    
    def _clean_row_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate row data."""
        cleaned = {}
        
        # Clean year
        year = row.get('year', '').strip()
        if year and year.isdigit():
            cleaned['year'] = int(year)
        else:
            cleaned['year'] = ''
        
        # Clean make and model
        cleaned['make'] = row.get('make', '').strip()
        cleaned['model'] = row.get('model', '').strip()
        
        # Clean price
        price_str = row.get('price', '').strip()
        if price_str:
            # Remove currency symbols and commas
            price_str = re.sub(r'[$,]', '', price_str)
            try:
                cleaned['price'] = int(float(price_str))
            except ValueError:
                cleaned['price'] = 0
        else:
            cleaned['price'] = 0
        
        # Clean features
        features = row.get('features', '').strip()
        cleaned['features'] = features if features else ''
        
        # Clean description
        description = row.get('description', '').strip()
        cleaned['description'] = description if description else ''
        
        # Clean mileage
        mileage_str = row.get('mileage', '').strip()
        if mileage_str:
            mileage_str = re.sub(r'[,\s]', '', mileage_str)
            try:
                cleaned['mileage'] = int(mileage_str)
            except ValueError:
                cleaned['mileage'] = 0
        else:
            cleaned['mileage'] = 0
        
        # Clean other fields
        cleaned['color'] = row.get('color', '').strip()
        cleaned['condition'] = row.get('condition', '').strip()
        cleaned['fuel_type'] = row.get('fuel_type', '').strip()
        cleaned['transmission'] = row.get('transmission', '').strip()
        cleaned['engine'] = row.get('engine', '').strip()
        cleaned['drivetrain'] = row.get('drivetrain', '').strip()
        
        # Clean numeric fields
        for field in ['doors', 'seats']:
            value = row.get(field, '').strip()
            if value and value.isdigit():
                cleaned[field] = int(value)
            else:
                cleaned[field] = 0
        
        return cleaned
    
    def process_inventory(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process inventory file and return formatted texts and metadata."""
        # Load raw data
        raw_vehicles = self.load_csv(file_path)
        
        formatted_texts = []
        metadata = []
        
        for i, vehicle_data in enumerate(raw_vehicles):
            try:
                # Create vehicle object
                vehicle = VehicleData(vehicle_data)
                
                # Format for embedding
                formatted_text = vehicle.format_for_embedding()
                formatted_texts.append(formatted_text)
                
                # Create metadata with backward compatibility
                meta = {
                    'index': i,
                    'vehicle': vehicle.to_dict(),
                    'formatted_text': formatted_text,
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
                logger.warning(f"Error processing vehicle {i}: {e}")
                continue
        
        self._processed_data = metadata
        logger.info(f"Processed {len(formatted_texts)} vehicles successfully")
        
        return formatted_texts, metadata
    
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
            'total_vehicles': len(vehicles)
        }
    
    def export_processed_data(self, output_path: str) -> None:
        """Export processed data to JSON file."""
        import json
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self._processed_data, f, indent=2)
            logger.info(f"Exported processed data to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise 