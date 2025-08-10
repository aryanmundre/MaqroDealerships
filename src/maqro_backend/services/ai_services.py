"""
AI Services for Maqro Dealership API

This module contains all AI-related helper functions for:
- Processing conversation history
- Generating AI responses using RAG system  
- Formatting responses for customers
"""

from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import re



async def get_all_conversation_history(lead_id: int, db: AsyncSession) -> list[Dict]:
    """
    Get complete conversation history for a lead (no limits)
    
    Returns conversations in chronological order (oldest first)
    """
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM messages WHERE lead_id = :lead_id ORDER BY created_at ASC"),
        {"lead_id": lead_id}
    )
    conversations = [dict(row._mapping) for row in result.fetchall()]
    return conversations

def get_last_customer_message(conversations: list[Dict]) -> str:
    """
    Extract the most recent customer message from conversation history
    
    Args:
        conversations: List of conversations in chronological order
        
    Returns:
        The last customer message, or None if no customer message found
    """
    for conversation in reversed(conversations):
        if conversation.get("sender") == "customer":
            return conversation.get("message")
    return None


def analyze_conversation_context(conversations: list[Dict]) -> Dict[str, Any]:
    """
    Analyze conversation context to understand customer intent and preferences
    
    Args:
        conversations: List of conversations in chronological order
        
    Returns:
        Dictionary containing analysis results
    """
    if not conversations:
        return {
            'intent': 'general_inquiry',
            'preferences': {},
            'urgency': 'low',
            'budget_range': None,
            'vehicle_type': None,
            'conversation_length': 0
        }
    
    # Extract customer messages
    customer_messages = [c.get("message", "").lower() for c in conversations if c.get("sender") == "customer"]
    
    # Analyze intent
    intent = _detect_intent(customer_messages)
    
    # Extract preferences
    preferences = _extract_preferences(customer_messages)
    
    # Detect urgency
    urgency = _detect_urgency(customer_messages)
    
    # Estimate budget range
    budget_range = _extract_budget_range(customer_messages)
    
    # Detect vehicle type preference
    vehicle_type = _detect_vehicle_type(customer_messages)
    
    return {
        'intent': intent,
        'preferences': preferences,
        'urgency': urgency,
        'budget_range': budget_range,
        'vehicle_type': vehicle_type,
        'conversation_length': len(customer_messages)
    }


def _detect_intent(messages: list[str]) -> str:
    """Detect customer intent from messages"""
    if not messages:
        return 'general_inquiry'
    
    last_message = messages[-1]
    
    # Intent keywords - order matters for priority
    intent_patterns = [
        ('test_drive', ['test drive', 'drive', 'test', 'schedule']),
        ('financing', ['finance', 'loan', 'credit', 'payment plan', 'financing']),
        ('pricing', ['price', 'cost', 'budget', 'afford', 'payment']),
        ('availability', ['available', 'in stock', 'have', 'stock']),
        ('features', ['feature', 'spec', 'specification', 'option']),
        ('trade_in', ['trade', 'trade-in', 'exchange', 'old car']),
        ('general_inquiry', ['help', 'looking', 'interested', 'information'])
    ]
    
    for intent, keywords in intent_patterns:
        if any(keyword in last_message for keyword in keywords):
            return intent
    
    return 'general_inquiry'


def _extract_preferences(messages: list[str]) -> Dict[str, Any]:
    """Extract customer preferences from messages"""
    preferences = {}
    
    # Common preference patterns
    preference_patterns = {
        'color': ['color', 'colour', 'red', 'blue', 'black', 'white', 'silver', 'gray'],
        'transmission': ['automatic', 'manual', 'transmission'],
        'fuel_type': ['gas', 'diesel', 'electric', 'hybrid', 'fuel'],
        'body_style': ['sedan', 'suv', 'truck', 'hatchback', 'coupe', 'convertible'],
        'features': ['leather', 'sunroof', 'navigation', 'backup camera', 'bluetooth']
    }
    
    # Check for body style in messages
    for message in messages:
        message_lower = message.lower()
        for body_style in ['sedan', 'suv', 'truck', 'hatchback', 'coupe', 'convertible']:
            if body_style in message_lower:
                if 'body_style' not in preferences:
                    preferences['body_style'] = []
                preferences['body_style'].append(body_style)
    
    for category, keywords in preference_patterns.items():
        found_preferences = []
        for message in messages:
            for keyword in keywords:
                if keyword in message:
                    found_preferences.append(keyword)
        if found_preferences:
            preferences[category] = list(set(found_preferences))
    
    # Add make/model preferences if found
    for message in messages:
        # Common car makes
        makes = ['toyota', 'honda', 'ford', 'chevrolet', 'bmw', 'mercedes', 'audi', 'lexus']
        for make in makes:
            if make in message.lower():
                if 'make' not in preferences:
                    preferences['make'] = []
                preferences['make'].append(make)
        
        # Common car models
        models = ['camry', 'accord', 'civic', 'corolla', 'cr-v', 'rav4', 'f-150', 'silverado']
        for model in models:
            if model in message.lower():
                if 'model' not in preferences:
                    preferences['model'] = []
                preferences['model'].append(model)
    
    return preferences


def _detect_urgency(messages: list[str]) -> str:
    """Detect urgency level from messages"""
    urgency_keywords = {
        'high': ['urgent', 'asap', 'quickly', 'immediately', 'today'],
        'medium': ['soon', 'this week', 'next week', 'interested'],
        'low': ['someday', 'future', 'maybe', 'thinking']
    }
    
    for urgency, keywords in urgency_keywords.items():
        for message in messages:
            if any(keyword in message for keyword in keywords):
                return urgency
    
    return 'medium'  # Default


def _extract_budget_range(messages: list[str]) -> Tuple[float, float] | None:
    """Extract budget range from messages"""
    for message in messages:
        # Look for price patterns like "$20,000-$30,000" or "20k to 30k"
        price_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*)\s*-\s*\$?(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,2})k\s*to\s*(\d{1,2})k',
            r'(\d{1,2})k\s*-\s*(\d{1,2})k'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, message)
            if matches:
                try:
                    min_price = float(matches[0][0].replace(',', ''))
                    max_price = float(matches[0][1].replace(',', ''))
                    return (min_price, max_price)
                except ValueError:
                    continue
    
    return None


def _detect_vehicle_type(messages: list[str]) -> str | None:
    """Detect preferred vehicle type from messages"""
    vehicle_types = {
        'sedan': ['sedan', 'car', 'passenger'],
        'suv': ['suv', 'crossover', 'sport utility'],
        'truck': ['truck', 'pickup', 'pick-up'],
        'hatchback': ['hatchback', 'hatch'],
        'coupe': ['coupe', 'sports car'],
        'convertible': ['convertible', 'convertible']
    }
    
    for vehicle_type, keywords in vehicle_types.items():
        for message in messages:
            if any(keyword in message for keyword in keywords):
                return vehicle_type
    
    return None


def format_conversation_context(conversations: list[Dict], lead_name: str | None = None) -> str:
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
        role = "Customer" if conv.get("sender") == "customer" else "Agent"
        message = conv.get("message", "")
        context_parts.append(f"{role}: {message}")
    
    return "\n".join(context_parts)


def generate_ai_response_text(query: str, vehicles: list[dict[str, Any]], customer_name: str | None = None) -> str:
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


def _generate_no_match_response(query: str, customer_name: str | None = None) -> str:
    """Generate response when no vehicles match the query"""
    greeting = f"Hi {customer_name}! " if customer_name else "Hello! "
    
    return (
        f"{greeting}Thank you for your inquiry about '{query}'. "
        "While I don't have exact matches in our current inventory, "
        "I'd be happy to help you find something similar or keep you updated "
        "when we get vehicles that match your criteria. "
        "Could you tell me more about your specific needs and budget?"
    )


def _generate_match_response(query: str, vehicles: list[dict[str, Any]], customer_name: str | None = None) -> str:
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
    conversations: list[Dict], 
    vehicles: list[dict[str, Any]], 
    lead_name: str | None = None
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
    # Analyze conversation context
    context_analysis = analyze_conversation_context(conversations)
    
    # Get the last customer message for RAG search
    last_message = get_last_customer_message(conversations)
    
    if not last_message:
        return _generate_welcome_response(lead_name, context_analysis)
    
    # Use new conversational prompt builder if available
    try:
        from maqro_rag.prompt_builder import PromptBuilder, AgentConfig
        
        # Create agent config from context
        agent_config = AgentConfig(
            tone="friendly",
            dealership_name="our dealership",
            persona_blurb="friendly, persuasive car salesperson"
        )
        
        prompt_builder = PromptBuilder(agent_config)
        
        if vehicles and len(vehicles) > 0:
            # Use grounded prompt with retrieved vehicles
            prompt = prompt_builder.build_grounded_prompt(
                user_message=last_message,
                retrieved_cars=vehicles,
                agent_config=agent_config
            )
        else:
            # Use generic prompt for fallback
            prompt = prompt_builder.build_generic_prompt(
                user_message=last_message,
                agent_config=agent_config
            )
        
        # For now, return a simple conversational response
        # In production, this would call the LLM with the prompt
        if vehicles and len(vehicles) > 0:
            vehicle = vehicles[0]['vehicle']
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            price = vehicle.get('price', 0)
            price_str = f"${price:,}" if price else "Price available upon request"
            
            greeting = f"Hi {lead_name}! " if lead_name else "Hey! "
            return f"{greeting}I found a {year} {make} {model} for {price_str}. It's in great condition and ready for a test drive. Would you like to come by this weekend to check it out?"
        else:
            greeting = f"Hi {lead_name}! " if lead_name else "Hey! "
            return f"{greeting}I'd love to help you find the perfect vehicle! What's your budget range and do you have any specific features you're looking for? This will help me show you the best options we have available."
            
    except ImportError:
        # Fallback to existing logic if RAG modules not available
        return _generate_personalized_response(last_message, vehicles, lead_name, context_analysis)


