"""
Test Suite for AI Response Generator

This module tests the complete AI Response Generator functionality including:
- Context analysis
- Response generation
- Quality validation
- Enhanced RAG integration
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maqro_backend.services.ai_services import (
    analyze_conversation_context,
    get_last_customer_message,
    generate_contextual_ai_response,
    _detect_intent,
    _extract_preferences,
    _detect_urgency,
    _extract_budget_range
)
from maqro_rag.rag_enhanced import EnhancedRAGService
from maqro_backend.services.response_validation import ResponseValidator, ResponseQualityMonitor
from maqro_backend.db.models.conversation import Conversation

class TestContextAnalysis:
    """Test conversation context analysis functionality"""
    
    def test_analyze_empty_conversation(self):
        """Test analysis of empty conversation"""
        conversations = []
        analysis = analyze_conversation_context(conversations)
        
        assert analysis['intent'] == 'general_inquiry'
        assert analysis['preferences'] == {}
        assert analysis['urgency'] == 'low'
        assert analysis['budget_range'] is None
        assert analysis['vehicle_type'] is None
        assert analysis['conversation_length'] == 0
    
    def test_detect_intent(self):
        """Test intent detection"""
        # Test drive intent
        messages = ["I want to test drive a car"]
        intent = _detect_intent(messages)
        assert intent == 'test_drive'
        
        # Pricing intent
        messages = ["What's the price of this vehicle?"]
        intent = _detect_intent(messages)
        assert intent == 'pricing'
        
        # Availability intent
        messages = ["Do you have this car in stock?"]
        intent = _detect_intent(messages)
        assert intent == 'availability'
        
        # Financing intent
        messages = ["What are the financing options?"]
        intent = _detect_intent(messages)
        assert intent == 'financing'
    
    def test_extract_preferences(self):
        """Test preference extraction"""
        messages = [
            "I'm looking for a red SUV with leather seats",
            "I prefer automatic transmission"
        ]
        preferences = _extract_preferences(messages)
        
        assert 'color' in preferences
        assert 'red' in preferences['color']
        assert 'body_style' in preferences
        assert 'suv' in preferences['body_style']
        assert 'features' in preferences
        assert 'leather' in preferences['features']
        assert 'transmission' in preferences
        assert 'automatic' in preferences['transmission']
    
    def test_detect_urgency(self):
        """Test urgency detection"""
        # High urgency
        messages = ["I need this urgently", "ASAP please"]
        urgency = _detect_urgency(messages)
        assert urgency == 'high'
        
        # Medium urgency
        messages = ["I'm interested in buying soon"]
        urgency = _detect_urgency(messages)
        assert urgency == 'medium'
        
        # Low urgency
        messages = ["Maybe someday", "I'm just thinking about it"]
        urgency = _detect_urgency(messages)
        assert urgency == 'low'
    
    def test_extract_budget_range(self):
        """Test budget range extraction"""
        # Dollar range
        messages = ["My budget is $20,000-$30,000"]
        budget = _extract_budget_range(messages)
        assert budget == (20000.0, 30000.0)
        
        # K format
        messages = ["I'm looking for something in the 25k to 35k range"]
        budget = _extract_budget_range(messages)
        assert budget == (25.0, 35.0)
        
        # No budget mentioned
        messages = ["I'm just looking around"]
        budget = _extract_budget_range(messages)
        assert budget is None


class TestResponseGeneration:
    """Test AI response generation functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_vehicles = [
            {
                'vehicle': {
                    'year': '2022',
                    'make': 'Toyota',
                    'model': 'Camry',
                    'price': 25000,
                    'features': 'Leather seats, Navigation',
                    'description': 'Excellent condition'
                },
                'similarity_score': 0.85
            },
            {
                'vehicle': {
                    'year': '2021',
                    'make': 'Honda',
                    'model': 'Accord',
                    'price': 23000,
                    'features': 'Sunroof, Backup camera',
                    'description': 'Well maintained'
                },
                'similarity_score': 0.78
            }
        ]
    
    def test_generate_contextual_response_with_vehicles(self):
        """Test contextual response generation with vehicles"""
        conversations = [
            Conversation(
                lead_id=1,
                message="I'm looking for a sedan under $30,000",
                sender="customer",
                created_at=datetime.now()
            )
        ]
        
        response = generate_contextual_ai_response(
            conversations,
            self.mock_vehicles,
            "John Doe"
        )
        
        assert "Hi John Doe!" in response
        assert "Toyota Camry" in response
        assert "Honda Accord" in response
        assert "$25,000" in response
        assert "$23,000" in response
        assert "test drive" in response.lower()
    
    def test_generate_response_no_vehicles(self):
        """Test response generation when no vehicles match"""
        conversations = [
            Conversation(
                lead_id=1,
                message="I'm looking for a rare sports car",
                sender="customer",
                created_at=datetime.now()
            )
        ]
        
        response = generate_contextual_ai_response(
            conversations,
            [],
            "John Doe"
        )
        
        assert "Hi John Doe!" in response
        assert "don't have exact matches" in response.lower()
        assert "budget" in response.lower()
    
    def test_get_last_customer_message(self):
        """Test extraction of last customer message"""
        conversations = [
            Conversation(
                lead_id=1,
                message="First message",
                sender="customer",
                created_at=datetime.now()
            ),
            Conversation(
                lead_id=1,
                message="Agent response",
                sender="agent",
                created_at=datetime.now()
            ),
            Conversation(
                lead_id=1,
                message="Last customer message",
                sender="customer",
                created_at=datetime.now()
            )
        ]
        
        last_message = get_last_customer_message(conversations)
        assert last_message == "Last customer message"


