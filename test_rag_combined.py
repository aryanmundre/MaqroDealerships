#!/usr/bin/env python3
"""
Combined RAG Pipeline Test Suite
Comprehensive testing framework that combines all test approaches:
- Core functionality testing
- Mock-based testing (no API dependencies)
- Performance testing
- Frontend integration testing
- Error handling validation
"""

import sys
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from loguru import logger

# Set up Python path
sys.path.insert(0, './src')

# Import RAG components
from maqro_rag import (
    Config, 
    VehicleRetriever, 
    EnhancedRAGService,
    InventoryProcessor
)


class CombinedRAGTester:
    """Combined RAG pipeline tester with comprehensive coverage"""
    
    def __init__(self):
        self.config = Config.from_yaml("config.yaml")
        self.test_inventory_file = "sample_inventory.csv"
        self.test_index_path = "combined_test_index"
        
        # Ensure test files exist
        if not Path(self.test_inventory_file).exists():
            raise FileNotFoundError(f"Test inventory file not found: {self.test_inventory_file}")
    
    def cleanup_test_files(self):
        """Clean up test index files"""
        for ext in ['.faiss', '.metadata']:
            test_file = f"{self.test_index_path}{ext}"
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_inventory_processing(self):
        """Test inventory processing - core functionality"""
        logger.info("🧪 Testing Inventory Processing")
        
        processor = InventoryProcessor(self.config)
        formatted_texts, metadata = processor.process_inventory(self.test_inventory_file)
        
        # Validate processing results
        assert len(formatted_texts) > 0, "No vehicles processed"
        assert len(metadata) == len(formatted_texts), "Metadata count mismatch"
        
        # Validate formatted text structure
        for text in formatted_texts[:3]:
            assert isinstance(text, str), "Formatted text must be string"
            assert len(text) > 10, "Formatted text too short"
        
        # Validate metadata structure
        for meta in metadata[:3]:
            assert 'year' in meta, "Missing year in metadata"
            assert 'make' in meta, "Missing make in metadata"
            assert 'model' in meta, "Missing model in metadata"
            assert 'features' in meta, "Missing features in metadata"
            assert 'formatted_text' in meta, "Missing formatted_text in metadata"
        
        logger.info(f"✅ Inventory processing: {len(formatted_texts)} vehicles processed")
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_vehicle_retriever(self, mock_embed_text, mock_embed_texts):
        """Test vehicle retriever with mock embeddings"""
        logger.info("🧪 Testing Vehicle Retriever")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        retriever = VehicleRetriever(self.config)
        
        # Test index building
        retriever.build_index(self.test_inventory_file, self.test_index_path)
        assert retriever.is_initialized, "Retriever not initialized after building index"
        
        # Test index loading
        new_retriever = VehicleRetriever(self.config)
        new_retriever.load_index(self.test_index_path)
        assert new_retriever.is_initialized, "Retriever not initialized after loading index"
        
        # Test index stats
        stats = new_retriever.get_index_stats()
        assert 'total_vehicles' in stats, "Missing total_vehicles in stats"
        assert stats['total_vehicles'] > 0, "No vehicles in index"
        
        # Test search functionality
        test_queries = ["sedan", "SUV", "luxury", "affordable"]
        
        for query in test_queries:
            results = retriever.search_vehicles(query, top_k=3)
            assert isinstance(results, list), "Search results must be list"
            
            if results:
                for result in results:
                    assert 'vehicle' in result, "Missing vehicle data"
                    assert 'similarity_score' in result, "Missing similarity score"
                    
                    # Validate score range
                    score = result['similarity_score']
                    assert 0 <= score <= 1, f"Invalid similarity score: {score}"
                    
                    # Validate vehicle data structure
                    vehicle = result['vehicle']
                    assert 'year' in vehicle, "Missing year in vehicle data"
                    assert 'make' in vehicle, "Missing make in vehicle data"
                    assert 'model' in vehicle, "Missing model in vehicle data"
                    assert 'features' in vehicle, "Missing features in vehicle data"
        
        logger.info(f"✅ Vehicle retriever: {len(test_queries)} queries tested, {stats['total_vehicles']} vehicles indexed")
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_enhanced_rag_service(self, mock_embed_text, mock_embed_texts):
        """Test enhanced RAG service with mock embeddings"""
        logger.info("🧪 Testing Enhanced RAG Service")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Initialize retriever
        retriever = VehicleRetriever(self.config)
        retriever.build_index(self.test_inventory_file, self.test_index_path)
        
        # Create enhanced RAG service with mock context analysis
        def mock_context_analysis(conversations):
            return {
                'intent': 'general_inquiry',
                'preferences': {},
                'urgency': 'medium',
                'budget_range': None,
                'vehicle_type': None,
                'conversation_length': len(conversations)
            }
        
        enhanced_rag = EnhancedRAGService(
            retriever=retriever,
            analyze_conversation_context_func=mock_context_analysis
        )
        
        # Test vehicle search with context
        test_conversations = [
            {"sender": "customer", "message": "I'm looking for a reliable sedan"}
        ]
        
        vehicles = enhanced_rag.search_vehicles_with_context(
            "reliable sedan", test_conversations, top_k=3
        )
        
        assert isinstance(vehicles, list), "Enhanced search results must be list"
        
        logger.info(f"✅ Enhanced RAG service: {len(vehicles)} vehicles found")
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_response_generation(self, mock_embed_text, mock_embed_texts):
        """Test response generation with mock embeddings"""
        logger.info("🧪 Testing Response Generation")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Initialize retriever
        retriever = VehicleRetriever(self.config)
        retriever.build_index(self.test_inventory_file, self.test_index_path)
        
        # Mock context analysis
        def mock_context_analysis(conversations):
            return {
                'intent': 'general_inquiry',
                'preferences': {},
                'urgency': 'medium',
                'budget_range': None,
                'vehicle_type': None,
                'conversation_length': len(conversations)
            }
        
        enhanced_rag = EnhancedRAGService(
            retriever=retriever,
            analyze_conversation_context_func=mock_context_analysis
        )
        
        # Test response generation with actual vehicle data
        test_scenarios = [
            {
                "query": "Looking for a reliable sedan",
                "conversations": [{"sender": "customer", "message": "I need a reliable sedan"}],
                "lead_name": "John Doe"
            },
            {
                "query": "Luxury car",
                "conversations": [{"sender": "customer", "message": "I want a luxury car"}],
                "lead_name": "Sarah Smith"
            }
        ]
        
        for scenario in test_scenarios:
            # Get actual vehicles from search
            vehicles = enhanced_rag.search_vehicles_with_context(
                scenario["query"], scenario["conversations"], top_k=3
            )
            
            # Generate response with actual vehicles
            response = enhanced_rag.generate_enhanced_response(
                query=scenario["query"],
                vehicles=vehicles,
                conversations=scenario["conversations"],
                lead_name=scenario["lead_name"]
            )
            
            # Validate response structure
            assert 'response_text' in response, "Missing response_text"
            assert 'quality_metrics' in response, "Missing quality_metrics"
            assert 'follow_up_suggestions' in response, "Missing follow_up_suggestions"
            assert 'context_analysis' in response, "Missing context_analysis"
            assert 'vehicles_found' in response, "Missing vehicles_found"
            assert 'query' in response, "Missing query"
            
            # Validate response text
            response_text = response['response_text']
            assert isinstance(response_text, str), "Response text must be string"
            assert len(response_text) > 20, "Response text too short"
            
            # Validate quality metrics
            quality_metrics = response['quality_metrics']
            expected_metrics = ['relevance_score', 'completeness_score', 'personalization_score', 'actionability_score']
            for metric in expected_metrics:
                assert metric in quality_metrics, f"Missing quality metric: {metric}"
                score = quality_metrics[metric]
                assert 0 <= score <= 1, f"Invalid quality score for {metric}: {score}"
            
            # Validate follow-up suggestions
            follow_ups = response['follow_up_suggestions']
            assert isinstance(follow_ups, list), "Follow-up suggestions must be list"
            assert len(follow_ups) > 0, "No follow-up suggestions provided"
        
        logger.info(f"✅ Response generation: {len(test_scenarios)} scenarios tested")
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_error_handling(self, mock_embed_text, mock_embed_texts):
        """Test error handling and graceful degradation"""
        logger.info("🧪 Testing Error Handling")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Test with invalid configuration
        try:
            invalid_config = Config()
            invalid_config.embedding.provider = "invalid_provider"
            retriever = VehicleRetriever(invalid_config)
            assert False, "Should have raised error for invalid provider"
        except ValueError:
            logger.info("✅ Correctly handled invalid embedding provider")
        
        # Test with non-existent file
        try:
            retriever = VehicleRetriever(self.config)
            retriever.build_index("non_existent_file.csv")
            assert False, "Should have raised error for non-existent file"
        except FileNotFoundError:
            logger.info("✅ Correctly handled non-existent inventory file")
        
        # Test with empty search results
        retriever = VehicleRetriever(self.config)
        if not os.path.exists(f"{self.test_index_path}.faiss"):
            # Build index for testing
            retriever.build_index(self.test_inventory_file, self.test_index_path)
        else:
            retriever.load_index(self.test_index_path)
        
        # Search for something that shouldn't exist
        results = retriever.search_vehicles("completely random query that should not match anything", top_k=3)
        assert isinstance(results, list), "Should return empty list, not error"
        
        logger.info("✅ Error handling: All error scenarios handled gracefully")
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_performance(self, mock_embed_text, mock_embed_texts):
        """Test performance baseline"""
        logger.info("🧪 Testing Performance Baseline")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Initialize retriever
        retriever = VehicleRetriever(self.config)
        retriever.build_index(self.test_inventory_file, self.test_index_path)
        
        # Test search performance
        import time
        
        test_queries = ["sedan", "SUV", "luxury", "affordable"]
        
        total_time = 0
        for query in test_queries:
            start_time = time.time()
            results = retriever.search_vehicles(query, top_k=3)
            end_time = time.time()
            
            query_time = end_time - start_time
            total_time += query_time
            
            # Each query should complete within reasonable time
            assert query_time < 2.0, f"Query took too long: {query_time:.2f}s"
        
        avg_time = total_time / len(test_queries)
        logger.info(f"✅ Performance: Average query time {avg_time:.3f}s")
        
        # Performance should be acceptable for frontend integration
        assert avg_time < 1.0, f"Average query time too slow: {avg_time:.3f}s"
        
        return True
    
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts')
    @patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text')
    def test_frontend_integration_readiness(self, mock_embed_text, mock_embed_texts):
        """Test readiness for frontend integration"""
        logger.info("🧪 Testing Frontend Integration Readiness")
        
        # Mock embedding responses
        mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
        mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
        
        # Test complete flow that frontend would use
        retriever = VehicleRetriever(self.config)
        retriever.build_index(self.test_inventory_file, self.test_index_path)
        
        # Mock context analysis
        def mock_context_analysis(conversations):
            return {
                'intent': 'general_inquiry',
                'preferences': {},
                'urgency': 'medium',
                'budget_range': None,
                'vehicle_type': None,
                'conversation_length': len(conversations)
            }
        
        enhanced_rag = EnhancedRAGService(
            retriever=retriever,
            analyze_conversation_context_func=mock_context_analysis
        )
        
        # Simulate frontend request
        customer_message = "I'm looking for a reliable sedan under $30,000"
        conversation_history = [
            {"sender": "customer", "message": customer_message}
        ]
        
        # Step 1: Search for vehicles
        vehicles = enhanced_rag.search_vehicles_with_context(
            customer_message, conversation_history, top_k=3
        )
        
        # Step 2: Generate response
        response = enhanced_rag.generate_enhanced_response(
            customer_message, vehicles, conversation_history, "Test Customer"
        )
        
        # Validate response structure for frontend
        required_fields = [
            'response_text',
            'quality_metrics',
            'follow_up_suggestions',
            'context_analysis',
            'vehicles_found',
            'query'
        ]
        
        for field in required_fields:
            assert field in response, f"Missing required field for frontend: {field}"
        
        # Validate response is JSON-serializable
        import json
        try:
            json.dumps(response)
            logger.info("✅ Response is JSON-serializable")
        except TypeError as e:
            assert False, f"Response not JSON-serializable: {e}"
        
        # Validate response quality
        quality_metrics = response['quality_metrics']
        total_score = sum(quality_metrics.values()) / len(quality_metrics)
        assert total_score > 0.3, f"Response quality too low: {total_score}"
        
        logger.info(f"✅ Frontend integration: Response quality score {total_score:.2f}")
        return True
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        logger.info("🧪 Testing Configuration Validation")
        
        # Test YAML config loading
        config = Config.from_yaml("config.yaml")
        assert config.embedding.provider == "openai", "Wrong embedding provider"
        assert config.vector_store.type == "faiss", "Wrong vector store type"
        assert config.retrieval.top_k == 3, "Wrong top_k value"
        
        # Test environment config
        env_config = Config.from_env()
        assert env_config.embedding.provider == "openai", "Wrong env embedding provider"
        assert env_config.vector_store.type == "faiss", "Wrong env vector store type"
        
        logger.info("✅ Configuration validation: All configs loaded correctly")
        return True
    
    def test_example_conversation_response(self):
        """Test and demonstrate example conversation response"""
        logger.info("🧪 Testing Example Conversation Response")
        
        # Mock embedding responses
        with patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_texts') as mock_embed_texts, \
             patch('maqro_rag.embedding.OpenAIEmbeddingProvider.embed_text') as mock_embed_text:
            
            mock_embed_texts.return_value = np.random.rand(10, 1536).astype(np.float32)
            mock_embed_text.return_value = np.random.rand(1, 1536).astype(np.float32)
            
            # Initialize retriever
            retriever = VehicleRetriever(self.config)
            retriever.build_index(self.test_inventory_file, self.test_index_path)
            
            # Mock context analysis
            def mock_context_analysis(conversations):
                return {
                    'intent': 'general_inquiry',
                    'preferences': {'budget': 'under $30,000'},
                    'urgency': 'medium',
                    'budget_range': (20000, 30000),
                    'vehicle_type': 'sedan',
                    'conversation_length': len(conversations)
                }
            
            enhanced_rag = EnhancedRAGService(
                retriever=retriever,
                analyze_conversation_context_func=mock_context_analysis
            )
            
            # Simulate customer conversation
            customer_message = "I'm looking for a reliable sedan under $30,000"
            conversation_history = [
                {"sender": "customer", "message": "Hi, I'm interested in buying a car"},
                {"sender": "agent", "message": "Great! What type of vehicle are you looking for?"},
                {"sender": "customer", "message": customer_message}
            ]
            
            # Generate AI response
            vehicles = enhanced_rag.search_vehicles_with_context(
                customer_message, conversation_history, top_k=3
            )
            
            response = enhanced_rag.generate_enhanced_response(
                customer_message, vehicles, conversation_history, "John Smith"
            )
            
            # Log example response
            logger.info("📝 Example Conversation Response:")
            logger.info(f"Query: {response['query']}")
            logger.info(f"Response Text: {response['response_text'][:200]}...")
            logger.info(f"Vehicles Found: {response['vehicles_found']}")
            logger.info(f"Quality Score: {sum(response['quality_metrics'].values()) / len(response['quality_metrics']):.2f}")
            logger.info(f"Follow-up Suggestions: {response['follow_up_suggestions']}")
            
            return True


