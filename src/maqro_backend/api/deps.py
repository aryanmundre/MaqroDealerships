from typing import Annotated
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_rag import VehicleRetriever, EnhancedRAGService
from ..db.session import get_db
from ..core.lifespan import get_retriever, get_enhanced_rag_service
import uuid


# Re-export for easy importing
get_db_session = get_db
get_rag_retriever = get_retriever   
get_enhanced_rag_services = get_enhanced_rag_service


async def get_current_user_id(
    x_user_id: str = Header(..., description="User ID from Supabase auth")
) -> str:
    """
    Extract user ID from request headers (Supabase auth integration)
    
    In a real implementation, you would validate the JWT token here.
    For now, we'll just validate the UUID format.
    """
    try:
        # Validate UUID format
        uuid.UUID(x_user_id)
        return x_user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401, 
            detail="Invalid user ID format. Must be a valid UUID."
        )


async def get_optional_user_id(
    x_user_id: str = Header(None, description="Optional User ID from Supabase auth")
) -> str | None:
    """
    Extract optional user ID from request headers
    Returns None if not provided or invalid
    """
    if not x_user_id:
        return None
    
    try:
        # Validate UUID format
        uuid.UUID(x_user_id)
        return x_user_id
    except (ValueError, TypeError):
        return None