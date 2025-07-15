from fastapi import APIRouter, Depends
from maqro_rag import VehicleRetriever
from maqro_backend.api.deps import get_rag_retriever
from maqro_backend.schemas.ai import VehicleSearchResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """Simple health check - always works"""
    return {"status": "healthy"}


@router.get("/search-vehicles", response_model=VehicleSearchResponse)
async def search_vehicles(
    query: str, 
    top_k: int = 3,
    retriever: VehicleRetriever = Depends(get_rag_retriever)
):
    """Search for vehicles using RAG system"""
    results = retriever.search_vehicles(query, top_k)
    return VehicleSearchResponse(query=query, results=results)