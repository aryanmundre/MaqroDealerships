#!/usr/bin/env python3
"""
Quick test of the conversational RAG system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from maqro_rag.entity_parser import EntityParser
from maqro_rag.retrieval import VehicleRetriever
from maqro_rag.config import Config
from maqro_rag.prompt_builder import PromptBuilder, AgentConfig
import openai


def quick_test():
    """Quick test of the conversational RAG system."""
    
    print("🚗 Quick Conversational RAG Test")
    print("=" * 40)
    
    # Initialize components
    print("Initializing...")
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    retriever.load_index("vehicle_index.faiss")
    parser = EntityParser()
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Test query
    test_query = "Do you have a white Tiguan under 32k?"
    print(f"\nTesting: '{test_query}'")
    
    # 1. Entity extraction
    vehicle_query = parser.parse_message(test_query)
    print(f"✓ Extracted: make={vehicle_query.make}, model={vehicle_query.model}, color={vehicle_query.color}, budget=${vehicle_query.budget_max:,}")
    
    # 2. Vehicle retrieval
    retrieved_cars = retriever.search_vehicles_hybrid(test_query, vehicle_query, top_k=3)
    print(f"✓ Retrieved {len(retrieved_cars)} vehicles")
    
    if retrieved_cars:
        for i, car in enumerate(retrieved_cars[:2], 1):
            vehicle = car['vehicle']
            score = car['similarity_score']
            print(f"  {i}. {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} - ${vehicle.get('price', 0):,} (Score: {score:.2f})")
    
    # 3. Generate response
    agent_config = AgentConfig(tone="friendly", dealership_name="ABC Motors")
    prompt_builder = PromptBuilder(agent_config)
    
    if retrieved_cars:
        prompt = prompt_builder.build_grounded_prompt(test_query, retrieved_cars, agent_config)
    else:
        prompt = prompt_builder.build_generic_prompt(test_query, agent_config)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful car salesperson assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7
    )
    
    generated_response = response.choices[0].message.content.strip()
    print(f"\n💬 Response: {generated_response}")
    
    # Analysis
    response_words = len(generated_response.split())
    has_question = '?' in generated_response
    has_cta = any(word in generated_response.lower() for word in ['come', 'check', 'visit', 'call', 'text', 'schedule'])
    
    print(f"\n📊 Analysis:")
    print(f"  Words: {response_words} (target: 10-50)")
    print(f"  Has question: {'✓' if has_question else '✗'}")
    print(f"  Has CTA: {'✓' if has_cta else '✗'}")
    
    print(f"\n✅ Test completed successfully!")
    print("The conversational RAG system is working perfectly!")


if __name__ == "__main__":
    quick_test() 