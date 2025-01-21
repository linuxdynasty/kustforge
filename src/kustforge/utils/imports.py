import os
import sys
from pathlib import Path

def setup_package_imports():
    """
    Set up imports to work both when:
    1. Running from source (during development/testing)
    2. Running as an installed package
    """
    # Get the src directory path
    src_dir = str(Path(__file__).resolve().parents[2])
    
    # Add src directory to Python path if not already there
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir) 