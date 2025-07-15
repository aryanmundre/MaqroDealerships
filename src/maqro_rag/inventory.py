"""
Inventory processor module for ingesting and formatting vehicle data.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from loguru import logger
from .config import Config


class InventoryProcessor:
    """Processes inventory data and formats it for embedding."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load inventory data from CSV file."""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} vehicles from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            raise
    
    def load_json(self, file_path: str) -> pd.DataFrame:
        """Load inventory data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'vehicles' in data:
                df = pd.DataFrame(data['vehicles'])
            else:
                raise ValueError("Invalid JSON format")
            
            logger.info(f"Loaded {len(df)} vehicles from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            raise
    
    def format_vehicle_text(self, row: pd.Series) -> str:
        """Format a vehicle row into a single text string for embedding."""
        try:
            # Extract basic vehicle information
            year = row.get('year', '')
            make = row.get('make', '')
            model = row.get('model', '')
            price = row.get('price', '')
            features = row.get('features', '')
            description = row.get('description', '')
            
            # Format price
            if price and pd.notna(price):
                if isinstance(price, (int, float)):
                    price_str = f"${price:,.0f}"
                else:
                    price_str = str(price)
            else:
                price_str = "Price not specified"
            
            # Format features
            if features and pd.notna(features):
                if isinstance(features, str):
                    features_str = features
                else:
                    features_str = ", ".join(features) if isinstance(features, list) else str(features)
            else:
                features_str = "Standard features"
            
            # Format description
            if description and pd.notna(description):
                description_str = str(description)
            else:
                description_str = ""
            
            # Create formatted text
            formatted_text = f"{year} {make} {model}, {price_str}, {features_str}"
            if description_str:
                formatted_text += f". {description_str}"
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting vehicle text: {e}")
            # Return a basic format as fallback
            return f"{row.get('year', '')} {row.get('make', '')} {row.get('model', '')}"
    
    def process_inventory(self, file_path: str) -> tuple[List[str], List[Dict[str, Any]]]:
        """Process inventory file and return formatted texts and metadata."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Inventory file not found: {file_path}")
        
        # Load data based on file extension
        if file_path.suffix.lower() == '.csv':
            df = self.load_csv(file_path)
        elif file_path.suffix.lower() == '.json':
            df = self.load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Process each vehicle
        formatted_texts = []
        metadata = []
        
        for idx, row in df.iterrows():
            try:
                # Format text for embedding
                formatted_text = self.format_vehicle_text(row)
                formatted_texts.append(formatted_text)
                
                # Create metadata
                vehicle_metadata = {
                    'index': idx,
                    'year': row.get('year'),
                    'make': row.get('make'),
                    'model': row.get('model'),
                    'price': row.get('price'),
                    'features': row.get('features'),
                    'description': row.get('description'),
                    'formatted_text': formatted_text
                }
                metadata.append(vehicle_metadata)
                
            except Exception as e:
                logger.warning(f"Error processing vehicle at index {idx}: {e}")
                continue
        
        logger.info(f"Processed {len(formatted_texts)} vehicles successfully")
        return formatted_texts, metadata
    
    def validate_inventory(self, df: pd.DataFrame) -> bool:
        """Validate that inventory data has required columns."""
        required_columns = ['year', 'make', 'model']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for empty values in required columns
        for col in required_columns:
            if df[col].isnull().any():
                logger.warning(f"Found empty values in required column: {col}")
        
        return True 