#!/usr/bin/env python3
"""
Simple test for the SMS parser test drive scheduling functionality
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_sms_parser():
    """Test the SMS parser for test drive scheduling"""
    
    try:
        from maqro_backend.services.sms_parser import SMSParser
        
        print("✅ Successfully imported SMS parser")
        
        # Test SMS parsing
        print("\n🧪 Testing SMS parsing for test drive scheduling...")
        
        parser = SMSParser()
        
        # Test messages
        test_messages = [
            "Customer Sarah wants to test drive the 2020 Toyota Camry tomorrow at 2pm. Her number is 555-1234. She mentioned she has a 2-hour window.",
            "John wants to test drive a Honda Civic next week at 10am. Phone: 555-9876",
            "Test drive request: Mary Johnson - 555-1111 - interested in 2019 Ford Escape - tomorrow 3pm",
            "Customer wants to schedule test drive for BMW X3. Available Friday at 1pm. Contact: 555-2222"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test Message {i} ---")
            print(f"Message: {message}")
            
            parsed = parser.parse_message(message)
            print(f"Parsed type: {parsed.get('type', 'unknown')}")
            
            if parsed.get('type') == 'test_drive_scheduling':
                print("✅ Correctly identified as test drive scheduling")
                data = parsed.get('data', {})
                print(f"Customer: {data.get('customer_name', 'Unknown')}")
                print(f"Vehicle: {data.get('vehicle_interest', 'Unknown')}")
                print(f"Date: {data.get('preferred_date', 'Unknown')}")
                print(f"Time: {data.get('preferred_time', 'Unknown')}")
            else:
                print(f"❌ Expected 'test_drive_scheduling', got '{parsed.get('type', 'unknown')}'")
        
        print("\n🎉 SMS Parser test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This might be due to missing dependencies. Try activating the virtual environment:")
        print("source venv/bin/activate")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sms_parser()
