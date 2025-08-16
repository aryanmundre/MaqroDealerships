# SMS Features for Dealership Management

This document describes the new LLM-powered SMS features that allow salespeople to create leads and update inventory by simply texting the Vonage number.

## Overview

The system now automatically detects when a salesperson sends an SMS and processes it for either:
1. **Lead Creation** - Creating new customer leads with contact information and preferences
2. **Inventory Updates** - Adding new vehicles to the dealership inventory

## How It Works

1. Salesperson texts the Vonage number with structured information
2. System automatically identifies the sender as a salesperson (by phone number)
3. LLM-powered parser extracts structured data from the message
4. Data is stored in the Supabase database
5. Confirmation message is sent back to the salesperson

## Lead Creation

### Message Format Examples

**Standard Format:**
```
I just met Anna Johnson. Her number is 555-123-4567 and her email is anna@gmail.com. she is interested in subarus in the price range of $10K. I met her at the dealership.
```

**Alternative Format:**
```
Met John Smith today. Phone: (555) 987-6543, Email: john@email.com. Interested in Honda Civic around $15K
```

**Dash-Separated Format:**
```
New lead: Sarah Wilson - 555-111-2222 - sarah@test.com - Toyota Camry - $12K
```

### Required Information
- **Name**: Customer's full name
- **Phone**: Contact phone number
- **Email**: Email address (optional but recommended)
- **Car Interest**: What type of vehicle they're interested in
- **Price Range**: Budget range (e.g., $10K, $25K, $50K)

### What Happens
1. Lead is created in the database
2. Lead is automatically assigned to the salesperson who sent the message
3. Source is marked as "SMS Lead Creation"
4. Initial message includes context about the interaction
5. Confirmation message sent back with lead details and ID

## Inventory Updates

### Message Format Examples

**Standard Format:**
```
I just picked up a 2006 Toyota Camry off facebook marketplace. It has 123456 miles. It is in good condition. Add it to the inventory
```

**Alternative Format:**
```
New inventory: 2018 Honda Civic - 45000 miles - excellent - $18K
```

**Comma-Separated Format:**
```
Add vehicle: 2015 Ford F-150, 75000 miles, good, $22K
```

### Required Information
- **Year**: Vehicle model year
- **Make**: Vehicle manufacturer (Toyota, Honda, Ford, etc.)
- **Model**: Vehicle model name
- **Mileage**: Current mileage (optional but recommended)
- **Condition**: Vehicle condition (good, excellent, fair, etc.)
- **Price**: Purchase price (optional - can be TBD)

### What Happens
1. Vehicle is added to inventory database
2. Status is set to "active"
3. Description and features are auto-generated
4. Price is set to "TBD" if not specified
5. Confirmation message sent back with vehicle details and inventory ID

## Smart Parsing Features

### Pattern Recognition
The system uses multiple regex patterns to extract information from various message formats.

### Fuzzy Parsing
When exact patterns don't match, the system uses intelligent parsing to extract:
- Names (capitalized words)
- Phone numbers (various formats)
- Email addresses
- Vehicle information
- Price ranges

### Confidence Scoring
Each parsed message gets a confidence score:
- **High**: Exact pattern match
- **Medium**: Fuzzy parsing successful
- **Low**: Unable to parse

### Phone Number Normalization
- Automatically formats phone numbers to international format
- Handles various input formats: (555) 123-4567, 555.123.4567, 5551234567
- Adds country code if missing

### Price Parsing
- Handles dollar amounts with or without $ symbol
- Converts K notation (10K = $10,000)
- Removes commas and formatting

## Setup Requirements

### 1. Salesperson Registration
Salespeople must have user profiles with:
- Phone numbers registered in the system
- Role set to "salesperson"
- Associated with the correct dealership

### 2. Vonage Configuration
- Vonage webhook endpoint configured
- Phone number set up for receiving SMS
- API credentials configured

### 3. Database Schema
- Leads table with required fields
- Inventory table with required fields
- User profiles table with phone numbers
- Conversations table for logging

## Error Handling

### Salesperson Not Found
If a phone number isn't registered as a salesperson:
```
Your phone number is not registered as a salesperson. Please contact your manager.
```

### Invalid Message Format
If the message can't be parsed:
```
I couldn't understand your message. Please use one of these formats:

For new leads: 'I just met [Name]. Her number is [Phone] and her email is [Email]. She is interested in [Car] in the price range of [Price]. I met her at the dealership.'

For inventory: 'I just picked up a [Year] [Make] [Model] off [Source]. It has [Mileage] miles. It is in [Condition] condition. Add it to the inventory.'
```

### Missing Required Fields
If essential information is missing:
```
Please provide both name and phone number for the lead.
```

## Testing

Run the test script to see examples:
```bash
python test_sms_parser.py
```

This will demonstrate various message formats and parsing results.

## Security Features

- Phone number validation
- Salesperson authentication via user profiles
- Dealership isolation (salespeople can only access their dealership data)
- Input sanitization and validation

## Benefits

1. **Efficiency**: Salespeople can create leads and update inventory on the go
2. **Accuracy**: Structured data extraction reduces manual entry errors
3. **Speed**: Instant processing and confirmation
4. **Integration**: Seamlessly integrates with existing CRM and inventory systems
5. **Audit Trail**: All actions are logged with timestamps and user attribution

## Future Enhancements

- Voice-to-text support
- Image processing for vehicle photos
- Advanced natural language processing
- Integration with calendar for scheduling follow-ups
- Automated follow-up reminders
- Performance analytics and reporting

## Support

For technical support or questions about these features, contact the development team or refer to the API documentation.
