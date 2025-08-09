#!/usr/bin/env python3
"""
Test script to simulate Vonage SMS webhook calls
Usage: python test_sms_webhook.py
"""

import requests
import sys

# Your backend URL (adjust port if needed)
BASE_URL = "http://localhost:8000"

def test_webhook(phone_number, message_text):
    """Test the webhook with a simulated SMS"""
    
    webhook_data = {
        'msisdn': phone_number,           # Customer's phone number
        'to': '14352381767',              # Your Vonage number (from test_vonage.js)
        'text': message_text,             # Customer's message
        'messageId': 'test_' + str(hash(message_text))[:8]  # Fake message ID
    }
    
    print(f"🔄 Testing webhook with:")
    print(f"   From: {phone_number}")
    print(f"   Message: {message_text}")
    print(f"   To: {webhook_data['to']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/vonage/webhook", 
            data=webhook_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📋 Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"🎉 Success! Lead ID: {result.get('lead_id')}")
                print(f"📤 Response sent: {result.get('response_sent', False)}")
            else:
                print(f"⚠️  Partial success or error: {result}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is your backend running?")
        print("   Try: python -m uvicorn src.maqro_backend.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Use a phone number that exists in your leads database
        ("+14084780050", "Hi, I'm interested a Toyota"),
    ]
    
    print("🚀 Testing Vonage SMS Webhook")
    print("=" * 50)
    
    for i, (phone, message) in enumerate(test_cases, 1):
        print(f"\n📞 Test {i}:")
        test_webhook(phone, message)
        print("-" * 30)