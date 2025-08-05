"""
Dealership schemas for Supabase integration
"""
from pydantic import BaseModel, Field
from datetime import datetime


class DealershipBase(BaseModel):
    name: str
    location: str | None = None


class DealershipCreate(DealershipBase):
    """Data structure for creating a new dealership"""
    pass


class DealershipUpdate(BaseModel):
    """Update model for dealerships"""
    name: str | None = None
    location: str | None = None


class DealershipResponse(DealershipBase):
    """Response model for dealerships (Supabase compatible)"""
    id: str = Field(..., description="UUID as string")
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }