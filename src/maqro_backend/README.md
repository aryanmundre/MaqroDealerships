# Maqro Dealership Backend API

A FastAPI-based backend for AI-powered automotive lead management with RAG (Retrieval-Augmented Generation) vehicle search capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A Supabase account for database and authentication

### 1. Environment Setup

#### Create and Configure Your Environment
First, create a `.env` file in the root of your project by copying the example file:

```bash
cp env.example .env
```

Next, you'll need to fill in the following required variables in your new `.env` file:

- `OPENAI_API_KEY`: Your API key for OpenAI, used for embedding generation.
- `SUPABASE_JWT_SECRET`: Your Supabase JWT secret for authenticating API requests. You can find this under **Project Settings > API**.
- `SUPABASE_USER`: Your Supabase database user.
- `SUPABASE_PASSWORD`: Your Supabase database password.
- `SUPABASE_HOST`: The host for your Supabase database.
- `SUPABASE_DBNAME`: The name of your Supabase database.
- `SUPABASE_PORT`: The port for your Supabase database (defaults to 5432 if not provided).

You can find your Supabase database credentials in your project's dashboard under **Project Settings > Database**.

### 2. Python Environment and Dependencies

#### Create a Virtual Environment
It's recommended to use a virtual environment to manage your project's dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

#### Install Dependencies
Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

Next, install the project's local packages in editable mode. This allows the backend to correctly import the `maqro_rag` module:

```bash
pip install -e .
```

### 3. Running the Server

With your environment configured and dependencies installed, you can now start the FastAPI server:

```bash
python -m uvicorn src.maqro_backend.main:app --reload --port 8000
```

The server will automatically reload when you make changes to the code.

### 4. Access API Documentation

Once the server is running, you can access the interactive API documentation in your browser:

-   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
-   **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
