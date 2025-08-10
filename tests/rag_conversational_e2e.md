# Conversational RAG End-to-End Test Scenarios

This document contains test scenarios for the enhanced conversational RAG system.

## Test Setup

1. Ensure the RAG index is built: `python -m src.maqro_rag.retrieval build_index sample_inventory.csv vehicle_index.faiss`
2. Start the backend server: `python -m src.maqro_backend.main`
3. Use the new endpoint: `POST /api/conversation/leads/{lead_id}/rag-response`

## Test Scenarios

### Scenario 1: Specific Vehicle Query with Budget
**Input:** "Do you have a white Tiguan under 32k?"

**Expected Retrieval Behavior:**
- Entity extraction: make="volkswagen", model="tiguan", color="white", budget_max=32000
- Metadata filters applied: make=volkswagen, model=tiguan, color=white, price<=32000
- Vector similarity ranking on filtered results
- Top 3-5 matches returned

**Expected Conversational Response:**
"Hey! I found a 2021 Volkswagen Tiguan in white for $29,500 with 28,000 miles. It's in great condition and ready for a test drive. Would you like to come by this weekend to check it out?"

### Scenario 2: Year Range with Model
**Input:** "Looking for a 2021–2023 Civic EX around 20k."

**Expected Retrieval Behavior:**
- Entity extraction: make="honda", model="civic", trim="ex", year_min=2021, year_max=2023, budget_max=20000
- Metadata filters: make=honda, model=civic, year between 2021-2023, price<=20000
- Hybrid search with vector ranking

**Expected Conversational Response:**
"Perfect! I've got a 2022 Honda Civic EX with 35,000 miles for $19,800. It's loaded with features and has a clean history. When would you like to take it for a spin?"

### Scenario 3: Body Type with Feature
**Input:** "SUV with 3rd row this weekend."

**Expected Retrieval Behavior:**
- Entity extraction: body_type="suv", features=["3rd row"]
- Weak signals - fallback to vector similarity search
- Semantic search for "SUV third row"

**Expected Conversational Response:**
"I'd love to help you find the perfect SUV with a third row! What's your budget range, and do you have a preference for make or size? This will help me show you the best options we have available."

### Scenario 4: Feature-Based Query
**Input:** "Any hybrids under 25k?"

**Expected Retrieval Behavior:**
- Entity extraction: features=["hybrid"], budget_max=25000
- Metadata filter: price<=25000, then vector search for hybrid features
- Semantic matching for hybrid/electric vehicles

**Expected Conversational Response:**
"Great timing! I have a 2021 Toyota Prius with 42,000 miles for $23,900. It's in excellent condition and gets amazing fuel economy. Want me to hold it for you to see this week?"

### Scenario 5: Specific Vehicle Reference
**Input:** "Do you still have the blue Camry SE from your site?"

**Expected Retrieval Behavior:**
- Entity extraction: make="toyota", model="camry", trim="se", color="blue"
- Metadata filters: make=toyota, model=camry, color=blue
- Vector similarity for "Camry SE blue"

**Expected Conversational Response:**
"Let me check our current inventory for that blue Camry SE. Can you tell me what year it was and roughly when you saw it on our site? This will help me find the exact vehicle you're interested in."

## Testing Commands

### 1. Test Entity Parser
```python
from src.maqro_rag.entity_parser import EntityParser

parser = EntityParser()
query = parser.parse_message("Do you have a white Tiguan under 32k?")
print(f"Make: {query.make}")
print(f"Model: {query.model}")
print(f"Color: {query.color}")
print(f"Budget: {query.budget_max}")
```

### 2. Test Hybrid Retrieval
```python
from src.maqro_rag.retrieval import VehicleRetriever
from src.maqro_rag.config import Config
from src.maqro_rag.entity_parser import EntityParser

config = Config.from_yaml("config.yaml")
retriever = VehicleRetriever(config)
retriever.load_index("vehicle_index.faiss")

parser = EntityParser()
query = parser.parse_message("Do you have a white Tiguan under 32k?")
results = retriever.search_vehicles_hybrid("Do you have a white Tiguan under 32k?", query)
print(f"Found {len(results)} vehicles")
```

### 3. Test Prompt Builder
```python
from src.maqro_rag.prompt_builder import PromptBuilder, AgentConfig

agent_config = AgentConfig(
    tone="friendly",
    dealership_name="ABC Motors",
    persona_blurb="friendly, persuasive car salesperson"
)

builder = PromptBuilder(agent_config)
prompt = builder.build_grounded_prompt(
    "Do you have a white Tiguan under 32k?",
    [{"vehicle": {"year": 2021, "make": "Volkswagen", "model": "Tiguan", "price": 29500, "color": "white"}}]
)
print(prompt)
```

### 4. Test API Endpoint
```bash
curl -X POST "http://localhost:8000/api/conversation/leads/{lead_id}/rag-response" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: {user_id}" \
  -d '{
    "message": "Do you have a white Tiguan under 32k?",
    "sender": "customer"
  }'
```

## Expected Response Format
```json
{
  "response": "Hey! I found a 2021 Volkswagen Tiguan in white for $29,500...",
  "retrieved_vehicles": 3,
  "vehicle_query": {
    "make": "volkswagen",
    "model": "tiguan",
    "year_min": null,
    "year_max": null,
    "color": "white",
    "budget_max": 32000.0,
    "body_type": null,
    "features": []
  },
  "lead_id": "uuid",
  "lead_name": "John Doe"
}
```

## Success Criteria

1. **Entity Extraction**: Correctly identifies make, model, year, color, budget, features
2. **Hybrid Retrieval**: Applies metadata filters first, then vector similarity
3. **Conversational Response**: 2-5 sentences, SMS-style, one clear CTA
4. **Fallback Handling**: Graceful handling when no strong matches found
5. **Performance**: Response time under 2 seconds for typical queries 