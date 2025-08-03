#!/bin/bash
# Startup script for Render deployment

# Set the Python path to include the src directory
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Start the FastAPI application
exec uvicorn src.maqro_backend.main:app --host 0.0.0.0 --port $PORT 