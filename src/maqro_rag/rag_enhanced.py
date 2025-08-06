"""
Enhanced RAG service for intelligent vehicle search and response generation.
"""

import os
import json
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .config import Config
from .retrieval import VehicleRetriever


@dataclass
class ConversationContext:
    """Context information extracted from conversation history."""
    
    intent: str = "general_inquiry"
    preferences: Dict[str, Any] = None
    urgency: str = "medium"
    budget_range: Optional[Tuple[int, int]] = None
    vehicle_type: Optional[str] = None
    conversation_length: int = 0
    
    def __post_init__(self):
        """Initialize default values."""
        if self.preferences is None:
            self.preferences = {}


@dataclass
class ResponseQuality:
    """Quality metrics for generated responses."""
    
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    personalization_score: float = 0.0
    actionability_score: float = 0.0
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        return sum([self.relevance_score, self.completeness_score, 
                   self.personalization_score, self.actionability_score]) / 4


class ResponseTemplate:
    """Template for generating structured responses."""
    
    def __init__(self):
        """Initialize response templates."""
        self.templates = {
            'general': {
                'greeting': "I found {count} vehicles that match your interests:",
                'vehicle_format': "{year} {make} {model}, {price}, {features}",
                'closing': "These vehicles are currently available. Would you like to schedule a test drive?"
            },
            'test_drive': {
                'greeting': "I found {count} vehicles perfect for a test drive:",
                'vehicle_format': "{year} {make} {model} - {price}",
                'closing': "Would you like to schedule a test drive for any of these vehicles?"
            },
            'pricing': {
                'greeting': "Here are {count} vehicles in your price range:",
                'vehicle_format': "{year} {make} {model} - {price}",
                'closing': "I can help you with financing options and pricing details."
            },
            'availability': {
                'greeting': "I found {count} vehicles currently available:",
                'vehicle_format': "{year} {make} {model} - {price}",
                'closing': "These vehicles are ready for immediate viewing or purchase."
            }
        }
    
    def get_template(self, intent: str) -> Dict[str, str]:
        """Get template for specific intent."""
        return self.templates.get(intent, self.templates['general'])
    
    def format_vehicle(self, vehicle: Dict[str, Any], template: Dict[str, str], score: float) -> str:
        """Format vehicle information using template."""
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price', 0)
        features = vehicle.get('features', '')
        description = vehicle.get('description', '')
        
        price_str = f"${price:,}" if price else "Price available upon request"
        
        # Use template format
        if 'features' in template['vehicle_format']:
            vehicle_text = template['vehicle_format'].format(
                year=year, make=make, model=model, price=price_str, features=features
            )
        else:
            vehicle_text = f"{year} {make} {model} - {price_str}"
        
        vehicle_text += f"\n   Match Score: {score:.1%}"
        
        return vehicle_text


