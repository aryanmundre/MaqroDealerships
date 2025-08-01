from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db.models import Lead, Conversation, Inventory, UserProfile
from .schemas.conversation import MessageCreate
from .schemas.lead import LeadCreate
import uuid
from typing import List

# =============================================================================
# LEAD CRUD OPERATIONS
# =============================================================================

async def create_lead(*, session: AsyncSession, lead_in: LeadCreate, user_id: str) -> Lead:
    """Create a new lead with Supabase compatibility"""
    db_obj = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        car=getattr(lead_in, 'car', 'Unknown'),  # Default if not provided
        source=getattr(lead_in, 'source', 'Website'),  # Default if not provided
        status="new",  # All leads start as "new"
        last_contact="Just now",
        message=getattr(lead_in, 'message', ''),  # Initial message
        user_id=uuid.UUID(user_id)  # Convert string to UUID
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_lead_by_id(*, session: AsyncSession, lead_id: str) -> Lead | None:
    """Get a lead by UUID (Supabase uses UUIDs as primary keys)"""
    try:
        lead_uuid = uuid.UUID(lead_id)
        return await session.get(Lead, lead_uuid)
    except (ValueError, TypeError):
        return None


async def get_all_leads_ordered(*, session: AsyncSession, user_id: str) -> list[Lead]:
    """Get all leads for a user ordered by creation date (newest first) - Supabase RLS compatible"""
    try:
        user_uuid = uuid.UUID(user_id)
        result = await session.execute(
            select(Lead)
            .where(Lead.user_id == user_uuid)  # Filter by user for RLS compatibility
            .order_by(Lead.created_at.desc())
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []


async def get_lead_by_email(*, session: AsyncSession, email: str, user_id: str) -> Lead | None:
    """Get a lead by email for a specific user (Supabase RLS compatible)"""
    try:
        user_uuid = uuid.UUID(user_id)
        statement = select(Lead).where(
            Lead.email == email,
            Lead.user_id == user_uuid  # Filter by user for RLS compatibility
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except (ValueError, TypeError):
        return None


# =============================================================================
# CONVERSATION CRUD OPERATIONS
# =============================================================================

async def create_conversation(*, session: AsyncSession, lead_id: str, message: str, sender: str) -> Conversation:
    """Create a new conversation message with Supabase UUID compatibility"""
    try:
        lead_uuid = uuid.UUID(lead_id)
        db_obj = Conversation(
            lead_id=lead_uuid,
            message=message,
            sender=sender,
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid lead_id format: {lead_id}") from e


async def create_message(*, session: AsyncSession, message_in: MessageCreate) -> Conversation:
    """Create a new message (customer conversation) with Supabase UUID compatibility"""
    return await create_conversation(
        session=session,
        lead_id=str(message_in.lead_id),  # Convert to string for UUID handling
        message=message_in.message,
        sender="customer"
    )


async def get_conversations_by_lead_id(*, session: AsyncSession, lead_id: str) -> list[Conversation]:
    """Get all conversations for a lead with Supabase UUID compatibility"""
    try:
        lead_uuid = uuid.UUID(lead_id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.lead_id == lead_uuid)
            .order_by(Conversation.created_at)
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []


async def get_all_conversation_history(*, session: AsyncSession, lead_id: str) -> list[Conversation]:
    """
    Get complete conversation history for a lead (no limits) with Supabase UUID compatibility
    
    Returns conversations in chronological order (oldest first)
    """
    try:
        lead_uuid = uuid.UUID(lead_id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.lead_id == lead_uuid)
            .order_by(Conversation.created_at.asc())  # Chronological order
        )
        conversations = result.scalars().all()
        return list(conversations)
    except (ValueError, TypeError):
        return []


# =============================================================================
# COMBINED OPERATIONS
# =============================================================================

async def create_lead_with_initial_message(*, session: AsyncSession, lead_in: LeadCreate, user_id: str) -> dict:
    """
    Create a new lead and their initial conversation message in one transaction (Supabase compatible)
    
    Returns dict with lead_id, status, and message
    """
    try:
        # 1. Create new lead record
        new_lead = await create_lead(session=session, lead_in=lead_in, user_id=user_id)
        
        # 2. Save their initial message as first conversation (if provided)
        if hasattr(lead_in, 'message') and lead_in.message:
            await create_conversation(
                session=session,
                lead_id=str(new_lead.id),
                message=lead_in.message,
                sender="customer"
            )
        
        return {
            "lead_id": str(new_lead.id),  # Convert UUID to string for JSON serialization
            "status": "created",
            "message": f"Lead {new_lead.name} created successfully"
        }
    except Exception as e:
        await session.rollback()
        raise e


# =============================================================================
# INVENTORY CRUD OPERATIONS (Supabase compatible)
# =============================================================================

async def create_inventory_item(*, session: AsyncSession, inventory_data: dict, dealership_id: str) -> Inventory:
    """Create a new inventory item"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        db_obj = Inventory(
            make=inventory_data['make'],
            model=inventory_data['model'],
            year=inventory_data['year'],
            price=str(inventory_data['price']),  # Convert to string for DECIMAL compatibility
            mileage=inventory_data.get('mileage'),
            description=inventory_data.get('description'),
            features=inventory_data.get('features'),
            dealership_id=dealership_uuid,
            status=inventory_data.get('status', 'active')
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid dealership_id format: {dealership_id}") from e


async def get_inventory_by_dealership(*, session: AsyncSession, dealership_id: str) -> list[Inventory]:
    """Get all inventory items for a dealership (Supabase RLS compatible)"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        result = await session.execute(
            select(Inventory)
            .where(Inventory.dealership_id == dealership_uuid)
            .order_by(Inventory.created_at.desc())
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []


async def get_inventory_by_id(*, session: AsyncSession, inventory_id: str) -> Inventory | None:
    """Get inventory item by UUID"""
    try:
        inventory_uuid = uuid.UUID(inventory_id)
        return await session.get(Inventory, inventory_uuid)
    except (ValueError, TypeError):
        return None
