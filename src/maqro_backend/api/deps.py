from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_rag import VehicleRetriever, EnhancedRAGService
from ..db.session import get_db
from ..core.lifespan import get_retriever, get_enhanced_rag_service
from .auth import get_current_user_id, get_optional_user_id


# Re-export for easy importing
get_db_session = get_db
get_rag_retriever = get_retriever   
get_enhanced_rag_services = get_enhanced_rag_service

# Re-export secure authentication functions from auth module
# These replace the old insecure header-based authentication
# get_current_user_id and get_optional_user_id are now imported from .auth