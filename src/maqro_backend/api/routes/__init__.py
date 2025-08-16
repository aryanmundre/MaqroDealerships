from fastapi import APIRouter
from .import health, leads, conversation, ai, inventory, dealerships, user_profiles, vonage, whatsapp

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(leads.router, tags=["leads"])
api_router.include_router(conversation.router, tags=["conversations"])
api_router.include_router(inventory.router, tags=["inventory"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(dealerships.router, tags=["dealerships"])
api_router.include_router(user_profiles.router, tags=["user-profiles"])
api_router.include_router(vonage.router, prefix="/vonage", tags=["vonage"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"]) 