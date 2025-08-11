#!/usr/bin/env python3
"""
Quick test to verify RAG system works with metadata structure
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from maqro_rag import Config, VehicleRetriever
    from maqro_rag.entity_parser import EntityParser
    
    print("✅ Successfully imported RAG modules")
    
    # Initialize with default config
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    entity_parser = EntityParser()
    
    print("✅ Initialized RAG components")
    
    # Try to load existing index
    index_path = "vehicle_index.faiss"
    if os.path.exists(f"{index_path}.faiss") and os.path.exists(f"{index_path}.metadata"):
        print(f"📁 Loading existing index: {index_path}")
        retriever.load_index(index_path)
        print("✅ Index loaded successfully")
    else:
        print(f"📁 Building new index from sample_inventory.csv")
        retriever.build_index("sample_inventory.csv", index_path)
        print("✅ Index built successfully")
    
    # Test entity parsing
    test_query = "Do you have any Mazda"
    print(f"\n🔍 Testing query: '{test_query}'")
    
    parsed = entity_parser.parse_message(test_query)
    print(f"   📋 Parsed make: {parsed.make}")
    print(f"   📋 Has strong signals: {parsed.has_strong_signals}")
    
    # Test vehicle search
    print(f"\n🚗 Searching for vehicles...")
    if parsed.has_strong_signals:
        results = retriever.search_vehicles_hybrid(test_query, parsed, top_k=3)
        print(f"   🎯 Used hybrid search")
    else:
        results = retriever.search_vehicles(test_query, top_k=3)
        print(f"   🎯 Used vector search")
    
    print(f"✅ Found {len(results)} vehicles")
    
    # Display results
    for i, result in enumerate(results, 1):
        vehicle = result['vehicle']
        score = result['similarity_score']
        print(f"   {i}. {vehicle.get('year', 'N/A')} {vehicle.get('make', 'N/A')} {vehicle.get('model', 'N/A')}")
        print(f"      💰 ${vehicle.get('price', 0):,} | 🎯 Score: {score:.3f}")
    
    print("\n🎉 RAG system test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)