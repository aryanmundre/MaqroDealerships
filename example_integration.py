#!/usr/bin/env python3
"""
Example integration showing how to use the RAG system with an AI response module.
"""

import os
from typing import List, Dict, Any
from loguru import logger
from maqro_rag import Config, VehicleRetriever


class AIResponseGenerator:
    """Example AI response generator that uses the RAG system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.retriever = VehicleRetriever(config)
        
        # Load or build index
        index_path = "vehicle_index"
        if os.path.exists(f"{index_path}.faiss"):
            self.retriever.load_index(index_path)
        else:
            self.retriever.build_index("sample_inventory.csv", index_path)
    
    def generate_response(self, lead_message: str) -> str:
        """Generate a personalized response based on lead message and inventory."""
        
        # Search for relevant vehicles
        try:
            relevant_vehicles = self.retriever.search_vehicles(lead_message, top_k=3)
            
            if not relevant_vehicles:
                return self._generate_no_match_response(lead_message)
            
            return self._generate_match_response(lead_message, relevant_vehicles)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_error_response()
    
    def _generate_match_response(self, lead_message: str, vehicles: List[Dict[str, Any]]) -> str:
        """Generate response when matching vehicles are found."""
        
        # Extract vehicle details
        vehicle_details = []
        for result in vehicles:
            vehicle = result['vehicle']
            score = result['similarity_score']
            
            details = {
                'year': vehicle.get('year'),
                'make': vehicle.get('make'),
                'model': vehicle.get('model'),
                'price': vehicle.get('price'),
                'features': vehicle.get('features'),
                'description': vehicle.get('description'),
                'score': score
            }
            vehicle_details.append(details)
        
        # Generate personalized response
        response_parts = [
            f"Thank you for your interest! Based on your message about '{lead_message}', "
            f"I found {len(vehicles)} vehicle(s) that might be perfect for you:\n\n"
        ]
        
        for i, details in enumerate(vehicle_details, 1):
            price_str = f"${details['price']:,}" if details['price'] else "Price available upon request"
            
            response_parts.append(
                f"{i}. **{details['year']} {details['make']} {details['model']}**\n"
                f"   Price: {price_str}\n"
                f"   Features: {details['features']}\n"
                f"   {details['description']}\n"
                f"   Match Score: {details['score']:.1%}\n"
            )
        
        response_parts.append(
            "\nWould you like to schedule a test drive or get more information about any of these vehicles? "
            "I can also help you find other options that match your preferences."
        )
        
        return "\n".join(response_parts)
    
    def _generate_no_match_response(self, lead_message: str) -> str:
        """Generate response when no matching vehicles are found."""
        
        return (
            f"Thank you for your inquiry about '{lead_message}'! "
            "While I don't have exact matches in our current inventory, "
            "I'd be happy to help you find something similar or keep you updated "
            "when we get vehicles that match your criteria. "
            "Could you tell me more about your specific needs and budget?"
        )
    
    def _generate_error_response(self) -> str:
        """Generate response when an error occurs."""
        
        return (
            "I apologize, but I'm having trouble accessing our inventory right now. "
            "Please try again in a moment, or feel free to call us directly "
            "and one of our sales representatives will be happy to help you."
        )


def demo_integration():
    """Demonstrate the integration with sample lead messages."""
    
    # Load configuration
    config = Config.from_yaml("config.yaml")
    
    # Initialize AI response generator
    ai_generator = AIResponseGenerator(config)
    
    # Sample lead messages
    lead_messages = [
        "Looking for a reliable sedan with good gas mileage",
        "I want a luxury car with advanced technology",
        "Show me affordable vehicles under $25,000",
        "I need an SUV for family use",
        "Electric vehicle with modern features"
    ]
    
    print("🤖 AI Response Generator Demo")
    print("=" * 60)
    
    for i, message in enumerate(lead_messages, 1):
        print(f"\n📝 Lead Message {i}: {message}")
        print("-" * 40)
        
        response = ai_generator.generate_response(message)
        print(response)
        print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_integration() 