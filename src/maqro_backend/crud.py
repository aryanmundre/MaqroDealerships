from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db.models.conversation import Conversation
from .db.models.lead import Lead
from .schemas.conversation import MessageCreate
from .schemas.lead import LeadCreate
from datetime import datetime
import pytz

# =============================================================================
# LEAD CRUD OPERATIONS
# =============================================================================

async def create_lead(*, session: AsyncSession, lead_in: LeadCreate) -> Lead:
    """Create a new lead"""
    db_obj = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        status="new"  # All leads start as "new"
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_lead_by_id(*, session: AsyncSession, lead_id: int) -> Lead | None:
    """Get a lead by ID"""
    return await session.get(Lead, lead_id)


async def get_all_leads_ordered(*, session: AsyncSession) -> list[Lead]:
    """Get all leads ordered by creation date (newest first)"""
    result = await session.execute(
        select(Lead).order_by(Lead.created_at.desc())
    )
    return result.scalars().all()


async def get_lead_by_email(*, session: AsyncSession, email: str) -> Lead | None:
    """Get a lead by email"""
    statement = select(Lead).where(Lead.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


# =============================================================================
# CONVERSATION CRUD OPERATIONS
# =============================================================================

async def create_conversation(*, session: AsyncSession, lead_id: int, message: str, sender: str, response_time_sec: int | None = None) -> Conversation:
    """Create a new conversation message. If sender is an agent, `response_time_sec` can capture latency to the previous customer message."""
    db_obj = Conversation(
        lead_id=lead_id,
        message=message,
        sender=sender,
        response_time_sec=response_time_sec
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def create_message(*, session: AsyncSession, message_in: MessageCreate) -> Conversation:
    """Create a new message (customer conversation)"""
    db_obj = Conversation(
        lead_id=message_in.lead_id,
        message=message_in.message,
        sender="customer"
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_conversations_by_lead_id(*, session: AsyncSession, lead_id: int) -> list[Conversation]:
    """Get all conversations for a lead"""
    result = await session.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at)
    )
    return result.scalars().all()


async def get_all_conversation_history(*, session: AsyncSession, lead_id: int) -> list[Conversation]:
    """
    Get complete conversation history for a lead (no limits)
    
    Returns conversations in chronological order (oldest first)
    """
    result = await session.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.asc())  # Chronological order
    )
    conversations = result.scalars().all()
    return list(conversations)


# =============================================================================
# COMBINED OPERATIONS
# =============================================================================

async def create_lead_with_initial_message(*, session: AsyncSession, lead_in: LeadCreate) -> dict:
    """
    Create a new lead and their initial conversation message in one transaction
    
    Returns dict with lead_id, status, and message
    """
    # 1. Create new lead record
    new_lead = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        status="new"
    )
    
    # 2. Save lead to database
    session.add(new_lead)
    await session.commit()
    await session.refresh(new_lead)
    
    # 3. Save their initial message as first conversation
    first_conversation = Conversation(
        lead_id=new_lead.id,
        message=lead_in.message,
        sender="customer"
    )
    
    # 4. Save conversation to database
    session.add(first_conversation)
    await session.commit()
    
    return {
        "lead_id": new_lead.id,
        "status": "created",
        "message": f"Lead {new_lead.name} created successfully"
    }


