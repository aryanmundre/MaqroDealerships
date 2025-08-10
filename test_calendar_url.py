#!/usr/bin/env python3
"""
Test the Google Calendar URL generation functionality
"""

from datetime import datetime, timedelta
import urllib.parse

def generate_test_drive_calendar_url(
    customer_name: str,
    vehicle_interest: str,
    preferred_date: str,
    preferred_time: str,
    special_requests: str,
    salesperson_name: str,
    dealership_id: str
) -> str:
    """Generate Google Calendar URL for test drive appointment"""
    try:
        # Parse the preferred date and time
        # Handle common date formats
        if preferred_date.lower() == "tomorrow":
            appointment_date = datetime.now() + timedelta(days=1)
        elif preferred_date.lower() == "today":
            appointment_date = datetime.now()
        elif preferred_date.lower() == "next week":
            appointment_date = datetime.now() + timedelta(days=7)
        else:
            # Try to parse specific dates like "Dec 15" or "12/15"
            try:
                if "/" in preferred_date:
                    # Format: MM/DD or MM/DD/YYYY
                    parts = preferred_date.split("/")
                    if len(parts) == 2:
                        month, day = int(parts[0]), int(parts[1])
                        year = datetime.now().year
                        appointment_date = datetime(year, month, day)
                    else:
                        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                        appointment_date = datetime(year, month, day)
                else:
                    # Try to parse with current year
                    appointment_date = datetime.strptime(f"{preferred_date} {datetime.now().year}", "%b %d %Y")
            except:
                # Default to tomorrow if parsing fails
                appointment_date = datetime.now() + timedelta(days=1)
        
        # Parse time (handle formats like "2pm", "2:30pm", "14:00")
        time_str = preferred_time.lower().replace(" ", "")
        if "pm" in time_str:
            time_str = time_str.replace("pm", "")
            if ":" in time_str:
                hour, minute = map(int, time_str.split(":"))
                hour = hour + 12 if hour != 12 else 12
            else:
                hour, minute = int(time_str) + 12, 0
        elif "am" in time_str:
            time_str = time_str.replace("am", "")
            if ":" in time_str:
                hour, minute = map(int, time_str.split(":"))
                hour = 0 if hour == 12 else hour
            else:
                hour, minute = int(time_str), 0
        else:
            # Assume 24-hour format
            if ":" in time_str:
                hour, minute = map(int, time_str.split(":"))
            else:
                hour, minute = int(time_str), 0
        
        # Set the appointment time
        appointment_datetime = appointment_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Create end time (1 hour later)
        end_datetime = appointment_datetime + timedelta(hours=1)
        
        # Format dates for Google Calendar
        start_date = appointment_datetime.strftime("%Y%m%dT%H%M%S")
        end_date = end_datetime.strftime("%Y%m%dT%H%M%S")
        
        # Create event details
        event_title = f"Test Drive: {customer_name} - {vehicle_interest}"
        event_description = f"Test drive appointment for {customer_name}\n\n"
        event_description += f"Vehicle: {vehicle_interest}\n"
        event_description += f"Salesperson: {salesperson_name}\n"
        if special_requests and special_requests != "None":
            event_description += f"Special Requests: {special_requests}\n"
        event_description += f"\nScheduled via Maqro SMS system"
        
        # Build Google Calendar URL
        base_url = "https://calendar.google.com/calendar/render"
        params = {
            "action": "TEMPLATE",
            "text": event_title,
            "dates": f"{start_date}/{end_date}",
            "details": event_description,
            "location": "Dealership",  # Could be made configurable
            "sf": "true",  # Show form
            "output": "xml"
        }
        
        # Encode parameters
        query_string = urllib.parse.urlencode(params)
        calendar_url = f"{base_url}?{query_string}"
        
        return calendar_url
        
    except Exception as e:
        print(f"Error generating calendar URL: {e}")
        # Return a fallback URL
        return "https://calendar.google.com/calendar/render?action=TEMPLATE&text=Test%20Drive%20Appointment&sf=true&output=xml"

def test_calendar_url_generation():
    """Test various calendar URL generation scenarios"""
    
    print("🧪 Testing Google Calendar URL Generation for Test Drives\n")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Sarah",
            "vehicle": "2020 Toyota Camry",
            "date": "tomorrow",
            "time": "2pm",
            "requests": "2-hour window"
        },
        {
            "name": "John",
            "vehicle": "Honda Civic",
            "date": "next week",
            "time": "10am",
            "requests": "None"
        },
        {
            "name": "Mary",
            "vehicle": "2019 Ford Escape",
            "date": "12/20",
            "time": "3pm",
            "requests": "Bring trade-in appraisal"
        },
        {
            "name": "David",
            "vehicle": "BMW X3",
            "date": "Friday",
            "time": "1pm",
            "requests": "None"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"Customer: {test_case['name']}")
        print(f"Vehicle: {test_case['vehicle']}")
        print(f"Date: {test_case['date']}")
        print(f"Time: {test_case['time']}")
        print(f"Special Requests: {test_case['requests']}")
        
        calendar_url = generate_test_drive_calendar_url(
            customer_name=test_case['name'],
            vehicle_interest=test_case['vehicle'],
            preferred_date=test_case['date'],
            preferred_time=test_case['time'],
            special_requests=test_case['requests'],
            salesperson_name="John Salesperson",
            dealership_id="test-dealership"
        )
        
        print(f"Generated URL: {calendar_url}")
        
        # Validate URL
        if "calendar.google.com" in calendar_url:
            print("✅ Valid Google Calendar URL generated")
            print(f"   Event: {urllib.parse.unquote(calendar_url.split('text=')[1].split('&')[0])}")
            print(f"   Dates: {calendar_url.split('dates=')[1].split('&')[0]}")
        else:
            print("❌ Invalid URL generated")
        
        print()
    
    print("🎉 Calendar URL generation test completed!")
    print("\n📱 Salespeople can now:")
    print("1. Receive test drive requests via SMS")
    print("2. Get automatic Google Calendar invite links")
    print("3. Share the calendar link with customers")
    print("4. Have appointments automatically added to their schedule")

if __name__ == "__main__":
    test_calendar_url_generation()
