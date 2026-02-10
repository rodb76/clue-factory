import test_config
"""
Test the improved JSON parser with edge cases.
"""

from setter_agent import SetterAgent

# Test cases for the hardened parser
test_cases = [
    # Case 1: Clean JSON
    ('{"wordplay_parts": {"fodder": "test"}}', "Clean JSON"),
    
    # Case 2: JSON in code block
    ('```json\n{"wordplay_parts": {"fodder": "test"}}\n```', "Code block"),
    
    # Case 3: Multiple JSON blocks (should take the LAST one)
    ('```json\n{"wrong": "first"}\n```\nWait, let me reconsider...\n```json\n{"wordplay_parts": {"fodder": "correct"}}\n```', "Multiple blocks"),
    
    # Case 4: JSON with extra text
    ('Here is my answer: {"wordplay_parts": {"fodder": "test"}} - and that\'s it.', "Extra text"),
    
    # Case 5: Nested JSON
    ('{"wordplay_parts": {"nested": {"deep": "value"}}}', "Nested JSON"),
]

print("\n" + "="*70)
print("JSON PARSER HARDENING TEST")
print("="*70 + "\n")

for test_input, description in test_cases:
    try:
        result = SetterAgent._parse_json_response(test_input)
        print(f"✓ {description}")
        print(f"  Input: {test_input[:50]}...")
        print(f"  Parsed: {result}")
        print()
    except Exception as e:
        print(f"✗ {description}")
        print(f"  Error: {e}")
        print()

print("="*70)
print("TEST COMPLETE")
print("="*70 + "\n")

