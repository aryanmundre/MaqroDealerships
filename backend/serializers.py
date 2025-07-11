from pydantic import BaseModel
from typing import Optional
from datetime import datetime

"""
Serializers for API respones to standardize data output and input formats
"""

# Response serializers (what we send back)
class LeadResponse(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: str
    last_response_at: Optional[datetime]
    follow_up_count: int
    next_follow_up_at: Optional[datetime]
    follow_up_disabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    lead_id: int
    message: str
    sender: str
    created_at: datetime

    class Config:
        from_attributes = True

# Request serializers (what we receive)
class LeadCreate(BaseModel):
    """Data structure for creating a new lead"""
    name: str
    email: str 
    phone: str
    message: str  # Their initial message/inquiry

class MessageCreate(BaseModel):
    """Data structure for adding a new message to existing lead"""
    lead_id: int
    message: str