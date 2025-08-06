#!/usr/bin/env python3
"""
Example Conversation Response Demo
Shows what an actual RAG pipeline response looks like for frontend integration.
"""

import sys
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch
from loguru import logger
import json

# Set up Python path
sys.path.insert(0, './src')

# Import RAG components
from maqro_rag import (
    Config, 
    VehicleRetriever, 
    EnhancedRAGService,
    InventoryProcessor
)


def demonstrate_conversation_response():
    """Demonstrate an example conversation response from the RAG pipeline"""
    
    logger.info("🚗 RAG Pipeline - Example Conversation Response Demo")
    logger.info("=" * 60)
    
    # Initialize components
    config = Config.from_yaml("config.yaml")
    test_inventory_file = "sample_inventory.csv"
    test_index_path = "demo_index"
    
    # Mock embedding responses
    with patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts') as mock_embed_texts, \
         patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text') as mock_embed_text:
        
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Initialize retriever
        retriever = VehicleRetriever(config)
        retriever.build_index(test_inventory_file, test_index_path)
        
        # Mock context analysis function
        def mock_context_analysis(conversations):
            """Mock conversation context analysis"""
            # Analyze conversation to extract intent and preferences
            customer_messages = [msg for msg in conversations if msg.get('sender') == 'customer']
            
            # Extract budget information
            budget_keywords = ['under', 'budget', 'affordable', 'cheap', 'expensive']
            budget_range = None
            for msg in customer_messages:
                text = msg.get('message', '').lower()
                if any(keyword in text for keyword in budget_keywords):
                    if 'under $30' in text or 'under 30' in text:
                        budget_range = (15000, 30000)
                    elif 'under $50' in text or 'under 50' in text:
                        budget_range = (25000, 50000)
                    break
            
            # Extract vehicle type preferences
            vehicle_type = None
            vehicle_keywords = {
                'sedan': ['sedan', 'car', 'compact'],
                'SUV': ['suv', 'truck', 'crossover'],
                'luxury': ['luxury', 'premium', 'bmw', 'mercedes', 'audi'],
                'electric': ['electric', 'ev', 'tesla', 'hybrid']
            }
            
            for msg in customer_messages:
                text = msg.get('message', '').lower()
                for vtype, keywords in vehicle_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        vehicle_type = vtype
                        break
                if vehicle_type:
                    break
            
            return {
                'intent': 'vehicle_inquiry',
                'preferences': {
                    'budget': budget_range,
                    'vehicle_type': vehicle_type,
                    'features': ['reliable', 'fuel efficient'] if 'reliable' in str(customer_messages).lower() else []
                },
                'urgency': 'medium',
                'budget_range': budget_range,
                'vehicle_type': vehicle_type,
                'conversation_length': len(conversations)
            }
        
        # Create enhanced RAG service
        enhanced_rag = EnhancedRAGService(
            retriever=retriever,
            analyze_conversation_context_func=mock_context_analysis
        )
        
        # Example conversation scenarios
        scenarios = [
            {
                "name": "Budget Sedan Inquiry",
                "customer_message": "I'm looking for a reliable sedan under $30,000",
                "conversation_history": [
                    {"sender": "customer", "message": "Hi, I'm interested in buying a car"},
                    {"sender": "agent", "message": "Great! What type of vehicle are you looking for?"},
                    {"sender": "customer", "message": "I'm looking for a reliable sedan under $30,000"}
                ],
                "lead_name": "John Smith"
            },
            {
                "name": "Luxury Vehicle Inquiry",
                "customer_message": "I want a luxury car with advanced features",
                "conversation_history": [
                    {"sender": "customer", "message": "I'm interested in a premium vehicle"},
                    {"sender": "agent", "message": "What's your budget range?"},
                    {"sender": "customer", "message": "I want a luxury car with advanced features"}
                ],
                "lead_name": "Sarah Johnson"
            },
            {
                "name": "SUV Family Vehicle",
                "customer_message": "I need an SUV for my family, something spacious and safe",
                "conversation_history": [
                    {"sender": "customer", "message": "I have a family and need a larger vehicle"},
                    {"sender": "agent", "message": "How many passengers do you need to accommodate?"},
                    {"sender": "customer", "message": "I need an SUV for my family, something spacious and safe"}
                ],
                "lead_name": "Mike Davis"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"\n📋 Scenario {i}: {scenario['name']}")
            logger.info("-" * 50)
            
            # Generate AI response
            vehicles = enhanced_rag.search_vehicles_with_context(
                scenario["customer_message"], 
                scenario["conversation_history"], 
                top_k=3
            )
            
            response = enhanced_rag.generate_enhanced_response(
                scenario["customer_message"], 
                vehicles, 
                scenario["conversation_history"], 
                scenario["lead_name"]
            )
            
            # Display the response
            logger.info(f"🎯 Customer Query: {response['query']}")
            logger.info(f"👤 Lead Name: {scenario['lead_name']}")
            logger.info(f"🚗 Vehicles Found: {response['vehicles_found']}")
            
            # Quality metrics
            quality_metrics = response['quality_metrics']
            avg_quality = sum(quality_metrics.values()) / len(quality_metrics)
            logger.info(f"📊 Response Quality Score: {avg_quality:.2f}")
            
            # Response text
            logger.info(f"💬 AI Response:")
            logger.info(f"   {response['response_text']}")
            
            # Follow-up suggestions
            logger.info(f"💡 Follow-up Suggestions:")
            for suggestion in response['follow_up_suggestions']:
                logger.info(f"   • {suggestion}")
            
            # Context analysis
            context = response['context_analysis']
            logger.info(f"🔍 Context Analysis:")
            logger.info(f"   Intent: {context.get('intent', 'unknown')}")
            logger.info(f"   Vehicle Type: {context.get('vehicle_type', 'none')}")
            logger.info(f"   Budget Range: {context.get('budget_range', 'none')}")
            logger.info(f"   Urgency: {context.get('urgency', 'unknown')}")
            
            # JSON response structure
            logger.info(f"📄 JSON Response Structure:")
            response_json = {
                "response_text": response['response_text'],
                "quality_metrics": response['quality_metrics'],
                "follow_up_suggestions": response['follow_up_suggestions'],
                "context_analysis": response['context_analysis'],
                "vehicles_found": response['vehicles_found'],
                "query": response['query']
            }
            
            # Pretty print JSON (first 500 chars)
            json_str = json.dumps(response_json, indent=2)
            logger.info(f"   {json_str[:500]}...")
            
            logger.info("=" * 60)
        
        # Cleanup
        for ext in ['.faiss', '.metadata']:
            test_file = f"{test_index_path}{ext}"
            if os.path.exists(test_file):
                os.remove(test_file)
        
        logger.info("✅ Demo completed successfully!")
        return True


if __name__ == "__main__":
    demonstrate_conversation_response() 