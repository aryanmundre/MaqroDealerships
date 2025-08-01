#!/usr/bin/env python3
"""
Test Runner for Supabase Integration

This script runs all tests in the correct order:
1. Database schema verification
2. Database connection and CRUD tests
3. API endpoint tests
"""
import asyncio
import subprocess
import sys
from pathlib import Path


def run_test_script(script_name: str, description: str) -> bool:
    """Run a test script and return success status"""
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING: {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True)
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ {description} - PASSED")
        else:
            print(f"\n❌ {description} - FAILED")
        
        return success
        
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all test scripts"""
    print("🚀 SUPABASE INTEGRATION TEST SUITE")
    print("🔍 Running comprehensive tests for your Supabase backend integration")
    print(f"📁 Working directory: {Path.cwd()}")
    
    # Check if test files exist
    test_files = [
        ("test_database_schema.py", "Database Schema Verification"),
        ("test_supabase_integration.py", "Database Connection & CRUD Tests"),
        ("test_api_endpoints.py", "API Endpoint Tests")
    ]
    
    missing_files = []
    for file_name, _ in test_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n❌ Missing test files: {missing_files}")
        print("Make sure all test files are in the current directory.")
        return False
    
    # Run tests in order
    results = []
    
    for script_name, description in test_files:
        success = run_test_script(script_name, description)
        results.append((description, success))
        
        # If a critical test fails, ask if we should continue
        if not success and script_name in ["test_database_schema.py", "test_supabase_integration.py"]:
            print(f"\n⚠️  Critical test failed: {description}")
            response = input("Continue with remaining tests? (y/n): ").lower().strip()
            if response != 'y':
                break
    
    # Final summary
    print(f"\n{'='*80}")
    print("🎯 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your Supabase integration is working perfectly!")
        print("\nNext steps:")
        print("1. Your backend is ready for production")
        print("2. Update your frontend to use the new UUID-based endpoints")
        print("3. Add proper JWT authentication to replace the X-User-Id header")
    else:
        print(f"\n💥 {total - passed} test suite(s) failed.")
        print("\nTroubleshooting steps:")
        print("1. Check your .env file configuration")
        print("2. Verify your Supabase database is accessible")
        print("3. Make sure your FastAPI server is running for API tests")
        print("4. Check the detailed error messages above")
    
    return passed == total


if __name__ == "__main__":
    print("📋 Pre-flight checklist:")
    print("✓ Make sure your .env file is configured with Supabase credentials")
    print("✓ For API tests: Start your server with 'uvicorn src.maqro_backend.main:app --reload'")
    print("✓ Make sure you have run the SQL schema from frontend/supabase/schema.sql")
    print()
    
    input("Press Enter to start the test suite...")
    
    success = main()
    
    if success:
        print("\n🚀 Your Supabase integration is ready!")
    else:
        print("\n🔧 Please fix the issues above and run the tests again.")
    
    sys.exit(0 if success else 1)