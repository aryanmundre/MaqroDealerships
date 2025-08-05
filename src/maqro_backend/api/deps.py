from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from maqro_rag import VehicleRetriever, EnhancedRAGService
from ..db.session import get_db
from ..core.lifespan import get_retriever, get_enhanced_rag_service
from ..db.models import UserProfile
from .auth import get_current_user_id, get_optional_user_id
import logging
import uuid

logger = logging.getLogger(__name__)


# Re-export for easy importing
get_db_session = get_db
get_rag_retriever = get_retriever   
get_enhanced_rag_services = get_enhanced_rag_service


async def get_user_dealership_id(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> str:
    """
    Extract user's dealership ID from their profile.
    
    This function gets the user ID from the JWT token and then looks up
    their dealership_id from the user_profiles table.
    
    Args:
        user_id: User ID from JWT token (via get_current_user_id dependency)
        db: Database session
        
    Returns:
        str: Dealership ID (UUID) from user's profile
        
    Raises:
        HTTPException: If user profile is missing or dealership_id is null
    """
    logger.info("🏢 Fetching user's dealership ID from profile")
    
    # Look up their profile to get dealership_id
    try:
        user_uuid = uuid.UUID(user_id)
        result = await db.execute(
            select(UserProfile.dealership_id)
            .where(UserProfile.user_id == user_uuid)
        )
        dealership_id = result.scalar_one_or_none()
        
        if not dealership_id:
            logger.error(f"❌ No dealership found for user {user_id}")
            raise HTTPException(
                status_code=403, 
                detail="User profile not found or not associated with a dealership"
            )
        
        logger.info(f"✅ Found dealership ID: {dealership_id} for user: {user_id}")
        return str(dealership_id)
        
    except ValueError:
        logger.error(f"❌ Invalid user ID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error(f"❌ Database error fetching dealership for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching user dealership information"
        )


async def get_optional_user_dealership_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[str]:
    """
    Extract user's dealership ID from their profile, returns None if no token provided.
    
    This is useful for endpoints that can work with or without authentication.
    
    Args:
        credentials: Optional HTTP credentials
        db: Database session
        
    Returns:
        Optional[str]: Dealership ID if valid token provided, None otherwise
    """
    if not credentials or credentials.scheme != "Bearer":
        return None
        
    try:
        user_id = await get_optional_user_id(credentials)
        if not user_id:
            return None
            
        user_uuid = uuid.UUID(user_id)
        result = await db.execute(
            select(UserProfile.dealership_id)
            .where(UserProfile.user_id == user_uuid)
        )
        dealership_id = result.scalar_one_or_none()
        return str(dealership_id) if dealership_id else None
        
    except Exception:
        return None


# Re-export secure authentication functions from auth module
# These replace the old insecure header-based authentication
# get_current_user_id and get_optional_user_id are now imported from .auth