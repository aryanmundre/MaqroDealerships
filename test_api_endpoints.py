#!/usr/bin/env python3
"""
API Endpoints Test Script for Supabase Integration

This script tests all API endpoints with proper authentication headers
and UUID handling.
"""
import asyncio
import httpx
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
API_PREFIX = "/api/routes"
TEST_USER_ID = str(uuid.uuid4())

# Test data
TEST_LEAD_DATA = {
    "name": "API Test Lead",
    "email": "apitest@example.com",
    "phone": "+1111111111",
    "car": "2023 Tesla Model 3",
    "source": "API Test",
    "message": "This is a test message from API testing"
}

TEST_INVENTORY_DATA = {
    "make": "BMW",
    "model": "X5",
    "year": 2023,
    "price": "65000.00",
    "mileage": 5000,
    "description": "Luxury SUV in excellent condition",
    "features": "Premium package, navigation, heated seats",
    "status": "active"
}


class APITestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = "", response_data=None):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message,
            "response_data": response_data
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
            if response_data:
                print(f"   Response: {json.dumps(response_data, indent=2, default=str)[:200]}...")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {message}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"API TEST SUMMARY")
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


async def test_health_endpoint(client: httpx.AsyncClient, results: APITestResults):
    """Test health check endpoint"""
    print("\n🔍 Testing health endpoint...")
    
    try:
        response = await client.get(f"{API_PREFIX}/health")
        
        if response.status_code == 200:
            results.add_result("Health Check", True, response_data=response.json())
        else:
            results.add_result("Health Check", False, f"Status code: {response.status_code}")
            
    except Exception as e:
        results.add_result("Health Check", False, str(e))


