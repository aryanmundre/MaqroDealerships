from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from maqro_rag import Config, VehicleRetriever
from backend.database import get_db, create_tables
from backend.models import Lead, Conversation
from backend.serializers import (
    LeadResponse, ConversationResponse, 
    LeadCreate, MessageCreate
)
from backend.ai_services import (
    get_all_conversation_history,
    get_last_customer_message,
    generate_ai_response_text,
    generate_contextual_ai_response
)

# Global variable to store retriever
retriever = None

# These define the structure of data we expect from the frontend

class AIResponseRequest(BaseModel):
    """Data structure for conversation-based AI response requests"""
    include_full_context: Optional[bool] = True

class GeneralAIRequest(BaseModel):
    """Data structure for general AI response (no conversation context)"""
    query: str
    customer_name: Optional[str] = None

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

@app.get("/leads", response_model=List[LeadResponse])
async def get_all_leads(db: AsyncSession = Depends(get_db)):
    """Get all leads with standardized response format"""
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    return leads  # Automatically serialized by Pydantic

@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific lead with standardized response format"""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead  # Automatically serialized by Pydantic

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



@app.post("/conversations/{lead_id}/ai-response")
async def generate_conversation_ai_response(lead_id: int, request_data: Optional[AIResponseRequest] = None,
    db: AsyncSession = Depends(get_db)):
    """
    Generate AI response based on complete conversation history and save it
    This endpoint uses the FULL conversation history to generate contextually aware responses.
    """
    print(f"Generating AI response for lead {lead_id}")
    
    # Check if lead exists
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        # Get complete conversation history (no limits)
        all_conversations = await get_all_conversation_history(lead_id, db)
        
        if not all_conversations:
            raise HTTPException(status_code=400, detail="No conversation history found")
        
        # Get the last customer message for RAG search
        last_customer_message = get_last_customer_message(all_conversations)
        
        if not last_customer_message:
            raise HTTPException(status_code=400, detail="No customer message found to respond to")
        
        # Use RAG system to find relevant vehicles based on last customer message
        vehicles = retriever.search_vehicles(last_customer_message, top_k=3)
        
        # Generate AI response using full conversation context
        ai_response_text = generate_contextual_ai_response(all_conversations, vehicles, lead.name)
        
        # Save AI response to database
        ai_response = Conversation(
            lead_id=lead_id,
            message=ai_response_text,
            sender="agent"
        )
        db.add(ai_response)
        await db.commit()
        await db.refresh(ai_response)
        
        print(f"AI response generated and saved for lead {lead.name}")
        
        return {
            "response_id": ai_response.id,
            "response_text": ai_response_text,
            "lead_id": lead_id,
            "lead_name": lead.name,
            "total_conversations": len(all_conversations),
            "last_customer_message": last_customer_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")


@app.post("/ai-response/general")
async def generate_general_ai_response(request_data: GeneralAIRequest):
    """
    Generate AI response based on general text query (no conversation context)
    """
    print(f"Generating general AI response for query: {request_data.query}")
    
    try:
        # Use RAG system directly
        vehicles = retriever.search_vehicles(request_data.query, top_k=3)
        
        # Generate response
        ai_response_text = generate_ai_response_text(
            request_data.query, 
            vehicles, 
            request_data.customer_name
        )
        
        return {
            "query": request_data.query,
            "response_text": ai_response_text,
            "vehicles_found": len(vehicles),
            "vehicles": vehicles
        }
        
    except Exception as e:
        print(f"Error generating general AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")


@app.get("/leads/{lead_id}/conversations", response_model=List[ConversationResponse])
async def get_conversations(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get all conversations for a lead with standardized response format"""
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
    
    return conversations  # Automatically serialized by Pydantic

@app.get("/leads/{lead_id}/conversations-with-lead")
async def get_conversations_with_lead_info(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get all conversations for a lead with lead information included"""
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
        "lead": LeadResponse.model_validate(lead),
        "conversations": [ConversationResponse.model_validate(conv) for conv in conversations]
    }