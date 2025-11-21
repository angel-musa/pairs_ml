"""
Pytest configuration for backend tests
"""

import sys
import os
from pathlib import Path

# Add parent directory and project root to Python path
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))
