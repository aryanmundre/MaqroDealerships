from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class LeadBase(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    car: str | None = None
    source: str | None = None


class LeadCreate(LeadBase):
    """Data structure for creating a new lead (Supabase compatible)"""
    name: str
    email: str | None = None
    phone: str | None = None
    car: str = "Unknown"  # Required field in Supabase
    source: str = "Website"  # Required field in Supabase
    message: str | None = None  # Their initial message/inquiry


class LeadResponse(LeadBase):
    """Response model for leads (Supabase compatible with UUIDs)"""
    id: str = Field(..., description="UUID as string")  # Supabase uses UUIDs
    status: str
    last_contact: str
    message: str | None = None
    user_id: str = Field(..., description="User UUID as string")
    created_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    """Update model for leads"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    car: str | None = None
    source: str | None = None
    status: str | None = None
    last_contact: str | None = None
    message: str | None = None