class TestEnhancedRAGService:
    """Test Enhanced RAG Service functionality"""
    
    def setup_method(self):
        """Setup mock retriever"""
        self.mock_retriever = Mock()
        self.enhanced_service = EnhancedRAGService(self.mock_retriever)
    
    def test_generate_search_queries(self):
        """Test search query generation"""
        query = "sedan"
        context_analysis = {
            'vehicle_type': 'sedan',
            'budget_range': (20000, 30000),
            'preferences': {'features': ['leather']},
            'intent': 'test_drive'
        }
        
        queries = self.enhanced_service._generate_search_queries(query, context_analysis)
        
        assert "sedan" in queries
        assert "sedan sedan" in queries  # vehicle_type + query
        assert "sedan under $30,000" in queries
        assert "sedan $20,000-$30,000" in queries
        assert "sedan leather" in queries
        assert "sedan available for test drive" in queries
    
    def test_deduplicate_results(self):
        """Test result deduplication"""
        results = [
            {
                'vehicle': {'year': '2022', 'make': 'Toyota', 'model': 'Camry', 'price': 25000},
                'similarity_score': 0.8
            },
            {
                'vehicle': {'year': '2022', 'make': 'Toyota', 'model': 'Camry', 'price': 25000},
                'similarity_score': 0.9
            },
            {
                'vehicle': {'year': '2021', 'make': 'Honda', 'model': 'Accord', 'price': 23000},
                'similarity_score': 0.7
            }
        ]
        
        unique_results = self.enhanced_service._deduplicate_results(results)
        assert len(unique_results) == 2  # Should remove duplicate Toyota Camry
    
    def test_apply_context_filters(self):
        """Test context-based filtering"""
        results = [
            {
                'vehicle': {'year': '2022', 'make': 'Toyota', 'model': 'Camry', 'price': 25000},
                'similarity_score': 0.8
            },
            {
                'vehicle': {'year': '2021', 'make': 'Honda', 'model': 'Accord', 'price': 35000},
                'similarity_score': 0.7
            }
        ]
        
        context_analysis = {
            'budget_range': (20000, 30000),
            'vehicle_type': 'sedan',
            'preferences': {'features': ['leather']}
        }
        
        filtered_results = self.enhanced_service._apply_context_filters(results, context_analysis)
        
        # Honda Accord should be filtered out due to price
        assert len(filtered_results) == 1
        assert filtered_results[0]['vehicle']['make'] == 'Toyota'


