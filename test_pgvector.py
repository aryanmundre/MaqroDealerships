#!/usr/bin/env python3
"""
Test if pgvector extension is properly installed in Supabase
"""
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_pgvector():
    """Test pgvector extension"""
    try:
        from maqro_backend.core.config import settings
        
        # Create database connection
        engine = create_async_engine(settings.database_url)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            print("🔍 Testing pgvector extension...")
            
            # Test 1: Check if pgvector extension exists
            result = await session.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector';")
            )
            extensions = result.fetchall()
            
            if extensions:
                print("✅ pgvector extension is installed")
                for ext in extensions:
                    print(f"   Extension: {ext.extname}, Version: {ext.extversion}")
            else:
                print("❌ pgvector extension is NOT installed")
                print("   Please run: CREATE EXTENSION vector; in Supabase")
                return False
            
            # Test 2: Check if our table exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM vehicle_embeddings;")
            )
            count = result.scalar()
            print(f"✅ vehicle_embeddings table exists with {count} rows")
            
            # Test 3: Test simple vector operation
            print("🧪 Testing vector operations...")
            
            test_embedding = "[0.1, 0.2, 0.3]"
            result = await session.execute(
                text(f"SELECT '{test_embedding}'::vector;")
            )
            vector_result = result.scalar()
            print(f"✅ Vector casting works: {vector_result}")
            
            # Test 4: Test vector similarity
            test_embedding2 = "[0.2, 0.3, 0.4]"
            result = await session.execute(
                text(f"SELECT '{test_embedding}'::vector <=> '{test_embedding2}'::vector as distance;")
            )
            distance = result.scalar()
            print(f"✅ Vector similarity works: distance = {distance}")
            
            # Test 5: Test our actual query structure (simplified)
            try:
                # Use a 1536-dimension test vector (matching OpenAI embeddings)
                test_vector_1536 = "[" + ",".join(["0.1"] * 1536) + "]"
                result = await session.execute(
                    text(f"""
                    SELECT COUNT(*) 
                    FROM vehicle_embeddings ve
                    WHERE ve.embedding <=> '{test_vector_1536}'::vector IS NOT NULL
                    """)
                )
                count = result.scalar()
                print(f"✅ Our query structure works: {count} embeddings tested")
                
            except Exception as e:
                print(f"❌ Query structure error: {e}")
                return False
        
        await engine.dispose()
        print("\n🎉 pgvector is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing pgvector: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pgvector())
    sys.exit(0 if success else 1)