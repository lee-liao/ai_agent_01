"""
Pytest configuration for backend tests.
Ensures proper path setup for imports.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path so 'app' module can be found
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add the parent directory (exercise_11) to Python path so 'rag' module can be found
exercise11_dir = backend_dir.parent
if str(exercise11_dir) not in sys.path:
    sys.path.insert(0, str(exercise11_dir))