class TestResponseValidation:
    """Test response validation functionality"""
    
    def setup_method(self):
        """Setup validator"""
        self.validator = ResponseValidator()
        self.quality_monitor = ResponseQualityMonitor()
    
    def test_validate_good_response(self):
        """Test validation of good quality response"""
        response_data = {
            'response_text': 'Hi John! I found 2 vehicles that match your criteria: 1. 2022 Toyota Camry - $25,000 2. 2021 Honda Accord - $23,000. Would you like to schedule a test drive?',
            'vehicles': [
                {'vehicle': {'make': 'Toyota', 'model': 'Camry', 'price': 25000}},
                {'vehicle': {'make': 'Honda', 'model': 'Accord', 'price': 23000}}
            ],
            'quality_metrics': {
                'relevance_score': 0.8,
                'completeness_score': 0.7,
                'personalization_score': 0.9,
                'actionability_score': 0.8
            }
        }
        
        is_valid, validation_details, fallback = self.validator.validate_response(
            response_data, "I'm looking for a sedan"
        )
        
        assert is_valid
        assert validation_details['quality_score'] > 0.7
        assert fallback is None
    
    def test_validate_poor_response(self):
        """Test validation of poor quality response"""
        response_data = {
            'response_text': 'Hello',
            'vehicles': [],
            'quality_metrics': {
                'relevance_score': 0.2,
                'completeness_score': 0.1,
                'personalization_score': 0.3,
                'actionability_score': 0.2
            }
        }
        
        is_valid, validation_details, fallback = self.validator.validate_response(
            response_data, "I'm looking for a car"
        )
        
        assert not is_valid
        assert validation_details['quality_score'] < 0.5
        assert fallback is not None
        assert "help you find" in fallback
    
    def test_enhance_response_quality(self):
        """Test response quality enhancement"""
        response_data = {
            'response_text': 'I found some vehicles for you.',
            'vehicles': [
                {'vehicle': {'make': 'Toyota', 'model': 'Camry'}}
            ]
        }
        
        enhanced_data = self.validator.enhance_response_quality(response_data, "John")
        
        assert enhanced_data['response_text'].startswith("Hi John!")
        assert "test drive" in enhanced_data['response_text']
        assert "vehicles that match your criteria" in enhanced_data['response_text']
    
    def test_quality_monitor(self):
        """Test quality monitoring"""
        response_data = {
            'response_text': 'Good response',
            'vehicles_found': 2,
            'response_metadata': {'generated_at': datetime.now().isoformat()}
        }
        
        validation_results = {
            'is_valid': True,
            'quality_score': 0.8,
            'issues': []
        }
        
        self.quality_monitor.record_response(response_data, validation_results)
        
        report = self.quality_monitor.get_performance_report()
        assert report['total_responses'] == 1
        assert report['high_quality_responses'] == 1
        assert report['average_quality_score'] == 0.8


class TestIntegration:
    """Integration tests for complete AI Response Generator"""
    
    @patch('backend.rag_enhanced.VehicleRetriever')
    def test_complete_response_generation_flow(self, mock_retriever_class):
        """Test complete response generation flow"""
        # Mock the retriever
        mock_retriever = Mock()
        mock_retriever.search_vehicles.return_value = [
            {
                'vehicle': {
                    'year': '2022',
                    'make': 'Toyota',
                    'model': 'Camry',
                    'price': 25000,
                    'features': 'Leather seats',
                    'description': 'Excellent condition'
                },
                'similarity_score': 0.85
            }
        ]
        mock_retriever_class.return_value = mock_retriever
        
        # Create enhanced service
        enhanced_service = EnhancedRAGService(mock_retriever)
        
        # Create test conversations
        conversations = [
            Conversation(
                lead_id=1,
                message="I'm looking for a sedan under $30,000 for a test drive",
                sender="customer",
                created_at=datetime.now()
            )
        ]
        
        # Mock the search_vehicles_with_context method
        enhanced_service.search_vehicles_with_context = Mock(return_value=[
            {
                'vehicle': {
                    'year': '2022',
                    'make': 'Toyota',
                    'model': 'Camry',
                    'price': 25000,
                    'features': 'Leather seats',
                    'description': 'Excellent condition'
                },
                'similarity_score': 0.85
            }
        ])
        
        # Generate response
        response = enhanced_service.generate_enhanced_response(
            "I'm looking for a sedan under $30,000 for a test drive",
            enhanced_service.search_vehicles_with_context("sedan", conversations),
            conversations,
            "John Doe"
        )
        
        # Validate response
        assert 'response_text' in response
        assert 'quality_metrics' in response
        assert 'follow_up_suggestions' in response
        assert 'context_analysis' in response
        
        # Validate response content
        response_text = response['response_text']
        assert "Hi John Doe!" in response_text
        assert "Toyota Camry" in response_text
        assert "test drive" in response_text.lower()
        
        # Validate quality metrics
        quality_metrics = response['quality_metrics']
        assert 'relevance_score' in quality_metrics
        assert 'completeness_score' in quality_metrics
        assert 'personalization_score' in quality_metrics
        assert 'actionability_score' in quality_metrics


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 