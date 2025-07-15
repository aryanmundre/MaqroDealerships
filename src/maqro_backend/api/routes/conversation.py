from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_backend.api.deps import get_db_session
from maqro_backend.schemas.conversation import MessageCreate, ConversationResponse
from maqro_backend.schemas.lead import LeadResponse
from maqro_backend.crud import (
    get_lead_by_id,
    create_message,
    get_conversations_by_lead_id
)

router = APIRouter()


@router.post("/messages")
async def add_message(message_data: MessageCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Add new message to existing conversation
    
    1. Frontend sends: lead_id, new message
    2. We verify the lead exists
    3. We save the message as a new Conversation record
    4. Return confirmation
    """
    print(f"Adding message for lead {message_data.lead_id}")
    
    # 1. Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=message_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 2. Create new conversation record
    await create_message(session=db, message_in=message_data)

    print(f"Message saved for lead {lead.name}")
    
    return {
        "message": "Message saved successfully",
        "lead_id": message_data.lead_id,
        "lead_name": lead.name
    }


@router.get("/leads/{lead_id}/conversations", response_model=list[ConversationResponse])
async def get_conversations(lead_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get all conversations for a lead with standardized response format"""
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    return conversations


@router.get("/leads/{lead_id}/conversations-with-lead")
async def get_conversations_with_lead_info(lead_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get all conversations for a lead with lead information included"""
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    
    return {
        "lead": LeadResponse.model_validate(lead),
        "conversations": [ConversationResponse.model_validate(conv) for conv in conversations]
    }
