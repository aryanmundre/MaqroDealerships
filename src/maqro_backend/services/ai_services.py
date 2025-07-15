"""
AI Services for Maqro Dealership API

This module contains all AI-related helper functions for:
- Processing conversation history
- Generating AI responses using RAG system  
- Formatting responses for customers
"""

import openai
from typing import List, Dict, Any
from maqro_rag import VehicleRetriever
from maqro_backend.db.models.conversation import Conversation


def get_last_customer_message(conversations: list[Conversation]) -> str:
    """
    Extract the most recent customer message from conversation history
    
    Args:
        conversations: List of conversations in chronological order
        
    Returns:
        The last customer message, or None if no customer message found
    """
    for conversation in reversed(conversations):
        if conversation.sender == "customer":
            return conversation.message
    return None


def format_conversation_context(conversations: list[Conversation], lead_name: str = None) -> str:
    """
    Format entire conversation history into a context string for AI processing
    
    Args:
        conversations: List of conversations in chronological order
        lead_name: Optional lead name for context
        
    Returns:
        Formatted conversation context string
    """
    context_parts = []
    
    if lead_name:
        context_parts.append(f"Customer: {lead_name}\n")
    
    for conv in conversations:
        role = "Customer" if conv.sender == "customer" else "Agent"
        context_parts.append(f"{role}: {conv.message}")
    
    return "\n".join(context_parts)


def generate_ai_response_text(query: str, vehicles: list[dict[str, Any]], customer_name: str = None) -> str:
    """
    Generate AI response text from RAG search results
    
    Args:
        query: Customer's query/message
        vehicles: List of matching vehicles from RAG search
        customer_name: Optional customer name for personalization
        
    Returns:
        Formatted AI response text
    """
    if not vehicles:
        return _generate_no_match_response(query, customer_name)
    
    return _generate_match_response(query, vehicles, customer_name)


def _generate_no_match_response(query: str, customer_name: str = None) -> str:
    """Generate response when no vehicles match the query"""
    greeting = f"Hi {customer_name}! " if customer_name else "Hello! "
    
    return (
        f"{greeting}Thank you for your inquiry about '{query}'. "
        "While I don't have exact matches in our current inventory, "
        "I'd be happy to help you find something similar or keep you updated "
        "when we get vehicles that match your criteria. "
        "Could you tell me more about your specific needs and budget?"
    )


def _generate_match_response(query: str, vehicles: list[dict[str, Any]], customer_name: str = None) -> str:
    """Generate response when vehicles match the query"""
    greeting = f"Hi {customer_name}! " if customer_name else "Hello! "
    
    response_parts = [
        f"{greeting}Based on your interest in '{query}', I found {len(vehicles)} vehicle(s) that might be perfect for you:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        score = result['similarity_score']
        
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        features = vehicle.get('features', '')
        description = vehicle.get('description', '')
        
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}**\n"
            f"   Price: {price_str}\n"
            f"   Features: {features}\n"
            f"   {description}\n"
            f"   Match Score: {score:.1%}\n"
        )
    
    response_parts.append(
        "\nWould you like to schedule a test drive or get more information about any of these vehicles? "
        "I can also help you find other options that match your preferences!"
    )
    
    return "\n".join(response_parts)


def generate_contextual_ai_response(
    conversations: list[Conversation], 
    vehicles: list[dict[str, Any]], 
    lead_name: str = None
) -> str:
    """
    Generate AI response considering full conversation context
    
    This can be used for more sophisticated responses that consider
    the entire conversation history, not just the last message.
    
    Args:
        conversations: Full conversation history
        vehicles: Matching vehicles from RAG search
        lead_name: Customer name for personalization
        
    Returns:
        Contextual AI response
    """
    # For now, use the last customer message, but this function
    # can be enhanced to consider full conversation context
    last_message = get_last_customer_message(conversations)
    
    if not last_message:
        return "I'd be happy to help you find the perfect vehicle! What are you looking for?"
    
    return generate_ai_response_text(last_message, vehicles, lead_name) 