async def test_leads_endpoints(client: httpx.AsyncClient, results: APITestResults):
    """Test leads API endpoints"""
    print("\n🔍 Testing leads endpoints...")
    
    headers = {"X-User-Id": TEST_USER_ID}
    lead_id = None
    
    try:
        # Test 1: Create lead
        response = await client.post(f"{API_PREFIX}/leads", json=TEST_LEAD_DATA, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            lead_id = data.get("lead_id")
            results.add_result("Create Lead", True, response_data=data)
        else:
            results.add_result("Create Lead", False, f"Status code: {response.status_code}, Response: {response.text}")
            return
        
        # Test 2: Get all leads
        response = await client.get(f"{API_PREFIX}/leads", headers=headers)
        
        if response.status_code == 200:
            leads = response.json()
            if isinstance(leads, list) and len(leads) > 0:
                results.add_result("Get All Leads", True, f"Found {len(leads)} leads")
            else:
                results.add_result("Get All Leads", False, "No leads returned")
        else:
            results.add_result("Get All Leads", False, f"Status code: {response.status_code}")
        
        # Test 3: Get specific lead
        if lead_id:
            response = await client.get(f"/leads/{lead_id}", headers=headers)
            
            if response.status_code == 200:
                lead_data = response.json()
                if lead_data.get("name") == TEST_LEAD_DATA["name"]:
                    results.add_result("Get Specific Lead", True, response_data=lead_data)
                else:
                    results.add_result("Get Specific Lead", False, "Lead data mismatch")
            else:
                results.add_result("Get Specific Lead", False, f"Status code: {response.status_code}")
        
        # Test 4: Test without authentication header
        response = await client.get(f"{API_PREFIX}/leads")
        
        if response.status_code == 422:  # Validation error for missing header
            results.add_result("Authentication Required", True, "Properly rejected request without auth header")
        else:
            results.add_result("Authentication Required", False, f"Should reject unauthenticated requests, got {response.status_code}")
        
        # Test 5: Test with invalid UUID header
        invalid_headers = {"X-User-Id": "invalid-uuid"}
        response = await client.get(f"{API_PREFIX}/leads", headers=invalid_headers)
        
        if response.status_code == 401:
            results.add_result("Invalid UUID Rejection", True, "Properly rejected invalid UUID")
        else:
            results.add_result("Invalid UUID Rejection", False, f"Should reject invalid UUID, got {response.status_code}")
            
    except Exception as e:
        results.add_result("Leads Endpoints", False, str(e))
    
    return lead_id


async def test_conversations_endpoints(client: httpx.AsyncClient, results: APITestResults, lead_id: str):
    """Test conversations API endpoints"""
    print("\n🔍 Testing conversations endpoints...")
    
    if not lead_id:
        results.add_result("Conversations Test", False, "No lead_id available from previous test")
        return
    
    headers = {"X-User-Id": TEST_USER_ID}
    
    try:
        # Test 1: Add message to conversation
        message_data = {
            "lead_id": lead_id,
            "message": "This is a test message from the API test"
        }
        
        response = await client.post(f"{API_PREFIX}/messages", json=message_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            results.add_result("Add Message", True, response_data=data)
        else:
            results.add_result("Add Message", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        # Test 2: Get conversations for lead
        response = await client.get(f"/leads/{lead_id}/conversations", headers=headers)
        
        if response.status_code == 200:
            conversations = response.json()
            if isinstance(conversations, list) and len(conversations) >= 2:  # Initial + our test message
                results.add_result("Get Conversations", True, f"Found {len(conversations)} conversations")
            else:
                results.add_result("Get Conversations", False, f"Expected >= 2 conversations, got {len(conversations) if isinstance(conversations, list) else 'non-list'}")
        else:
            results.add_result("Get Conversations", False, f"Status code: {response.status_code}")
        
        # Test 3: Get conversations with lead info
        response = await client.get(f"/leads/{lead_id}/conversations-with-lead", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "lead" in data and "conversations" in data:
                results.add_result("Get Conversations with Lead Info", True, "Got lead and conversations data")
            else:
                results.add_result("Get Conversations with Lead Info", False, "Missing lead or conversations data")
        else:
            results.add_result("Get Conversations with Lead Info", False, f"Status code: {response.status_code}")
            
    except Exception as e:
        results.add_result("Conversations Endpoints", False, str(e))


async def test_inventory_endpoints(client: httpx.AsyncClient, results: APITestResults):
    """Test inventory API endpoints"""
    print("\n🔍 Testing inventory endpoints...")
    
    headers = {"X-User-Id": TEST_USER_ID}
    inventory_id = None
    
    try:
        # Test 1: Create inventory item
        response = await client.post(f"{API_PREFIX}/inventory", json=TEST_INVENTORY_DATA, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            inventory_id = data.get("id")
            results.add_result("Create Inventory", True, response_data=data)
        else:
            results.add_result("Create Inventory", False, f"Status code: {response.status_code}, Response: {response.text}")
            return
        
        # Test 2: Get all inventory for dealership
        response = await client.get(f"{API_PREFIX}/inventory", headers=headers)
        
        if response.status_code == 200:
            inventory_items = response.json()
            if isinstance(inventory_items, list) and len(inventory_items) > 0:
                results.add_result("Get All Inventory", True, f"Found {len(inventory_items)} items")
            else:
                results.add_result("Get All Inventory", False, "No inventory items returned")
        else:
            results.add_result("Get All Inventory", False, f"Status code: {response.status_code}")
        
        # Test 3: Get specific inventory item
        if inventory_id:
            response = await client.get(f"/inventory/{inventory_id}", headers=headers)
            
            if response.status_code == 200:
                item_data = response.json()
                if item_data.get("make") == TEST_INVENTORY_DATA["make"]:
                    results.add_result("Get Specific Inventory", True, response_data=item_data)
                else:
                    results.add_result("Get Specific Inventory", False, "Inventory data mismatch")
            else:
                results.add_result("Get Specific Inventory", False, f"Status code: {response.status_code}")
        
        # Test 4: Update inventory item
        if inventory_id:
            update_data = {"price": "67000.00", "mileage": 6000}
            response = await client.put(f"/inventory/{inventory_id}", json=update_data, headers=headers)
            
            if response.status_code == 200:
                updated_data = response.json()
                if updated_data.get("price") == "67000.00":
                    results.add_result("Update Inventory", True, "Successfully updated inventory")
                else:
                    results.add_result("Update Inventory", False, "Update data not reflected")
            else:
                results.add_result("Update Inventory", False, f"Status code: {response.status_code}")
        
        # Test 5: Delete inventory item
        if inventory_id:
            response = await client.delete(f"/inventory/{inventory_id}", headers=headers)
            
            if response.status_code == 200:
                results.add_result("Delete Inventory", True, "Successfully deleted inventory")
            else:
                results.add_result("Delete Inventory", False, f"Status code: {response.status_code}")
            
    except Exception as e:
        results.add_result("Inventory Endpoints", False, str(e))


async def test_cross_user_access(client: httpx.AsyncClient, results: APITestResults, lead_id: str):
    """Test that users cannot access other users' data"""
    print("\n🔍 Testing cross-user access restrictions...")
    
    if not lead_id:
        results.add_result("Cross-User Access Test", False, "No lead_id available")
        return
    
    # Use a different user ID
    other_user_id = str(uuid.uuid4())
    other_headers = {"X-User-Id": other_user_id}
    
    try:
        # Test 1: Try to access another user's lead
        response = await client.get(f"/leads/{lead_id}", headers=other_headers)
        
        if response.status_code == 403:
            results.add_result("Cross-User Lead Access Denied", True, "Properly denied access to other user's lead")
        elif response.status_code == 404:
            results.add_result("Cross-User Lead Access Denied", True, "Lead not found for other user (RLS working)")
        else:
            results.add_result("Cross-User Lead Access Denied", False, f"Should deny access, got {response.status_code}")
        
        # Test 2: Try to add message to another user's lead
        message_data = {
            "lead_id": lead_id,
            "message": "Trying to access another user's lead"
        }
        
        response = await client.post(f"{API_PREFIX}/messages", json=message_data, headers=other_headers)
        
        if response.status_code in [403, 404]:
            results.add_result("Cross-User Message Access Denied", True, "Properly denied message access")
        else:
            results.add_result("Cross-User Message Access Denied", False, f"Should deny access, got {response.status_code}")
            
    except Exception as e:
        results.add_result("Cross-User Access Test", False, str(e))


async def main():
    """Run all API endpoint tests"""
    print("🚀 Starting API Endpoint Tests...")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}\n")
    
    # Load environment variables
    load_dotenv()
    
    results = APITestResults()
    
    # Create HTTP client
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Test if server is running
        try:
            response = await client.get(f"{API_PREFIX}/health")
            print(f"✅ Server is running (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Server is not running or not accessible: {e}")
            print("Make sure to start your FastAPI server with: uvicorn src.maqro_backend.main:app --reload")
            return False
        
        # Run all tests
        await test_health_endpoint(client, results)
        lead_id = await test_leads_endpoints(client, results)
        await test_conversations_endpoints(client, results, lead_id)
        await test_inventory_endpoints(client, results)
        await test_cross_user_access(client, results, lead_id)
    
    # Print summary
    results.print_summary()
    
    return results.failed == 0


if __name__ == "__main__":
    print("📋 API Endpoint Test Instructions:")
    print("1. Make sure your FastAPI server is running:")
    print("   uvicorn src.maqro_backend.main:app --reload")
    print("2. Make sure your .env file is configured with Supabase credentials")
    print("3. Run this test script")
    print()
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 All API tests passed! Your Supabase integration is working correctly.")
    else:
        print("\n💥 Some API tests failed. Check the output above for details.")
    
    exit(0 if success else 1)