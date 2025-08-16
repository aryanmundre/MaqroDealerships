"""
Vonage SMS API routes for sending and receiving SMS messages
"""
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging
from datetime import datetime
import pytz

from maqro_rag import EnhancedRAGService
from ...api.deps import get_db_session, get_current_user_id, get_user_dealership_id, get_enhanced_rag_services
from ...services.sms_service import sms_service
from ...services.salesperson_sms_service import salesperson_sms_service
from ...crud import (
    get_lead_by_phone, 
    create_lead, 
    create_conversation,
    get_all_conversation_history,
    get_user_profile_by_user_id,
    get_salesperson_by_phone,
    create_pending_approval,
    get_pending_approval_by_user,
    update_approval_status,
    is_approval_command,
    parse_approval_command
)
from ...schemas.lead import LeadCreate
from ...services.ai_services import get_last_customer_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send-sms")
async def send_sms(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """
    Send SMS via Vonage API
    Replaces the frontend /api/send-message route
    """
    try:
        body = await request.json()
        to = body.get("to")
        message = body.get("body")
        
        if not to or not message:
            raise HTTPException(status_code=400, detail="Missing 'to' or 'body' parameters")
        
        logger.info(f"Sending SMS to {to}: {message}")
        
        # Send SMS via Vonage service
        result = await sms_service.send_sms(to, message)
        
        if result["success"]:
            return {
                "success": True,
                "message_id": result["message_id"],
                "to": to,
                "message": "SMS sent successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")


@router.api_route("/webhook", methods=["GET", "POST"])
async def vonage_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    enhanced_rag_service: EnhancedRAGService = Depends(get_enhanced_rag_services)
):
    """
    Vonage webhook endpoint for receiving inbound SMS messages
    
    This endpoint:
    1. Receives incoming SMS from customers
    2. Looks up existing lead by phone number
    3. Creates new lead if phone number doesn't exist
    4. Adds message to conversation history
    5. Generates AI response using RAG system
    6. Sends AI response back to customer
    """
    try:
        # Handle both GET (query params) and POST (form data) requests
        if request.method == "GET":
            # Vonage sends data as query parameters
            from_number = request.query_params.get("msisdn")
            to_number = request.query_params.get("to")
            message_text = request.query_params.get("text")
            message_id = request.query_params.get("messageId")
        else:
            # POST - Vonage sends form data
            form_data = await request.form()
            from_number = form_data.get("msisdn")
            to_number = form_data.get("to")
            message_text = form_data.get("text")
            message_id = form_data.get("messageId")
        
        logger.info(f"Received webhook: from={from_number}, to={to_number}, text={message_text}")
        
        if not from_number or not message_text:
            logger.error("Missing required webhook parameters")
            return {"status": "error", "message": "Missing required parameters"}
        
        # Normalize phone number
        normalized_phone = sms_service.normalize_phone_number(from_number)
        
        # Use specific dealership ID for testing
        default_dealership_id = "d660c7d6-99e2-4fa8-b99b-d221def53d20"
        
        # FIRST: Check if this is an approval/rejection from a salesperson with pending approval
        salesperson_profile = await get_salesperson_by_phone(
            session=db,
            phone=normalized_phone,
            dealership_id=default_dealership_id
        )
        
        logger.info(f"Checking for salesperson with phone {normalized_phone}: {'Found' if salesperson_profile else 'Not found'}")
        
        if salesperson_profile:
            logger.info(f"Found salesperson {salesperson_profile.user_id}, checking for pending approval")
            # Check if they have a pending approval
            pending_approval = await get_pending_approval_by_user(
                session=db,
                user_id=str(salesperson_profile.user_id),
                dealership_id=default_dealership_id
            )
            
            logger.info(f"Pending approval: {'Found' if pending_approval else 'Not found'}")
            logger.info(f"Is approval command '{message_text}': {is_approval_command(message_text)}")
            
            if pending_approval and is_approval_command(message_text):
                # This is an approval/rejection command
                approval_decision = parse_approval_command(message_text)
                
                if approval_decision == "approved":
                    logger.info(f"Approval decision: approved. Sending RAG response to customer {pending_approval.customer_phone}")
                    # Send the generated response to the customer
                    sms_result = await sms_service.send_sms(
                        pending_approval.customer_phone, 
                        pending_approval.generated_response
                    )
                    logger.info(f"SMS send result: {sms_result}")
                    
                    # Update approval status
                    await update_approval_status(
                        session=db,
                        approval_id=str(pending_approval.id),
                        status="approved"
                    )
                    
                    # Save agent response to conversation history
                    await create_conversation(
                        session=db,
                        lead_id=str(pending_approval.lead_id),
                        message=pending_approval.generated_response,
                        sender="agent"
                    )
                    
                    if sms_result["success"]:
                        return {
                            "status": "success",
                            "message": "Response approved and sent to customer",
                            "approval_id": str(pending_approval.id),
                            "sent_to_customer": True
                        }
                    else:
                        return {
                            "status": "error",
                            "message": "Response approved but failed to send to customer",
                            "approval_id": str(pending_approval.id),
                            "error": sms_result["error"]
                        }
                        
                elif approval_decision == "rejected":
                    # Mark as rejected, don't send to customer
                    await update_approval_status(
                        session=db,
                        approval_id=str(pending_approval.id),
                        status="rejected"
                    )
                    
                    return {
                        "status": "success",
                        "message": "Response rejected, not sent to customer",
                        "approval_id": str(pending_approval.id),
                        "sent_to_customer": False
                    }
                else:
                    # Unknown command, let them know
                    help_message = "I didn't understand. Reply with 'YES' to send the response to the customer, or 'NO' to reject it."
                    await sms_service.send_sms(normalized_phone, help_message)
                    
                    return {
                        "status": "help_sent",
                        "message": "Sent help message for approval command",
                        "approval_id": str(pending_approval.id)
                    }
        
        # SECOND: Check if this is a salesperson message (they would have a user profile)
        # Try to process as salesperson message (existing logic)
        salesperson_result = await salesperson_sms_service.process_salesperson_message(
            session=db,
            from_number=normalized_phone,
            message_text=message_text,
            dealership_id=default_dealership_id
        )
        
        # If this was a salesperson message, send response and return
        if salesperson_result["success"] or "Salesperson not found" not in salesperson_result.get("error", ""):
            # Send response back to salesperson
            sms_result = await sms_service.send_sms(normalized_phone, salesperson_result["message"])
            
            if sms_result["success"]:
                logger.info(f"Sent salesperson response to {normalized_phone}")
                return {
                    "status": "success",
                    "message": "Salesperson message processed",
                    "response_sent": True,
                    "result": salesperson_result
                }
            else:
                logger.error(f"Failed to send salesperson response: {sms_result['error']}")
                return {
                    "status": "partial_success",
                    "message": "Salesperson message processed but response failed to send",
                    "response_sent": False,
                    "result": salesperson_result,
                    "error": sms_result["error"]
                }
        
        # If not a salesperson message, check if this is a message from an existing lead
        existing_lead = await get_lead_by_phone(
            session=db, 
            phone=normalized_phone, 
            dealership_id=default_dealership_id
        )
        
        # If this is a message from an existing lead WITH an assigned user, forward it to the user
        if existing_lead and existing_lead.user_id:
            logger.info(f"Found existing lead {existing_lead.id} assigned to user {existing_lead.user_id}")
            
            # Add customer message to conversation history
            await create_conversation(
                session=db,
                lead_id=str(existing_lead.id),
                message=message_text,
                sender="customer"
            )
            logger.info("Added customer message to conversation")
            
            # Get the assigned user's phone number to forward the message
            assigned_user = await get_user_profile_by_user_id(session=db, user_id=str(existing_lead.user_id))
            
            if assigned_user and assigned_user.phone:
                # Generate RAG response for the lead's message
                try:
                    # Get conversation history for AI response
                    all_conversations_raw = await get_all_conversation_history(session=db, lead_id=str(existing_lead.id))
                    
                    # Convert SQLAlchemy objects to dictionaries for RAG service
                    all_conversations = [
                        {
                            "id": str(conv.id),
                            "message": conv.message,
                            "sender": conv.sender,
                            "created_at": conv.created_at.isoformat() if conv.created_at else None
                        }
                        for conv in all_conversations_raw
                    ]
                    
                    # Use enhanced RAG system to find relevant vehicles
                    vehicles = enhanced_rag_service.search_vehicles_with_context(
                        message_text, 
                        all_conversations, 
                        top_k=3
                    )
                    
                    # Generate enhanced AI response
                    enhanced_response = enhanced_rag_service.generate_enhanced_response(
                        message_text,
                        vehicles,
                        all_conversations,
                        existing_lead.name
                    )
                    
                    ai_response_text = enhanced_response['response_text']
                    
                    # Create pending approval for the RAG response
                    pending_approval = await create_pending_approval(
                        session=db,
                        lead_id=str(existing_lead.id),
                        user_id=str(existing_lead.user_id),
                        customer_message=message_text,
                        generated_response=ai_response_text,
                        customer_phone=normalized_phone,
                        dealership_id=default_dealership_id
                    )
                    
                    # Send verification message to salesperson
                    verification_message = f"RAG Response for {existing_lead.name} ({normalized_phone}):\n\nCustomer: {message_text}\n\nSuggested Reply: {ai_response_text}\n\n📱 Reply 'YES' to send or 'NO' to reject."
                    
                    sms_result = await sms_service.send_sms(assigned_user.phone, verification_message)
                    
                    if sms_result["success"]:
                        logger.info(f"Created pending approval {pending_approval.id} and sent to user {existing_lead.user_id}")
                        return {
                            "status": "success",
                            "message": "RAG response pending approval from assigned user",
                            "lead_id": str(existing_lead.id),
                            "approval_id": str(pending_approval.id),
                            "sent_to": assigned_user.phone,
                            "response_sent": True,
                            "rag_response": ai_response_text
                        }
                    else:
                        logger.error(f"Failed to send verification message to user: {sms_result['error']}")
                        return {
                            "status": "error",
                            "message": "Failed to send verification message to assigned user",
                            "lead_id": str(existing_lead.id),
                            "approval_id": str(pending_approval.id),
                            "error": sms_result["error"]
                        }
                        
                except Exception as rag_error:
                    logger.error(f"Error generating RAG response: {rag_error}")
                    # Fallback to simple message forwarding if RAG fails
                    fallback_message = f"RAG system error. Raw message from lead {existing_lead.name} ({normalized_phone}): {message_text}"
                    
                    sms_result = await sms_service.send_sms(assigned_user.phone, fallback_message)
                    
                    return {
                        "status": "fallback",
                        "message": "RAG error, sent raw message to assigned user",
                        "lead_id": str(existing_lead.id),
                        "sent_to": assigned_user.phone,
                        "response_sent": sms_result["success"],
                        "rag_error": str(rag_error)
                    }
            else:
                logger.warning(f"Assigned user {existing_lead.user_id} not found or has no phone number")
                return {
                    "status": "error",
                    "message": "Assigned user not found or has no phone number",
                    "lead_id": str(existing_lead.id)
                }
        
        # If existing lead but no assigned user, or new lead, process with RAG system
        if existing_lead:
            logger.info(f"Found existing lead: {existing_lead.name} ({existing_lead.id}) - no assigned user, processing with RAG")
            lead = existing_lead
        else:
            # Create new lead from SMS
            logger.info(f"Creating new lead for phone number: {normalized_phone}")
            
            # Extract information from message if possible (basic extraction)
            extracted_name = None
            extracted_car = "Unknown"
            
            # Simple extraction patterns - you can enhance this with LLM later
            message_lower = message_text.lower()
            if "my name is" in message_lower:
                try:
                    # Extract name after "my name is"
                    name_part = message_text[message_lower.find("my name is") + 11:].strip()
                    extracted_name = name_part.split()[0] if name_part else None
                except:
                    pass
            
            # Extract car interest
            car_keywords = ["toyota", "honda", "ford", "bmw", "mercedes", "audi", "lexus", "nissan", "mazda"]
            for keyword in car_keywords:
                if keyword in message_lower:
                    extracted_car = keyword.title()
                    break
            
            lead_data = LeadCreate(
                name=extracted_name,  # Will auto-generate if None
                phone=normalized_phone,
                email=None,
                car_interest=extracted_car,
                source="SMS",
                message=message_text
            )
            
            # Use specific user ID for testing
            default_user_id = "d245e4bb-91ae-4ec4-ad0f-18307b38daa6"
            
            lead = await create_lead(
                session=db,
                lead_in=lead_data,
                user_id=default_user_id,
                dealership_id=default_dealership_id
            )
            logger.info(f"Created new lead: {lead.id}")
        
        # Add customer message to conversation history
        await create_conversation(
            session=db,
            lead_id=str(lead.id),
            message=message_text,
            sender="customer"
        )
        logger.info("Added customer message to conversation")
        
        # Get conversation history for AI response
        all_conversations_raw = await get_all_conversation_history(session=db, lead_id=str(lead.id))
        
        # Convert SQLAlchemy objects to dictionaries for RAG service
        all_conversations = [
            {
                "id": str(conv.id),
                "message": conv.message,
                "sender": conv.sender,
                "created_at": conv.created_at.isoformat() if conv.created_at else None
            }
            for conv in all_conversations_raw
        ]
        
        # Generate AI response using RAG system
        try:
            # Use enhanced RAG system to find relevant vehicles
            vehicles = enhanced_rag_service.search_vehicles_with_context(
                message_text, 
                all_conversations, 
                top_k=3
            )
            
            # Generate enhanced AI response
            enhanced_response = enhanced_rag_service.generate_enhanced_response(
                message_text,
                vehicles,
                all_conversations,
                lead.name
            )
            
            ai_response_text = enhanced_response['response_text']
            
            # Save AI response to database
            await create_conversation(
                session=db,
                lead_id=str(lead.id),
                message=ai_response_text,
                sender="agent"
            )
            
            # Send AI response back to customer via SMS
            sms_result = await sms_service.send_sms(normalized_phone, ai_response_text)
            
            if sms_result["success"]:
                logger.info(f"Sent AI response to {normalized_phone}")
                
                return {
                    "status": "success",
                    "message": "Message processed and response sent",
                    "lead_id": str(lead.id),
                    "response_sent": True
                }
            else:
                logger.error(f"Failed to send AI response: {sms_result['error']}")
                return {
                    "status": "partial_success", 
                    "message": "Message processed but response failed to send",
                    "lead_id": str(lead.id),
                    "response_sent": False,
                    "error": sms_result["error"]
                }
                
        except Exception as ai_error:
            logger.error(f"Error generating AI response: {ai_error}")
            
            # Send a fallback response
            fallback_message = f"Hi {lead.name}, thanks for your message! A team member will get back to you soon."
            
            sms_result = await sms_service.send_sms(normalized_phone, fallback_message)
            
            return {
                "status": "fallback",
                "message": "Message processed with fallback response",
                "lead_id": str(lead.id),
                "response_sent": sms_result["success"],
                "ai_error": str(ai_error)
            }
            
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": f"Internal processing error: {str(e)}"}


