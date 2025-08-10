#!/usr/bin/env python3
"""
CLI script to build RAG index from inventory file.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from maqro_rag.retrieval import VehicleRetriever
from maqro_rag.config import Config


def main():
    parser = argparse.ArgumentParser(description="Build RAG index from inventory file")
    parser.add_argument("inventory_file", help="Path to inventory CSV file")
    parser.add_argument("index_path", help="Path to save the index file")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    
    # Check if inventory file exists
    if not os.path.exists(args.inventory_file):
        print(f"Error: Inventory file '{args.inventory_file}' not found")
        sys.exit(1)
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found")
        sys.exit(1)
    
    try:
        # Load config
        config = Config.from_yaml(args.config)
        
        # Initialize retriever
        retriever = VehicleRetriever(config)
        
        # Build index
        print(f"Building index from '{args.inventory_file}'...")
        retriever.build_index(args.inventory_file, args.index_path)
        
        print(f"Index built successfully and saved to '{args.index_path}'")
        
        # Show stats
        stats = retriever.get_index_stats()
        print(f"Index stats: {stats}")
        
    except Exception as e:
        print(f"Error building index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 