class EnhancedRAGService:
    """Enhanced RAG service for intelligent vehicle search and response generation."""
    
    def __init__(self, retriever: VehicleRetriever, analyze_conversation_context_func: Callable):
        """Initialize enhanced RAG service."""
        self.retriever = retriever
        self.analyze_conversation_context = analyze_conversation_context_func
        self.response_template = ResponseTemplate()
        
        logger.info("Initialized EnhancedRAGService")
    
    def search_vehicles_with_context(
        self, 
        query: str, 
        conversations: List[Dict], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search vehicles with conversation context."""
        try:
            # Analyze conversation context
            context_analysis = self.analyze_conversation_context(conversations)
            context = ConversationContext(**context_analysis)
            
            # Generate search queries based on context
            search_queries = self._generate_search_queries(query, context)
            
            # Perform searches
            all_results = []
            for search_query in search_queries:
                try:
                    results = self.retriever.search_vehicles(search_query, top_k)
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Error searching with query '{search_query}': {e}")
                    continue
            
            # Deduplicate and filter results
            deduplicated_results = self._deduplicate_results(all_results)
            filtered_results = self._apply_context_filters(deduplicated_results, context)
            reranked_results = self._rerank_by_context(filtered_results, context)
            
            return reranked_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in search_vehicles_with_context: {e}")
            raise
    
    def _generate_search_queries(self, query: str, context: ConversationContext) -> List[str]:
        """Generate multiple search queries based on context."""
        queries = [query]
        
        # Add context-specific queries
        if context.budget_range:
            min_price, max_price = context.budget_range
            queries.append(f"{query} under ${max_price:,}")
            queries.append(f"{query} ${min_price:,}-${max_price:,}")
        
        if context.vehicle_type:
            queries.append(f"{context.vehicle_type} {query}")
        
        # Add urgency-based queries
        if context.urgency == "high":
            queries.append(f"{query} available immediately")
        
        # Add preference-based queries
        if context.preferences:
            for key, value in context.preferences.items():
                if isinstance(value, str):
                    queries.append(f"{query} {value}")
        
        return list(set(queries))  # Remove duplicates
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate vehicles from results."""
        seen_vehicles = set()
        unique_results = []
        
        for result in results:
            vehicle = result['vehicle']
            vehicle_key = f"{vehicle.get('year')}-{vehicle.get('make')}-{vehicle.get('model')}"
            
            if vehicle_key not in seen_vehicles:
                seen_vehicles.add(vehicle_key)
                unique_results.append(result)
        
        return unique_results
    
    def _apply_context_filters(self, results: List[Dict[str, Any]], context: ConversationContext) -> List[Dict[str, Any]]:
        """Apply context-based filters to results."""
        filtered_results = []
        
        for result in results:
            vehicle = result['vehicle']
            include = True
            
            # Budget filter
            if context.budget_range and vehicle.get('price'):
                min_price, max_price = context.budget_range
                if not (min_price <= vehicle['price'] <= max_price):
                    include = False
            
            # Vehicle type filter
            if context.vehicle_type and context.vehicle_type.lower() not in vehicle.get('description', '').lower():
                include = False
            
            if include:
                filtered_results.append(result)
        
        return filtered_results
    
    def _rerank_by_context(self, results: List[Dict[str, Any]], context: ConversationContext) -> List[Dict[str, Any]]:
        """Rerank results based on context preferences."""
        if not context.preferences:
            return results
        
        # Simple reranking based on preference matches
        for result in results:
            vehicle = result['vehicle']
            bonus_score = 0.0
            
            # Check for preference matches
            for key, value in context.preferences.items():
                if key in vehicle and vehicle[key] == value:
                    bonus_score += 0.1
            
            # Apply bonus to similarity score
            result['similarity_score'] = min(1.0, result['similarity_score'] + bonus_score)
        
        # Sort by updated scores
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    
    def generate_enhanced_response(
        self,
        query: str,
        vehicles: List[Dict[str, Any]],
        conversations: List[Dict],
        lead_name: str = None
    ) -> Dict[str, Any]:
        """Generate enhanced AI response with quality scoring."""
        try:
            # Analyze context
            context_analysis = self.analyze_conversation_context(conversations)
            context = ConversationContext(**context_analysis)
            
            # Generate response text
            response_text = self._generate_response_text(query, vehicles, context, lead_name)
            
            # Calculate response quality metrics
            quality_metrics = self._calculate_response_quality(response_text, vehicles, context)
            
            # Generate follow-up suggestions
            follow_ups = self._generate_follow_up_suggestions(context, vehicles)
            
            return {
                'response_text': response_text,
                'quality_metrics': quality_metrics.__dict__,
                'follow_up_suggestions': follow_ups,
                'context_analysis': context_analysis,
                'vehicles_found': len(vehicles),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            raise
    
    def _generate_response_text(
        self,
        query: str,
        vehicles: List[Dict[str, Any]],
        context: ConversationContext,
        lead_name: str
    ) -> str:
        """Generate response text using templates and context."""
        if not vehicles:
            return self._generate_no_match_response(query, lead_name, context)
        
        template = self.response_template.get_template(context.intent)
        greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
        
        # Build response parts
        response_parts = [greeting + template['greeting'].format(count=len(vehicles))]
        
        # Add vehicle information
        for i, result in enumerate(vehicles, 1):
            vehicle = result['vehicle']
            score = result['similarity_score']
            
            vehicle_text = self.response_template.format_vehicle(vehicle, template, score)
            response_parts.append(f"{i}. **{vehicle_text}**\n")
        
        # Add closing
        response_parts.append(template['closing'])
        
        return "\n".join(response_parts)
    
    def _generate_no_match_response(self, query: str, lead_name: str, context: ConversationContext) -> str:
        """Generate response when no vehicles match."""
        greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
        
        if context.intent == 'test_drive':
            return (
                f"{greeting}I understand you're interested in test driving something like '{query}'. "
                "While I don't have exact matches available for test drive right now, "
                "I'd be happy to help you find something similar or keep you updated "
                "when we get vehicles that match your criteria. "
                "Could you tell me more about your specific needs and budget?"
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
        context: ConversationContext
    ) -> ResponseQuality:
        """Calculate response quality metrics."""
        quality = ResponseQuality()
        
        # Relevance score based on vehicle match quality
        if vehicles:
            avg_similarity = sum(v['similarity_score'] for v in vehicles) / len(vehicles)
            quality.relevance_score = avg_similarity
        
        # Completeness score based on response length and vehicle count
        response_length = len(response_text)
        if response_length > 200 and len(vehicles) > 0:
            quality.completeness_score = min(1.0, response_length / 500)
        
        # Personalization score based on context usage
        context_usage = 0
        if context.intent != 'general_inquiry':
            context_usage += 0.3
        if context.preferences:
            context_usage += 0.3
        if context.budget_range:
            context_usage += 0.2
        if context.vehicle_type:
            context_usage += 0.2
        quality.personalization_score = min(1.0, context_usage)
        
        # Actionability score based on call-to-action presence
        action_words = ['schedule', 'test drive', 'contact', 'call', 'visit', 'financing', 'payment']
        action_count = sum(1 for word in action_words if word.lower() in response_text.lower())
        quality.actionability_score = min(1.0, action_count / 3)
        
        return quality
    
    def _generate_follow_up_suggestions(
        self,
        context: ConversationContext,
        vehicles: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up suggestions based on context."""
        suggestions = []
        
        if context.intent == 'test_drive':
            suggestions.extend([
                "Schedule a test drive",
                "Get more vehicle details",
                "Discuss financing options"
            ])
        elif context.intent == 'pricing':
            suggestions.extend([
                "Get financing estimate",
                "Schedule a viewing",
                "Compare with similar vehicles"
            ])
        elif context.intent == 'availability':
            suggestions.extend([
                "Schedule immediate viewing",
                "Hold vehicle for you",
                "Get delivery options"
            ])
        elif context.intent == 'financing':
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
        if context.urgency == 'high':
            suggestions.append("Schedule immediate appointment")
        
        if context.budget_range:
            suggestions.append("Find vehicles in your budget")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        try:
            retriever_stats = self.retriever.get_index_stats()
            
            return {
                "retriever_stats": retriever_stats,
                "service_type": "EnhancedRAGService",
                "templates_available": list(self.response_template.templates.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {"error": str(e)} 