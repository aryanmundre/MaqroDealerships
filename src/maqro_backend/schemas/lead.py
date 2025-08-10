from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class LeadBase(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    car_interest: str | None = None
    source: str | None = None
    max_price: str | None = None


class LeadCreate(LeadBase):
    """Data structure for creating a new lead (Supabase compatible)"""
    name: str | None = None  # Allow None, will auto-generate if missing
    email: str | None = None
    phone: str | None = None
    car_interest: str = "Unknown"  # Required field in Supabase
    source: str = "Website"  # Required field in Supabase
    max_price: str | None = None  # Maximum price range for the lead
    message: str | None = None  # Their initial message/inquiry
    dealership_id: str | None = None  # Will be auto-populated from user's dealership


class LeadResponse(LeadBase):
    """Response model for leads (Supabase compatible with UUIDs)"""
    id: str = Field(..., description="UUID as string")  # Supabase uses UUIDs
    status: str
    last_contact_at: datetime
    message: str | None = None
    deal_value: str | None = None
    appointment_datetime: datetime | None = None
    user_id: str | None = Field(None, description="Assigned salesperson UUID as string")
    dealership_id: str = Field(..., description="Dealership UUID as string")
    created_at: datetime
    model_config = {
        "from_attributes": True
    }


class LeadUpdate(BaseModel):
    """Update model for leads"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    car_interest: str | None = None
    source: str | None = None
    status: str | None = None
    last_contact_at: datetime | None = None
    message: str | None = None
    deal_value: str | None = None
    max_price: str | None = None
    appointment_datetime: datetime | None = None
    user_id: str | None = None  # For assigning/reassigning salesperson
