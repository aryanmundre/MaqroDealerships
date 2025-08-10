#!/usr/bin/env python3
"""
Simple RAG Pipeline Test Script

This script allows you to test the RAG pipeline directly without going through the API.
It uses the same components as the conversation endpoint but in a simplified way.

Usage:
    python test_rag_pipeline.py "Do you have a white Tiguan under 32k?"
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from maqro_rag.entity_parser import EntityParser
from maqro_rag.retrieval import VehicleRetriever
from maqro_rag.prompt_builder import PromptBuilder, AgentConfig
from maqro_rag.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipelineTester:
    def __init__(self):
        """Initialize the RAG pipeline components"""
        self.config = Config.from_yaml("config.yaml")
        self.vehicle_retriever = VehicleRetriever(self.config)
        self.entity_parser = EntityParser()
        
        # Load vector index if available
        index_path = "vehicle_index.faiss"
        if os.path.exists(index_path):
            try:
                self.vehicle_retriever.load_index(index_path)
                logger.info("✅ Loaded RAG vector index successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load RAG index: {e}")
        else:
            logger.warning("⚠️ No vector index found. Please run build_rag_index.py first.")
        
        # Default agent config
        self.agent_config = AgentConfig(
            tone="friendly",
            dealership_name="our dealership",
            persona_blurb="friendly, persuasive car salesperson"
        )
        
        self.prompt_builder = PromptBuilder(self.agent_config)
    
    def test_entity_parsing(self, message: str) -> Dict[str, Any]:
        """Test entity parsing from user message"""
        logger.info("🔍 Testing entity parsing...")
        vehicle_query = self.entity_parser.parse_message(message)
        
        result = {
            "make": vehicle_query.make,
            "model": vehicle_query.model,
            "year_min": vehicle_query.year_min,
            "year_max": vehicle_query.year_max,
            "color": vehicle_query.color,
            "budget_max": vehicle_query.budget_max,
            "body_type": vehicle_query.body_type,
            "features": vehicle_query.features,
            "has_strong_signals": vehicle_query.has_strong_signals
        }
        
        logger.info(f"📋 Extracted entities: {result}")
        return result
    
    def test_retrieval(self, message: str, vehicle_query: Any) -> List[Dict[str, Any]]:
        """Test vehicle retrieval"""
        logger.info("🔎 Testing vehicle retrieval...")
        
        try:
            if vehicle_query.has_strong_signals:
                retrieved_cars = self.vehicle_retriever.search_vehicles_hybrid(
                    query=message,
                    vehicle_query=vehicle_query,
                    top_k=5
                )
                logger.info(f"🔍 Using hybrid retrieval (metadata + vector)")
            else:
                retrieved_cars = self.vehicle_retriever.search_vehicles(
                    query=message,
                    top_k=5
                )
                logger.info(f"🔍 Using vector-only retrieval")
            
            logger.info(f"✅ Retrieved {len(retrieved_cars)} vehicles")
            
            # Log retrieved vehicles
            for i, car in enumerate(retrieved_cars[:3]):  # Show first 3
                vehicle = car['vehicle']
                logger.info(f"   {i+1}. {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} - ${vehicle.get('price', 0):,}")
            
            return retrieved_cars
            
        except Exception as e:
            logger.error(f"❌ Error in vehicle retrieval: {e}")
            return []
    
    def test_prompt_building(self, message: str, retrieved_cars: List[Dict[str, Any]]) -> str:
        """Test prompt building"""
        logger.info("📝 Testing prompt building...")
        
        try:
            if retrieved_cars and len(retrieved_cars) > 0:
                prompt = self.prompt_builder.build_grounded_prompt(
                    user_message=message,
                    retrieved_cars=retrieved_cars,
                    agent_config=self.agent_config
                )
                logger.info("📝 Built grounded prompt (with retrieved vehicles)")
            else:
                prompt = self.prompt_builder.build_generic_prompt(
                    user_message=message,
                    agent_config=self.agent_config
                )
                logger.info("📝 Built generic prompt (no vehicles found)")
            
            # Show a preview of the prompt
            preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
            logger.info(f"📄 Prompt preview: {preview}")
            
            return prompt
            
        except Exception as e:
            logger.error(f"❌ Error in prompt building: {e}")
            return ""
    
    async def test_llm_generation(self, prompt: str) -> str:
        """Test LLM generation (requires OpenAI API key)"""
        logger.info("🤖 Testing LLM generation...")
        
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("❌ OPENAI_API_KEY not set. Please set it first:")
            logger.error("export OPENAI_API_KEY='sk-your-api-key-here'")
            return "❌ No OpenAI API key available"
        
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful car salesperson assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content
            logger.info(f"✅ Generated response: {generated_response}")
            return generated_response
            
        except ImportError:
            logger.error("❌ OpenAI package not installed. Run: pip install openai")
            return "❌ OpenAI package not available"
        except Exception as e:
            logger.error(f"❌ Error in LLM generation: {e}")
            return f"❌ LLM generation failed: {str(e)}"
    
    async def test_full_pipeline(self, message: str) -> Dict[str, Any]:
        """Test the complete RAG pipeline"""
        logger.info(f"🚀 Testing full RAG pipeline for: '{message}'")
        logger.info("=" * 60)
        
        # 1. Entity parsing
        vehicle_query = self.entity_parser.parse_message(message)
        entities = self.test_entity_parsing(message)
        
        # 2. Retrieval
        retrieved_cars = self.test_retrieval(message, vehicle_query)
        
        # 3. Prompt building
        prompt = self.test_prompt_building(message, retrieved_cars)
        
        # 4. LLM generation
        response = await self.test_llm_generation(prompt)
        
        logger.info("=" * 60)
        logger.info("🎯 PIPELINE RESULTS:")
        logger.info(f"📝 User Message: {message}")
        logger.info(f"🔍 Entities Found: {entities}")
        logger.info(f"🚗 Vehicles Retrieved: {len(retrieved_cars)}")
        logger.info(f"🤖 AI Response: {response}")
        
        return {
            "user_message": message,
            "entities": entities,
            "retrieved_vehicles": len(retrieved_cars),
            "vehicle_details": [car['vehicle'] for car in retrieved_cars[:3]],
            "ai_response": response
        }


async def main():
    """Main function to run the RAG pipeline test"""
    if len(sys.argv) < 2:
        print("Usage: python test_rag_pipeline.py \"Your message here\"")
        print("\nExample queries:")
        print("  python test_rag_pipeline.py \"Do you have a white Tiguan under 32k?\"")
        print("  python test_rag_pipeline.py \"Looking for a 2021-2023 Civic EX around 20k\"")
        print("  python test_rag_pipeline.py \"SUV with 3rd row this weekend\"")
        print("  python test_rag_pipeline.py \"Any hybrids under 25k?\"")
        return
    
    message = sys.argv[1]
    
    # Initialize tester
    tester = RAGPipelineTester()
    
    # Run full pipeline test
    result = await tester.test_full_pipeline(message)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY:")
    print(f"Query: {result['user_message']}")
    print(f"Entities: {result['entities']}")
    print(f"Vehicles Found: {result['retrieved_vehicles']}")
    print(f"AI Response: {result['ai_response']}")


if __name__ == "__main__":
    asyncio.run(main()) 