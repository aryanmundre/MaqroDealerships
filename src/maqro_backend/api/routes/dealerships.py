"""
Dealership API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from maqro_backend.api.deps import get_db_session, get_current_user_id, get_user_dealership_id
from maqro_backend.schemas.dealership import DealershipCreate, DealershipResponse, DealershipUpdate
from maqro_backend.crud import (
    create_dealership,
    get_dealership_by_id,
    update_dealership
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/dealerships", response_model=DealershipResponse)
async def create_new_dealership(
    dealership_data: DealershipCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new dealership
    
    Note: This endpoint should typically be restricted to admin users only
    """
    logger.info(f"Creating new dealership: {dealership_data.name}")
    
    dealership = await create_dealership(
        session=db,
        name=dealership_data.name,
        location=dealership_data.location
    )
    
    logger.info(f"Dealership created with ID: {dealership.id}")
    
    return DealershipResponse(
        id=str(dealership.id),
        name=dealership.name,
        location=dealership.location,
        created_at=dealership.created_at,
        updated_at=dealership.updated_at
    )


@router.get("/dealerships/current", response_model=DealershipResponse)
async def get_current_dealership(
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get the current user's dealership information
    """
    dealership = await get_dealership_by_id(session=db, dealership_id=dealership_id)
    if not dealership:
        raise HTTPException(status_code=404, detail="Dealership not found")
    
    return DealershipResponse(
        id=str(dealership.id),
        name=dealership.name,
        location=dealership.location,
        created_at=dealership.created_at,
        updated_at=dealership.updated_at
    )


@router.put("/dealerships/current", response_model=DealershipResponse)
async def update_current_dealership(
    dealership_update: DealershipUpdate,
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Update the current user's dealership information
    
    Note: This should typically be restricted to admin users only
    """
    update_data = dealership_update.model_dump(exclude_unset=True)
    
    dealership = await update_dealership(
        session=db,
        dealership_id=dealership_id,
        **update_data
    )
    
    if not dealership:
        raise HTTPException(status_code=404, detail="Dealership not found")
    
    return DealershipResponse(
        id=str(dealership.id),
        name=dealership.name,
        location=dealership.location,
        created_at=dealership.created_at,
        updated_at=dealership.updated_at
    )