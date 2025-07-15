from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_backend.api.deps import get_db_session
from maqro_backend.schemas.lead import LeadCreate, LeadResponse
from maqro_backend.crud import create_lead_with_initial_message, get_all_leads_ordered, get_lead_by_id

router = APIRouter()


@router.post("/leads")
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Create a new lead from frontend chat
    
    1. Frontend sends: name, email, phone, initial message
    2. We create a Lead record in database
    3. We save their first message as a Conversation record
    4. Return the lead ID so frontend can reference it
    """
    print(f"Creating new lead: {lead_data.name}")
    
    # Use the combined CRUD operation
    result = await create_lead_with_initial_message(session=db, lead_in=lead_data)
    
    print(f"Lead created with ID: {result['lead_id']}")
    
    return result


@router.get("/leads", response_model=list[LeadResponse])
async def get_all_leads(db: AsyncSession = Depends(get_db_session)):
    """Get all leads with standardized response format"""
    leads = await get_all_leads_ordered(session=db)
    return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get specific lead with standardized response format"""
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
