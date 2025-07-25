from pydantic import BaseModel


class AIResponseRequest(BaseModel):
    """Data structure for conversation-based AI response requests"""
    include_full_context: bool | None = True


class GeneralAIRequest(BaseModel):
    """Data structure for general AI response (no conversation context)"""
    query: str
    customer_name: str | None = None


class AIResponse(BaseModel):
    """Response from AI endpoints"""
    response_text: str
    query: str | None = None
    lead_id: int | None = None
    lead_name: str | None = None
    response_time_sec: int | None = None


class VehicleSearchResponse(BaseModel):
    """Response from vehicle search"""
    query: str
    results: list