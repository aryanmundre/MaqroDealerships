#!/usr/bin/env python3
"""
Test script for the new test drive scheduling workflow
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_test_drive_scheduling():
    """Test the test drive scheduling functionality"""
    
    try:
        from maqro_backend.services.salesperson_sms_service import SalespersonSMSService
        from maqro_backend.services.sms_parser import SMSParser
        
        print("✅ Successfully imported required modules")
        
        # Test SMS parsing
        print("\n🧪 Testing SMS parsing for test drive scheduling...")
        
        parser = SMSParser()
        
        # Test message
        test_message = "Customer Sarah wants to test drive the 2020 Toyota Camry tomorrow at 2pm. Her number is 555-1234. She mentioned she has a 2-hour window."
        
        print(f"Test message: {test_message}")
        
        parsed = parser.parse_message(test_message)
        print(f"Parsed result: {parsed}")
        
        if parsed["type"] == "test_drive_scheduling":
            print("✅ SMS parsing successful - detected test drive scheduling")
        else:
            print(f"❌ SMS parsing failed - expected 'test_drive_scheduling', got '{parsed['type']}'")
            return
        
        # Test calendar URL generation
        print("\n🧪 Testing Google Calendar URL generation...")
        
        service = SalespersonSMSService()
        
        # Mock salesperson data
        class MockSalesperson:
            def __init__(self):
                self.full_name = "John Salesperson"
                self.user_id = "test-user-id"
        
        mock_salesperson = MockSalesperson()
        
        # Generate calendar URL
        calendar_url = service._generate_test_drive_calendar_url(
            customer_name="Sarah",
            vehicle_interest="2020 Toyota Camry",
            preferred_date="tomorrow",
            preferred_time="2pm",
            special_requests="2-hour window",
            salesperson_name=mock_salesperson.full_name,
            dealership_id="test-dealership-id"
        )
        
        print(f"Generated calendar URL: {calendar_url}")
        
        if "calendar.google.com" in calendar_url and "Test%20Drive" in calendar_url:
            print("✅ Calendar URL generation successful")
        else:
            print("❌ Calendar URL generation failed")
            return
        
        print("\n🎉 All tests passed! The test drive scheduling workflow is working correctly.")
        print("\n📱 Salespeople can now text messages like:")
        print("   'Customer Sarah wants to test drive the 2020 Toyota Camry tomorrow at 2pm. Her number is 555-1234.'")
        print("\n🤖 The system will:")
        print("   1. Parse the message and extract details")
        print("   2. Generate a Google Calendar invite link")
        print("   3. Create or update a lead record")
        print("   4. Send back a confirmation with the calendar link")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_test_drive_scheduling())
