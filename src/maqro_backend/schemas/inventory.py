"""
Inventory schemas for Supabase integration
"""
from pydantic import BaseModel, Field
from datetime import datetime


class InventoryBase(BaseModel):
    make: str
    model: str
    year: int
    price: str  # Using string to match DECIMAL type in Supabase
    mileage: int | None = None
    description: str | None = None
    features: str | None = None
    condition: str | None = None


class InventoryCreate(InventoryBase):
    """Data structure for creating inventory items"""
    status: str = "active"


class InventoryUpdate(BaseModel):
    """Update model for inventory items"""
    make: str | None = None
    model: str | None = None
    year: int | None = None
    price: str | None = None
    mileage: int | None = None
    description: str | None = None
    features: str | None = None
    condition: str | None = None
    status: str | None = None


class InventoryResponse(BaseModel):
    """Response model for inventory items (Frontend compatible)"""
    id: str = Field(..., description="UUID as string")
    make: str
    model: str
    year: int
    price: str  # Keep as string to handle "TBD", "Call for price" etc.
    mileage: int | None = None
    description: str | None = None
    features: str | None = None
    condition: str | None = None
    dealership_id: str = Field(..., description="Dealership UUID as string")
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }
