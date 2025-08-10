#!/usr/bin/env python3
"""
Test script for entity parser functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from maqro_rag.entity_parser import EntityParser


def test_entity_parser():
    """Test the entity parser with various inputs."""
    
    parser = EntityParser()
    
    test_cases = [
        "Do you have a white Tiguan under 32k?",
        "Looking for a 2021-2023 Civic EX around 20k.",
        "SUV with 3rd row this weekend.",
        "Any hybrids under 25k?",
        "Do you still have the blue Camry SE from your site?",
        "I want a red BMW 3 series",
        "Show me trucks under 40k",
        "Need a 2022 Honda Accord with leather seats"
    ]
    
    print("Testing Entity Parser\n")
    print("=" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_input}'")
        print("-" * 30)
        
        try:
            query = parser.parse_message(test_input)
            
            print(f"Make: {query.make}")
            print(f"Model: {query.model}")
            print(f"Trim: {query.trim}")
            print(f"Year Range: {query.year_min}-{query.year_max}")
            print(f"Color: {query.color}")
            print(f"Budget Max: {query.budget_max}")
            print(f"Body Type: {query.body_type}")
            print(f"Features: {query.features}")
            print(f"Has Strong Signals: {query.has_strong_signals}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Entity parser test completed!")


if __name__ == "__main__":
    test_entity_parser() 