#!/usr/bin/env python3
"""
Test script for actual conversations with the full RAG system.
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


def test_actual_conversations():
    """Test actual conversations with the full RAG system."""
    
    print("Testing Actual Conversations with RAG System\n")
    print("=" * 60)
    
    # Initialize components
    print("Initializing RAG components...")
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    retriever.load_index("vehicle_index.faiss")
    parser = EntityParser()
    
    # Initialize OpenAI client
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Test conversations
    test_conversations = [
        {
            "query": "Do you have a white Tiguan under 32k?",
            "expected_make": "volkswagen",
            "expected_model": "tiguan",
            "expected_budget": 32000
        },
        {
            "query": "Looking for a 2021-2023 Civic EX around 20k.",
            "expected_make": "honda", 
            "expected_model": "civic",
            "expected_budget": 20000
        },
        {
            "query": "Any hybrids under 25k?",
            "expected_budget": 25000
        },
        {
            "query": "Do you still have the blue Camry SE from your site?",
            "expected_make": "toyota",
            "expected_model": "camry"
        },
        {
            "query": "Show me SUVs with 3rd row seating",
            "expected_body_type": "suv"
        }
    ]
    
    for i, conv in enumerate(test_conversations, 1):
        print(f"\n{'='*50}")
        print(f"Conversation {i}: '{conv['query']}'")
        print(f"{'='*50}")
        
        # 1. Entity extraction
        print("\n1. Entity Extraction:")
        print("-" * 20)
        vehicle_query = parser.parse_message(conv['query'])
        print(f"  Make: {vehicle_query.make}")
        print(f"  Model: {vehicle_query.model}")
        print(f"  Year Range: {vehicle_query.year_min}-{vehicle_query.year_max}")
        print(f"  Color: {vehicle_query.color}")
        print(f"  Budget: {vehicle_query.budget_max}")
        print(f"  Body Type: {vehicle_query.body_type}")
        print(f"  Features: {vehicle_query.features}")
        print(f"  Strong Signals: {vehicle_query.has_strong_signals}")
        
        # 2. Vehicle retrieval
        print("\n2. Vehicle Retrieval:")
        print("-" * 20)
        try:
            if vehicle_query.has_strong_signals:
                retrieved_cars = retriever.search_vehicles_hybrid(
                    query=conv['query'],
                    vehicle_query=vehicle_query,
                    top_k=5
                )
            else:
                retrieved_cars = retriever.search_vehicles(
                    query=conv['query'],
                    top_k=5
                )
            
            print(f"  Found {len(retrieved_cars)} vehicles")
            for j, car in enumerate(retrieved_cars[:3], 1):
                vehicle = car['vehicle']
                score = car['similarity_score']
                print(f"  {j}. {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} - ${vehicle.get('price', 0):,} (Score: {score:.2f})")
                
        except Exception as e:
            print(f"  Error in retrieval: {e}")
            retrieved_cars = []
        
        # 3. Prompt building
        print("\n3. Prompt Building:")
        print("-" * 20)
        agent_config = AgentConfig(
            tone="friendly",
            dealership_name="ABC Motors",
            persona_blurb="friendly, persuasive car salesperson"
        )
        
        prompt_builder = PromptBuilder(agent_config)
        
        if retrieved_cars and len(retrieved_cars) > 0:
            prompt = prompt_builder.build_grounded_prompt(
                user_message=conv['query'],
                retrieved_cars=retrieved_cars,
                agent_config=agent_config
            )
            prompt_type = "Grounded"
        else:
            prompt = prompt_builder.build_generic_prompt(
                user_message=conv['query'],
                agent_config=agent_config
            )
            prompt_type = "Generic"
        
        print(f"  Prompt Type: {prompt_type}")
        print(f"  Prompt Length: {len(prompt)} characters")
        print(f"  Prompt Preview: {prompt[:200]}...")
        
        # 4. Generate response
        print("\n4. Generated Response:")
        print("-" * 20)
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
            print(f"  Response: {generated_response}")
            
        except Exception as e:
            print(f"  Error generating response: {e}")
            generated_response = "Sorry, I couldn't generate a response at the moment."
        
        # 5. Validation
        print("\n5. Validation:")
        print("-" * 20)
        validation_results = []
        
        if 'expected_make' in conv and vehicle_query.make:
            validation_results.append(f"✓ Make detected: {vehicle_query.make}")
        elif 'expected_make' in conv:
            validation_results.append(f"✗ Make not detected (expected: {conv['expected_make']})")
            
        if 'expected_model' in conv and vehicle_query.model:
            validation_results.append(f"✓ Model detected: {vehicle_query.model}")
        elif 'expected_model' in conv:
            validation_results.append(f"✗ Model not detected (expected: {conv['expected_model']})")
            
        if 'expected_budget' in conv and vehicle_query.budget_max:
            validation_results.append(f"✓ Budget detected: ${vehicle_query.budget_max:,}")
        elif 'expected_budget' in conv:
            validation_results.append(f"✗ Budget not detected (expected: ${conv['expected_budget']:,})")
            
        if 'expected_body_type' in conv and vehicle_query.body_type:
            validation_results.append(f"✓ Body type detected: {vehicle_query.body_type}")
        elif 'expected_body_type' in conv:
            validation_results.append(f"✗ Body type not detected (expected: {conv['expected_body_type']})")
        
        for result in validation_results:
            print(f"  {result}")
        
        # Check response quality
        response_words = len(generated_response.split())
        if 10 <= response_words <= 50:
            print(f"  ✓ Response length: {response_words} words (good)")
        else:
            print(f"  ⚠ Response length: {response_words} words (should be 10-50)")
        
        if '?' in generated_response:
            print("  ✓ Response includes a question/CTA")
        else:
            print("  ⚠ Response missing question/CTA")
    
    print(f"\n{'='*60}")
    print("Conversation testing completed!")
    print("\nKey Metrics:")
    print("✓ Entity extraction accuracy")
    print("✓ Vehicle retrieval relevance")
    print("✓ Prompt generation quality")
    print("✓ Response conversational tone")
    print("✓ Response length and CTA presence")


if __name__ == "__main__":
    test_actual_conversations() 