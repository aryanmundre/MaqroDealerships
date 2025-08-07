from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .db.models import Lead, Conversation, Inventory, UserProfile, Dealership
from .schemas.conversation import MessageCreate
from .schemas.lead import LeadCreate
import uuid
from typing import List
from datetime import datetime
import pytz

# =============================================================================
# LEAD CRUD OPERATIONS
# =============================================================================

async def create_lead(*, session: AsyncSession, lead_in: LeadCreate, user_id: str, dealership_id: str) -> Lead:
    """Create a new lead with Supabase compatibility"""
    db_obj = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        car=getattr(lead_in, 'car', 'Unknown'),  # Default if not provided
        source=getattr(lead_in, 'source', 'Website'),  # Default if not provided
        status="new",  # All leads start as "new"
        last_contact_at=datetime.now(pytz.timezone('utc')),  # Current time in UTC
        message=getattr(lead_in, 'message', ''),  # Initial message
        user_id=uuid.UUID(user_id) if user_id else None,  # Assigned salesperson (nullable)
        dealership_id=uuid.UUID(dealership_id)  # Required dealership ID
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


async def get_all_leads_ordered(*, session: AsyncSession, dealership_id: str) -> list[Lead]:
    """Get all leads for a dealership ordered by creation date (newest first) - Supabase RLS compatible"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        result = await session.execute(
            select(Lead)
            .where(Lead.dealership_id == dealership_uuid)  # Filter by dealership for RLS compatibility
            .order_by(Lead.created_at.desc())
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []


async def get_lead_by_email(*, session: AsyncSession, email: str, dealership_id: str) -> Lead | None:
    """Get a lead by email for a specific dealership (Supabase RLS compatible)"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        statement = select(Lead).where(
            Lead.email == email,
            Lead.dealership_id == dealership_uuid  # Filter by dealership for RLS compatibility
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except (ValueError, TypeError):
        return None

async def get_leads_by_salesperson(
        *, session: AsyncSession, salesperson_id: str
) -> list[Lead]:
    """Return all leads assigned to a specific salesperson (newest first)"""
    try:
        salesperson_uuid = uuid.UUID(salesperson_id)
        result = await session.execute(
            select(Lead)
            .where(Lead.user_id == salesperson_uuid)
            .order_by(Lead.created_at.desc())
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []
    


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

async def create_lead_with_initial_message(*, session: AsyncSession, lead_in: LeadCreate, user_id: str, dealership_id: str) -> dict:
    """
    Create a new lead and their initial conversation message in one transaction (Supabase compatible)
    
    Returns dict with lead_id, status, and message
    """
    try:
        # 1. Create new lead record
        new_lead = await create_lead(session=session, lead_in=lead_in, user_id=user_id, dealership_id=dealership_id)
        
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


async def bulk_create_inventory_items(
    *, 
    session: AsyncSession, 
    inventory_data: list[dict], 
    dealership_id: str
) -> int:
    """Bulk create inventory items from a list of dicts"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        
        db_objects = [
            Inventory(
                make=item.get('make'),
                model=item.get('model'),
                year=item.get('year'),
                price=str(item.get('price')),
                mileage=item.get('mileage'),
                description=item.get('description'),
                features=item.get('features'),
                dealership_id=dealership_uuid,
                status=item.get('status', 'active')
            ) for item in inventory_data
        ]
        
        session.add_all(db_objects)
        await session.commit()
        return len(db_objects)
    except Exception as e:
        await session.rollback()
        raise e


async def get_inventory_count(*, session: AsyncSession, dealership_id: str) -> int:
    """Get the total count of inventory items for a dealership."""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        result = await session.execute(
            select(func.count(Inventory.id))
            .where(Inventory.dealership_id == dealership_uuid)
        )
        return result.scalar_one()
    except (ValueError, TypeError):
        return 0


async def get_lead_stats(*, session: AsyncSession, dealership_id: str) -> dict:
    """Get lead statistics for a dealership."""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        
        # Get total leads
        total_leads_result = await session.execute(
            select(func.count(Lead.id))
            .where(Lead.dealership_id == dealership_uuid)
        )
        total = total_leads_result.scalar_one()

        # Get leads by status
        by_status_result = await session.execute(
            select(Lead.status, func.count(Lead.id))
            .where(Lead.dealership_id == dealership_uuid)
            .group_by(Lead.status)
        )
        by_status = {status: count for status, count in by_status_result}

        return {"total": total, "by_status": by_status}
    except (ValueError, TypeError):
        return {"total": 0, "by_status": {}}


# =============================================================================
# DEALERSHIP CRUD OPERATIONS
# =============================================================================

async def create_dealership(*, session: AsyncSession, name: str, location: str = None) -> Dealership:
    """Create a new dealership"""
    db_obj = Dealership(
        name=name,
        location=location
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_dealership_by_id(*, session: AsyncSession, dealership_id: str) -> Dealership | None:
    """Get a dealership by UUID"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        return await session.get(Dealership, dealership_uuid)
    except (ValueError, TypeError):
        return None


async def update_dealership(*, session: AsyncSession, dealership_id: str, **kwargs) -> Dealership | None:
    """Update dealership information"""
    dealership = await get_dealership_by_id(session=session, dealership_id=dealership_id)
    if not dealership:
        return None
    
    for field, value in kwargs.items():
        if hasattr(dealership, field) and value is not None:
            setattr(dealership, field, value)
    
    await session.commit()
    await session.refresh(dealership)
    return dealership


# =============================================================================
# USER PROFILE CRUD OPERATIONS
# =============================================================================

async def create_user_profile(*, session: AsyncSession, user_id: str, dealership_id: str = None, **kwargs) -> UserProfile:
    """Create a new user profile"""
    try:
        user_uuid = uuid.UUID(user_id)
        dealership_uuid = uuid.UUID(dealership_id) if dealership_id else None
        
        db_obj = UserProfile(
            user_id=user_uuid,
            dealership_id=dealership_uuid,
            full_name=kwargs.get('full_name'),
            phone=kwargs.get('phone'),
            role=kwargs.get('role', 'salesperson'),  # Default to salesperson for MVP
            timezone=kwargs.get('timezone', 'America/New_York')
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid UUID format: {str(e)}")


async def get_user_profile_by_user_id(*, session: AsyncSession, user_id: str) -> UserProfile | None:
    """Get user profile by user UUID"""
    try:
        user_uuid = uuid.UUID(user_id)
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_uuid)
        )
        return result.scalar_one_or_none()
    except (ValueError, TypeError):
        return None


async def get_user_profiles_by_dealership(*, session: AsyncSession, dealership_id: str) -> list[UserProfile]:
    """Get all user profiles for a dealership"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        result = await session.execute(
            select(UserProfile)
            .where(UserProfile.dealership_id == dealership_uuid)
            .order_by(UserProfile.created_at.desc())
        )
        return result.scalars().all()
    except (ValueError, TypeError):
        return []


async def update_user_profile(*, session: AsyncSession, user_id: str, **kwargs) -> UserProfile | None:
    """Update user profile information"""
    profile = await get_user_profile_by_user_id(session=session, user_id=user_id)
    if not profile:
        return None
    
    for field, value in kwargs.items():
        if hasattr(profile, field) and value is not None:
            if field == 'dealership_id':
                # Handle dealership_id as UUID
                try:
                    value = uuid.UUID(value) if value else None
                except (ValueError, TypeError):
                    continue
            setattr(profile, field, value)
    
    await session.commit()
    await session.refresh(profile)
    return profile
    