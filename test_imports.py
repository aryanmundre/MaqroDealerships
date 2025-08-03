#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")

try:
    from maqro_rag import Config, VehicleRetriever, EnhancedRAGService
    print("✅ maqro_rag imports successful")
except ImportError as e:
    print(f"❌ maqro_rag import failed: {e}")

try:
    from maqro_backend.core.config import settings
    print("✅ maqro_backend config import successful")
except ImportError as e:
    print(f"❌ maqro_backend config import failed: {e}")

try:
    from maqro_backend.core.lifespan import lifespan
    print("✅ maqro_backend lifespan import successful")
except ImportError as e:
    print(f"❌ maqro_backend lifespan import failed: {e}")

print("Import test completed!") 