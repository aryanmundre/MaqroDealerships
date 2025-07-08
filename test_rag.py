#!/usr/bin/env python3
"""
Test script for Maqro RAG system (without API calls).
"""

import sys
from pathlib import Path
from loguru import logger
from maqro_rag import Config, InventoryProcessor


def test_inventory_processing():
    """Test inventory processing functionality."""
    logger.info("🧪 Testing Inventory Processing")
    
    try:
        # Create test config
        config = Config()
        
        # Initialize processor
        processor = InventoryProcessor(config)
        
        # Test CSV loading
        inventory_file = "sample_inventory.csv"
        if not Path(inventory_file).exists():
            logger.error(f"Test file not found: {inventory_file}")
            return False
        
        # Process inventory
        formatted_texts, metadata = processor.process_inventory(inventory_file)
        
        logger.info(f"✅ Successfully processed {len(formatted_texts)} vehicles")
        
        # Show sample formatted texts
        logger.info("\nSample formatted texts:")
        for i, text in enumerate(formatted_texts[:3]):
            logger.info(f"{i+1}. {text}")
        
        # Show sample metadata
        logger.info("\nSample metadata:")
        for i, meta in enumerate(metadata[:2]):
            logger.info(f"{i+1}. {meta}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_config_loading():
    """Test configuration loading."""
    logger.info("🧪 Testing Configuration Loading")
    
    try:
        # Test YAML config
        config = Config.from_yaml("config.yaml")
        logger.info(f"✅ YAML config loaded: embedding provider = {config.embedding.provider}")
        
        # Test environment config
        env_config = Config.from_env()
        logger.info(f"✅ Environment config loaded: vector store = {env_config.vector_store.type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Config test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("🚗 Starting Maqro RAG System Tests")
    logger.info("=" * 50)
    
    tests = [
        test_config_loading,
        test_inventory_processing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        logger.info("-" * 30)
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 