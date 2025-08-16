from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from maqro_backend.api.deps import get_db_session, get_current_user_id, get_user_dealership_id
from maqro_backend.schemas.lead import LeadCreate, LeadResponse
from maqro_backend.crud import (
    create_lead_with_initial_message, 
    get_all_leads_ordered, 
    get_lead_by_id,
    get_lead_stats,
    get_leads_by_salesperson,
    get_leads_with_conversations_summary_by_salesperson
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
me_router = APIRouter(prefix="/me", tags=["Me / My Leads"])
dealer_router = APIRouter(prefix="/dealership", tags=["Dealer Leads"])


@me_router.get("/leads", response_model=List[LeadResponse])
async def get_my_leads(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
):
    leads = await get_leads_by_salesperson(session=db, salesperson_id=user_id)
    return [
        LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car_interest=lead.car_interest,
            source=lead.source,
            status=lead.status,
            last_contact_at=lead.last_contact_at,
            message=lead.message,
            deal_value=lead.deal_value,
            max_price=lead.max_price,
            appointment_datetime=lead.appointment_datetime,
            user_id=str(lead.user_id) if lead.user_id else None,
            dealership_id=str(lead.dealership_id),
            created_at=lead.created_at
        ) for lead in leads
    ]  

@me_router.get("/leads-with-conversations-summary")
async def get_my_leads_with_conversations_summary(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Optimized endpoint that returns leads with their latest conversation in one query.
    This replaces the N+1 query pattern and dramatically improves performance.
    """
    leads_with_conversations = await get_leads_with_conversations_summary_by_salesperson(
        session=db, 
        salesperson_id=user_id
    )
    return leads_with_conversations


@me_router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_my_lead_by_id(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
):
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead or str(lead.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    return LeadResponse(
        id=str(lead.id),
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        car_interest=lead.car_interest,
        source=lead.source,
        status=lead.status,
        last_contact_at=lead.last_contact_at,
        message=lead.message,
        deal_value=lead.deal_value,
        max_price=lead.max_price,
        appointment_datetime=lead.appointment_datetime,
        user_id=str(lead.user_id) if lead.user_id else None,
        dealership_id=str(lead.dealership_id),
        created_at=lead.created_at
    )


@dealer_router.get("/{dealership_id}/leads", response_model=List[LeadResponse])
async def get_dealership_leads(
    dealership_id: str,
    db: AsyncSession = Depends(get_db_session),
    caller_dealership_id: str = Depends(get_user_dealership_id)
    ):
    if dealership_id != caller_dealership_id:
        raise HTTPException(status_code=403, detail="Access denied to this dealership's leads")
    leads = await get_all_leads_ordered(session=db, dealership_id=dealership_id)
    return [
        LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car_interest=lead.car_interest,
            source=lead.source,
            status=lead.status,
            last_contact_at=lead.last_contact_at,
            message=lead.message,
            deal_value=lead.deal_value,
            max_price=lead.max_price,
            appointment_datetime=lead.appointment_datetime,
            user_id=str(lead.user_id) if lead.user_id else None,
            dealership_id=str(lead.dealership_id),
            created_at=lead.created_at
        ) for lead in leads
    ]

router.include_router(me_router)
router.include_router(dealer_router)

@router.post("/leads")
async def create_lead(
    lead_data: LeadCreate, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Create a new lead from frontend chat (Supabase compatible)
    
    1. Frontend sends: name, email, phone, car, source, initial message
    2. We create a Lead record in database with dealership_id for RLS
    3. We save their first message as a Conversation record (if provided)
    4. Return the lead UUID so frontend can reference it
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    logger.info(f"Creating new lead: {lead_data.name} for dealership: {dealership_id}")
    
    # Use the combined CRUD operation with dealership_id for RLS compliance
    result = await create_lead_with_initial_message(
        session=db, 
        lead_in=lead_data, 
        user_id=user_id,  # Assigned salesperson
        dealership_id=dealership_id
    )
    
    logger.info(f"Lead created with ID: {result['lead_id']}")
    
    return result


@router.get("/leads", response_model=List[LeadResponse])
async def get_all_leads(
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get all leads for the authenticated user's dealership (JWT authenticated)
    
    Authentication: Bearer token required in Authorization header
    """
    logger.info(f"📊 Fetching all leads for dealership: {dealership_id}")
    leads = await get_all_leads_ordered(session=db, dealership_id=dealership_id)
    logger.info(f"✅ Found {len(leads)} leads for dealership {dealership_id}")
    
    # Convert UUIDs to strings for JSON serialization
    return [
        LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car_interest=lead.car_interest,
            source=lead.source,
            status=lead.status,
            last_contact_at=lead.last_contact_at,
            message=lead.message,
            deal_value=lead.deal_value,
            max_price=lead.max_price,
            appointment_datetime=lead.appointment_datetime,
            user_id=str(lead.user_id) if lead.user_id else None,
            dealership_id=str(lead.dealership_id),
            created_at=lead.created_at
        ) for lead in leads
    ]


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get specific lead by UUID (Supabase compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user's dealership (additional RLS check)
    if str(lead.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return LeadResponse(
        id=str(lead.id),
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        car_interest=lead.car_interest,
        source=lead.source,
        status=lead.status,
        last_contact_at=lead.last_contact_at,
        message=lead.message,
        deal_value=lead.deal_value,
        max_price=lead.max_price,
        appointment_datetime=lead.appointment_datetime,
        user_id=str(lead.user_id) if lead.user_id else None,
        dealership_id=str(lead.dealership_id),
        created_at=lead.created_at
    )


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Update a lead
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != 'dealership_id':  # Don't allow changing dealership
            setattr(lead, field, value)
        
    await db.commit()
    await db.refresh(lead)
    
    return LeadResponse(
        id=str(lead.id),
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        car_interest=lead.car_interest,
        source=lead.source,
        status=lead.status,
        last_contact_at=lead.last_contact_at,
        message=lead.message,
        deal_value=lead.deal_value,
        max_price=lead.max_price,
        appointment_datetime=lead.appointment_datetime,
        user_id=str(lead.user_id) if lead.user_id else None,
        dealership_id=str(lead.dealership_id),
        created_at=lead.created_at
    )


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Delete a lead
    """
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    await db.delete(lead)
    await db.commit()
    
    return {"message": "Lead deleted successfully"}


@router.get("/leads/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get lead statistics for the dealership
    """
    return await get_lead_stats(session=db, dealership_id=dealership_id)
