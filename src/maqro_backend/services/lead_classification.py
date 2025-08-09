"""
Automated Lead Classification Service

This service automatically classifies leads based on time-based engagement patterns.
It only handles time-based statuses that can be determined from conversation data:

- "new":       Lead created within the last 24 hours (no engagement yet)
- "warm":      Customer actively engaging (replied within 24 hours)  
- "hot":       High engagement (multiple exchanges, quick responses)
- "follow_up": Customer went quiet after engagement (1-7 days since last reply)
- "cold":      Long period of silence (7+ days since last customer message)

Manual statuses (set by salespeople/AI) are preserved:
- "appointment_booked", "deal_won", "deal_lost"
"""

from __future__ import annotations

from datetime import datetime, timedelta
import pytz 
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_backend.crud import get_conversations_by_lead_id
from maqro_backend.db.models import Lead


# Classification thresholds
NEW_LEAD_THRESHOLD = timedelta(hours=24)      # Lead is "new" for first 24 hours
WARM_THRESHOLD = timedelta(hours=24)          # Customer replied within 24 hours
HOT_MIN_MESSAGES = 6                          # At least 6 total messages for "hot" status
HOT_RESPONSE_TIME = timedelta(hours=4)        # Quick back-and-forth for "hot" status
FOLLOW_UP_THRESHOLD = timedelta(days=7)       # After 7 days of silence, becomes "cold"

# Statuses that should not be overridden by automated classification
MANUAL_STATUSES = {"appointment_booked", "deal_won", "deal_lost"}



async def classify_lead(session: AsyncSession, lead: Lead) -> bool:
    """
    Classify a single lead based on conversation patterns and timing.
    
    Returns:
        bool: True if status was updated, False otherwise
    """
    # Don't override manual statuses
    if lead.status in MANUAL_STATUSES:
        return False
    
    # Get current time in UTC
    now = datetime.now(pytz.UTC)
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=session, lead_id=str(lead.id))
    
    # Determine new status based on engagement pattern
    new_status = _determine_lead_status(lead, conversations, now)
    
    # Update status if it changed
    if lead.status != new_status:
        lead.status = new_status
        session.add(lead)
        return True
    
    return False


def _determine_lead_status(lead: Lead, conversations: list, now: datetime) -> str:
    """
    Determine the appropriate status for a lead based on conversation patterns.
    """
    # Ensure lead.created_at is timezone-aware
    lead_created = lead.created_at
    if lead_created.tzinfo is None:
        lead_created = lead_created.replace(tzinfo=pytz.UTC)
    
    lead_age = now - lead_created
    
    # No conversations yet
    if not conversations:
        # Lead is "new" if created within the last 24 hours
        return "new" if lead_age < NEW_LEAD_THRESHOLD else "cold"
    
    # Find the most recent customer message
    last_customer_message = None
    last_customer_time = None
    
    for conv in reversed(conversations):
        if conv.sender == "customer":
            last_customer_message = conv
            # Ensure created_at is timezone-aware
            last_customer_time = conv.created_at
            if last_customer_time.tzinfo is None:
                last_customer_time = last_customer_time.replace(tzinfo=pytz.UTC)
            break
    
    # No customer messages yet (only agent messages)
    if last_customer_message is None:
        return "new" if lead_age < NEW_LEAD_THRESHOLD else "cold"
    
    # Calculate time since last customer engagement
    time_since_customer_reply = now - last_customer_time
    
    # Classification logic
    if time_since_customer_reply >= FOLLOW_UP_THRESHOLD:
        # Customer hasn't replied in 7+ days
        return "cold"
    
    elif time_since_customer_reply <= WARM_THRESHOLD:
        # Customer replied within last 24 hours
        if _is_hot_lead(conversations, now):
            return "hot"
        else:
            return "warm"
    
    else:
        # Customer replied 1-7 days ago - needs follow up
        return "follow_up"


def _is_hot_lead(conversations: list, now: datetime) -> bool:
    """
    Determine if a lead should be classified as "hot" based on engagement patterns.
    
    A lead is "hot" if:
    1. There are at least 6 total messages (3+ exchanges)
    2. There's been recent back-and-forth activity
    3. Response times are relatively quick
    """
    if len(conversations) < HOT_MIN_MESSAGES:
        return False
    
    # Check for recent back-and-forth activity
    recent_messages = [c for c in conversations if _is_recent_message(c, now)]
    
    if len(recent_messages) < 4:  # At least 2 exchanges in recent activity
        return False
    
    # Check for alternating conversation (back-and-forth pattern)
    return _has_back_and_forth_pattern(recent_messages)


def _is_recent_message(conversation, now: datetime, hours: int = 48) -> bool:
    """Check if a message was sent within the last X hours."""
    msg_time = conversation.created_at
    if msg_time.tzinfo is None:
        msg_time = msg_time.replace(tzinfo=pytz.UTC)
    
    return (now - msg_time) <= timedelta(hours=hours)


def _has_back_and_forth_pattern(conversations: list) -> bool:
    """
    Check if there's a back-and-forth conversation pattern.
    
    Returns True if there are alternating customer/agent messages,
    indicating active engagement.
    """
    if len(conversations) < 4:
        return False
    
    # Check last 6 messages for alternating pattern
    recent_senders = [c.sender for c in conversations[-6:]]
    
    # Count sender changes (indicates back-and-forth)
    sender_changes = 0
    for i in range(1, len(recent_senders)):
        if recent_senders[i] != recent_senders[i-1]:
            sender_changes += 1
    
    # At least 2 sender changes indicates back-and-forth
    return sender_changes >= 2


async def classify_all_leads(session: AsyncSession, dealership_id: str = None, batch_size: int = 100) -> dict:
    """
    Classify all leads in the system or for a specific dealership.
    
    Args:
        session: Database session
        dealership_id: Optional dealership ID to limit classification scope
        batch_size: Number of leads to process in each batch
        
    Returns:
        dict: Summary of classification results
    """
    offset = 0
    total_processed = 0
    total_updated = 0
    status_counts = {}
    
    while True:
        # Build query
        query = select(Lead).order_by(Lead.id).limit(batch_size).offset(offset)
        
        if dealership_id:
            query = query.where(Lead.dealership_id == dealership_id)
        
        # Get batch of leads
        result = await session.execute(query)
        leads = list(result.scalars())
        
        if not leads:
            break
        
        # Process each lead in the batch
        batch_updated = 0
        for lead in leads:
            # Skip leads with manual statuses
            if lead.status in MANUAL_STATUSES:
                continue
                
            was_updated = await classify_lead(session, lead)
            if was_updated:
                batch_updated += 1
                
            # Track status counts
            status = lead.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Commit batch
        await session.commit()
        
        total_processed += len(leads)
        total_updated += batch_updated
        offset += batch_size
    
    return {
        "total_processed": total_processed,
        "total_updated": total_updated,
        "status_distribution": status_counts,
        "timestamp": datetime.now(pytz.UTC).isoformat()
    } 