from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from maqro_backend.api.deps import get_db_session, get_current_user_id
from maqro_backend.schemas.lead import LeadCreate, LeadResponse
from maqro_backend.crud import (
    create_lead_with_initial_message, 
    get_all_leads_ordered, 
    get_lead_by_id,
    get_lead_stats
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/leads")
async def create_lead(
    lead_data: LeadCreate, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new lead from frontend chat (Supabase compatible)
    
    1. Frontend sends: name, email, phone, car, source, initial message
    2. We create a Lead record in database with user_id for RLS
    3. We save their first message as a Conversation record (if provided)
    4. Return the lead UUID so frontend can reference it
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    logger.info(f"Creating new lead: {lead_data.name} for user: {user_id}")
    
    # Use the combined CRUD operation with user_id for RLS compliance
    result = await create_lead_with_initial_message(
        session=db, 
        lead_in=lead_data, 
        user_id=user_id
    )
    
    logger.info(f"Lead created with ID: {result['lead_id']}")
    
    return result


@router.get("/leads", response_model=List[LeadResponse])
async def get_all_leads(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all leads for the authenticated user (JWT authenticated)
    
    Authentication: Bearer token required in Authorization header
    """
    logger.info(f"📊 Fetching all leads for authenticated user: {user_id}")
    leads = await get_all_leads_ordered(session=db, user_id=user_id)
    logger.info(f"✅ Found {len(leads)} leads for user {user_id}")
    
    # Convert UUIDs to strings for JSON serialization
    return [
        LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car=lead.car,
            source=lead.source,
            status=lead.status,
            last_contact=lead.last_contact,
            message=lead.message,
            user_id=str(lead.user_id),
            created_at=lead.created_at
        ) for lead in leads
    ]


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get specific lead by UUID (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user (additional RLS check)
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return LeadResponse(
        id=str(lead.id),
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        car=lead.car,
        source=lead.source,
        status=lead.status,
        last_contact=lead.last_contact,
        message=lead.message,
        user_id=str(lead.user_id),
        created_at=lead.created_at
    )


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a lead
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
        
    await db.commit()
    await db.refresh(lead)
    
    return lead


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a lead
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    await db.delete(lead)
    await db.commit()
    
    return {"message": "Lead deleted successfully"}


@router.get("/leads/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get lead statistics
    """
    return await get_lead_stats(session=db, user_id=user_id)
