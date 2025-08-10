#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced SMS parser handling different message types
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from maqro_backend.services.sms_parser import SMSParser

def test_enhanced_sms_parser():
    """Test the enhanced SMS parser with different message types"""
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it first:")
        print("export OPENAI_API_KEY='sk-your-api-key-here'")
        return
    
    print("🚀 Testing Enhanced SMS Parser with Different Message Types")
    print("=" * 60)
    
    # Initialize the parser
    try:
        parser = SMSParser()
        print("✅ SMS Parser initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SMS Parser: {e}")
        return
    
    # Test messages covering different types
    test_messages = [
        # Lead Creation
        "I just met Sarah Johnson. Her number is 555-1234 and her email is sarah@email.com. She is interested in a Honda Civic around $25K. I met her at the dealership.",
        
        # Inventory Update
        "I just picked up a 2020 Toyota Camry off auction. It has 45,000 miles. It is in excellent condition. Add it to the inventory.",
        
        # Lead Inquiry
        "What's the status of lead John Smith?",
        "Check details for lead #123",
        "How is customer Mary doing?",
        
        # Inventory Inquiry
        "Do we have any Honda Civics in stock?",
        "What's the price of the 2020 Camry?",
        "Are there any SUVs under $30K?",
        
        # General Questions
        "What's my schedule today?",
        "I need help with a difficult customer",
        "Can you tell me about the new promotion?",
        
        # Status Updates
        "Lead John Smith is coming in for test drive tomorrow",
        "Customer #123 decided to go with the Honda",
        "Sarah Johnson scheduled follow-up for next week",
        
        # Edge Cases
        "Hello, how are you?",
        "Thanks for the help!",
        "Meeting at 3pm today"
    ]
    
    print(f"\n📝 Testing {len(test_messages)} different message types...\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i:2d}: {message[:60]}{'...' if len(message) > 60 else ''}")
        
        try:
            result = parser.parse_message(message)
            
            print(f"     Type: {result['type']}")
            print(f"     Confidence: {result['confidence']}")
            
            if result['type'] != 'unknown':
                data = result['data']
                if result['type'] == 'lead_creation':
                    print(f"     Extracted: {data.get('name', 'N/A')} - {data.get('phone', 'N/A')} - {data.get('car_interest', 'N/A')}")
                elif result['type'] == 'inventory_update':
                    print(f"     Extracted: {data.get('year', 'N/A')} {data.get('make', 'N/A')} {data.get('model', 'N/A')}")
                elif result['type'] == 'lead_inquiry':
                    print(f"     Extracted: {data.get('lead_identifier', 'N/A')} - {data.get('inquiry_type', 'N/A')}")
                elif result['type'] == 'inventory_inquiry':
                    search = data.get('search_criteria', {})
                    print(f"     Extracted: {search.get('make', 'Any')} {search.get('model', 'Any')}")
                elif result['type'] == 'general_question':
                    print(f"     Extracted: {data.get('question_topic', 'N/A')} - {data.get('urgency', 'N/A')}")
                elif result['type'] == 'status_update':
                    print(f"     Extracted: {data.get('lead_identifier', 'N/A')} - {data.get('update_type', 'N/A')}")
            else:
                print(f"     Result: Message not recognized")
            
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
        print()
    
    print("🎯 Enhanced SMS Parser Test Complete!")
    print("\nKey Improvements:")
    print("• Now handles 6 message types instead of just 2")
    print("• Intelligent classification using LLM")
    print("• Better fallback parsing for edge cases")
    print("• Appropriate responses for each message type")

if __name__ == "__main__":
    test_enhanced_sms_parser()
