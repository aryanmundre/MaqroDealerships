from contextlib import asynccontextmanager
from fastapi import FastAPI
from maqro_rag import Config, VehicleRetriever

# Global variable to store retriever
retriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global retriever
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    retriever.load_index("vehicle_index")
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(title="Maqro Dealership API", lifespan=lifespan)

@app.get("/search-vehicles")
async def search_vehicles(query: str, top_k: int = 3):
    results = retriever.search_vehicles(query, top_k)
    return {"query": query, "results": results}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}