#!/usr/bin/env python3
"""
Test script to verify package imports work correctly.
This should be run after installation to ensure all modules can be imported.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all required modules can be imported."""
    try:
        print("Testing package imports...")
        
        # Test maqro_rag imports
        print("  Testing maqro_rag imports...")
        from maqro_rag import Config, VehicleRetriever, EnhancedRAGService
        print("    ✓ maqro_rag imports successful")
        
        # Test maqro_backend imports
        print("  Testing maqro_backend imports...")
        from maqro_backend.main import app
        from maqro_backend.core.config import settings
        print("    ✓ maqro_backend imports successful")
        
        # Test FastAPI app creation
        print("  Testing FastAPI app creation...")
        from maqro_backend.main import app
        print(f"    ✓ FastAPI app created: {app.title}")
        
        print("\n✅ All imports successful! Package is ready for deployment.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 