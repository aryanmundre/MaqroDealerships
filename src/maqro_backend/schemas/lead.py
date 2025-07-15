from pydantic import BaseModel
from datetime import datetime


class LeadBase(BaseModel):
    name: str | None = None
    email: str | None = None  
    phone: str | None = None


class LeadCreate(LeadBase):
    """Data structure for creating a new lead"""
    name: str
    email: str 
    phone: str
    message: str  # Their initial message/inquiry


class LeadResponse(LeadBase):
    id: int
    status: str
    last_response_at: datetime | None = None
    follow_up_count: int
    next_follow_up_at: datetime | None = None
    follow_up_disabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True