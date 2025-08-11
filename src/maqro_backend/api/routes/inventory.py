"""
Inventory API routes for Supabase integration
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import pandas as pd
from io import BytesIO

from maqro_backend.api.deps import get_db_session, get_current_user_id, get_optional_user_id, get_user_dealership_id, get_optional_user_dealership_id
from maqro_backend.schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate
from maqro_backend.crud import (
    create_inventory_item,
    get_inventory_by_dealership,
    get_inventory_by_id,
    bulk_create_inventory_items,
    get_inventory_count,
    ensure_embeddings_for_dealership
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/inventory", response_model=InventoryResponse)
async def create_inventory(
    inventory_data: InventoryCreate,
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Create a new inventory item (Supabase compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    logger.info(f"Creating inventory item: {inventory_data.make} {inventory_data.model} for dealership: {dealership_id}")
    
    # Convert InventoryCreate to dict for CRUD function
    inventory_dict = inventory_data.model_dump()
    
    inventory = await create_inventory_item(
        session=db,
        inventory_data=inventory_dict,
        dealership_id=dealership_id
    )
    
    # Auto-generate embedding for this new inventory item
    try:
        logger.info(f"🧠 Generating embedding for new inventory item: {inventory.make} {inventory.model}")
        embedding_result = await ensure_embeddings_for_dealership(
            session=db,
            dealership_id=dealership_id
        )
        logger.info(f"✅ Generated {embedding_result.get('built_count', 0)} embeddings")
    except Exception as e:
        logger.warning(f"⚠️ Failed to generate embedding (creation still successful): {e}")
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price or "0",
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
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get all inventory items for the authenticated dealership (Supabase RLS compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    inventory_items = await get_inventory_by_dealership(session=db, dealership_id=dealership_id)
    
    # Log sample items for debugging
    if inventory_items:
        sample_item = inventory_items[0]
        logger.info(f"📝 Sample item: {sample_item.make} {sample_item.model} ({sample_item.year}) - ${sample_item.price}")
    else:
        logger.warning(f"⚠️ No inventory items found for dealership {dealership_id}")
    
    response_items = [
        InventoryResponse(
            id=str(item.id),
            make=item.make,
            model=item.model,
            year=item.year,
            price=item.price or "0",  # Keep as string to handle "TBD", "Call for price" etc.
            mileage=item.mileage,
            description=item.description,
            features=item.features,
            dealership_id=str(item.dealership_id),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ) for item in inventory_items
    ]
    
    logger.info(f"✅ Returning {len(response_items)} formatted inventory items")
    return response_items


@router.get("/inventory/{inventory_id}", response_model=InventoryResponse)
async def get_inventory_item(
    inventory_id: str,
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get specific inventory item by UUID (Supabase compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price or "0",
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
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Update inventory item (Supabase compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields that are provided
    update_data = inventory_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory, field, value)
    
    await db.commit()
    await db.refresh(inventory)
    
    # Auto-refresh embedding for the updated inventory item
    try:
        logger.info(f"🧠 Refreshing embedding for updated inventory item: {inventory.make} {inventory.model}")
        embedding_result = await ensure_embeddings_for_dealership(
            session=db,
            dealership_id=dealership_id
        )
        logger.info(f"✅ Generated {embedding_result.get('built_count', 0)} embeddings")
    except Exception as e:
        logger.warning(f"⚠️ Failed to refresh embedding (update still successful): {e}")
    
    return InventoryResponse(
        id=str(inventory.id),
        make=inventory.make,
        model=inventory.model,
        year=inventory.year,
        price=inventory.price or "0",
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
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Delete inventory item (Supabase compatible)
    
    Headers required:
    - Authorization: Bearer <JWT token>
    """
    inventory = await get_inventory_by_id(session=db, inventory_id=inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Verify the inventory belongs to the authenticated dealership
    if str(inventory.dealership_id) != dealership_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.delete(inventory)
    await db.commit()
        
    return {"message": "Inventory item deleted successfully"}


@router.post("/inventory/upload")
async def upload_inventory_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Upload and process inventory file (CSV or Excel)
    """
        
    # Read file into a pandas DataFrame
    try:
        content = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV or Excel file.")
    except Exception as e:
        logger.error(f"Failed to parse file: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing file: {e}")

    # Data transformation and validation
    df = df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))
    
    required_columns = ['make', 'model', 'year', 'price']
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail=f"Missing required columns: {required_columns}")

    # Convert to list of dicts for CRUD operation
    inventory_list = df.to_dict(orient='records')
    
    # Save to database
    try:
        num_created = await bulk_create_inventory_items(
            session=db,
            inventory_data=inventory_list,
            dealership_id=dealership_id
        )
        
        # Auto-generate embeddings for RAG system
        embedding_result = {"built_count": 0, "error": None}
        try:
            logger.info(f"🧠 Generating embeddings for {num_created} new inventory items...")
            embedding_result = await ensure_embeddings_for_dealership(
                session=db,
                dealership_id=dealership_id
            )
            logger.info(f"✅ Generated {embedding_result.get('built_count', 0)} embeddings")
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate embeddings (upload still successful): {e}")
            embedding_result["error"] = str(e)
        
        return {
            "message": f"Successfully uploaded {num_created} inventory items.",
            "success_count": num_created,
            "error_count": len(inventory_list) - num_created,
            "embeddings_generated": embedding_result.get("built_count", 0),
            "embeddings_error": embedding_result.get("error")
        }
    except Exception as e:
        logger.error(f"Database error during bulk insert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save inventory to database: {e}")


@router.get("/inventory/count", response_model=int)
async def get_inventory_count_for_dealership(
    db: AsyncSession = Depends(get_db_session),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Get the total count of inventory items for the authenticated dealership.
    """
    count = await get_inventory_count(session=db, dealership_id=dealership_id)
    return count
    