@router.api_route("/delivery", methods=["GET", "POST"])
async def vonage_delivery_webhook(request: Request):
    """
    Vonage delivery receipt webhook endpoint
    
    This endpoint receives delivery status updates for outbound SMS messages
    Vonage sends delivery receipts here when SMS messages are delivered, failed, etc.
    """
    try:
        # Handle both GET (query params) and POST (form data) requests
        if request.method == "GET":
            # Vonage sends data as query parameters
            message_id = request.query_params.get("messageId")
            status = request.query_params.get("status")
            err_code = request.query_params.get("err-code")
            to = request.query_params.get("to")
            network_code = request.query_params.get("network-code")
            price = request.query_params.get("price")
        else:
            # POST - Vonage sends form data
            form_data = await request.form()
            message_id = form_data.get("messageId")
            status = form_data.get("status")
            err_code = form_data.get("err-code")
            to = form_data.get("to")
            network_code = form_data.get("network-code")
            price = form_data.get("price")
        
        logger.info(f"Delivery receipt: messageId={message_id}, status={status}, to={to}, err_code={err_code}")
        
        # You can store delivery status in database if needed
        # For now, just log the delivery status
        
        return {"status": "ok", "message": "Delivery receipt processed"}
        
    except Exception as e:
        logger.error(f"Delivery webhook processing error: {e}")
        return {"status": "error", "message": f"Error processing delivery receipt: {str(e)}"}