def _generate_welcome_response(lead_name: str, context_analysis: Dict[str, Any]) -> str:
    """Generate welcome response for new conversations"""
    greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
    
    return (
        f"{greeting}Welcome to Maqro Dealerships! I'm here to help you find the perfect vehicle. "
        "What type of car are you looking for today? I can help you with:\n"
        "• Finding vehicles in your budget\n"
        "• Scheduling test drives\n"
        "• Financing options\n"
        "• Trade-in evaluations\n\n"
        "Just let me know what you're interested in!"
    )


def _generate_personalized_response(
    query: str, 
    vehicles: list[Dict[str, Any]], 
    lead_name: str, 
    context_analysis: Dict[str, Any]
) -> str:
    """Generate personalized response based on conversation context"""
    
    # Base response
    if not vehicles:
        return _generate_no_match_response(query, lead_name)
    
    # Customize response based on intent
    intent = context_analysis.get('intent', 'general_inquiry')
    urgency = context_analysis.get('urgency', 'medium')
    budget_range = context_analysis.get('budget_range')
    
    greeting = f"Hi {lead_name}! " if lead_name else "Hello! "
    
    # Intent-specific responses
    if intent == 'test_drive':
        return _generate_test_drive_response(greeting, vehicles, context_analysis)
    elif intent == 'pricing':
        return _generate_pricing_response(greeting, vehicles, context_analysis)
    elif intent == 'availability':
        return _generate_availability_response(greeting, vehicles, context_analysis)
    elif intent == 'financing':
        return _generate_financing_response(greeting, vehicles, context_analysis)
    else:
        return _generate_general_response(greeting, vehicles, context_analysis)


def _generate_test_drive_response(greeting: str, vehicles: list[Dict[str, Any]], context_analysis: Dict[str, Any]) -> str:
    """Generate response focused on test drive scheduling"""
    response_parts = [
        f"{greeting}Great! I'd be happy to help you schedule a test drive. "
        f"Here are {len(vehicles)} vehicles that match your criteria:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}** - {price_str}\n"
        )
    
    response_parts.append(
        "\nI can schedule a test drive for any of these vehicles. "
        "What's your preferred date and time? I'll make sure the vehicle is ready for you!"
    )
    
    return "\n".join(response_parts)


def _generate_pricing_response(greeting: str, vehicles: list[Dict[str, Any]], context_analysis: Dict[str, Any]) -> str:
    """Generate response focused on pricing information"""
    response_parts = [
        f"{greeting}Here are the pricing details for vehicles that match your criteria:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}**\n"
            f"   Price: {price_str}\n"
        )
    
    response_parts.append(
        "\nThese prices are current and include all standard features. "
        "I can also provide financing options and payment estimates if you're interested!"
    )
    
    return "\n".join(response_parts)


def _generate_availability_response(greeting: str, vehicles: list[Dict[str, Any]], context_analysis: Dict[str, Any]) -> str:
    """Generate response focused on vehicle availability"""
    response_parts = [
        f"{greeting}Great news! I found {len(vehicles)} vehicles that are currently available:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}** - {price_str} ✅ In Stock\n"
        )
    
    response_parts.append(
        "\nAll these vehicles are ready for immediate purchase or test drive. "
        "Would you like to schedule a viewing or test drive?"
    )
    
    return "\n".join(response_parts)


def _generate_financing_response(greeting: str, vehicles: list[Dict[str, Any]], context_analysis: Dict[str, Any]) -> str:
    """Generate response focused on financing options"""
    response_parts = [
        f"{greeting}I'd be happy to help you with financing options! "
        f"Here are {len(vehicles)} vehicles that might fit your budget:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}** - {price_str}\n"
        )
    
    response_parts.append(
        "\nWe offer competitive financing rates and flexible payment plans. "
        "I can provide a quick financing estimate based on your credit profile. "
        "Would you like to discuss financing options?"
    )
    
    return "\n".join(response_parts)


def _generate_general_response(greeting: str, vehicles: list[Dict[str, Any]], context_analysis: Dict[str, Any]) -> str:
    """Generate general response for various inquiries"""
    response_parts = [
        f"{greeting}I found {len(vehicles)} vehicles that match your interests:\n"
    ]
    
    for i, result in enumerate(vehicles, 1):
        vehicle = result['vehicle']
        score = result['similarity_score']
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        price = vehicle.get('price')
        features = vehicle.get('features', '')
        
        price_str = f"${price:,}" if price else "Price available upon request"
        
        response_parts.append(
            f"{i}. **{year} {make} {model}**\n"
            f"   Price: {price_str}\n"
            f"   Features: {features}\n"
            f"   Match Score: {score:.1%}\n"
        )
    
    response_parts.append(
        "\nThese vehicles are currently available. "
        "Would you like to schedule a test drive, get more details, or discuss financing options?"
    )
    
    return "\n".join(response_parts)
