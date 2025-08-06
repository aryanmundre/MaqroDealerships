#!/usr/bin/env python3
"""
Test RAG pipeline with real OpenAI API calls
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Set up Python path
sys.path.insert(0, './src')

from maqro_rag import (
    Config, 
    VehicleRetriever, 
    EnhancedRAGService,
    InventoryProcessor
)

def test_real_openai_integration():
    """Test RAG pipeline with real OpenAI API calls"""
    
    logger.info("🚀 Testing RAG Pipeline with Real OpenAI API")
    logger.info("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not set! Please set it first:")
        logger.error("export OPENAI_API_KEY='sk-your-api-key-here'")
        return False
    
    if api_key == "your_openai_api_key_here":
        logger.error("❌ Please replace 'your_openai_api_key_here' with your actual API key")
        return False
    
    logger.info("✅ OpenAI API key found")
    
    try:
        # Initialize components
        config = Config.from_yaml("config.yaml")
        test_inventory_file = "sample_inventory.csv"
        test_index_path = "real_openai_test_index"
        
        # Test inventory processing
        logger.info("📊 Processing inventory...")
        processor = InventoryProcessor(config)
        formatted_texts, metadata = processor.process_inventory(test_inventory_file)
        logger.info(f"✅ Processed {len(formatted_texts)} vehicles")
        
        # Test vehicle retriever with real embeddings
        logger.info("🔍 Building vector index with real embeddings...")
        retriever = VehicleRetriever(config)
        retriever.build_index(test_inventory_file, test_index_path)
        logger.info("✅ Vector index built successfully")
        
        # Test search with real embeddings
        logger.info("🔎 Testing semantic search...")
        test_queries = [
            "reliable sedan under $30,000",
            "luxury car with advanced features", 
            "family SUV spacious and safe"
        ]
        
        for query in test_queries:
            logger.info(f"Query: '{query}'")
            results = retriever.search_vehicles(query, top_k=3)
            
            if results:
                logger.info(f"Found {len(results)} vehicles:")
                for i, result in enumerate(results, 1):
                    vehicle = result['vehicle']
                    score = result['similarity_score']
                    logger.info(f"  {i}. {vehicle['year']} {vehicle['make']} {vehicle['model']} - ${vehicle['price']:,} (Score: {score:.1%})")
            else:
                logger.info("No vehicles found")
            logger.info("-" * 40)
        
        # Test enhanced RAG service
        logger.info("🤖 Testing Enhanced RAG Service...")
        
        def mock_context_analysis(conversations):
            return {
                'intent': 'vehicle_inquiry',
                'preferences': {},
                'urgency': 'medium',
                'budget_range': [15000, 30000],
                'vehicle_type': 'sedan',
                'conversation_length': len(conversations)
            }
        
        enhanced_rag = EnhancedRAGService(
            retriever=retriever,
            analyze_conversation_context_func=mock_context_analysis
        )
        
        # Test real conversation
        customer_message = "I'm looking for a reliable sedan under $30,000"
        conversation_history = [
            {"sender": "customer", "message": "Hi, I'm interested in buying a car"},
            {"sender": "agent", "message": "Great! What type of vehicle are you looking for?"},
            {"sender": "customer", "message": customer_message}
        ]
        
        logger.info(f"Customer: {customer_message}")
        
        # Generate response
        vehicles = enhanced_rag.search_vehicles_with_context(
            customer_message, conversation_history, top_k=3
        )
        
        response = enhanced_rag.generate_enhanced_response(
            customer_message, vehicles, conversation_history, "John Smith"
        )
        
        logger.info("🤖 AI Response:")
        logger.info(response['response_text'])
        
        logger.info(f"📊 Quality Score: {sum(response['quality_metrics'].values()) / len(response['quality_metrics']):.2f}")
        logger.info(f"💡 Follow-ups: {', '.join(response['follow_up_suggestions'])}")
        
        # Cleanup
        for ext in ['.faiss', '.metadata']:
            test_file = f"{test_index_path}{ext}"
            if os.path.exists(test_file):
                os.remove(test_file)
        
        logger.info("✅ Real OpenAI API test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_real_openai_integration() 