@router.api_route("/webhook-simple", methods=["GET", "POST"])
async def vonage_simple_webhook(request: Request):
    """
    Simple webhook endpoint for testing Vonage SMS receive/send functionality
    Just receives a message and sends back a simple test response
    """
    try:
        # Handle both GET (query params) and POST (form data) requests
        if request.method == "GET":
            # Vonage sends data as query parameters
            from_number = request.query_params.get("msisdn")
            to_number = request.query_params.get("to")
            message_text = request.query_params.get("text")
            message_id = request.query_params.get("messageId")
        else:
            # POST - Vonage sends form data
            form_data = await request.form()
            from_number = form_data.get("msisdn")
            to_number = form_data.get("to")
            message_text = form_data.get("text")
            message_id = form_data.get("messageId")
        
        logger.info(f"Simple webhook received: from={from_number}, text={message_text}")
        
        if not from_number or not message_text:
            logger.error("Missing required webhook parameters")
            return {"status": "error", "message": "Missing required parameters"}
        
        # Normalize phone number
        normalized_phone = sms_service.normalize_phone_number(from_number)
        
        # Simple test response
        test_response = f"Hello! I received your message: '{message_text}'. This is a test response from the dealership bot."
        
        # Send simple response back to customer via SMS
        sms_result = await sms_service.send_sms(normalized_phone, test_response)
        
        if sms_result["success"]:
            logger.info(f"Sent test response to {normalized_phone}")
            return {
                "status": "success",
                "message": "Test message processed and response sent",
                "from": from_number,
                "response_sent": True,
                "test_response": test_response
            }
        else:
            logger.error(f"Failed to send test response: {sms_result['error']}")
            return {
                "status": "error", 
                "message": "Failed to send response",
                "from": from_number,
                "response_sent": False,
                "error": sms_result["error"]
            }
            
    except Exception as e:
        logger.error(f"Simple webhook processing error: {e}")
        return {"status": "error", "message": f"Processing error: {str(e)}"}


@router.get("/webhook-test")
async def test_webhook():
    """
    Test endpoint to verify webhook URL is reachable
    Vonage may call this to verify your webhook URL
    """
    return {"status": "ok", "message": "Vonage webhook endpoint is active"}