#!/usr/bin/env python3
"""
Test server for Maqro API without requiring OpenAI API key
This mocks the RAG system for testing basic functionality
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from maqro_backend.db.session import get_db, create_tables
from maqro_backend.db.models.lead import Lead
from maqro_backend.db.models.conversation import Conversation
from maqro_backend.schemas import (
    LeadResponse, ConversationResponse,
    LeadCreate, MessageCreate
)
from maqro_backend.services.ai_services import (
    get_all_conversation_history,
    get_last_customer_message
    generate_ai_response_text,
    generate_contextual_ai_response
)

# Mock RAG system for testing
class MockRetriever:
    """Mock RAG retriever that returns fake vehicle data for testing"""
    
    def search_vehicles(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return mock vehicle search results"""
        mock_vehicles = [
            {
                'rank': 1,
                'similarity_score': 0.95,
                'vehicle': {
                    'year': 2022,
                    'make': 'Toyota',
                    'model': 'Corolla',
                    'price': 21000,
                    'features': 'Lane Assist, Android Auto, Apple CarPlay',
                    'description': 'Compact and reliable sedan, ideal for commuters with excellent fuel economy'
                }
            },
            {
                'rank': 2,
                'similarity_score': 0.87,
                'vehicle': {
                    'year': 2023,
                    'make': 'Honda',
                    'model': 'Civic',
                    'price': 23500,
                    'features': 'Honda Sensing, Apple CarPlay, Android Auto',
                    'description': 'Sporty compact car with advanced safety features and great handling'
                }
            },
            {
                'rank': 3,
                'similarity_score': 0.82,
                'vehicle': {
                    'year': 2023,
                    'make': 'Tesla',
                    'model': 'Model 3',
                    'price': 42000,
                    'features': 'Autopilot, Supercharging, Premium Interior',
                    'description': 'Electric sedan with cutting-edge technology and instant acceleration'
                }
            }
        ]
        
        # Filter to return only top_k results
        return mock_vehicles[:top_k]

# Global mock retriever
retriever = MockRetriever()

# Request/Response models (imported from serializers)

class AIResponseRequest(BaseModel):
    include_full_context: Optional[bool] = True

class GeneralAIRequest(BaseModel):
    query: str
    customer_name: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simplified lifespan that only creates database tables"""
    print("Starting up Maqro TEST API...")
    
    # Only create database tables (no RAG system)
    await create_tables()
    print("Database tables ready")
    print("Using MOCK RAG system for testing")
    
    yield
    
    print("Shutting down...")

app = FastAPI(title="Maqro Dealership TEST API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "mode": "test"}

@app.get("/search-vehicles")
async def search_vehicles(query: str, top_k: int = 3):
    """Search for vehicles using mock RAG system"""
    results = retriever.search_vehicles(query, top_k)
    return {"query": query, "results": results, "mode": "mock"}

@app.post("/leads")
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Create a new lead"""
    print(f"Creating new lead: {lead_data.name}")
    
    new_lead = Lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        status="new"
    )
    
    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)
    
    first_conversation = Conversation(
        lead_id=new_lead.id,
        message=lead_data.message,
        sender="customer"
    )
    
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
    """Add new message to existing conversation"""
    print(f"Adding message for lead {message_data.lead_id}")
    
    lead = await db.get(Lead, message_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    new_conversation = Conversation(
        lead_id=message_data.lead_id,
        message=message_data.message,
        sender="customer"
    )
    
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
    """Generate AI response using mock RAG system"""
    print(f"Generating AI response for lead {lead_id}")
    
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        all_conversations = await get_all_conversation_history(lead_id, db)
        
        if not all_conversations:
            raise HTTPException(status_code=400, detail="No conversation history found")
        
        last_customer_message = get_last_customer_message(all_conversations)
        
        if not last_customer_message:
            raise HTTPException(status_code=400, detail="No customer message found to respond to")
        
        # Use mock RAG system
        vehicles = retriever.search_vehicles(last_customer_message, top_k=3)
        
        ai_response_text = generate_contextual_ai_response(all_conversations, vehicles, lead.name)
        
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
            "last_customer_message": last_customer_message,
            "mode": "mock"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

@app.post("/ai-response/general")
async def generate_general_ai_response(request_data: GeneralAIRequest):
    """Generate AI response using mock RAG system"""
    print(f"Generating general AI response for query: {request_data.query}")
    
    try:
        vehicles = retriever.search_vehicles(request_data.query, top_k=3)
        
        ai_response_text = generate_ai_response_text(
            request_data.query, 
            vehicles, 
            request_data.customer_name
        )
        
        return {
            "query": request_data.query,
            "response_text": ai_response_text,
            "vehicles_found": len(vehicles),
            "vehicles": vehicles,
            "mode": "mock"
        }
        
    except Exception as e:
        print(f"Error generating general AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

@app.get("/leads", response_model=List[LeadResponse])
async def get_all_leads(db: AsyncSession = Depends(get_db)):
    """Get all leads with standardized response format"""
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    return leads  # Automatically serialized by Pydantic

@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lead by ID with standardized response format"""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead  # Automatically serialized by Pydantic

@app.get("/leads/{lead_id}/conversations", response_model=List[ConversationResponse])
async def get_conversations(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get all conversations for a lead with standardized response format"""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
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
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 