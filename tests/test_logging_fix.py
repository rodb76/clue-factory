"""
Test to verify logging handlers are not duplicated on module import.
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging (should only happen once)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("\n" + "="*70)
print("TESTING: No Duplicate Logging Handlers")
print("="*70)

# Count handlers before imports
root_logger = logging.getLogger()
initial_handler_count = len(root_logger.handlers)
print(f"\nInitial handler count: {initial_handler_count}")

# Import all the modules that previously had logging.basicConfig()
print("\nImporting modules...")
from setter_agent import SetterAgent
from auditor import XimeneanAuditor
from solver_agent import SolverAgent
from word_selector import WordSelector
from word_pool_loader import WordPoolLoader
from explanation_agent import ExplanationAgent
from mechanic import validate_clue_complete
from referee import referee_with_validation

# Count handlers after imports
final_handler_count = len(root_logger.handlers)
print(f"Final handler count: {final_handler_count}")

# Test by printing something
print("\nTest message (should appear only once):")
print("="*70)
print("This is a test message that should NOT be duplicated")
print("="*70)

# Verify
if final_handler_count == initial_handler_count:
    print("\n✓ SUCCESS: No duplicate handlers added")
    print(f"  Handlers remained at {final_handler_count}")
else:
    print(f"\n✗ FAILURE: Handler count changed!")
    print(f"  Expected: {initial_handler_count}")
    print(f"  Got: {final_handler_count}")
    print(f"  Extra handlers: {final_handler_count - initial_handler_count}")
    sys.exit(1)

print("\n" + "="*70)
print("Test Complete")
print("="*70 + "\n")
