#!/usr/bin/env python3
"""
Interactive demo of the conversational RAG system.
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


def demo_conversational_rag():
    """Interactive demo of the conversational RAG system."""
    
    print("🚗 Conversational RAG System Demo")
    print("=" * 50)
    print("This demo shows how the RAG system processes natural language")
    print("queries and generates conversational responses.")
    print()
    
    # Initialize components
    print("Initializing RAG components...")
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    retriever.load_index("vehicle_index.faiss")
    parser = EntityParser()
    
    # Initialize OpenAI client
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Sample queries for demonstration
    sample_queries = [
        "Do you have a white Tiguan under 32k?",
        "Looking for a 2021-2023 Civic EX around 20k.",
        "Any hybrids under 25k?",
        "Do you still have the blue Camry SE from your site?",
        "Show me SUVs with 3rd row seating",
        "I want a red BMW 3 series",
        "What's your best deal on a sedan?",
        "Need a truck for work"
    ]
    
    print(f"Available sample queries:")
    for i, query in enumerate(sample_queries, 1):
        print(f"  {i}. {query}")
    print()
    
    while True:
        print("\n" + "="*50)
        choice = input("Enter a number (1-8) for sample query, or type your own query (or 'quit' to exit): ").strip()
        
        if choice.lower() == 'quit':
            break
            
        # Handle sample query selection
        if choice.isdigit() and 1 <= int(choice) <= len(sample_queries):
            user_query = sample_queries[int(choice) - 1]
            print(f"Using sample query: {user_query}")
        else:
            user_query = choice
            if not user_query:
                continue
        
        print(f"\n🔍 Processing: '{user_query}'")
        print("-" * 50)
        
        # Step 1: Entity Extraction
        print("\n1️⃣ Entity Extraction:")
        vehicle_query = parser.parse_message(user_query)
        print(f"   Make: {vehicle_query.make or 'None'}")
        print(f"   Model: {vehicle_query.model or 'None'}")
        print(f"   Year Range: {vehicle_query.year_min}-{vehicle_query.year_max}" if vehicle_query.year_min or vehicle_query.year_max else "   Year Range: None")
        print(f"   Color: {vehicle_query.color or 'None'}")
        print(f"   Budget: ${vehicle_query.budget_max:,}" if vehicle_query.budget_max else "   Budget: None")
        print(f"   Body Type: {vehicle_query.body_type or 'None'}")
        print(f"   Features: {vehicle_query.features}")
        print(f"   Strong Signals: {vehicle_query.has_strong_signals}")
        
        # Step 2: Vehicle Retrieval
        print("\n2️⃣ Vehicle Retrieval:")
        try:
            if vehicle_query.has_strong_signals:
                retrieved_cars = retriever.search_vehicles_hybrid(
                    query=user_query,
                    vehicle_query=vehicle_query,
                    top_k=5
                )
                search_type = "Hybrid (metadata filters + vector similarity)"
            else:
                retrieved_cars = retriever.search_vehicles(
                    query=user_query,
                    top_k=5
                )
                search_type = "Vector similarity only"
            
            print(f"   Search Type: {search_type}")
            print(f"   Found {len(retrieved_cars)} vehicles")
            
            if retrieved_cars:
                print("   Top matches:")
                for i, car in enumerate(retrieved_cars[:3], 1):
                    vehicle = car['vehicle']
                    score = car['similarity_score']
                    print(f"   {i}. {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} - ${vehicle.get('price', 0):,} (Score: {score:.2f})")
            else:
                print("   No vehicles found")
                
        except Exception as e:
            print(f"   Error in retrieval: {e}")
            retrieved_cars = []
        
        # Step 3: Prompt Building
        print("\n3️⃣ Prompt Building:")
        agent_config = AgentConfig(
            tone="friendly",
            dealership_name="ABC Motors",
            persona_blurb="friendly, persuasive car salesperson"
        )
        
        prompt_builder = PromptBuilder(agent_config)
        
        if retrieved_cars and len(retrieved_cars) > 0:
            prompt = prompt_builder.build_grounded_prompt(
                user_message=user_query,
                retrieved_cars=retrieved_cars,
                agent_config=agent_config
            )
            prompt_type = "Grounded (with vehicle data)"
        else:
            prompt = prompt_builder.build_generic_prompt(
                user_message=user_query,
                agent_config=agent_config
            )
            prompt_type = "Generic (fallback)"
        
        print(f"   Prompt Type: {prompt_type}")
        print(f"   Prompt Length: {len(prompt)} characters")
        
        # Step 4: Generate Response
        print("\n4️⃣ Generated Response:")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful car salesperson assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content.strip()
            print(f"   💬 {generated_response}")
            
            # Response analysis
            response_words = len(generated_response.split())
            has_question = '?' in generated_response
            has_cta = any(word in generated_response.lower() for word in ['come', 'check', 'visit', 'call', 'text', 'schedule'])
            
            print(f"\n   📊 Response Analysis:")
            print(f"      Words: {response_words} (target: 10-50)")
            print(f"      Has question: {'✓' if has_question else '✗'}")
            print(f"      Has CTA: {'✓' if has_cta else '✗'}")
            
        except Exception as e:
            print(f"   Error generating response: {e}")
        
        print("\n" + "="*50)
        print("🎯 Key Features Demonstrated:")
        print("   ✓ Entity extraction from natural language")
        print("   ✓ Hybrid retrieval (metadata + vector similarity)")
        print("   ✓ Conversational prompt building")
        print("   ✓ SMS-style response generation")
        print("   ✓ Fallback handling for weak signals")
    
    print("\n👋 Thanks for trying the Conversational RAG Demo!")


if __name__ == "__main__":
    demo_conversational_rag() 