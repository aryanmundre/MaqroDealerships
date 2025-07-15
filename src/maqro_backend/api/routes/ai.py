from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from maqro_rag import VehicleRetriever
from maqro_backend.api.deps import get_db_session, get_rag_retriever
from maqro_backend.schemas.ai import AIResponseRequest, GeneralAIRequest
from maqro_backend.crud import (
    get_lead_by_id,
    get_all_conversation_history,
    create_conversation
)
from ...services.ai_services import (
    get_last_customer_message,
    generate_ai_response_text,
    generate_contextual_ai_response
)

router = APIRouter()


@router.post("/conversations/{lead_id}/ai-response")
async def generate_conversation_ai_response(
    lead_id: int, 
    request_data: AIResponseRequest = None,
    db: AsyncSession = Depends(get_db_session),
    retriever: VehicleRetriever = Depends(get_rag_retriever)
):
    """
    Generate AI response based on complete conversation history and save it
    This endpoint uses the FULL conversation history to generate contextually aware responses.
    """
    print(f"Generating AI response for lead {lead_id}")
    
    # Check if lead exists
    lead = await get_lead_by_id(session=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        # Get complete conversation history (no limits)
        all_conversations = await get_all_conversation_history(session=db, lead_id=lead_id)
        
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
        ai_response = await create_conversation(
            session=db,
            lead_id=lead_id,
            message=ai_response_text,
            sender="agent"
        )
        
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


@router.post("/ai-response/general")
async def generate_general_ai_response(
    request_data: GeneralAIRequest,
    retriever: VehicleRetriever = Depends(get_rag_retriever)
):
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