def run_combined_tests():
    """Run all combined tests"""
    logger.info("🚗 Starting Combined RAG Pipeline Tests")
    logger.info("=" * 60)
    
    tester = CombinedRAGTester()
    test_methods = [
        tester.test_inventory_processing,
        tester.test_vehicle_retriever,
        tester.test_enhanced_rag_service,
        tester.test_response_generation,
        tester.test_error_handling,
        tester.test_performance,
        tester.test_frontend_integration_readiness,
        tester.test_configuration_validation,
        tester.test_example_conversation_response,
    ]
    
    passed = 0
    total = len(test_methods)
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
            logger.info(f"✅ {test_method.__name__} passed")
        except Exception as e:
            logger.error(f"❌ {test_method.__name__} failed: {e}")
        logger.info("-" * 40)
    
    # Cleanup
    tester.cleanup_test_files()
    
    logger.info(f"📊 Combined Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! RAG pipeline is ready for frontend integration!")
        logger.info("✅ RAG Pipeline Status: READY FOR FRONTEND INTEGRATION")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed. Review issues before frontend integration.")
        logger.error("❌ RAG Pipeline Status: NEEDS FIXES BEFORE FRONTEND INTEGRATION")
        return 1


if __name__ == "__main__":
    sys.exit(run_combined_tests()) 