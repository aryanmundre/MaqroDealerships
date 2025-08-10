from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from maqro_backend.api.deps import get_db_session, get_current_user_id
from maqro_backend.schemas.conversation import MessageCreate, ConversationResponse
from maqro_backend.schemas.lead import LeadResponse
from maqro_backend.crud import (
    get_lead_by_id,
    create_message,
    get_conversations_by_lead_id
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/messages")
async def add_message(
    message_data: MessageCreate, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add new message to existing conversation (Supabase compatible)
    
    1. Frontend sends: lead_id (UUID), new message
    2. We verify the lead exists and belongs to the user
    3. We save the message as a new Conversation record
    4. Return confirmation
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    logger.info(f"Adding message for lead {message_data.lead_id}")
    
    # 1. Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=message_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 2. Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Create new conversation record
    conversation = await create_message(session=db, message_in=message_data)

    logger.info(f"Message saved for lead {lead.name}")
    
    return {
        "message": "Message saved successfully",
        "lead_id": message_data.lead_id,
        "lead_name": lead.name,
        "conversation_id": conversation.id
    }


@router.get("/leads/{lead_id}/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all conversations for a lead (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    
    # Convert to response format
    return [
        ConversationResponse(
            id=str(conv.id),
            lead_id=str(conv.lead_id),
            message=conv.message,
            sender=conv.sender,
            created_at=conv.created_at
        ) for conv in conversations
    ]


@router.get("/leads/{lead_id}/conversations-with-lead")
async def get_conversations_with_lead_info(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all conversations for a lead with lead information included (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    
    return {
        "lead": LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car_interest=lead.car_interest,
            source=lead.source,
            status=lead.status,
            last_contact_at=lead.last_contact_at,
            message=lead.message,
            user_id=str(lead.user_id),
            created_at=lead.created_at
        ),
        "conversations": [
            ConversationResponse(
                id=str(conv.id),
                lead_id=str(conv.lead_id),
                message=conv.message,
                sender=conv.sender,
                created_at=conv.created_at,
            ) for conv in conversations
        ]
    }
