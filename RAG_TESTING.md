# RAG Pipeline Testing Guide

This guide explains how to test the conversational RAG pipeline that powers the dealership AI assistant.

## Quick Start

### 1. Set up your OpenAI API key
```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

### 2. Test the RAG pipeline directly
```bash
python test_rag_pipeline.py "Do you have a white Tiguan under 32k?"
```

## What the RAG Pipeline Does

The RAG (Retrieval-Augmented Generation) pipeline consists of 4 main steps:

1. **Entity Parsing**: Extracts structured information from user messages
   - Make, model, year, color, budget, body type, features
   - Example: "white Tiguan under 32k" → Volkswagen, Tiguan, white, budget_max: 32000

2. **Hybrid Retrieval**: Searches for matching vehicles using both:
   - **Metadata filters**: Exact matches on make, model, year, price, etc.
   - **Vector similarity**: Semantic search for similar vehicles

3. **Prompt Building**: Creates conversational prompts with:
   - **Grounded prompts**: When vehicles are found, include specific details
   - **Generic prompts**: When no vehicles match, ask clarifying questions

4. **LLM Generation**: Uses GPT-4o-mini to generate SMS-style responses

## Example Test Queries

### Specific Vehicle Queries
```bash
python test_rag_pipeline.py "Do you have a white Tiguan under 32k?"
python test_rag_pipeline.py "Looking for a 2021-2023 Civic EX around 20k"
python test_rag_pipeline.py "Any blue Camry SE from 2022?"
```

### General Queries
```bash
python test_rag_pipeline.py "SUV with 3rd row this weekend"
python test_rag_pipeline.py "Any hybrids under 25k?"
python test_rag_pipeline.py "What's your cheapest sedan?"
```

### Clarifying Questions
```bash
python test_rag_pipeline.py "I need a car for my family"
python test_rag_pipeline.py "What do you have in stock?"
```

## Expected Behavior

### When Vehicles Are Found
- **Entity parsing**: Should extract relevant details (make, model, year, budget, etc.)
- **Retrieval**: Should find 1-5 matching vehicles using hybrid search
- **Response**: Conversational, includes specific vehicle details, asks one follow-up question

Example response:
> "Hey! I found a 2022 Volkswagen Tiguan in white for $31,500. It's in great condition with 45k miles and comes with a clean Carfax. Would you like to schedule a test drive this weekend?"

### When No Vehicles Match
- **Entity parsing**: May still extract some details
- **Retrieval**: Returns empty list or low-confidence matches
- **Response**: Helpful, asks clarifying questions

Example response:
> "Hi! I'd love to help you find the perfect vehicle. What's your budget range and do you have any specific features you're looking for? This will help me show you the best options we have available."

## Model Configuration

- **Embedding Model**: `text-embedding-ada-002` (OpenAI)
- **Generation Model**: `gpt-4o-mini` (OpenAI)
- **Vector Store**: FAISS (local file-based)
- **Index File**: `vehicle_index.faiss`

## Troubleshooting

### No OpenAI API Key
```
❌ OPENAI_API_KEY not set. Please set it first:
export OPENAI_API_KEY='sk-your-api-key-here'
```

### No Vector Index
```
⚠️ No vector index found. Please run build_rag_index.py first.
```

### Import Errors
```bash
pip install openai faiss-cpu
```

## Integration with API

The same RAG pipeline is used in the conversation API endpoint:
```
POST /api/conversation/leads/{lead_id}/rag-response
```

This endpoint:
1. Takes a customer message
2. Runs the full RAG pipeline
3. Returns a conversational response
4. Saves the conversation to the database

## Files

- `test_rag_pipeline.py` - Standalone test script
- `src/maqro_rag/` - RAG components (entity parsing, retrieval, prompts)
- `src/maqro_backend/api/routes/conversation.py` - API integration
- `config.yaml` - Configuration settings
- `vehicle_index.faiss` - Vector index (generated from inventory) 