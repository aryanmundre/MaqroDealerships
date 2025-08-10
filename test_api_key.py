#!/usr/bin/env python3
"""
Simple test to verify OpenAI API key is working.
"""

import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set API key
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")

# Test OpenAI API
try:
    client = openai.OpenAI(api_key=api_key)
    
    # Simple test
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'Hello, API key is working!'"}
        ],
        max_tokens=50
    )
    
    print("✅ API Key is working!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ API Key error: {e}") 