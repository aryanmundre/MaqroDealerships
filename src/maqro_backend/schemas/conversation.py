from pydantic import BaseModel, Field
from datetime import datetime


class ConversationBase(BaseModel):
    message: str


class MessageCreate(ConversationBase):
    """Data structure for adding a new message to existing lead (Supabase compatible)"""
    lead_id: str = Field(..., description="Lead UUID as string")  # Changed to string for UUID compatibility


class ConversationResponse(ConversationBase):
    """Response model for conversations (Supabase compatible)"""
    id: str  # Auto-increment integer ID
    lead_id: str = Field(..., description="Lead UUID as string")
    sender: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(ConversationBase):
    """Create model for conversations"""
    lead_id: str = Field(..., description="Lead UUID as string")
    sender: str
