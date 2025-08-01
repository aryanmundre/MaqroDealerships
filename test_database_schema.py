#!/usr/bin/env python3
"""
Database Schema Verification Test

This script verifies that your Supabase database has the correct tables
and columns as expected by the SQLAlchemy models.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Add src to path so we can import maqro_backend
sys.path.append(str(Path(__file__).parent / "src"))

from maqro_backend.db.session import engine


async def test_database_schema():
    """Test that database schema matches expectations"""
    print("🔍 Testing database schema...\n")
    
    # Expected schema structure
    expected_tables = {
        'leads': {
            'id': 'uuid',
            'created_at': 'timestamp with time zone',
            'name': 'text',
            'car': 'text',
            'source': 'text',
            'status': 'text',
            'last_contact': 'text',
            'email': 'text',
            'phone': 'text',
            'message': 'text',
            'user_id': 'uuid'
        },
        'conversations': {
            'id': 'uuid',
            'created_at': 'timestamp with time zone',
            'lead_id': 'uuid',
            'message': 'text',
            'sender': 'text'
        },
        'inventory': {
            'id': 'uuid',
            'created_at': 'timestamp with time zone',
            'updated_at': 'timestamp with time zone',
            'make': 'text',
            'model': 'text',
            'year': 'integer',
            'price': 'numeric',
            'mileage': 'integer',
            'description': 'text',
            'features': 'text',
            'dealership_id': 'uuid',
            'status': 'text'
        },
        'user_profiles': {
            'id': 'uuid',
            'user_id': 'uuid',
            'full_name': 'text',
            'phone': 'text',
            'role': 'text',
            'timezone': 'text',
            'created_at': 'timestamp with time zone',
            'updated_at': 'timestamp with time zone'
        }
    }
    
    results = []
    
    try:
        async with engine.begin() as conn:
            # Test 1: Check if tables exist
            print("📋 Checking table existence...")
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            existing_tables = {row.table_name for row in result.fetchall()}
            expected_table_names = set(expected_tables.keys())
            
            missing_tables = expected_table_names - existing_tables
            extra_tables = existing_tables - expected_table_names
            
            if not missing_tables:
                print("✅ All required tables exist")
                results.append(("Table Existence", True))
            else:
                print(f"❌ Missing tables: {missing_tables}")
                results.append(("Table Existence", False))
            
            if extra_tables:
                print(f"ℹ️  Extra tables found: {extra_tables}")
            
            # Test 2: Check column structure for each table
            print("\n📊 Checking column structure...")
            
            for table_name, expected_columns in expected_tables.items():
                if table_name not in existing_tables:
                    continue
                
                print(f"\n  Checking {table_name} table...")
                
                # Get column information
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                    ORDER BY ordinal_position
                """), {"table_name": table_name})
                
                actual_columns = {}
                for row in result.fetchall():
                    actual_columns[row.column_name] = {
                        'type': row.data_type,
                        'nullable': row.is_nullable == 'YES'
                    }
                
                # Check each expected column
                table_ok = True
                for col_name, expected_type in expected_columns.items():
                    if col_name not in actual_columns:
                        print(f"    ❌ Missing column: {col_name}")
                        table_ok = False
                    else:
                        actual_type = actual_columns[col_name]['type']
                        # Normalize type names for comparison
                        if (expected_type == 'uuid' and actual_type == 'uuid') or \
                           (expected_type == 'text' and actual_type == 'text') or \
                           (expected_type == 'integer' and actual_type == 'integer') or \
                           (expected_type == 'numeric' and actual_type == 'numeric') or \
                           ('timestamp' in expected_type and 'timestamp' in actual_type):
                            print(f"    ✅ {col_name}: {actual_type}")
                        else:
                            print(f"    ⚠️  {col_name}: expected {expected_type}, got {actual_type}")
                            table_ok = False
                
                # Show any extra columns
                extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
                if extra_columns:
                    print(f"    ℹ️  Extra columns: {extra_columns}")
                
                results.append((f"{table_name} Schema", table_ok))
            
            # Test 3: Check foreign key constraints
            print("\n🔗 Checking foreign key constraints...")
            
            result = await conn.execute(text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name
            """))
            
            foreign_keys = result.fetchall()
            
            expected_fks = [
                ('leads', 'user_id'),
                ('conversations', 'lead_id'),
                ('inventory', 'dealership_id'),
                ('user_profiles', 'user_id')
            ]
            
            found_fks = [(fk.table_name, fk.column_name) for fk in foreign_keys]
            
            fks_ok = True
            for table, column in expected_fks:
                if (table, column) in found_fks:
                    print(f"    ✅ {table}.{column} foreign key exists")
                else:
                    print(f"    ❌ {table}.{column} foreign key missing")
                    fks_ok = False
            
            if not fks_ok:
                 print("    ⚠️  Note: Missing foreign keys to 'auth.users' might be due to the test user's permissions.")

            results.append(("Foreign Key Check", fks_ok))

            # Test 4: Test basic data operations
            print("\n🧪 Testing basic data operations...")
            
            # Test UUID generation
            result = await conn.execute(text("SELECT uuid_generate_v4() as test_uuid"))
            test_uuid = result.fetchone().test_uuid
            print(f"    ✅ UUID generation works: {test_uuid}")
            
            # Test NOW() function
            result = await conn.execute(text("SELECT NOW() as current_time"))
            current_time = result.fetchone().current_time
            print(f"    ✅ Timestamp generation works: {current_time}")
            
            results.append(("Basic Operations", True))
            
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        results.append(("Database Schema Test", False))
    
    # Summary
    print(f"\n{'='*60}")
    print("DATABASE SCHEMA TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All schema tests passed! Your database is properly configured.")
    else:
        print("💥 Some schema tests failed. Check your database setup.")
        print("\nTo fix schema issues:")
        print("1. Make sure you've run the SQL from frontend/supabase/schema.sql")
        print("2. Check that uuid-ossp extension is enabled: CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        print("3. Verify your database connection and permissions")
    
    await engine.dispose()
    return passed == total


if __name__ == "__main__":
    load_dotenv()
    success = asyncio.run(test_database_schema())
    sys.exit(0 if success else 1)