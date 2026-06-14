"""
pytest configuration and shared fixtures
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path so we can import novel_crawler / modules
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
