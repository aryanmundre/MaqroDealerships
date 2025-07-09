from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from maqro_rag import Config, VehicleRetriever
from backend.database import get_db, create_tables
from backend.models import Lead, Conversation

# Global variable to store retriever
retriever = None

# These define the structure of data we expect from the frontend

class LeadCreate(BaseModel):
    """Data structure for creating a new lead"""
    name: str
    email: str 
    phone: str
    message: str  # Their initial message/inquiry

class MessageCreate(BaseModel):
    """Data structure for adding a new message to existing lead"""
    lead_id: int
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs when the app starts up and shuts down
    - Startup: Load RAG system + Create database tables
    - Shutdown: Cleanup (if needed)
    """

    global retriever
    print("Starting up Maqro API...")
    
    # 1. Load RAG system for vehicle search
    config = Config.from_yaml("config.yaml")
    retriever = VehicleRetriever(config)
    retriever.load_index("vehicle_index")
    print("RAG system loaded")
    
    # 2. Create database tables if they don't exist
    await create_tables()
    print("Database tables ready")
    
    yield  # App runs here
    
    # ===== SHUTDOWN =====
    print("Shutting down...")

app = FastAPI(title="Maqro Dealership API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Simple health check - always works"""
    return {"status": "healthy"}

@app.get("/search-vehicles")
async def search_vehicles(query: str, top_k: int = 3):
    """Search for vehicles using RAG system"""
    results = retriever.search_vehicles(query, top_k)
    return {"query": query, "results": results}



@app.post("/leads")
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new lead from frontend chat
    
    1. Frontend sends: name, email, phone, initial message
    2. We create a Lead record in database
    3. We save their first message as a Conversation record
    4. Return the lead ID so frontend can reference it
    """
    print(f" Creating new lead: {lead_data.name}")
    
    # 1. Create new lead record
    new_lead = Lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        status="new"  # All leads start as "new"
    )
    
    # 2. Save lead to database
    db.add(new_lead)
    await db.commit()  # This saves it and assigns an ID
    await db.refresh(new_lead)  # This gets the assigned ID
    
    # 3. Save their initial message as first conversation
    first_conversation = Conversation(
        lead_id=new_lead.id,
        message=lead_data.message,
        sender="customer"
    )
    
    # 4. Save conversation to database
    db.add(first_conversation)
    await db.commit()
    
    print(f"Lead created with ID: {new_lead.id}")
    
    return {
        "lead_id": new_lead.id,
        "status": "created",
        "message": f"Lead {new_lead.name} created successfully"
    }

@app.post("/messages")
async def add_message(message_data: MessageCreate, db: AsyncSession = Depends(get_db)):
    """
    Add new message to existing conversation
    
    1. Frontend sends: lead_id, new message
    2. We verify the lead exists
    3. We save the message as a new Conversation record
    4. Return confirmation
    """
    print(f"Adding message for lead {message_data.lead_id}")
    
    # 1. Check if lead exists
    lead = await db.get(Lead, message_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 2. Create new conversation record
    new_conversation = Conversation(
        lead_id=message_data.lead_id,
        message=message_data.message,
        sender="customer"
    )
    
    # 3. Save to database
    db.add(new_conversation)
    await db.commit()
    
    print(f"Message saved for lead {lead.name}")
    
    return {
        "message": "Message saved successfully",
        "lead_id": message_data.lead_id,
        "lead_name": lead.name
    }


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lead by ID"""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "status": lead.status,
        "created_at": lead.created_at
    }

@app.get("/leads/{lead_id}/conversations")
async def get_conversations(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get all conversations for a lead"""
    # Check if lead exists
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get all conversations for this lead
    result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at)
    )
    conversations = result.scalars().all()
    
    return {
        "lead_name": lead.name,
        "conversations": [
            {
                "id": conv.id,
                "message": conv.message,
                "sender": conv.sender,
                "created_at": conv.created_at
            }
            for conv in conversations
        ]
    }