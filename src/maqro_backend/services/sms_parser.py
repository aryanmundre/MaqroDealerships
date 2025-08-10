"""
SMS Parser Service for extracting structured data from salesperson messages using LLM
"""
import re
import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import os

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


class SMSParser:
    """Service for parsing SMS messages and extracting structured data using LLM"""
    
    def __init__(self):
        """Initialize SMS parser with LLM"""
        if openai is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency
        
        # System prompt for the LLM
        self.system_prompt = """You are an SMS parser for a car dealership. Your job is to extract structured data from salesperson messages and classify the message type.

Extract information for these message types:

1. LEAD CREATION: When a salesperson meets a potential customer
   - Extract: name, phone, email, car_interest, price_range, source
   - Example: "I just met John. His number is 555-1234 and his email is john@email.com. He is interested in a Toyota Camry in the price range of $25K. I met him at the dealership."

2. INVENTORY UPDATE: When a salesperson adds a new vehicle
   - Extract: year, make, model, mileage, condition, price, description, features
   - Example: "I just picked up a 2020 Toyota Camry off auction. It has 45,000 miles. It is in excellent condition. Add it to the inventory."

3. LEAD_INQUIRY: When a salesperson asks about existing leads
   - Extract: lead_identifier (name, phone, or ID), inquiry_type (status, details, follow_up)
   - Example: "What's the status of lead John Smith?" or "Check details for lead #123"

4. INVENTORY_INQUIRY: When a salesperson asks about inventory
   - Extract: search_criteria (make, model, year, price_range), inquiry_type (availability, details, search)
   - Example: "Do we have any Honda Civics in stock?" or "What's the price of the 2020 Camry?"

5. GENERAL_QUESTION: When a salesperson asks general questions
   - Extract: question_topic (schedule, help, information), urgency (high, medium, low)
   - Example: "What's my schedule today?" or "I need help with a customer"

6. STATUS_UPDATE: When a salesperson provides updates on existing leads/opportunities
   - Extract: lead_identifier, update_type (progress, outcome, next_steps), details
   - Example: "Lead John Smith is coming in for test drive tomorrow" or "Customer #123 decided to go with the Honda"

7. TEST_DRIVE_SCHEDULING: When a salesperson receives a text about scheduling a test drive
   - Extract: customer_name, customer_phone, vehicle_interest, preferred_date, preferred_time, special_requests
   - Example: "Customer Sarah wants to test drive the 2020 Toyota Camry tomorrow at 2pm. Her number is 555-1234. She mentioned she has a 2-hour window."

Return ONLY a valid JSON object with the extracted data. If you can't extract certain fields, use null. Always include a "type" field indicating the message type.

For lead creation, the JSON should look like:
{
  "type": "lead_creation",
  "name": "John Doe",
  "phone": "+15551234",
  "email": "john@email.com",
  "car_interest": "Toyota Camry",
  "price_range": "25000",
  "source": "SMS Lead Creation"
}

For inventory updates, the JSON should look like:
{
  "type": "inventory_update",
  "year": 2020,
  "make": "Toyota",
  "model": "Camry",
  "mileage": 45000,
  "condition": "excellent",
  "price": null,
  "description": "excellent condition 2020 Toyota Camry",
  "features": "Condition: excellent"
}

For lead inquiries, the JSON should look like:
{
  "type": "lead_inquiry",
  "lead_identifier": "John Smith",
  "inquiry_type": "status",
  "search_by": "name"
}

For inventory inquiries, the JSON should look like:
{
  "type": "inventory_inquiry",
  "search_criteria": {
    "make": "Honda",
    "model": "Civic",
    "year": null,
    "price_range": null
  },
  "inquiry_type": "availability"
}

For general questions, the JSON should look like:
{
  "type": "general_question",
  "question_topic": "schedule",
  "urgency": "medium",
  "details": "What's my schedule today?"
}

For status updates, the JSON should look like:
{
  "type": "status_update",
  "lead_identifier": "John Smith",
  "update_type": "progress",
  "details": "Coming in for test drive tomorrow"
}

For test drive scheduling, the JSON should look like:
{
  "type": "test_drive_scheduling",
  "customer_name": "Sarah Johnson",
  "customer_phone": "555-1234",
  "vehicle_interest": "2020 Toyota Camry",
  "preferred_date": "tomorrow",
  "preferred_time": "2pm",
  "special_requests": "2-hour window"
}"""

    def parse_message(self, message: str) -> Dict[str, Any]:
        """
        Parse SMS message using LLM to determine if it's a lead creation or inventory update
        
        Args:
            message: Raw SMS message text
            
        Returns:
            Dict with parsed data and message type
        """
        message = message.strip()
        
        try:
            # Use LLM to parse the message
            parsed_data = self._parse_with_llm(message)
            
            if parsed_data and "type" in parsed_data:
                # Determine confidence based on extracted data quality
                confidence = self._assess_confidence(parsed_data)
                
                return {
                    "type": parsed_data["type"],
                    "data": parsed_data,
                    "confidence": confidence
                }
            else:
                return {
                    "type": "unknown",
                    "data": {},
                    "confidence": "low"
                }
                
        except Exception as e:
            logger.error(f"Error parsing message with LLM: {e}")
            # Fallback to basic pattern matching if LLM fails
            return self._fallback_parse(message)
    
    def _parse_with_llm(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse message using OpenAI chat completions"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Parse this SMS message: {message}"}
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting if present
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0]
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0]
                
                parsed_data = json.loads(content)
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _assess_confidence(self, parsed_data: Dict[str, Any]) -> str:
        """Assess confidence level based on extracted data quality"""
        if parsed_data["type"] == "lead_creation":
            required_fields = ["name", "phone", "car_interest"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            elif extracted_fields >= 2:
                return "medium"
            else:
                return "low"
                
        elif parsed_data["type"] == "inventory_update":
            required_fields = ["year", "make", "model"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            elif extracted_fields >= 2:
                return "medium"
            else:
                return "low"
        
        elif parsed_data["type"] == "lead_inquiry":
            required_fields = ["lead_identifier", "inquiry_type"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            elif extracted_fields >= 1:
                return "medium"
            else:
                return "low"
        
        elif parsed_data["type"] == "inventory_inquiry":
            required_fields = ["inquiry_type"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            else:
                return "medium"
        
        elif parsed_data["type"] == "general_question":
            required_fields = ["question_topic"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            else:
                return "medium"
        
        elif parsed_data["type"] == "status_update":
            required_fields = ["lead_identifier", "update_type"]
            extracted_fields = sum(1 for field in required_fields if parsed_data.get(field))
            
            if extracted_fields == len(required_fields):
                return "high"
            elif extracted_fields >= 1:
                return "medium"
            else:
                return "low"
        
        return "low"
    
    def _fallback_parse(self, message: str) -> Dict[str, Any]:
        """Fallback parsing using basic pattern matching if LLM fails"""
        message_lower = message.lower()
        
        # Simple keyword-based fallback for different message types
        if any(word in message_lower for word in ["met", "lead", "customer", "prospect"]):
            return {
                "type": "lead_creation",
                "data": {
                    "name": "Unknown",
                    "phone": None,
                    "email": None,
                    "car_interest": "Unknown",
                    "price_range": None,
                    "source": "SMS Lead Creation (Fallback)"
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["picked up", "inventory", "vehicle", "car", "add"]):
            return {
                "type": "inventory_update",
                "data": {
                    "year": None,
                    "make": "Unknown",
                    "model": "Unknown",
                    "mileage": None,
                    "condition": "Unknown",
                    "price": None,
                    "description": "Vehicle from SMS",
                    "features": "Unknown condition"
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["status", "check", "details", "lead", "customer"]) and any(word in message_lower for word in ["what", "how", "?"]):
            return {
                "type": "lead_inquiry",
                "data": {
                    "lead_identifier": "Unknown",
                    "inquiry_type": "status",
                    "search_by": "unknown"
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["stock", "available", "have", "price"]) and any(word in message_lower for word in ["what", "how", "?"]):
            return {
                "type": "inventory_inquiry",
                "data": {
                    "search_criteria": {
                        "make": "Unknown",
                        "model": "Unknown",
                        "year": None,
                        "price_range": None
                    },
                    "inquiry_type": "availability"
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["schedule", "help", "need", "question"]) or "?" in message:
            return {
                "type": "general_question",
                "data": {
                    "question_topic": "general",
                    "urgency": "medium",
                    "details": message
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["update", "progress", "coming", "decided", "test drive"]):
            return {
                "type": "status_update",
                "data": {
                    "lead_identifier": "Unknown",
                    "update_type": "progress",
                    "details": message
                },
                "confidence": "low"
            }
        elif any(word in message_lower for word in ["test drive", "schedule", "appointment"]) and any(word in message_lower for word in ["customer", "wants", "interested"]):
            return {
                "type": "test_drive_scheduling",
                "data": {
                    "customer_name": "Unknown",
                    "customer_phone": "Unknown",
                    "vehicle_interest": "Unknown",
                    "preferred_date": "Unknown",
                    "preferred_time": "Unknown",
                    "special_requests": "None"
                },
                "confidence": "low"
            }
        
        return {
            "type": "unknown",
            "data": {},
            "confidence": "low"
        }
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and normalize phone number"""
        if not phone:
            return None
            
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif len(digits) > 11:
            # International number, keep as is
            return f"+{digits}"
        else:
            # Return as is if can't parse
            return phone.strip()
    
    def _parse_price(self, price_str: str) -> Optional[str]:
        """Parse price string and return standardized format"""
        if not price_str:
            return None
        
        # Remove common characters
        clean_price = price_str.replace('$', '').replace(',', '').strip()
        
        # Handle K notation (thousands)
        if clean_price.upper().endswith('K'):
            try:
                value = float(clean_price[:-1]) * 1000
                return f"{value:.0f}"
            except ValueError:
                return clean_price
        
        # Try to parse as number
        try:
            value = float(clean_price)
            return f"{value:.0f}"
        except ValueError:
            return clean_price
    
    def _parse_mileage(self, mileage_str: str) -> Optional[int]:
        """Parse mileage string and return integer"""
        if not mileage_str:
            return None
        
        try:
            # Remove commas and convert to int
            clean_mileage = mileage_str.replace(',', '')
            return int(clean_mileage)
        except ValueError:
            return None


# Global instance
sms_parser = SMSParser()
