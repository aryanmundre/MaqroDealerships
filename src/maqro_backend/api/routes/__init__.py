from fastapi import APIRouter
from .import health, leads, conversation, ai

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(leads.router, tags=["leads"])
api_router.include_router(conversation.router, tags=["conversations"])
api_router.include_router(ai.router, tags=["ai"]) 