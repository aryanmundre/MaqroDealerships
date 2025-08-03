#!/bin/bash
# Build script for Render deployment

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

echo "Build completed successfully!" 