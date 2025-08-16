#!/usr/bin/env python3
"""
Test script for Database RAG system
"""
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_db_rag():
    """Test the database RAG system"""
    try:
        print("🧪 Testing Database RAG System...")
        
        # Import modules
        from maqro_rag.config import Config
        from maqro_rag.db_retriever import DatabaseRAGRetriever
        from maqro_rag.entity_parser import EntityParser
        from maqro_backend.core.config import settings
        
        # Create database connection
        engine = create_async_engine(settings.database_url)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Initialize components
        config = Config.from_yaml("config.yaml")
        db_retriever = DatabaseRAGRetriever(config)
        entity_parser = EntityParser()
        
        print("✅ Components initialized")
        
        # Test dealership ID (adjust as needed)
        dealership_id = "d660c7d6-99e2-4fa8-b99b-d221def53d20"
        
        async with async_session_maker() as session:
            print(f"🏢 Testing with dealership: {dealership_id}")
            
            # Check current RAG stats
            stats = await db_retriever.get_retriever_stats(session, dealership_id)
            print(f"📊 Current RAG stats: {stats}")
            
            # Build embeddings if needed
            if stats.get("missing_embeddings", 0) > 0 or stats.get("total_embeddings", 0) == 0:
                print("🔨 Building embeddings...")
                built_count = await db_retriever.build_embeddings_for_dealership(
                    session=session,
                    dealership_id=dealership_id,
                    force_rebuild=False
                )
                print(f"✅ Built {built_count} embeddings")
            
            # Test search queries
            test_queries = [
                "Do you have any Toyota",
                "Looking for a Honda Civic",
                "Show me SUVs under 30k",
                "Any luxury sedans?"
            ]
            
            for query in test_queries:
                print(f"\n🔍 Testing query: '{query}'")
                
                # Parse entities
                vehicle_query = entity_parser.parse_message(query)
                print(f"   📋 Parsed: make={vehicle_query.make}, strong_signals={vehicle_query.has_strong_signals}")
                
                # Search vehicles
                if vehicle_query.has_strong_signals:
                    results = await db_retriever.search_vehicles_hybrid(
                        session=session,
                        query=query,
                        vehicle_query=vehicle_query,
                        dealership_id=dealership_id,
                        top_k=3
                    )
                    print(f"   🎯 Used hybrid search")
                else:
                    results = await db_retriever.search_vehicles(
                        session=session,
                        query=query,
                        dealership_id=dealership_id,
                        top_k=3
                    )
                    print(f"   🎯 Used vector search")
                
                # Display results
                if results:
                    print(f"   ✅ Found {len(results)} vehicles:")
                    for i, result in enumerate(results, 1):
                        vehicle = result['vehicle']
                        score = result['similarity_score']
                        print(f"      {i}. {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')} - ${vehicle.get('price'):,} (Score: {score:.3f})")
                else:
                    print("   ❌ No vehicles found")
        
        await engine.dispose()
        print("\n🎉 Database RAG test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in database RAG test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_rag())
    sys.exit(0 if success else 1)