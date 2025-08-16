#!/bin/bash
# Installation script for Maqro Dealership Backend on Render

set -e

echo "Installing Maqro Dealership Backend..."

# Install Python dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

echo "Installation completed successfully!" 