"""
User profile schemas for Supabase integration
"""
from pydantic import BaseModel, Field
from datetime import datetime


class UserProfileBase(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    role: str | None = None
    timezone: str = "America/New_York"


class UserProfileCreate(UserProfileBase):
    """Data structure for creating a new user profile"""
    dealership_id: str | None = None  # UUID as string


class UserProfileUpdate(BaseModel):
    """Update model for user profiles"""
    dealership_id: str | None = None
    full_name: str | None = None
    phone: str | None = None
    role: str | None = None
    timezone: str | None = None


class UserProfileResponse(UserProfileBase):
    """Response model for user profiles (Supabase compatible)"""
    id: str = Field(..., description="UUID as string")
    user_id: str = Field(..., description="User UUID as string")
    dealership_id: str | None = Field(None, description="Dealership UUID as string")
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }