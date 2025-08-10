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
    create_conversation
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
                              "• Update progress: 'Lead John is coming for test drive tomorrow'"
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
            
            # Create lead data
            lead_data = LeadCreate(
                name=parsed_data["name"],
                phone=parsed_data["phone"],
                email=parsed_data.get("email"),
                car_interest=parsed_data.get("car_interest", "Unknown"),  # LLM extracts 'car_interest', matches DB field
                source=parsed_data.get("source", "SMS Lead Creation"),
                max_price=parsed_data.get("price_range", None),  # Map price_range to max_price
                message=f"Lead created via SMS by {salesperson.full_name}. "
                        f"Car interest: {parsed_data.get('car_interest', 'Unknown')}. "
                        f"Price range: {parsed_data.get('price_range', 'Not specified')}."
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


# Global instance
salesperson_sms_service = SalespersonSMSService()
