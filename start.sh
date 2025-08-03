#!/bin/bash
# Startup script for Render deployment

# Set the Python path to include the src directory
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Print current directory and Python path for debugging
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Listing src directory:"
ls -la src/

# Start the FastAPI application
exec uvicorn src.maqro_backend.main:app --host 0.0.0.0 --port $PORT 