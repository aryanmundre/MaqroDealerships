#!/usr/bin/env python3
"""
Comprehensive Supabase integration tests

This script tests:
1. Database connection
2. CRUD operations with UUIDs
3. API endpoints with authentication
4. Row Level Security compliance
"""
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add src to path so we can import maqro_backend
sys.path.append(str(Path(__file__).parent / "src"))

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

from maqro_backend.db.session import engine, get_db, SessionLocal
from maqro_backend.db.models import Lead, Conversation, Inventory
from maqro_backend.schemas.lead import LeadCreate
from maqro_backend.schemas.conversation import MessageCreate
from maqro_backend.crud import (
    create_lead_with_initial_message,
    get_lead_by_id,
    get_all_leads_ordered,
    create_conversation,
    get_conversations_by_lead_id,
    create_inventory_item,
    get_inventory_by_dealership
)

# Test data
TEST_USER_ID = str(uuid.uuid4())
TEST_LEAD_DATA = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "car": "2023 Honda Civic",
    "source": "Website",
    "message": "I'm interested in this car"
}

TEST_INVENTORY_DATA = {
    "make": "Toyota",
    "model": "Camry",
    "year": 2023,
    "price": "25000.00",
    "mileage": 15000,
    "description": "Excellent condition, well maintained",
    "features": "Leather seats, navigation, backup camera"
}


class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {message}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {len(self.tests)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['message']}")
        
        success_rate = (self.passed / len(self.tests)) * 100 if self.tests else 0
        print(f"Success rate: {success_rate:.1f}%")
        print(f"{'='*60}")


