from pydantic import BaseModel
from datetime import datetime


class ConversationBase(BaseModel):
    message: str


class MessageCreate(ConversationBase):
    """Data structure for adding a new message to existing lead"""
    lead_id: int


class ConversationResponse(ConversationBase):
    id: int
    lead_id: int
    sender: str
    created_at: datetime

    class Config:
        from_attributes = True