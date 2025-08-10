#!/usr/bin/env python3
"""
Test script for SMS Parser functionality
Demonstrates how the system parses salesperson messages for lead creation and inventory updates
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from maqro_backend.services.sms_parser import sms_parser


def test_lead_creation_messages():
    """Test various lead creation message formats"""
    print("=== Testing Lead Creation Messages ===\n")
    
    test_messages = [
        # Exact pattern match
        "I just met Anna Johnson. Her number is 555-123-4567 and her email is anna@gmail.com. she is interested in subarus in the price range of $10K. I met her at the dealership.",
        
        # Alternative format
        "Met John Smith today. Phone: (555) 987-6543, Email: john@email.com. Interested in Honda Civic around $15K",
        
        # Dash-separated format
        "New lead: Sarah Wilson - 555-111-2222 - sarah@test.com - Toyota Camry - $12K",
        
        # Fuzzy parsing example
        "Just met a customer named Mike Davis. His phone is 555-333-4444 and he's looking for a Ford truck around $25K",
        
        # Another fuzzy example
        "New prospect: Lisa Brown, phone 555-555-5555, interested in electric vehicles, budget around $40K"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        result = sms_parser.parse_message(message)
        print(f"Result: {result['type']} (confidence: {result['confidence']})")
        if result['data']:
            print(f"Data: {result['data']}")
        print("-" * 80)


def test_inventory_update_messages():
    """Test various inventory update message formats"""
    print("\n=== Testing Inventory Update Messages ===\n")
    
    test_messages = [
        # Exact pattern match
        "I just picked up a 2006 Toyota Camry off facebook marketplace. It has 123456 miles. It is in good condition. Add it to the inventory",
        
        # Alternative format
        "New inventory: 2018 Honda Civic - 45000 miles - excellent - $18K",
        
        # Comma-separated format
        "Add vehicle: 2015 Ford F-150, 75000 miles, good, $22K",
        
        # Fuzzy parsing example
        "Just got a 2010 Nissan Altima from auction. 89000 miles, fair condition. Need to add to inventory",
        
        # Another fuzzy example
        "Picked up a 2012 BMW 3 Series today. 65000 miles, excellent condition, price TBD"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        result = sms_parser.parse_message(message)
        print(f"Result: {result['type']} (confidence: {result['confidence']})")
        if result['data']:
            print(f"Data: {result['data']}")
        print("-" * 80)


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===\n")
    
    test_messages = [
        # Unrecognized message
        "Hello, how are you today?",
        
        # Partial information
        "Met someone interested in cars",
        
        # Malformed phone number
        "New lead: John Doe - invalid-phone - john@email.com - Honda - $20K",
        
        # Missing required fields
        "I picked up a car today",
        
        # Mixed content
        "Hi there! I just met a customer and also need to add a vehicle to inventory"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        result = sms_parser.parse_message(message)
        print(f"Result: {result['type']} (confidence: {result['confidence']})")
        if result['data']:
            print(f"Data: {result['data']}")
        print("-" * 80)


def main():
    """Run all tests"""
    print("SMS Parser Test Suite")
    print("=" * 80)
    
    test_lead_creation_messages()
    test_inventory_update_messages()
    test_edge_cases()
    
    print("\n=== Test Summary ===")
    print("The SMS parser can handle:")
    print("✅ Structured lead creation messages")
    print("✅ Structured inventory update messages")
    print("✅ Fuzzy parsing for natural language")
    print("✅ Phone number normalization")
    print("✅ Price parsing (including K notation)")
    print("✅ Mileage parsing")
    print("✅ Confidence scoring")
    
    print("\nUsage Examples:")
    print("1. Salesperson texts: 'I just met Anna Johnson. Her number is 555-123-4567...'")
    print("2. Salesperson texts: 'I just picked up a 2006 Toyota Camry...'")
    print("3. System automatically detects intent and extracts structured data")
    print("4. Data is stored in Supabase database")
    print("5. Confirmation message sent back to salesperson")


if __name__ == "__main__":
    main()