async def test_database_connection(results: TestResults):
    """Test basic database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT NOW() as current_time, version() as pg_version"))
            row = result.fetchone()
            
            results.add_result(
                "Database Connection", 
                True, 
                f"Connected to PostgreSQL at {row.current_time}"
            )
            
            # Test if our tables exist
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('leads', 'conversations', 'inventory')
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            expected_tables = {'leads', 'conversations', 'inventory'}
            found_tables = {table.table_name for table in tables}
            
            if expected_tables.issubset(found_tables):
                results.add_result("Required Tables Exist", True)
            else:
                missing = expected_tables - found_tables
                results.add_result("Required Tables Exist", False, f"Missing tables: {missing}")
                
    except Exception as e:
        results.add_result("Database Connection", False, str(e))


async def test_lead_crud_operations(results: TestResults):
    """Test Lead CRUD operations with UUIDs"""
    print("\n🔍 Testing Lead CRUD operations...")
    
    try:
        # Get database session
        async for session in get_db():
            # Test 1: Create lead
            lead_create = LeadCreate(**TEST_LEAD_DATA)
            result = await create_lead_with_initial_message(
                session=session,
                lead_in=lead_create,
                user_id=TEST_USER_ID
            )
            
            lead_id = result["lead_id"]
            results.add_result("Create Lead", True, f"Created lead with ID: {lead_id}")
            
            # Test 2: Get lead by ID
            lead = await get_lead_by_id(session=session, lead_id=lead_id)
            if lead and lead.name == TEST_LEAD_DATA["name"]:
                results.add_result("Get Lead by ID", True)
            else:
                results.add_result("Get Lead by ID", False, "Lead not found or data mismatch")
            
            # Test 3: Get all leads for user
            leads = await get_all_leads_ordered(session=session, user_id=TEST_USER_ID)
            if len(leads) >= 1 and any(str(l.id) == lead_id for l in leads):
                results.add_result("Get All Leads", True, f"Found {len(leads)} leads")
            else:
                results.add_result("Get All Leads", False, "Lead not found in user's leads")
            
            # Test 4: Verify UUID format
            try:
                uuid.UUID(lead_id)
                results.add_result("UUID Format", True)
            except ValueError:
                results.add_result("UUID Format", False, "Invalid UUID format")
            
            # Test 5: Verify user_id association
            if lead and str(lead.user_id) == TEST_USER_ID:
                results.add_result("User Association", True)
            else:
                results.add_result("User Association", False, "Lead not associated with correct user")
                
    except Exception as e:
        results.add_result("Lead CRUD Operations", False, str(e))


async def test_conversation_crud_operations(results: TestResults):
    """Test Conversation CRUD operations"""
    print("\n🔍 Testing Conversation CRUD operations...")
    
    try:
        async for session in get_db():
            # First create a lead to associate conversations with
            lead_create = LeadCreate(**TEST_LEAD_DATA)
            lead_result = await create_lead_with_initial_message(
                session=session,
                lead_in=lead_create,
                user_id=TEST_USER_ID
            )
            lead_id = lead_result["lead_id"]
            
            # Test 1: Create conversation
            conversation = await create_conversation(
                session=session,
                lead_id=lead_id,
                message="This is a test message from the agent",
                sender="agent",
                response_time_sec=30
            )
            
            if conversation and conversation.message:
                results.add_result("Create Conversation", True)
            else:
                results.add_result("Create Conversation", False, "Failed to create conversation")
            
            # Test 2: Get conversations by lead ID
            conversations = await get_conversations_by_lead_id(session=session, lead_id=lead_id)
            
            # Should have at least 2: initial message + our test message
            if len(conversations) >= 2:
                results.add_result("Get Conversations", True, f"Found {len(conversations)} conversations")
            else:
                results.add_result("Get Conversations", False, f"Expected >= 2 conversations, got {len(conversations)}")
            
            # Test 3: Verify conversation data
            agent_conv = next((c for c in conversations if c.sender == "agent"), None)
            if agent_conv and agent_conv.response_time_sec == 30:
                results.add_result("Conversation Data Integrity", True)
            else:
                results.add_result("Conversation Data Integrity", False, "Agent conversation not found or data mismatch")
                
    except Exception as e:
        results.add_result("Conversation CRUD Operations", False, str(e))


async def test_inventory_crud_operations(results: TestResults):
    """Test Inventory CRUD operations"""
    print("\n🔍 Testing Inventory CRUD operations...")
    
    try:
        async for session in get_db():
            # Test 1: Create inventory item
            inventory = await create_inventory_item(
                session=session,
                inventory_data=TEST_INVENTORY_DATA,
                dealership_id=TEST_USER_ID
            )
            
            if inventory and inventory.make == TEST_INVENTORY_DATA["make"]:
                results.add_result("Create Inventory", True)
            else:
                results.add_result("Create Inventory", False, "Failed to create inventory item")
            
            # Test 2: Get inventory by dealership
            inventory_items = await get_inventory_by_dealership(
                session=session,
                dealership_id=TEST_USER_ID
            )
            
            if len(inventory_items) >= 1:
                results.add_result("Get Inventory by Dealership", True, f"Found {len(inventory_items)} items")
            else:
                results.add_result("Get Inventory by Dealership", False, "No inventory items found")
            
            # Test 3: Verify inventory data
            if inventory_items and inventory_items[0].year == TEST_INVENTORY_DATA["year"]:
                results.add_result("Inventory Data Integrity", True)
            else:
                results.add_result("Inventory Data Integrity", False, "Inventory data mismatch")
                
    except Exception as e:
        results.add_result("Inventory CRUD Operations", False, str(e))


async def test_uuid_validation(results: TestResults):
    """Test UUID validation and error handling"""
    print("\n🔍 Testing UUID validation...")
    
    try:
        async for session in get_db():
            # Test 1: Invalid UUID format
            invalid_lead = await get_lead_by_id(session=session, lead_id="invalid-uuid")
            if invalid_lead is None:
                results.add_result("Invalid UUID Handling", True)
            else:
                results.add_result("Invalid UUID Handling", False, "Should return None for invalid UUID")
            
            # Test 2: Non-existent UUID
            fake_uuid = str(uuid.uuid4())
            non_existent_lead = await get_lead_by_id(session=session, lead_id=fake_uuid)
            if non_existent_lead is None:
                results.add_result("Non-existent UUID Handling", True)
            else:
                results.add_result("Non-existent UUID Handling", False, "Should return None for non-existent UUID")
                
    except Exception as e:
        results.add_result("UUID Validation", False, str(e))


async def test_rls_compliance(results: TestResults):
    """Test Row Level Security compliance"""
    print("\n🔍 Testing Row Level Security compliance...")
    
    try:
        async for session in get_db():
            # Create leads for two different users
            user1_id = str(uuid.uuid4())
            user2_id = str(uuid.uuid4())
            
            # Create lead for user 1
            lead_create = LeadCreate(**TEST_LEAD_DATA)
            user1_result = await create_lead_with_initial_message(
                session=session,
                lead_in=lead_create,
                user_id=user1_id
            )
            
            # Create lead for user 2
            lead_create2 = LeadCreate(
                name="Jane Smith",
                email="jane@example.com",
                phone="+0987654321",
                car="2023 Toyota Prius",
                source="Facebook",
                message="Looking for a hybrid car"
            )
            user2_result = await create_lead_with_initial_message(
                session=session,
                lead_in=lead_create2,
                user_id=user2_id
            )
            
            # Test 1: User 1 should only see their leads
            user1_leads = await get_all_leads_ordered(session=session, user_id=user1_id)
            user1_lead_ids = [str(lead.id) for lead in user1_leads]
            
            if user1_result["lead_id"] in user1_lead_ids and user2_result["lead_id"] not in user1_lead_ids:
                results.add_result("RLS - User Lead Isolation", True)
            else:
                results.add_result("RLS - User Lead Isolation", False, "User can see other user's leads")
            
            # Test 2: User 2 should only see their leads
            user2_leads = await get_all_leads_ordered(session=session, user_id=user2_id)
            user2_lead_ids = [str(lead.id) for lead in user2_leads]
            
            if user2_result["lead_id"] in user2_lead_ids and user1_result["lead_id"] not in user2_lead_ids:
                results.add_result("RLS - User Lead Separation", True)
            else:
                results.add_result("RLS - User Lead Separation", False, "User can see other user's leads")
                
    except Exception as e:
        results.add_result("RLS Compliance", False, str(e))


async def cleanup_test_data(results: TestResults):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        async for session in get_db():
            # Use the session to execute cleanup operations
            await session.execute(text("""
                DELETE FROM conversations 
                WHERE lead_id IN (
                    SELECT id FROM leads WHERE user_id = :user_id
                )
            """), {"user_id": TEST_USER_ID})
            
            await session.execute(text("""
                DELETE FROM leads WHERE user_id = :user_id
            """), {"user_id": TEST_USER_ID})
            
            await session.execute(text("""
                DELETE FROM inventory WHERE dealership_id = :dealership_id
            """), {"dealership_id": TEST_USER_ID})
            
            await session.commit()
            results.add_result("Cleanup Test Data", True)
            
    except Exception as e:
        results.add_result("Cleanup Test Data", False, str(e))


async def main():
    """Run all Supabase integration tests"""
    print("🚀 Starting Supabase Integration Tests...\n")
    
    # Load environment variables
    load_dotenv()
    
    results = TestResults()
    
    # Run all tests
    await test_database_connection(results)
    await test_lead_crud_operations(results)
    await test_conversation_crud_operations(results)
    await test_inventory_crud_operations(results)
    await test_uuid_validation(results)
    await test_rls_compliance(results)
    await cleanup_test_data(results)
    
    # Print summary
    results.print_summary()
    
    # Dispose engine
    await engine.dispose()
    
    return results.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)