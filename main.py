#!/usr/bin/env python3
"""
Main script to demonstrate Maqro RAG system functionality.
"""

import os
import sys
from pathlib import Path
from loguru import logger
from maqro_rag import Config, VehicleRetriever


def setup_logging(config: Config):
    """Setup logging configuration."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format=config.logging.format,
        level=config.logging.level
    )


def main():
    """Main function to demonstrate RAG system."""
    try:
        # Load configuration
        config = Config.from_yaml("config.yaml")
        setup_logging(config)
        
        logger.info("🚗 Starting Maqro RAG System Demo")
        
        # Initialize vehicle retriever
        retriever = VehicleRetriever(config)
        
        # Check if inventory file exists
        inventory_file = "sample_inventory.csv"
        if not Path(inventory_file).exists():
            logger.error(f"Inventory file not found: {inventory_file}")
            logger.info("Please ensure sample_inventory.csv exists in the current directory")
            return
        
        # Build or load index
        index_path = "vehicle_index"
        if Path(f"{index_path}.faiss").exists():
            logger.info("Loading existing index...")
            retriever.load_index(index_path)
        else:
            logger.info("Building new index...")
            retriever.build_index(inventory_file, index_path)
        
        # Get index statistics
        stats = retriever.get_index_stats()
        logger.info(f"Index stats: {stats}")
        
        # Demo queries
        demo_queries = [
            "Looking for a reliable sedan with good gas mileage",
            "I want a luxury car with advanced technology",
            "Show me affordable vehicles under $25,000",
            "I need an SUV for family use",
            "Electric vehicle with modern features"
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🔍 DEMO QUERIES")
        logger.info("="*60)
        
        for i, query in enumerate(demo_queries, 1):
            logger.info(f"\nQuery {i}: {query}")
            logger.info("-" * 40)
            
            try:
                results = retriever.search_vehicles(query, top_k=3)
                
                if results:
                    formatted_results = retriever.format_search_results(results)
                    logger.info(formatted_results)
                else:
                    logger.info("No vehicles found matching the criteria.")
                    
            except Exception as e:
                logger.error(f"Error processing query: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Demo completed successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 