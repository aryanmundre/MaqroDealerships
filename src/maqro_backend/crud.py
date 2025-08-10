from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from .db.models import Lead, Conversation, Inventory, UserProfile, Dealership, PendingApproval
from .schemas.conversation import MessageCreate
from .schemas.lead import LeadCreate
from .utils.phone_utils import normalize_phone_number
import uuid
from typing import List, Optional
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# LEAD CRUD OPERATIONS
# =============================================================================

async def create_lead(*, session: AsyncSession, lead_in: LeadCreate, user_id: str, dealership_id: str) -> Lead:
    """Create a new lead with Supabase compatibility"""
    
    # Auto-generate name if not provided
    lead_name = lead_in.name
    if not lead_name:
        if lead_in.phone:
            # Use phone number for name
            lead_name = f"SMS Lead {lead_in.phone}"
        elif lead_in.email:
            # Use email for name
            lead_name = f"Lead {lead_in.email.split('@')[0]}"
        else:
            # Fallback to generic name with timestamp
            timestamp = datetime.now().strftime("%m%d_%H%M")
            lead_name = f"New Lead {timestamp}"
    
    # Normalize phone number before storage
    normalized_phone = normalize_phone_number(lead_in.phone) if lead_in.phone else None
    
    db_obj = Lead(
        name=lead_name,
        email=lead_in.email,
        phone=normalized_phone,
        car_interest=getattr(lead_in, 'car_interest', 'Unknown'),  # Default if not provided
        source=getattr(lead_in, 'source', 'Website'),  # Default if not provided
        status="new",  # All leads start as "new"
        last_contact_at=datetime.now(pytz.timezone('utc')),  # Current time in UTC
        message=getattr(lead_in, 'message', ''),  # Initial message
        max_price=getattr(lead_in, 'max_price', None),  # Maximum price range
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


async def get_lead_by_phone(*, session: AsyncSession, phone: str, dealership_id: str) -> Lead | None:
    """Get a lead by phone number for a specific dealership (Supabase RLS compatible)"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        # Use centralized phone normalization
        normalized_phone = normalize_phone_number(phone)
        
        if not normalized_phone:
            return None
        
        statement = select(Lead).where(
            Lead.phone == normalized_phone,  # Exact match on normalized format
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


async def get_leads_with_conversations_summary_by_salesperson(
    *, session: AsyncSession, salesperson_id: str
) -> list[dict]:
    """
    Return all leads with their latest conversation for a specific salesperson.
    Uses a simple JOIN approach optimized for direct Supabase connection.
    """
    try:
        salesperson_uuid = uuid.UUID(salesperson_id)
        
        # Simple and efficient query with LEFT JOIN
        result = await session.execute(
            select(
                Lead.id,
                Lead.name,
                Lead.car_interest,
                Lead.status,
                Lead.email,
                Lead.phone,
                Lead.created_at,
                func.max(Conversation.message).label('latest_message'),
                func.max(Conversation.created_at).label('latest_message_time'),
                func.count(Conversation.id).label('conversation_count')
            )
            .outerjoin(Conversation, Conversation.lead_id == Lead.id)
            .where(Lead.user_id == salesperson_uuid)
            .group_by(
                Lead.id,
                Lead.name,
                Lead.car_interest,
                Lead.status,
                Lead.email,
                Lead.phone,
                Lead.created_at
            )
            .order_by(Lead.created_at.desc())
        )
        
        def format_time_ago(date_obj):
            if not date_obj:
                return "Never"
            
            from datetime import datetime
            import pytz
            
            now = datetime.now(pytz.UTC)
            if date_obj.tzinfo is None:
                date_obj = pytz.UTC.localize(date_obj)
            
            diff = now - date_obj
            diff_mins = int(diff.total_seconds() // 60)
            diff_hours = int(diff.total_seconds() // 3600)
            diff_days = int(diff.total_seconds() // 86400)
            
            if diff_mins < 1:
                return "Just now"
            elif diff_mins < 60:
                return f"{diff_mins}m ago"
            elif diff_hours < 24:
                return f"{diff_hours}h ago"
            else:
                return f"{diff_days}d ago"
        
        # Convert results to expected format
        leads_with_conversations = []
        for row in result:
            leads_with_conversations.append({
                'id': str(row.id),
                'name': row.name,
                'car_interest': row.car_interest or '',
                'status': row.status,
                'email': row.email,
                'phone': row.phone,
                'lastMessage': row.latest_message or 'No messages yet',
                'lastMessageTime': format_time_ago(row.latest_message_time),
                'unreadCount': 0,  # TODO: implement unread counting logic
                'created_at': row.created_at.isoformat() if row.created_at else '',
                'conversationCount': int(row.conversation_count) if row.conversation_count else 0
            })
        
        return leads_with_conversations
        
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
            condition=inventory_data.get('condition'),
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
        logger.info(f"🔍 Searching inventory for dealership: {dealership_id}")
        dealership_uuid = uuid.UUID(dealership_id)
        logger.info(f"🔑 Converted to UUID: {dealership_uuid}")
        
        result = await session.execute(
            select(Inventory)
            .where(Inventory.dealership_id == dealership_uuid)
            .order_by(Inventory.created_at.desc())
        )
        inventory_items = result.scalars().all()
        logger.info(f"📋 Found {len(inventory_items)} inventory items in database for dealership {dealership_id}")
        
        # Log all dealership IDs in inventory for debugging
        all_dealership_ids = await session.execute(
            select(Inventory.dealership_id).distinct()
        )
        all_ids = [str(did[0]) for did in all_dealership_ids.fetchall()]
        logger.info(f"🏢 All dealership IDs in inventory table: {all_ids}")
        
        return inventory_items
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Error querying inventory: {e}")
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
                condition=item.get('condition'),
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
        
        # Normalize phone number before storage
        normalized_phone = normalize_phone_number(kwargs.get('phone')) if kwargs.get('phone') else None
        
        db_obj = UserProfile(
            user_id=user_uuid,
            dealership_id=dealership_uuid,
            full_name=kwargs.get('full_name'),
            phone=normalized_phone,
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
            elif field == 'phone':
                # Normalize phone number
                value = normalize_phone_number(value)
            setattr(profile, field, value)
    
    await session.commit()
    await session.refresh(profile)
    return profile


async def get_salesperson_by_phone(*, session: AsyncSession, phone: str, dealership_id: str) -> UserProfile | None:
    """Get salesperson by phone number for a specific dealership"""
    try:
        dealership_uuid = uuid.UUID(dealership_id)
        # Use centralized phone normalization
        normalized_phone = normalize_phone_number(phone)
        
        if not normalized_phone:
            return None
        
        statement = select(UserProfile).where(
            UserProfile.phone == normalized_phone,  # Exact match on normalized format
            UserProfile.dealership_id == dealership_uuid
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except (ValueError, TypeError):
        return None


# =============================================================================
# PENDING APPROVAL CRUD OPERATIONS
# =============================================================================

async def create_pending_approval(
    *,
    session: AsyncSession,
    lead_id: str,
    user_id: str,
    customer_message: str,
    generated_response: str,
    customer_phone: str,
    dealership_id: str
) -> PendingApproval:
    """Create a new pending approval for RAG response verification"""
    try:
        # Expire existing approvals and create new one in single transaction
        user_uuid = uuid.UUID(user_id)
        
        # Mark existing pending approvals as expired
        await session.execute(
            update(PendingApproval)
            .where(
                PendingApproval.user_id == user_uuid,
                PendingApproval.status == "pending"
            )
            .values(status="expired", updated_at=datetime.now(pytz.UTC))
        )
        
        # Create new approval
        db_obj = PendingApproval(
            lead_id=uuid.UUID(lead_id),
            user_id=user_uuid,
            customer_message=customer_message,
            generated_response=generated_response,
            customer_phone=customer_phone,
            dealership_id=uuid.UUID(dealership_id),
            status="pending"
        )
        
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.info(f"Created pending approval {db_obj.id} for user {user_id}")
        return db_obj
        
    except (ValueError, TypeError) as e:
        await session.rollback()
        raise ValueError(f"Invalid UUID format: {str(e)}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating pending approval: {e}")
        raise


async def get_pending_approval_by_user(
    *, session: AsyncSession, user_id: str, dealership_id: str = None
) -> Optional[PendingApproval]:
    """Get the current pending approval for a user"""
    try:
        user_uuid = uuid.UUID(user_id)
        
        query = select(PendingApproval).where(
            PendingApproval.user_id == user_uuid,
            PendingApproval.status == "pending",
            PendingApproval.expires_at > datetime.now(pytz.UTC)
        )
        
        # Add dealership filter if provided
        if dealership_id:
            dealership_uuid = uuid.UUID(dealership_id)
            query = query.where(PendingApproval.dealership_id == dealership_uuid)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    except (ValueError, TypeError):
        return None


async def update_approval_status(
    *, 
    session: AsyncSession, 
    approval_id: str, 
    status: str
) -> Optional[PendingApproval]:
    """Update the status of a pending approval"""
    try:
        approval_uuid = uuid.UUID(approval_id)
        approval = await session.get(PendingApproval, approval_uuid)
        
        if not approval:
            return None
        
        approval.status = status
        approval.updated_at = datetime.now(pytz.UTC)
        
        await session.commit()
        await session.refresh(approval)
        logger.info(f"Updated approval {approval_id} status to {status}")
        return approval
    except (ValueError, TypeError):
        return None


async def expire_pending_approvals_for_user(
    *, session: AsyncSession, user_id: str
) -> int:
    """Expire all pending approvals for a user (ensures only one pending at a time)"""
    try:
        user_uuid = uuid.UUID(user_id)
        
        # Find all pending approvals for this user
        result = await session.execute(
            select(PendingApproval).where(
                PendingApproval.user_id == user_uuid,
                PendingApproval.status == "pending"
            )
        )
        approvals = result.scalars().all()
        
        # Mark them as expired
        count = 0
        for approval in approvals:
            approval.status = "expired"
            approval.updated_at = datetime.now(pytz.UTC)
            count += 1
        
        if count > 0:
            await session.commit()
            logger.info(f"Expired {count} pending approvals for user {user_id}")
        
        return count
    except (ValueError, TypeError):
        return 0


async def cleanup_expired_approvals(*, session: AsyncSession) -> int:
    """Clean up expired approvals (can be run periodically)"""
    try:
        # Find all approvals that are past their expiration time but still pending
        result = await session.execute(
            select(PendingApproval).where(
                PendingApproval.status == "pending",
                PendingApproval.expires_at <= datetime.now(pytz.UTC)
            )
        )
        approvals = result.scalars().all()
        
        # Mark them as expired
        count = 0
        for approval in approvals:
            approval.status = "expired"
            approval.updated_at = datetime.now(pytz.UTC)
            count += 1
        
        if count > 0:
            await session.commit()
            logger.info(f"Cleaned up {count} expired approvals")
        
        return count
    except Exception as e:
        logger.error(f"Error cleaning up expired approvals: {e}")
        return 0


def is_approval_command(message: str) -> bool:
    """Check if a message is an approval/rejection command"""
    if not message:
        return False
    
    message_lower = message.lower().strip()
    
    # Approval commands
    approval_commands = [
        "yes", "y", "send", "approve", "ok", "okay", "👍", "✅", 
        "send it", "looks good", "good", "go ahead", "approve it"
    ]
    
    # Rejection commands
    rejection_commands = [
        "no", "n", "reject", "cancel", "skip", "👎", "❌", "don't send",
        "do not send", "reject it", "cancel it", "skip it", "no thanks"
    ]
    
    all_commands = approval_commands + rejection_commands
    
    return message_lower in all_commands


def parse_approval_command(message: str) -> str:
    """Parse approval command and return 'approved' or 'rejected'"""
    if not message:
        return "unknown"
    
    message_lower = message.lower().strip()
    
    approval_commands = [
        "yes", "y", "send", "approve", "ok", "okay", "👍", "✅", 
        "send it", "looks good", "good", "go ahead", "approve it"
    ]
    
    rejection_commands = [
        "no", "n", "reject", "cancel", "skip", "👎", "❌", "don't send",
        "do not send", "reject it", "cancel it", "skip it", "no thanks"
    ]
    
    if message_lower in approval_commands:
        return "approved"
    elif message_lower in rejection_commands:
        return "rejected"
    else:
        return "unknown"