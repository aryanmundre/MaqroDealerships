from fastapi import FastAPI
from .core.config import settings
from .core.lifespan import lifespan
from .api.routes import api_router


app = FastAPI(
    title=settings.title,
    version=settings.version,
    lifespan=lifespan
)

# Include all API routes
app.include_router(api_router, prefix="/api/routes")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Maqro Dealership API", "version": settings.version} 