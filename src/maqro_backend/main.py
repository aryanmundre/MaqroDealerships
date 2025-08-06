import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.lifespan import lifespan
from .api.routes import api_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.title,
    version=settings.version,
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:3000",  # Allow frontend origin
    "https://your-frontend-domain.vercel.app",  # Add your Vercel domain here
    "https://*.vercel.app",  # Allow all Vercel subdomains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router, prefix="/api")

# Startup event to log authentication configuration
@app.on_event("startup")
async def startup_event():
    """Log authentication configuration on startup"""
    if hasattr(settings, 'supabase_jwt_secret') and settings.supabase_jwt_secret:
        logger.info(" JWT Authentication ENABLED - Supabase JWT secret configured")
        logger.info(" Protected endpoints will require valid Bearer tokens")
    else:
        logger.error(" JWT Authentication NOT CONFIGURED - SUPABASE_JWT_SECRET missing!")
        logger.error(" All protected endpoints will reject requests!")
    
    logger.info(f"🚀 {settings.title} v{settings.version} started successfully")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Maqro Dealership API", "version": settings.version}
