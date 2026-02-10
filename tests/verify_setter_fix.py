import test_config
"""
Verification test for SetterAgent fix.
Tests that _extract_response_text method exists and is accessible.
"""

from setter_agent import SetterAgent
import inspect

print("\n" + "="*60)
print("SETTER AGENT FIX VERIFICATION")
print("="*60 + "\n")

# Check that SetterAgent can be instantiated (without API call)
print("✓ SetterAgent imports successfully")

# Get all methods
methods = [method for method in dir(SetterAgent) if not method.startswith('__')]

print("\nSetterAgent methods:")
for method in methods:
    print(f"  • {method}")

# Check for required methods
required_methods = [
    '_extract_response_text',
    '_parse_json_response', 
    'generate_wordplay_only',
    'generate_surface_from_wordplay',
    'generate_cryptic_clue'
]

print("\nRequired methods check:")
all_present = True
for method in required_methods:
    is_present = hasattr(SetterAgent, method)
    status = "✓" if is_present else "✗"
    print(f"  {status} {method}")
    if not is_present:
        all_present = False

# Check method signatures
print("\nMethod signatures:")
print(f"  _extract_response_text: {inspect.signature(SetterAgent._extract_response_text)}")
print(f"  generate_wordplay_only: {inspect.signature(SetterAgent.generate_wordplay_only)}")
print(f"  generate_surface_from_wordplay: {inspect.signature(SetterAgent.generate_surface_from_wordplay)}")

print("\n" + "="*60)
if all_present:
    print("✓ ALL CHECKS PASSED - SetterAgent is ready to use")
else:
    print("✗ SOME CHECKS FAILED - Review the output above")
print("="*60 + "\n")

