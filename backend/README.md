# Maqro Dealership Backend API

A FastAPI-based backend for AI-powered automotive lead management with RAG (Retrieval-Augmented Generation) vehicle search capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Homebrew (macOS)

### 1. Database Setup

#### Install PostgreSQL (macOS)
```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create the database
createdb maqro_dealership
```

#### Verify Database Connection
```bash
psql -h localhost -d maqro_dealership -c "\dt"
```

### 2. Python Environment Setup

#### Install Dependencies
```bash
# From project root directory
pip install -r requirements.txt

# Install additional required packages
pip install greenlet
```

#### Verify Installation
```bash
python -c "
import asyncio
from backend.database import create_tables, engine

async def test_db():
    try:
        await create_tables()
        print('Database connection successful!')
        print('Tables created successfully!')
    except Exception as e:
        print(f'Database error: {e}')
    finally:
        await engine.dispose()

asyncio.run(test_db())
"
```

### 3. Running the Server

#### Option A: Test Server (No API Key Required)
```bash
# Run test server with mock RAG system
python test_server.py
```

#### Option B: Production Server (Requires OpenAI API Key)
```bash
# Set OpenAI API key
export OPENAI_API_KEY="your_openai_api_key_here"

# Build vector index (one-time setup)
python main.py

# Run production server
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access API Documentation
- **Interactive Swagger UI:** http://localhost:8000/docs
- **ReDoc Documentation:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

