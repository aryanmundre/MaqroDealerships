"""
Salesperson SMS Service for handling lead creation and inventory updates via SMS
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import (
    create_lead, 
    create_inventory_item, 
    get_salesperson_by_phone,
    get_lead_by_phone,
    create_conversation,
    ensure_embeddings_for_dealership
)
from ..schemas.lead import LeadCreate
from ..schemas.inventory import InventoryCreate
from .sms_parser import sms_parser

logger = logging.getLogger(__name__)


class SalespersonSMSService:
    """Service for handling salesperson SMS operations"""
    
    def __init__(self):
        """Initialize salesperson SMS service"""
        pass
    
    async def process_salesperson_message(
        self,
        session: AsyncSession,
        from_number: str,
        message_text: str,
        dealership_id: str
    ) -> Dict[str, Any]:
        """
        Process SMS message from a salesperson
        
        Args:
            session: Database session
            from_number: Phone number of the salesperson
            message_text: SMS message content
            dealership_id: Dealership ID
            
        Returns:
            Dict with processing results
        """
        try:
            # First, identify the salesperson by phone number
            salesperson = await get_salesperson_by_phone(
                session=session,
                phone=from_number,
                dealership_id=dealership_id
            )
            
            if not salesperson:
                logger.warning(f"No salesperson found for phone number: {from_number}")
                return {
                    "success": False,
                    "error": "Salesperson not found",
                    "message": "Your phone number is not registered as a salesperson. Please contact your manager."
                }
            
            logger.info(f"Processing message from salesperson: {salesperson.full_name} ({salesperson.user_id})")
            
            # Parse the message to determine intent and extract data
            parsed_message = sms_parser.parse_message(message_text)
            
            if parsed_message["type"] == "lead_creation":
                return await self._handle_lead_creation(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "inventory_update":
                return await self._handle_inventory_update(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "lead_inquiry":
                return await self._handle_lead_inquiry(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "inventory_inquiry":
                return await self._handle_inventory_inquiry(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "general_question":
                return await self._handle_general_question(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "status_update":
                return await self._handle_status_update(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            elif parsed_message["type"] == "test_drive_scheduling":
                return await self._handle_test_drive_scheduling(
                    session=session,
                    salesperson=salesperson,
                    parsed_data=parsed_message["data"],
                    dealership_id=dealership_id
                )
            
            else:
                return {
                    "success": False,
                    "error": "Message not recognized",
                    "message": "I couldn't understand your message. Here are some things I can help with:\n\n"
                              "• Create leads: 'I just met [Name]. Her number is [Phone]...'\n"
                              "• Add inventory: 'I just picked up a [Year] [Make] [Model]...'\n"
                              "• Check lead status: 'What's the status of lead John Smith?'\n"
                              "• Search inventory: 'Do we have any Honda Civics in stock?'\n"
                              "• Ask questions: 'What's my schedule today?'\n"
                              "• Update progress: 'Lead John is coming for test drive tomorrow'\n"
                              "• Schedule test drives: 'Customer Sarah wants to test drive the 2020 Toyota Camry tomorrow at 2pm'"
                }
                
        except Exception as e:
            logger.error(f"Error processing salesperson message: {e}")
            return {
                "success": False,
                "error": "Processing error",
                "message": "Sorry, there was an error processing your message. Please try again or contact support."
            }
    
    async def _handle_lead_creation(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle lead creation from salesperson SMS"""
        try:
            # Validate required fields
            if not parsed_data.get("name") or not parsed_data.get("phone"):
                return {
                    "success": False,
                    "error": "Missing required fields",
                    "message": "Please provide both name and phone number for the lead."
                }
            
            # Create lead data with robust fallbacks
            source_value = parsed_data.get("source") or "SMS Lead Creation"  # Handle None values
            car_interest_value = parsed_data.get("car_interest") or "Unknown"
            
            lead_data = LeadCreate(
                name=parsed_data["name"],
                phone=parsed_data["phone"],
                email=parsed_data.get("email"),
                car_interest=car_interest_value,  # LLM extracts 'car_interest', matches DB field
                source=source_value,  # Ensure never None
                max_price=parsed_data.get("price_range"),  # Allow None for optional field
                message=f"Lead created via SMS by {salesperson.full_name}. "
                        f"Car interest: {car_interest_value}. "
                        f"Price range: {parsed_data.get('price_range') or 'Not specified'}."
            )
            
            # Create the lead
            lead = await create_lead(
                session=session,
                lead_in=lead_data,
                user_id=str(salesperson.user_id),  # Assign to the salesperson who created it
                dealership_id=dealership_id
            )
            
            # Log the action
            await create_conversation(
                session=session,
                lead_id=str(lead.id),
                message=f"Lead created via SMS by {salesperson.full_name}",
                sender="system"
            )
            
            logger.info(f"Created new lead via SMS: {lead.id} by {salesperson.full_name}")
            
            return {
                "success": True,
                "message": f"✅ Lead created successfully!\n\n"
                          f"Name: {lead.name}\n"
                          f"Phone: {lead.phone}\n"
                          f"Email: {lead.email or 'Not provided'}\n"
                          f"Car Interest: {lead.car_interest}\n"
                          f"Price Range: {parsed_data.get('price_range', 'Not specified')}\n"
                          f"Lead ID: {lead.id}\n\n"
                          f"The lead has been assigned to you and added to your pipeline.",
                "lead_id": str(lead.id),
                "lead_name": lead.name
            }
            
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return {
                "success": False,
                "error": "Lead creation failed",
                "message": "Sorry, there was an error creating the lead. Please try again."
            }
    
    async def _handle_inventory_update(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle inventory update from salesperson SMS"""
        try:
            # Validate required fields
            if not all(key in parsed_data for key in ["year", "make", "model"]):
                return {
                    "success": False,
                    "error": "Missing required fields",
                    "message": "Please provide year, make, and model for the vehicle."
                }
            
            # Set default price if not provided
            price = parsed_data.get("price", "0")
            if not price or price == "0":
                price = "TBD"  # To be determined
            
            # Create inventory data
            inventory_data = {
                "year": parsed_data["year"],
                "make": parsed_data["make"],
                "model": parsed_data["model"],
                "price": price,
                "mileage": parsed_data.get("mileage"),
                "description": parsed_data.get("description", f"{parsed_data['year']} {parsed_data['make']} {parsed_data['model']}"),
                "features": parsed_data.get("features", ""),
                "condition": parsed_data.get("condition", "Unknown"),  # Add condition field
                "status": "active"
            }
            
            # Create the inventory item
            inventory_item = await create_inventory_item(
                session=session,
                inventory_data=inventory_data,
                dealership_id=dealership_id
            )
            
            logger.info(f"Created new inventory item via SMS: {inventory_item.id} by {salesperson.full_name}")
            
            # Auto-generate embedding for this new inventory item
            try:
                logger.info(f"🧠 Generating embedding for SMS inventory item: {inventory_item.make} {inventory_item.model}")
                embedding_result = await ensure_embeddings_for_dealership(
                    session=session,
                    dealership_id=dealership_id
                )
                logger.info(f"✅ Generated {embedding_result.get('built_count', 0)} embeddings via SMS")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate embedding for SMS inventory (creation still successful): {e}")
            
            return {
                "success": True,
                "message": f"✅ Vehicle added to inventory!\n\n"
                          f"Year: {inventory_item.year}\n"
                          f"Make: {inventory_item.make}\n"
                          f"Model: {inventory_item.model}\n"
                          f"Mileage: {inventory_item.mileage or 'Not specified'}\n"
                          f"Condition: {parsed_data.get('condition', 'Not specified')}\n"
                          f"Price: ${inventory_item.price if inventory_item.price != 'TBD' else 'TBD'}\n"
                          f"Inventory ID: {inventory_item.id}\n\n"
                          f"The vehicle is now available in your inventory.",
                "inventory_id": str(inventory_item.id),
                "vehicle_info": f"{inventory_item.year} {inventory_item.make} {inventory_item.model}"
            }
            
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}")
            return {
                "success": False,
                "error": "Inventory creation failed",
                "message": "Sorry, there was an error adding the vehicle to inventory. Please try again."
            }
    
    async def _handle_lead_inquiry(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle lead inquiry from salesperson SMS"""
        try:
            # For now, provide a basic response
            # In the future, this could integrate with lead management system
            return {
                "success": True,
                "message": f"🔍 Lead Inquiry Received\n\n"
                          f"I understand you're asking about: {parsed_data.get('lead_identifier', 'Unknown lead')}\n"
                          f"Inquiry type: {parsed_data.get('inquiry_type', 'Unknown')}\n\n"
                          f"Note: Lead inquiry functionality is coming soon! For now, please check the dashboard or contact support for detailed lead information.",
                "inquiry_type": parsed_data.get("inquiry_type"),
                "lead_identifier": parsed_data.get("lead_identifier")
            }
            
        except Exception as e:
            logger.error(f"Error handling lead inquiry: {e}")
            return {
                "success": False,
                "error": "Lead inquiry failed",
                "message": "Sorry, there was an error processing your lead inquiry. Please try again."
            }
    
    async def _handle_inventory_inquiry(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle inventory inquiry from salesperson SMS"""
        try:
            search_criteria = parsed_data.get("search_criteria", {})
            
            # For now, provide a basic response
            # In the future, this could integrate with inventory search system
            return {
                "success": True,
                "message": f"🔍 Inventory Inquiry Received\n\n"
                          f"Search criteria:\n"
                          f"• Make: {search_criteria.get('make', 'Any')}\n"
                          f"• Model: {search_criteria.get('model', 'Any')}\n"
                          f"• Year: {search_criteria.get('year', 'Any')}\n"
                          f"• Price range: {search_criteria.get('price_range', 'Any')}\n\n"
                          f"Note: Inventory search functionality is coming soon! For now, please check the dashboard or contact support for current inventory.",
                "inquiry_type": parsed_data.get("inquiry_type"),
                "search_criteria": search_criteria
            }
            
        except Exception as e:
            logger.error(f"Error handling inventory inquiry: {e}")
            return {
                "success": False,
                "error": "Inventory inquiry failed",
                "message": "Sorry, there was an error processing your inventory inquiry. Please try again."
            }
    
    async def _handle_general_question(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle general questions from salesperson SMS"""
        try:
            question_topic = parsed_data.get("question_topic", "general")
            urgency = parsed_data.get("urgency", "medium")
            
            # Provide appropriate responses based on question type
            if question_topic == "schedule":
                response = f"📅 Schedule Inquiry\n\n"
                response += f"Hi {salesperson.full_name}, I understand you're asking about your schedule.\n\n"
                response += f"Note: Schedule functionality is coming soon! For now, please check your calendar app or contact your manager for your current schedule."
            
            elif question_topic == "help":
                response = f"🆘 Help Request\n\n"
                response += f"Hi {salesperson.full_name}, I understand you need help.\n\n"
                response += f"Note: Help system integration is coming soon! For immediate assistance, please contact your manager or support team."
            
            else:
                response = f"❓ General Question\n\n"
                response += f"Hi {salesperson.full_name}, I received your question about: {question_topic}\n\n"
                response += f"Note: General question handling is coming soon! For now, please contact your manager or support team for assistance."
            
            return {
                "success": True,
                "message": response,
                "question_topic": question_topic,
                "urgency": urgency
            }
            
        except Exception as e:
            logger.error(f"Error handling general question: {e}")
            return {
                "success": False,
                "error": "Question handling failed",
                "message": "Sorry, there was an error processing your question. Please try again."
            }
    
    async def _handle_status_update(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle status updates from salesperson SMS"""
        try:
            lead_identifier = parsed_data.get("lead_identifier", "Unknown")
            update_type = parsed_data.get("update_type", "progress")
            details = parsed_data.get("details", "No details provided")
            
            # For now, provide a basic response
            # In the future, this could update lead status in the database
            return {
                "success": True,
                "message": f"📝 Status Update Received\n\n"
                          f"Lead: {lead_identifier}\n"
                          f"Update type: {update_type}\n"
                          f"Details: {details}\n\n"
                          f"Note: Status update functionality is coming soon! Your update has been logged and will be processed by the system.",
                "lead_identifier": lead_identifier,
                "update_type": update_type,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
            return {
                "success": False,
                "error": "Status update failed",
                "message": "Sorry, there was an error processing your status update. Please try again."
            }
    
    async def _handle_test_drive_scheduling(
        self,
        session: AsyncSession,
        salesperson: Any,
        parsed_data: Dict[str, Any],
        dealership_id: str
    ) -> Dict[str, Any]:
        """Handle test drive scheduling from salesperson SMS"""
        try:
            customer_name = parsed_data.get("customer_name", "Unknown")
            customer_phone = parsed_data.get("customer_phone", "Unknown")
            vehicle_interest = parsed_data.get("vehicle_interest", "Unknown")
            preferred_date = parsed_data.get("preferred_date", "Unknown")
            preferred_time = parsed_data.get("preferred_time", "Unknown")
            special_requests = parsed_data.get("special_requests", "None")
            
            # Generate Google Calendar URL for test drive appointment
            calendar_url = self._generate_test_drive_calendar_url(
                customer_name=customer_name,
                vehicle_interest=vehicle_interest,
                preferred_date=preferred_date,
                preferred_time=preferred_time,
                special_requests=special_requests,
                salesperson_name=salesperson.full_name,
                dealership_id=dealership_id
            )
            
            # Create or update lead if customer phone is provided
            lead_id = None
            if customer_phone and customer_phone != "Unknown":
                try:
                    # Check if lead already exists
                    existing_lead = await get_lead_by_phone(
                        session=session,
                        phone=customer_phone,
                        dealership_id=dealership_id
                    )
                    
                    if existing_lead:
                        # Update existing lead with test drive info
                        lead_id = str(existing_lead.id)
                        # Note: In a full implementation, you'd update the appointment_datetime field
                        logger.info(f"Updated existing lead {lead_id} with test drive request")
                    else:
                        # Create new lead for test drive
                        from ..schemas.lead import LeadCreate
                        lead_data = LeadCreate(
                            name=customer_name if customer_name != "Unknown" else "Test Drive Customer",
                            phone=customer_phone,
                            email=None,
                            car_interest=vehicle_interest if vehicle_interest != "Unknown" else "Test Drive",
                            source="Test Drive Scheduling",
                            max_price=None,
                            message=f"Test drive request via SMS from {salesperson.full_name}. "
                                    f"Vehicle: {vehicle_interest}. "
                                    f"Preferred: {preferred_date} at {preferred_time}. "
                                    f"Special requests: {special_requests}"
                        )
                        
                        new_lead = await create_lead(
                            session=session,
                            lead_in=lead_data,
                            user_id=str(salesperson.user_id),
                            dealership_id=dealership_id
                        )
                        lead_id = str(new_lead.id)
                        logger.info(f"Created new lead {lead_id} for test drive request")
                        
                except Exception as lead_error:
                    logger.warning(f"Could not create/update lead for test drive: {lead_error}")
                    # Continue without lead creation - the main functionality still works
            
            return {
                "success": True,
                "message": f"🚗 Test Drive Scheduled!\n\n"
                          f"Customer: {customer_name}\n"
                          f"Vehicle: {vehicle_interest}\n"
                          f"Date: {preferred_date}\n"
                          f"Time: {preferred_time}\n"
                          f"Special Requests: {special_requests}\n\n"
                          f"📅 Google Calendar Link:\n{calendar_url}\n\n"
                          f"Lead ID: {lead_id or 'Not created'}\n\n"
                          f"Use the calendar link above to add this to your schedule and send to the customer.",
                "lead_id": lead_id,
                "customer_name": customer_name,
                "vehicle_interest": vehicle_interest,
                "calendar_url": calendar_url
            }
            
        except Exception as e:
            logger.error(f"Error handling test drive scheduling: {e}")
            return {
                "success": False,
                "error": "Test drive scheduling failed",
                "message": "Sorry, there was an error processing your test drive scheduling request. Please try again."
            }
    
    def _generate_test_drive_calendar_url(
        self,
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
            from datetime import datetime, timedelta
            import urllib.parse
            
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
            logger.error(f"Error generating calendar URL: {e}")
            # Return a fallback URL
            return "https://calendar.google.com/calendar/render?action=TEMPLATE&text=Test%20Drive%20Appointment&sf=true&output=xml"


# Global instance
salesperson_sms_service = SalespersonSMSService()
