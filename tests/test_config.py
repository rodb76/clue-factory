import test_config
"""
Test configuration and path setup.

This module ensures that tests can import from the parent directory (where the main source code lives).
Import this at the top of test files before importing project modules.
"""

import sys
import os

# Add parent directory to path so we can import project modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

