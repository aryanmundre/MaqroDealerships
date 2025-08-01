"""
Inventory API routes for Supabase integration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from maqro_backend.api.deps import get_db_session, get_current_user_id
from maqro_backend.schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate
from maqro_backend.crud import (
    create_inventory_item,
    get_inventory_by_dealership,
    get_inventory_by_id
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/inventory", response_model=InventoryResponse)
async def create_inventory(
    inventory_data: InventoryCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new inventory item (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated dealership (from Supabase)
    """
    logger.info(f"Creating inventory item: {inventory_data.make} {inventory_data.model} for dealership: {user_id}")
    
    # Convert InventoryCreate to dict for CRUD function
    inventory_dict = inventory_data.model_dump()
    
    inventory = await create_inventory_item(
        session=db,
        inventory_data=inventory_dict,
        dealership_id=user_id
    )
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price,
        mileage=inventory.mileage,
        description=inventory.description,
        features=inventory.features,
        dealership_id=str(inventory.dealership_id),
        status=inventory.status,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at
    )


@router.get("/inventory", response_model=List[InventoryResponse])
async def get_dealership_inventory(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all inventory items for the authenticated dealership (Supabase RLS compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated dealership (from Supabase)
    """
    inventory_items = await get_inventory_by_dealership(session=db, dealership_id=user_id)
    
    return [
        InventoryResponse(
            id=str(item.id),
            make=item.make,
            model=item.model,
            year=item.year,
            price=item.price,
            mileage=item.mileage,
            description=item.description,
            features=item.features,
            dealership_id=str(item.dealership_id),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ) for item in inventory_items
    ]


@router.get("/inventory/{inventory_id}", response_model=InventoryResponse)
async def get_inventory_item(
    inventory_id: str,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get specific inventory item by UUID (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated dealership (from Supabase)
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price,
        mileage=inventory.mileage,
        description=inventory.description,
        features=inventory.features,
        dealership_id=str(inventory.dealership_id),
        status=inventory.status,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at
    )


@router.put("/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory_item(
    inventory_id: str,
    inventory_update: InventoryUpdate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update inventory item (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated dealership (from Supabase)
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields that are provided
    update_data = inventory_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory, field, value)
    
    await db.commit()
    await db.refresh(inventory)
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price,
        mileage=inventory.mileage,
        description=inventory.description,
        features=inventory.features,
        dealership_id=str(inventory.dealership_id),
        status=inventory.status,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at
    )


@router.delete("/inventory/{inventory_id}")
async def delete_inventory_item(
    inventory_id: str,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete inventory item (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated dealership (from Supabase)
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.delete(inventory)
    await db.commit()
    
    return {"message": "Inventory item deleted successfully"}
