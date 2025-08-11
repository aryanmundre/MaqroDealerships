from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from maqro_backend.api.deps import get_db_session, get_current_user_id, get_user_dealership_id
from maqro_backend.schemas.conversation import MessageCreate, ConversationResponse
from maqro_backend.schemas.lead import LeadResponse
from maqro_backend.crud import (
    get_lead_by_id,
    create_message,
    get_conversations_by_lead_id
)
from maqro_backend.services.ai_services import get_all_conversation_history
from maqro_rag.entity_parser import EntityParser
from maqro_rag.db_retriever import DatabaseRAGRetriever
from maqro_rag.prompt_builder import PromptBuilder, AgentConfig
from maqro_rag.config import Config
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Database RAG components
rag_config = Config.from_yaml("config.yaml")
vehicle_retriever = DatabaseRAGRetriever(rag_config)
entity_parser = EntityParser()

logger.info("Initialized Database RAG system for conversation API")

# Default agent config
default_agent_config = AgentConfig(
    tone="friendly",
    dealership_name="our dealership",
    persona_blurb="friendly, persuasive car salesperson"
)


@router.post("/messages")
async def add_message(
    message_data: MessageCreate, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add new message to existing conversation (Supabase compatible)
    
    1. Frontend sends: lead_id (UUID), new message
    2. We verify the lead exists and belongs to the user
    3. We save the message as a new Conversation record
    4. Return confirmation
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    logger.info(f"Adding message for lead {message_data.lead_id}")
    
    # 1. Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=message_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 2. Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Create new conversation record
    conversation = await create_message(session=db, message_in=message_data)

    logger.info(f"Message saved for lead {lead.name}")
    
    return {
        "message": "Message saved successfully",
        "lead_id": message_data.lead_id,
        "lead_name": lead.name,
        "conversation_id": conversation.id
    }


@router.get("/leads/{lead_id}/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all conversations for a lead (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    
    # Convert to response format
    return [
        ConversationResponse(
            id=str(conv.id),
            lead_id=str(conv.lead_id),
            message=conv.message,
            sender=conv.sender,
            created_at=conv.created_at
        ) for conv in conversations
    ]


@router.get("/leads/{lead_id}/conversations-with-lead")
async def get_conversations_with_lead_info(
    lead_id: str, 
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all conversations for a lead with lead information included (Supabase compatible)
    
    Headers required:
    - X-User-Id: UUID of the authenticated user (from Supabase)
    """
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify the lead belongs to the authenticated user
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all conversations for this lead
    conversations = await get_conversations_by_lead_id(session=db, lead_id=lead_id)
    
    return {
        "lead": LeadResponse(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            car_interest=lead.car_interest,
            source=lead.source,
            status=lead.status,
            last_contact_at=lead.last_contact_at,
            message=lead.message,
            user_id=str(lead.user_id),
            created_at=lead.created_at
        ),
        "conversations": [
            ConversationResponse(
                id=str(conv.id),
                lead_id=str(conv.lead_id),
                message=conv.message,
                sender=conv.sender,
                created_at=conv.created_at,
            ) for conv in conversations
        ]
    }


@router.post("/leads/{lead_id}/rag-response")
async def generate_rag_response(
    lead_id: str,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    dealership_id: str = Depends(get_user_dealership_id)
):
    """
    Generate conversational RAG response for a customer message.
    
    This endpoint:
    1. Extracts entities from the customer message
    2. Performs hybrid retrieval (metadata filters + vector similarity)
    3. Builds conversational prompt
    4. Generates SMS-style response
    """
    logger.info(f"Generating RAG response for lead {lead_id}")
    
    # 1. Check if lead exists and belongs to user
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if str(lead.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 2. Get conversation history
    conversations = await get_all_conversation_history(lead_id=int(lead_id), db=db)
    
    # 3. Extract entities from customer message
    customer_message = message_data.message
    vehicle_query = entity_parser.parse_message(customer_message)
    
    logger.info(f"Extracted vehicle query: {vehicle_query}")
    
    # 4. Perform database RAG hybrid retrieval
    logger.info(f"Using dealership ID: {dealership_id} for RAG search")
    try:
        if vehicle_query.has_strong_signals:
            retrieved_cars = await vehicle_retriever.search_vehicles_hybrid(
                session=db,
                query=customer_message,
                vehicle_query=vehicle_query,
                dealership_id=dealership_id,
                top_k=5
            )
        else:
            retrieved_cars = await vehicle_retriever.search_vehicles(
                session=db,
                query=customer_message,
                dealership_id=dealership_id,
                top_k=5
            )
        
        logger.info(f"Database RAG retrieved {len(retrieved_cars)} vehicles")
        
    except Exception as e:
        logger.error(f"Error in database vehicle retrieval: {e}")
        retrieved_cars = []
    
    # 5. Build prompt and generate response
    try:
        prompt_builder = PromptBuilder(default_agent_config)
        
        if retrieved_cars and len(retrieved_cars) > 0:
            # Use grounded prompt with retrieved vehicles
            prompt = prompt_builder.build_grounded_prompt(
                user_message=customer_message,
                retrieved_cars=retrieved_cars,
                agent_config=default_agent_config
            )
        else:
            # Use generic prompt for fallback
            prompt = prompt_builder.build_generic_prompt(
                user_message=customer_message,
                agent_config=default_agent_config
            )
        
        # 6. Generate response using existing AI service
        from maqro_backend.services.ai_services import generate_contextual_ai_response
        
        response_text = await generate_contextual_ai_response(
            conversations=conversations,
            vehicles=retrieved_cars,
            lead_name=lead.name
        )
        
        # 7. Save the customer message
        await create_message(session=db, message_in=message_data)
        
        return {
            "response": response_text,
            "retrieved_vehicles": len(retrieved_cars),
            "vehicle_query": {
                "make": vehicle_query.make,
                "model": vehicle_query.model,
                "year_min": vehicle_query.year_min,
                "year_max": vehicle_query.year_max,
                "color": vehicle_query.color,
                "budget_max": vehicle_query.budget_max,
                "body_type": vehicle_query.body_type,
                "features": vehicle_query.features
            },
            "lead_id": lead_id,
            "lead_name": lead.name
        }
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
