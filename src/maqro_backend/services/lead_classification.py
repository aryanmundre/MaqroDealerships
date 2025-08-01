"""
Lead classification criteria:
    - "new":          Lead created within the last 24 h.
    - "warm":         Customer replied within the last 48 h.
    - "follow_up":    No customer reply for 2-4 days after the last agent message.
    - "cold":         No customer reply for 4+ days.
    - "hot":          Ongoing thread of at least 3 agent/customer pairs
                       (≥ 6 total messages).
"""

from __future__ import annotations

from datetime import datetime, timedelta
import pytz 
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_backend.crud import get_conversations_by_lead_id
# from maqro_backend.db.models.lead import Lead  # Removed - using raw SQL now
# from maqro_backend.db.models.conversation import Conversation  # Removed - using raw SQL now


WARM_THRESHOLD = timedelta(days=2)
FOLLOW_UP_MIN = timedelta(days=2)
FOLLOW_UP_MAX = timedelta(days=4)
COLD_THRESHOLD = timedelta(days=4)
HOT_MIN_MESSAGES = 4 
HOT_FOLLOW_UP_THRESHOLD = timedelta(days=4)
HOT_COLD_THRESHOLD = timedelta(days=10)



async def classify_lead(session: AsyncSession, lead: Lead) -> None:
    """Classify one lead and update its status"""

    conversations = await get_conversations_by_lead_id(session, lead.id)
    if not conversations:
        return  

    last_msg = conversations[-1]
    if last_msg.sender != "agent":
        return

    now = datetime.now(pytz.utc)

    last_customer_time = None
    for conv in reversed(conversations):
        if conv.sender == "customer":
            last_customer_time = conv.created_at.replace(tzinfo=pytz.utc)
            break
        
        

    if last_customer_time is None:
        # Set to new unless lead is older than 1 day
        age = now - lead.created_at.replace(tzinfo=pytz.utc)
        new_status = "new" if age < timedelta(days=1) else "cold"
    else:
        silence = now - last_customer_time
        if len(conversations) >= HOT_MIN_MESSAGES:
            if silence < HOT_FOLLOW_UP_THRESHOLD:
                new_status = "hot"
            elif HOT_FOLLOW_UP_THRESHOLD <= silence  < HOT_COLD_THRESHOLD:
                new_status = "follow_up"
            else:
                new_status = "cold"
        elif silence < WARM_THRESHOLD:
            new_status = "warm"
        elif silence < COLD_THRESHOLD:
            new_status = "follow_up"
        else:
            new_status = "cold"


    if lead.status != new_status:
        lead.status = new_status
        session.add(lead)


async def classify_all_leads(session: AsyncSession, batch_size: int = 500) -> None:
    """Iterate over all the leads and classify them by their status."""

    offset = 0
    while True:
        result = await session.execute(
            select(Lead).order_by(Lead.id).limit(batch_size).offset(offset)
        )
        leads = list(result.scalars())
        if not leads:
            break

        for lead in leads:
            await classify_lead(session, lead)

        await session.commit()
        offset += batch_size 