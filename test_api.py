#!/usr/bin/env python3
"""
Simple test script for the Maqro API endpoints
Run this after starting the FastAPI server to test lead creation and messaging
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_create_lead():
    """Test creating a new lead"""
    print("Testing lead creation...")
    
    lead_data = {
        "name": "John Doe",
        "email": "john.doe@example.com", 
        "phone": "555-1234",
        "message": "Hi, I'm looking for a reliable sedan with good gas mileage for my daily commute"
    }
    
    response = requests.post(f"{BASE_URL}/leads", json=lead_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        lead_id = response.json()["lead_id"]
        print(f"Lead created with ID: {lead_id}")
        return lead_id
    else:
        print("Failed to create lead")
        return None

def test_add_message(lead_id):
    """Test adding a message to existing lead"""
    print(f"Testing message addition for lead {lead_id}...")
    
    message_data = {
        "lead_id": lead_id,
        "message": "Actually, I'm also interested in electric vehicles. Do you have any Tesla models?"
    }
    
    response = requests.post(f"{BASE_URL}/messages", json=message_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_lead(lead_id):
    """Test getting lead details"""
    print(f"Testing get lead details for ID {lead_id}...")
    
    response = requests.get(f"{BASE_URL}/leads/{lead_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_conversations(lead_id):
    """Test getting all conversations for a lead"""
    print(f"Testing get conversations for lead {lead_id}...")
    
    response = requests.get(f"{BASE_URL}/leads/{lead_id}/conversations")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def main():
    """Run all tests"""
    print("Starting Maqro API Tests")
    print("=" * 50)
    
    # Test 1: Health check
    test_health()
    
    # Test 2: Create a lead
    lead_id = test_create_lead()
    if not lead_id:
        print("Cannot continue tests without lead ID")
        return
    
    print()
    
    # Test 3: Add a message
    test_add_message(lead_id)
    
    # Test 4: Get lead details
    test_get_lead(lead_id)
    
    # Test 5: Get conversations
    test_get_conversations(lead_id)
    
    print("All tests completed!")

if __name__ == "__main__":
    main() 