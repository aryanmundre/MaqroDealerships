"""
Response Validation and Quality Assurance

This module provides validation and quality assurance for AI responses,
including content filtering, response quality scoring, and fallback responses.
"""

from typing import Dict, Any, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates and ensures quality of AI responses"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_length': 50,
            'max_length': 1000,
            'min_vehicles': 1,
            'max_vehicles': 5,
            'min_relevance_score': 0.3,
            'min_completeness_score': 0.4
        }
        
        self.inappropriate_content_patterns = [
            r'\b(offensive|inappropriate|unprofessional)\b',
            r'\b(price\s+too\s+high|expensive|overpriced)\b',
            r'\b(not\s+interested|don\'t\s+want|hate)\b'
        ]
        
        self.fallback_responses = {
            'no_vehicles': "I'd be happy to help you find the perfect vehicle! Could you tell me more about what you're looking for?",
            'low_quality': "Thank you for your inquiry. Let me help you find vehicles that match your needs. What type of car are you interested in?",
            'error': "I'm here to help you find the perfect vehicle. What are you looking for today?",
            'generic': "Welcome to Maqro Dealerships! I can help you find vehicles, schedule test drives, and discuss financing options. What can I assist you with?"
        }
    
    def validate_response(
        self, 
        response_data: Dict[str, Any], 
        original_query: str
    ) -> Tuple[bool, Dict[str, Any], str | None]:
        """
        Validate AI response and return validation results
        
        Args:
            response_data: Response data from AI service
            original_query: Original customer query
            
        Returns:
            Tuple of (is_valid, validation_details, fallback_response)
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'quality_score': 0.0,
            'recommendations': []
        }
        
        # Extract response components
        response_text = response_data.get('response_text', '')
        vehicles = response_data.get('vehicles', [])
        quality_metrics = response_data.get('quality_metrics', {})
        
        # Check response length
        if len(response_text) < self.quality_thresholds['min_length']:
            validation_results['is_valid'] = False
            validation_results['issues'].append('Response too short')
            validation_results['recommendations'].append('Increase response detail')
        
        if len(response_text) > self.quality_thresholds['max_length']:
            validation_results['issues'].append('Response too long')
            validation_results['recommendations'].append('Condense response')
        
        # Check vehicle count
        if len(vehicles) < self.quality_thresholds['min_vehicles']:
            validation_results['issues'].append('Too few vehicles found')
            validation_results['recommendations'].append('Expand search criteria')
        
        if len(vehicles) > self.quality_thresholds['max_vehicles']:
            validation_results['issues'].append('Too many vehicles found')
            validation_results['recommendations'].append('Narrow search criteria')
        
        # Check content appropriateness
        if self._contains_inappropriate_content(response_text):
            validation_results['is_valid'] = False
            validation_results['issues'].append('Inappropriate content detected')
            validation_results['recommendations'].append('Use professional language')
        
        # Check quality metrics
        if quality_metrics:
            relevance_score = quality_metrics.get('relevance_score', 0)
            completeness_score = quality_metrics.get('completeness_score', 0)
            
            if relevance_score < self.quality_thresholds['min_relevance_score']:
                validation_results['issues'].append('Low relevance score')
                validation_results['recommendations'].append('Improve vehicle matching')
            
            if completeness_score < self.quality_thresholds['min_completeness_score']:
                validation_results['issues'].append('Low completeness score')
                validation_results['recommendations'].append('Add more details')
            
            # Calculate overall quality score
            validation_results['quality_score'] = (
                relevance_score + completeness_score + 
                quality_metrics.get('personalization_score', 0) + 
                quality_metrics.get('actionability_score', 0)
            ) / 4
        
        # Determine if fallback is needed
        fallback_response = None
        if not validation_results['is_valid'] or validation_results['quality_score'] < 0.5:
            fallback_response = self._generate_fallback_response(original_query, validation_results)
        
        return validation_results['is_valid'], validation_results, fallback_response
    
    def _contains_inappropriate_content(self, text: str) -> bool:
        """Check if response contains inappropriate content"""
        text_lower = text.lower()
        
        for pattern in self.inappropriate_content_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _generate_fallback_response(self, query: str, validation_results: Dict[str, Any]) -> str:
        """Generate appropriate fallback response"""
        issues = validation_results.get('issues', [])
        
        if 'Too few vehicles found' in issues or 'no vehicles' in str(issues).lower():
            return self.fallback_responses['no_vehicles']
        elif 'Inappropriate content detected' in issues:
            return self.fallback_responses['low_quality']
        elif 'Response too short' in issues or 'Low relevance score' in issues:
            return self.fallback_responses['low_quality']
        else:
            return self.fallback_responses['generic']
    
    def enhance_response_quality(
        self, 
        response_data: Dict[str, Any], 
        customer_name: str | None = None
    ) -> Dict[str, Any]:
        """
        Enhance response quality by adding missing elements
        
        Args:
            response_data: Original response data
            customer_name: Customer name for personalization
            
        Returns:
            Enhanced response data
        """
        enhanced_data = response_data.copy()
        response_text = enhanced_data.get('response_text', '')
        
        # Add personalization if missing
        if customer_name and not response_text.startswith(f"Hi {customer_name}"):
            enhanced_data['response_text'] = f"Hi {customer_name}! {response_text}"
        
        # Get the updated response text after personalization
        response_text = enhanced_data.get('response_text', '')
        
        # Add call-to-action if missing
        if not self._has_call_to_action(response_text):
            enhanced_data['response_text'] += "\n\nWould you like to schedule a test drive or get more information?"
        
        # Add vehicle count if missing
        vehicles = enhanced_data.get('vehicles', [])
        if vehicles and 'vehicles that match' not in response_text.lower():
            # Find a good place to insert vehicle count
            if "I found" in response_text:
                enhanced_data['response_text'] = response_text.replace(
                    "I found", f"I found {len(vehicles)} vehicles that match your criteria"
                )
            else:
                # Add vehicle count at the beginning if not already present
                enhanced_data['response_text'] = f"I found {len(vehicles)} vehicles that match your criteria. {response_text}"
        
        return enhanced_data
    
    def _has_call_to_action(self, text: str) -> bool:
        """Check if response has a call-to-action"""
        cta_patterns = [
            r'schedule.*test drive',
            r'contact.*us',
            r'call.*us',
            r'visit.*us',
            r'would you like',
            r'can I help',
            r'let me know'
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in cta_patterns)
    
    def get_response_insights(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights about the response for analytics
        
        Args:
            response_data: Response data
            
        Returns:
            Dictionary with response insights
        """
        response_text = response_data.get('response_text', '')
        vehicles = response_data.get('vehicles', [])
        quality_metrics = response_data.get('quality_metrics', {})
        
        insights = {
            'response_length': len(response_text),
            'vehicle_count': len(vehicles),
            'has_call_to_action': self._has_call_to_action(response_text),
            'has_personalization': 'Hi ' in response_text,
            'has_pricing_info': any('$' in str(v.get('vehicle', {}).get('price', '')) for v in vehicles),
            'quality_score': sum(quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0,
            'response_type': self._classify_response_type(response_text),
            'customer_intent': self._extract_customer_intent(response_text)
        }
        
        return insights
    
    def _classify_response_type(self, text: str) -> str:
        """Classify the type of response"""
        text_lower = text.lower()
        
        if 'test drive' in text_lower:
            return 'test_drive_focused'
        elif 'price' in text_lower and 'financing' in text_lower:
            return 'pricing_financing'
        elif 'available' in text_lower or 'in stock' in text_lower:
            return 'availability_focused'
        elif 'welcome' in text_lower:
            return 'welcome'
        else:
            return 'general_inquiry'
    
    def _extract_customer_intent(self, text: str) -> str:
        """Extract customer intent from response context"""
        text_lower = text.lower()
        
        if 'looking for' in text_lower or 'interested in' in text_lower:
            return 'vehicle_search'
        elif 'test drive' in text_lower:
            return 'test_drive_request'
        elif 'price' in text_lower or 'cost' in text_lower:
            return 'pricing_inquiry'
        elif 'available' in text_lower:
            return 'availability_check'
        else:
            return 'general_inquiry'


class ResponseQualityMonitor:
    """Monitors and tracks response quality over time"""
    
    def __init__(self):
        self.quality_history = []
        self.performance_metrics = {
            'total_responses': 0,
            'high_quality_responses': 0,
            'fallback_responses': 0,
            'average_quality_score': 0.0
        }
    
    def record_response(self, response_data: Dict[str, Any], validation_results: Dict[str, Any]):
        """Record response quality metrics"""
        quality_score = validation_results.get('quality_score', 0.0)
        
        self.quality_history.append({
            'timestamp': response_data.get('response_metadata', {}).get('generated_at'),
            'quality_score': quality_score,
            'is_valid': validation_results.get('is_valid', False),
            'issues': validation_results.get('issues', []),
            'vehicles_found': response_data.get('vehicles_found', 0)
        })
        
        # Update performance metrics
        self.performance_metrics['total_responses'] += 1
        
        if quality_score >= 0.7:
            self.performance_metrics['high_quality_responses'] += 1
        
        if not validation_results.get('is_valid', True):
            self.performance_metrics['fallback_responses'] += 1
        
        # Update average quality score
        total_score = sum(h['quality_score'] for h in self.quality_history)
        self.performance_metrics['average_quality_score'] = total_score / len(self.quality_history)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report"""
        if not self.quality_history:
            return self.performance_metrics
        
        recent_history = self.quality_history[-100:]  # Last 100 responses
        
        return {
            **self.performance_metrics,
            'recent_quality_trend': self._calculate_trend(recent_history),
            'common_issues': self._get_common_issues(),
            'response_volume': len(recent_history)
        }
    
    def _calculate_trend(self, history: list[Dict[str, Any]]) -> str:
        """Calculate quality trend"""
        if len(history) < 2:
            return 'insufficient_data'
        
        recent_scores = [h['quality_score'] for h in history[-10:]]
        earlier_scores = [h['quality_score'] for h in history[-20:-10]]
        
        if not earlier_scores:
            return 'stable'
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        earlier_avg = sum(earlier_scores) / len(earlier_scores)
        
        if recent_avg > earlier_avg + 0.1:
            return 'improving'
        elif recent_avg < earlier_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _get_common_issues(self) -> list[str]:
        """Get most common quality issues"""
        all_issues = []
        for record in self.quality_history:
            all_issues.extend(record.get('issues', []))
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Return top 3 most common issues
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues[:3]]
