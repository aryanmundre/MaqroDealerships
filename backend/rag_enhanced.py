"""
Enhanced RAG Integration for Maqro Dealership API

This module provides advanced RAG capabilities including:
- Multi-query search strategies
- Dynamic response generation
- Context-aware vehicle matching
- Response quality scoring
"""

from typing import List, Dict, Any, Optional, Tuple
from maqro_rag import VehicleRetriever
from backend.ai_services import analyze_conversation_context
from backend.models import Conversation
import logging

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """Enhanced RAG service with advanced vehicle matching and response generation"""
    
    def __init__(self, retriever: VehicleRetriever):
        self.retriever = retriever
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Load response templates for different scenarios"""
        return {
            'test_drive': {
                'greeting': "Great! I'd be happy to help you schedule a test drive.",
                'vehicle_format': "{year} {make} {model} - {price}",
                'closing': "I can schedule a test drive for any of these vehicles. What's your preferred date and time?"
            },
            'pricing': {
                'greeting': "Here are the pricing details for vehicles that match your criteria:",
                'vehicle_format': "{year} {make} {model}\n   Price: {price}",
                'closing': "These prices are current and include all standard features."
            },
            'availability': {
                'greeting': "Great news! I found {count} vehicles that are currently available:",
                'vehicle_format': "{year} {make} {model} - {price} ✅ In Stock",
                'closing': "All these vehicles are ready for immediate purchase or test drive."
            },
            'financing': {
                'greeting': "I'd be happy to help you with financing options!",
                'vehicle_format': "{year} {make} {model} - {price}",
                'closing': "We offer competitive financing rates and flexible payment plans."
            },
            'general': {
                'greeting': "I found {count} vehicles that match your interests:",
                'vehicle_format': "{year} {make} {model}\n   Price: {price}\n   Features: {features}",
                'closing': "These vehicles are currently available. Would you like to schedule a test drive?"
            }
        }
    
    def search_vehicles_with_context(
        self, 
        query: str, 
        conversations: List[Conversation],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Enhanced vehicle search using conversation context
        
        Args:
            query: Current customer query
            conversations: Full conversation history
            top_k: Number of vehicles to retrieve
            
        Returns:
            List of matching vehicles with enhanced context
        """
        # Analyze conversation context
        context_analysis = analyze_conversation_context(conversations)
        
        # Generate multiple search queries based on context
        search_queries = self._generate_search_queries(query, context_analysis)
        
        # Perform multi-query search
        all_results = []
        for search_query in search_queries:
            try:
                results = self.retriever.search_vehicles(search_query, top_k=top_k)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Search failed for query '{search_query}': {e}")
        
        # Deduplicate and rank results
        unique_results = self._deduplicate_results(all_results)
        
        # Apply context-based filtering
        filtered_results = self._apply_context_filters(unique_results, context_analysis)
        
        # Re-rank based on context relevance
        ranked_results = self._rerank_by_context(filtered_results, context_analysis)
        
        return ranked_results[:top_k]
    
    def _generate_search_queries(self, query: str, context_analysis: Dict[str, Any]) -> List[str]:
        """Generate multiple search queries based on context"""
        queries = [query]  # Start with original query
        
        # Add queries based on detected preferences
        preferences = context_analysis.get('preferences', {})
        
        # Vehicle type preference
        vehicle_type = context_analysis.get('vehicle_type')
        if vehicle_type:
            queries.append(f"{vehicle_type} {query}")
        
        # Budget-based queries
        budget_range = context_analysis.get('budget_range')
        if budget_range:
            min_price, max_price = budget_range
            queries.append(f"{query} under ${max_price:,}")
            queries.append(f"{query} ${min_price:,}-${max_price:,}")
        
        # Feature-based queries
        if 'features' in preferences:
            for feature in preferences['features']:
                queries.append(f"{query} {feature}")
        
        # Intent-based queries
        intent = context_analysis.get('intent', 'general_inquiry')
        if intent == 'test_drive':
            queries.append(f"{query} available for test drive")
        elif intent == 'pricing':
            queries.append(f"{query} price")
        elif intent == 'availability':
            queries.append(f"{query} in stock")
        
        return list(set(queries))  # Remove duplicates
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate vehicles from results"""
        seen_vehicles = set()
        unique_results = []
        
        for result in results:
            vehicle = result['vehicle']
            vehicle_key = f"{vehicle.get('year')}-{vehicle.get('make')}-{vehicle.get('model')}-{vehicle.get('price')}"
            
            if vehicle_key not in seen_vehicles:
                seen_vehicles.add(vehicle_key)
                unique_results.append(result)
        
        return unique_results
    
    def _apply_context_filters(self, results: List[Dict[str, Any]], context_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply context-based filters to results"""
        filtered_results = []
        
        budget_range = context_analysis.get('budget_range')
        vehicle_type = context_analysis.get('vehicle_type')
        preferences = context_analysis.get('preferences', {})
        
        for result in results:
            vehicle = result['vehicle']
            should_include = True
            
            # Budget filter
            if budget_range:
                min_price, max_price = budget_range
                vehicle_price = vehicle.get('price')
                if vehicle_price and (vehicle_price < min_price or vehicle_price > max_price):
                    should_include = False
            
            # Vehicle type filter - be more lenient
            if vehicle_type and should_include:
                vehicle_make_model = f"{vehicle.get('make', '').lower()} {vehicle.get('model', '').lower()}"
                # Don't filter out if vehicle type doesn't match exactly
                # Just lower the score slightly
                if vehicle_type not in vehicle_make_model:
                    result['similarity_score'] *= 0.9
            
            # Feature preferences filter
            if preferences.get('features') and should_include:
                vehicle_features = vehicle.get('features', '').lower()
                preferred_features = [f.lower() for f in preferences['features']]
                if not any(feature in vehicle_features for feature in preferred_features):
                    # Don't exclude, but lower the score
                    result['similarity_score'] *= 0.8
            
            if should_include:
                filtered_results.append(result)
        
        return filtered_results
    
    def _rerank_by_context(self, results: List[Dict[str, Any]], context_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Re-rank results based on context relevance"""
        for result in results:
            base_score = result['similarity_score']
            context_boost = 1.0
            
            # Boost based on intent alignment
            intent = context_analysis.get('intent', 'general_inquiry')
            vehicle = result['vehicle']
            
            if intent == 'test_drive':
                # Prefer vehicles that are likely available for test drive
                if vehicle.get('price') and vehicle.get('price') < 50000:
                    context_boost *= 1.2
            
            elif intent == 'pricing':
                # Prefer vehicles with clear pricing
                if vehicle.get('price'):
                    context_boost *= 1.1
            
            elif intent == 'availability':
                # Prefer vehicles that are likely in stock
                if vehicle.get('price') and vehicle.get('price') < 100000:
                    context_boost *= 1.15
            
            # Boost based on urgency
            urgency = context_analysis.get('urgency', 'medium')
            if urgency == 'high':
                context_boost *= 1.1
            
            # Apply context boost
            result['similarity_score'] = min(1.0, base_score * context_boost)
        
        # Sort by updated scores
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results
    
    def generate_enhanced_response(
        self,
        query: str,
        vehicles: List[Dict[str, Any]],
        conversations: List[Conversation],
        lead_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced AI response with quality scoring
        
        Args:
            query: Customer query
            vehicles: Matching vehicles
            conversations: Conversation history
            lead_name: Customer name
            
        Returns:
            Dictionary containing response and metadata
        """
        # Analyze context
        context_analysis = analyze_conversation_context(conversations)
        
        # Generate response text
        response_text = self._generate_response_text(query, vehicles, context_analysis, lead_name)
        
        # Calculate response quality metrics
        quality_metrics = self._calculate_response_quality(response_text, vehicles, context_analysis)
        
        # Generate follow-up suggestions
        follow_ups = self._generate_follow_up_suggestions(context_analysis, vehicles)
        
        return {
            'response_text': response_text,
            'quality_metrics': quality_metrics,
            'follow_up_suggestions': follow_ups,
            'context_analysis': context_analysis,
            'vehicles_found': len(vehicles),
            'query': query
        }
    
    def _generate_response_text(
        self,
        query: str,
        vehicles: List[Dict[str, Any]],
        context_analysis: Dict[str, Any],
        lead_name: str
    ) -> str:
        """Generate response text using templates and context"""
        if not vehicles:
            return self._generate_no_match_response(query, lead_name, context_analysis)
        
        intent = context_analysis.get('intent', 'general_inquiry')
        template = self.response_templates.get(intent, self.response_templates['general'])
        
        greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
        
        # Build response parts
        response_parts = [greeting + template['greeting']]
        
        # Add vehicle information
        for i, result in enumerate(vehicles, 1):
            vehicle = result['vehicle']
            score = result['similarity_score']
            
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            price = vehicle.get('price')
            features = vehicle.get('features', '')
            
            price_str = f"${price:,}" if price else "Price available upon request"
            
            if intent == 'general':
                vehicle_text = template['vehicle_format'].format(
                    year=year, make=make, model=model, price=price_str, features=features
                )
                vehicle_text += f"\n   Match Score: {score:.1%}"
            else:
                vehicle_text = template['vehicle_format'].format(
                    year=year, make=make, model=model, price=price_str
                )
            
            response_parts.append(f"{i}. **{vehicle_text}**\n")
        
        # Add closing
        response_parts.append(template['closing'])
        
        return "\n".join(response_parts)
    
    def _generate_no_match_response(self, query: str, lead_name: str, context_analysis: Dict[str, Any]) -> str:
        """Generate response when no vehicles match"""
        greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
        
        intent = context_analysis.get('intent', 'general_inquiry')
        
        if intent == 'test_drive':
            return (
                f"{greeting}I understand you're interested in test driving something like '{query}'. "
                "While I don't have exact matches available for test drive right now, "
                "I can help you find similar vehicles or schedule a test drive when we get them in. "
                "Would you like me to show you what we do have available?"
            )
        elif intent == 'pricing':
            return (
                f"{greeting}I understand you're asking about pricing for '{query}'. "
                "While I don't have exact matches in our current inventory, "
                "I can provide pricing estimates for similar vehicles or help you find options in your budget. "
                "What's your target price range?"
            )
        else:
            return (
                f"{greeting}Thank you for your inquiry about '{query}'. "
                "While I don't have exact matches in our current inventory, "
                "I'd be happy to help you find something similar or keep you updated "
                "when we get vehicles that match your criteria. "
                "Could you tell me more about your specific needs and budget?"
            )
    
    def _calculate_response_quality(
        self,
        response_text: str,
        vehicles: List[Dict[str, Any]],
        context_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate response quality metrics"""
        metrics = {
            'relevance_score': 0.0,
            'completeness_score': 0.0,
            'personalization_score': 0.0,
            'actionability_score': 0.0
        }
        
        # Relevance score based on vehicle match quality
        if vehicles:
            avg_similarity = sum(v['similarity_score'] for v in vehicles) / len(vehicles)
            metrics['relevance_score'] = avg_similarity
        
        # Completeness score based on response length and vehicle count
        response_length = len(response_text)
        if response_length > 200 and len(vehicles) > 0:
            metrics['completeness_score'] = min(1.0, response_length / 500)
        
        # Personalization score based on context usage
        context_usage = 0
        if context_analysis.get('intent') != 'general_inquiry':
            context_usage += 0.3
        if context_analysis.get('preferences'):
            context_usage += 0.3
        if context_analysis.get('budget_range'):
            context_usage += 0.2
        if context_analysis.get('vehicle_type'):
            context_usage += 0.2
        metrics['personalization_score'] = min(1.0, context_usage)
        
        # Actionability score based on call-to-action presence
        action_words = ['schedule', 'test drive', 'contact', 'call', 'visit', 'financing', 'payment']
        action_count = sum(1 for word in action_words if word.lower() in response_text.lower())
        metrics['actionability_score'] = min(1.0, action_count / 3)
        
        return metrics
    
    def _generate_follow_up_suggestions(
        self,
        context_analysis: Dict[str, Any],
        vehicles: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up suggestions based on context"""
        suggestions = []
        
        intent = context_analysis.get('intent', 'general_inquiry')
        
        if intent == 'test_drive':
            suggestions.extend([
                "Schedule a test drive",
                "Get more vehicle details",
                "Discuss financing options"
            ])
        elif intent == 'pricing':
            suggestions.extend([
                "Get financing estimate",
                "Schedule a viewing",
                "Compare with similar vehicles"
            ])
        elif intent == 'availability':
            suggestions.extend([
                "Schedule immediate viewing",
                "Hold vehicle for you",
                "Get delivery options"
            ])
        elif intent == 'financing':
            suggestions.extend([
                "Get pre-approval",
                "Calculate monthly payments",
                "Discuss trade-in value"
            ])
        else:
            suggestions.extend([
                "Schedule a test drive",
                "Get more information",
                "Discuss pricing and financing"
            ])
        
        # Add context-specific suggestions
        if context_analysis.get('urgency') == 'high':
            suggestions.append("Schedule immediate appointment")
        
        if context_analysis.get('budget_range'):
            suggestions.append("Find vehicles in your budget")
        
        return suggestions[:5]  # Limit to 5 suggestions 