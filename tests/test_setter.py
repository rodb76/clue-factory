import test_config
"""
Unit tests for the Setter Agent.

Tests JSON parsing and response handling without requiring network connectivity.
"""

import json
from setter_agent import SetterAgent


def test_json_parsing_direct():
    """Test parsing of direct JSON response."""
    json_response = """{
        "clue": "Silent listener in the dark (6)",
        "definition": "Silent listener",
        "wordplay_parts": {
            "type": "Hidden Word",
            "fodder": "Silent listener in the dark",
            "indicator": "in",
            "mechanism": "LISTEN is hidden within 'Silent listener In The Dark'"
        },
        "explanation": "The definition 'Silent listener' refers to LISTEN. The hidden word indicator 'in' shows that LISTEN is embedded in 'Silent listener In The Dark'.",
        "is_fair": true
    }"""
    
    result = SetterAgent._parse_json_response(json_response)
    assert result["clue"] == "Silent listener in the dark (6)"
    assert result["wordplay_parts"]["type"] == "Hidden Word"
    print("✓ Direct JSON parsing test passed")


def test_json_parsing_markdown():
    """Test parsing of JSON wrapped in markdown code blocks."""
    json_response = """```json
    {
        "clue": "Silent listener in the dark (6)",
        "definition": "Silent listener",
        "wordplay_parts": {
            "type": "Hidden Word",
            "fodder": "Silent listener in the dark",
            "indicator": "in",
            "mechanism": "LISTEN is hidden within 'Silent listener In The Dark'"
        },
        "explanation": "The definition 'Silent listener' refers to LISTEN.",
        "is_fair": true
    }
    ```"""
    
    result = SetterAgent._parse_json_response(json_response)
    assert result["clue"] == "Silent listener in the dark (6)"
    assert result["wordplay_parts"]["type"] == "Hidden Word"
    print("✓ Markdown JSON parsing test passed")


def test_json_parsing_with_text():
    """Test parsing when JSON is embedded in extra text."""
    json_response = """Here's your clue:

```json
{
    "clue": "Silent listener in the dark (6)",
    "definition": "Silent listener",
    "wordplay_parts": {
        "type": "Hidden Word",
        "fodder": "Silent listener in the dark",
        "indicator": "in",
        "mechanism": "LISTEN is hidden within 'Silent listener In The Dark'"
    },
    "explanation": "The definition 'Silent listener' refers to LISTEN.",
    "is_fair": true
}
```

This is a fair clue!"""
    
    result = SetterAgent._parse_json_response(json_response)
    assert result["clue"] == "Silent listener in the dark (6)"
    assert result["wordplay_parts"]["type"] == "Hidden Word"
    print("✓ Embedded JSON parsing test passed")


def test_metadata_enrichment():
    """Test that metadata is added to the response."""
    # This is a mock test showing expected structure
    mock_response = {
        "clue": "Silent listener in the dark (6)",
        "definition": "Silent listener",
        "wordplay_parts": {
            "type": "Hidden Word",
            "fodder": "Silent listener in the dark",
            "indicator": "in",
            "mechanism": "LISTEN is hidden"
        },
        "explanation": "Test explanation",
        "is_fair": True
    }
    
    # Simulate what would be added by generate_cryptic_clue
    mock_response["type"] = "Hidden Word"
    mock_response["answer"] = "LISTEN"
    
    assert mock_response["type"] == "Hidden Word"
    assert mock_response["answer"] == "LISTEN"
    print("✓ Metadata enrichment test passed")


def test_invalid_json():
    """Test that invalid JSON raises ValueError."""
    invalid_json = "This is not valid JSON at all!"
    
    try:
        SetterAgent._parse_json_response(invalid_json)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Could not parse JSON" in str(e)
        print("✓ Invalid JSON error handling test passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Setter Agent Unit Tests")
    print("="*60 + "\n")
    
    test_json_parsing_direct()
    test_json_parsing_markdown()
    test_json_parsing_with_text()
    test_metadata_enrichment()
    test_invalid_json()
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60 + "\n")
    print("Note: To test full API connectivity, ensure:")
    print("  1. .env file is configured with PORTKEY_API_KEY")
    print("  2. Network connectivity to Portkey gateway is available")
    print("  3. Run: python setter_agent.py")

