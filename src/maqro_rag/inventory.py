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
        """Format vehicle data with semantic enrichment for better embedding generation."""
        parts = [f"{self.year} {self.make} {self.model}"]
        
        # Add semantic vehicle type enrichment based on model
        semantic_terms = self._get_semantic_terms()
        if semantic_terms:
            parts.append(f"Vehicle type: {', '.join(semantic_terms)}")
        
        # Price with semantic context
        if self.price:
            price_str = f"${self.price:,}"
            price_category = self._get_price_category(self.price)
            parts.append(f"{price_str} ({price_category})")
        else:
            parts.append("Price available upon request")
        
        # Enhanced features with semantic enrichment
        if self.features:
            enhanced_features = self._enhance_features_semantically(self.features)
            parts.append(f"Features: {enhanced_features}")
        
        # Description with semantic context
        if self.description:
            parts.append(f"Description: {self.description}")
        
        # Mileage with semantic context
        if self.mileage:
            mileage_category = self._get_mileage_category(self.mileage)
            parts.append(f"{self.mileage:,} miles ({mileage_category})")
        
        # Color with enhanced searchability
        if self.color:
            parts.append(f"Color: {self.color}")
        
        # Condition with semantic meaning
        if self.condition:
            condition_synonyms = self._get_condition_synonyms(self.condition)
            parts.append(f"Condition: {self.condition} {condition_synonyms}")
        
        # Technical specifications
        tech_specs = []
        if self.fuel_type:
            fuel_synonyms = self._get_fuel_synonyms(self.fuel_type)
            tech_specs.append(f"{self.fuel_type} {fuel_synonyms}".strip())
        
        if self.transmission:
            trans_synonyms = self._get_transmission_synonyms(self.transmission)
            tech_specs.append(f"{self.transmission} {trans_synonyms}".strip())
        
        if self.engine:
            tech_specs.append(f"Engine: {self.engine}")
        
        if self.drivetrain:
            drivetrain_synonyms = self._get_drivetrain_synonyms(self.drivetrain)
            tech_specs.append(f"{self.drivetrain} {drivetrain_synonyms}".strip())
        
        if tech_specs:
            parts.append(f"Specifications: {', '.join(tech_specs)}")
        
        return ". ".join(parts)
    
    def _get_semantic_terms(self) -> List[str]:
        """Get semantic terms based on make and model for better searchability."""
        semantic_terms = []
        model_lower = str(self.model).lower()
        make_lower = str(self.make).lower()
        
        # SUV/Crossover models
        suv_models = ['tiguan', 'cr-v', 'rav4', 'highlander', 'pilot', 'pathfinder', 'murano', 'rogue', 
                      'escape', 'explorer', 'edge', 'expedition', 'tahoe', 'suburban', 'equinox', 'traverse',
                      'tucson', 'santa fe', 'palisade', 'sportage', 'sorento', 'telluride', 'cx-5', 'cx-9',
                      'outback', 'forester', 'crosstrek', 'ascent', 'wrangler', 'grand cherokee', 'cherokee',
                      'compass', 'renegade', 'durango', 'q5', 'q7', 'q8', 'x3', 'x5', 'x7', 'glc', 'gle', 'gls',
                      'nx', 'rx', 'gx', 'lx', 'mdx', 'rdx', 'qx50', 'qx60', 'qx80', 'encore', 'enclave', 'envision']
        
        if any(suv_model in model_lower for suv_model in suv_models):
            semantic_terms.extend(['SUV', 'crossover', 'utility vehicle', 'family vehicle'])
        
        # Sedan models
        sedan_models = ['civic', 'accord', 'corolla', 'camry', 'altima', 'sentra', 'maxima', 'malibu', 'impala',
                        'elantra', 'sonata', 'forte', 'k5', 'mazda3', 'mazda6', 'impreza', 'legacy', 'a3', 'a4',
                        'a6', 'a8', '3 series', '5 series', '7 series', 'c-class', 'e-class', 's-class',
                        'es', 'is', 'gs', 'ls', 'ilx', 'tl', 'tsx', 'q50', 'q60']
        
        if any(sedan_model in model_lower for sedan_model in sedan_models):
            semantic_terms.extend(['sedan', 'car', 'passenger car', 'family car', 'commuter car'])
        
        # Truck models
        truck_models = ['f-150', 'f-250', 'f-350', 'silverado', 'sierra', 'ram', 'colorado', 'canyon', 'ranger',
                        'tacoma', 'tundra', 'frontier', 'titan', 'ridgeline', 'gladiator']
        
        if any(truck_model in model_lower for truck_model in truck_models):
            semantic_terms.extend(['truck', 'pickup', 'pickup truck', 'work vehicle', 'hauling vehicle'])
        
        # Luxury brands
        luxury_brands = ['bmw', 'mercedes-benz', 'audi', 'lexus', 'acura', 'infiniti', 'cadillac', 'lincoln',
                        'porsche', 'jaguar', 'land rover', 'maserati', 'ferrari', 'lamborghini', 'bentley',
                        'rolls royce', 'aston martin']
        
        if make_lower in luxury_brands:
            semantic_terms.extend(['luxury', 'premium', 'upscale', 'high-end'])
        
        # Electric/Hybrid indicators
        description_lower = str(self.description).lower()
        features_lower = str(self.features).lower()
        
        if any(term in description_lower or term in features_lower for term in ['hybrid', 'electric', 'ev', 'phev', 'plug-in']):
            semantic_terms.extend(['eco-friendly', 'fuel efficient', 'green vehicle', 'environmentally friendly'])
        
        return list(set(semantic_terms))  # Remove duplicates
    
    def _get_price_category(self, price: int) -> str:
        """Get semantic price category."""
        if price < 15000:
            return "budget-friendly"
        elif price < 25000:
            return "affordable"
        elif price < 40000:
            return "mid-range"
        elif price < 60000:
            return "premium"
        else:
            return "luxury"
    
    def _get_mileage_category(self, mileage: int) -> str:
        """Get semantic mileage category."""
        if mileage < 20000:
            return "low mileage"
        elif mileage < 50000:
            return "moderate mileage"
        elif mileage < 100000:
            return "higher mileage"
        else:
            return "high mileage"
    
    def _enhance_features_semantically(self, features: str) -> str:
        """Enhance features with semantic synonyms."""
        enhanced_features = features
        
        # Feature synonym mapping
        feature_synonyms = {
            'navigation': 'GPS nav system',
            'leather': 'premium leather upholstery',
            'sunroof': 'panoramic roof',
            'backup camera': 'rear view camera parking assist',
            'bluetooth': 'wireless connectivity hands-free',
            'heated seats': 'warm seating comfort',
            'awd': 'all-wheel drive traction control',
            '4wd': 'four-wheel drive off-road capable',
            'hybrid': 'fuel-efficient eco-friendly',
            'turbo': 'turbocharged performance engine',
            'automatic': 'automatic transmission smooth shifting'
        }
        
        for feature, synonyms in feature_synonyms.items():
            if feature.lower() in enhanced_features.lower():
                enhanced_features += f" ({synonyms})"
        
        return enhanced_features
    
    def _get_condition_synonyms(self, condition: str) -> str:
        """Get synonyms for vehicle condition."""
        condition_lower = condition.lower()
        
        if 'excellent' in condition_lower or 'like new' in condition_lower:
            return "(pristine well-maintained)"
        elif 'good' in condition_lower:
            return "(well-cared-for reliable)"
        elif 'fair' in condition_lower:
            return "(functional needs attention)"
        elif 'poor' in condition_lower:
            return "(project vehicle fixer-upper)"
        else:
            return ""
    
    def _get_fuel_synonyms(self, fuel_type: str) -> str:
        """Get synonyms for fuel type."""
        fuel_lower = fuel_type.lower()
        
        if 'gas' in fuel_lower or 'gasoline' in fuel_lower:
            return "gasoline petrol"
        elif 'diesel' in fuel_lower:
            return "diesel fuel efficient"
        elif 'hybrid' in fuel_lower:
            return "hybrid eco-friendly fuel-efficient"
        elif 'electric' in fuel_lower or 'ev' in fuel_lower:
            return "electric zero-emissions eco-friendly"
        else:
            return ""
    
    def _get_transmission_synonyms(self, transmission: str) -> str:
        """Get synonyms for transmission type."""
        trans_lower = transmission.lower()
        
        if 'automatic' in trans_lower:
            return "automatic smooth-shifting easy-drive"
        elif 'manual' in trans_lower:
            return "manual stick-shift driver-control"
        elif 'cvt' in trans_lower:
            return "CVT continuously-variable smooth"
        else:
            return ""
    
    def _get_drivetrain_synonyms(self, drivetrain: str) -> str:
        """Get synonyms for drivetrain."""
        drivetrain_lower = drivetrain.lower()
        
        if 'awd' in drivetrain_lower or 'all wheel' in drivetrain_lower:
            return "all-wheel-drive traction-control weather-capable"
        elif '4wd' in drivetrain_lower or 'four wheel' in drivetrain_lower:
            return "four-wheel-drive off-road-capable rugged"
        elif 'fwd' in drivetrain_lower or 'front wheel' in drivetrain_lower:
            return "front-wheel-drive fuel-efficient"
        elif 'rwd' in drivetrain_lower or 'rear wheel' in drivetrain_lower:
            return "rear-wheel-drive performance-oriented"
        else:
            return ""


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