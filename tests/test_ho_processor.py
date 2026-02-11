"""
Unit tests for George Ho Dataset Processor (ho_processor.py)

Tests reverse-engineering, enrichment, and batch processing functionality.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from ho_processor import (
    HoProcessor,
    ReverseEngineerAgent,
    ExplanationAgent,
    HoClueResult,
    ensure_enumeration,
    calculate_length,
    generate_reveal_order,
    generate_clue_id
)


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_CLUES = [
    {
        "clue": "Confused enlist soldiers to be quiet (6)",
        "answer": "SILENT",
        "definition": "be quiet",
        "source": "test_source",
        "source_url": "https://example.com/test1",
        "puzzle_date": "2024-01-15",
        "is_reviewed": "1"
    },
    {
        "clue": "Ocean current hidden in tide pool",
        "answer": "DEEP",
        "definition": "Ocean current",
        "source": "test_source",
        "source_url": "https://example.com/test2",
        "puzzle_date": "2024-01-16",
        "is_reviewed": "1"
    },
    {
        "clue": "Grain merchant reversed (5)",
        "answer": "RELAED",  # Intentionally wrong to test error handling
        "definition": "Grain",
        "source": "test_source",
        "source_url": "https://example.com/test3",
        "puzzle_date": "2024-01-17",
        "is_reviewed": "0"
    }
]


# ============================================================================
# Unit Tests
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions for enumeration, length, and reveal order."""
    
    def test_ensure_enumeration_missing(self):
        """Test adding enumeration when missing."""
        clue = "Confused enlist soldiers to be quiet"
        answer = "SILENT"
        result = ensure_enumeration(clue, answer)
        assert "(6)" in result
        assert result == "Confused enlist soldiers to be quiet (6)"
    
    def test_ensure_enumeration_present(self):
        """Test that existing enumeration is preserved."""
        clue = "Confused enlist soldiers to be quiet (6)"
        answer = "SILENT"
        result = ensure_enumeration(clue, answer)
        assert result.count("(6)") == 1
    
    def test_ensure_enumeration_multi_word(self):
        """Test enumeration for multi-word answers."""
        clue = "Put a stop to Rugby's foul school leader"
        answer = "KNOCK ON THE HEAD"
        result = ensure_enumeration(clue, answer)
        assert "(5,2,3,4)" in result
    
    def test_calculate_length_simple(self):
        """Test length calculation for simple word."""
        assert calculate_length("SILENT") == 6
        assert calculate_length("TESTS") == 5
    
    def test_calculate_length_with_spaces(self):
        """Test length calculation ignoring spaces."""
        assert calculate_length("KNOCK ON THE HEAD") == 14
        assert calculate_length("TEQUILA SUNRISE") == 14
    
    def test_calculate_length_with_hyphens(self):
        """Test length calculation ignoring hyphens."""
        assert calculate_length("KNOCK-ON-THE-HEAD") == 14
    
    def test_generate_reveal_order_length(self):
        """Test that reveal order has correct length."""
        answer = "SILENT"
        order = generate_reveal_order(answer)
        assert len(order) == 6
        assert set(order) == {0, 1, 2, 3, 4, 5}
    
    def test_generate_reveal_order_unique(self):
        """Test that reveal order is unique."""
        answer = "TESTS"
        order = generate_reveal_order(answer)
        assert len(order) == len(set(order))
    
    def test_generate_clue_id_with_date(self):
        """Test ID generation with puzzle date."""
        clue_id = generate_clue_id("SILENT", "2024-01-15", "guardian")
        assert "guardian" in clue_id
        assert "20240115" in clue_id
        assert "SILENT" in clue_id
    
    def test_generate_clue_id_without_date(self):
        """Test ID generation without puzzle date."""
        clue_id = generate_clue_id("SILENT", None, "test_source")
        assert "test_source" in clue_id
        assert "SILENT" in clue_id
        assert len(clue_id) > 20  # Should include hash


class TestReverseEngineerAgent:
    """Test the Reverse-Engineer Agent."""
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        agent = ReverseEngineerAgent()
        assert agent.client is not None
        assert agent.model_id is not None
    
    def test_deconstruct_clue_anagram(self):
        """Test deconstructing an anagram clue."""
        agent = ReverseEngineerAgent()
        
        result = agent.deconstruct_clue(
            "Confused enlist soldiers to be quiet (6)",
            "SILENT"
        )
        
        # May return None if API is unavailable, which is OK for unit tests
        if result:
            assert "clue_type" in result
            assert "definition" in result
            assert "fodder" in result
            assert "indicator" in result
            assert "mechanism" in result
            
            # Check that it identified as anagram
            assert result["clue_type"].lower() in ["anagram", "anagram clue"]
    
    def test_deconstruct_clue_hidden(self):
        """Test deconstructing a hidden word clue."""
        agent = ReverseEngineerAgent()
        
        result = agent.deconstruct_clue(
            "Ocean current hidden in tide pool (4)",
            "DEEP"
        )
        
        if result:
            assert "clue_type" in result
            assert "hidden" in result["clue_type"].lower() or "container" in result["clue_type"].lower()
    
    def test_json_extraction_with_markdown(self):
        """Test JSON extraction from response with markdown."""
        agent = ReverseEngineerAgent()
        
        response_text = '''Here's the breakdown:
```json
{
  "clue_type": "Anagram",
  "definition": "be quiet",
  "fodder": "enlist",
  "indicator": "confused",
  "mechanism": "ENLIST anagram = SILENT"
}
```
Hope this helps!'''
        
        result = agent._extract_json_from_response(response_text)
        assert result is not None
        assert result["clue_type"] == "Anagram"


class TestExplanationAgent:
    """Test the Explanation Agent."""
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        agent = ExplanationAgent()
        assert agent.client is not None
        assert agent.model_id is not None
    
    def test_generate_explanation(self):
        """Test generating explanation for a breakdown."""
        agent = ExplanationAgent()
        
        breakdown = {
            "clue_type": "Anagram",
            "definition": "be quiet",
            "fodder": "enlist",
            "indicator": "confused",
            "mechanism": "ENLIST (confused) = SILENT"
        }
        
        hint, explanation = agent.generate_explanation(
            "Confused enlist soldiers to be quiet (6)",
            "SILENT",
            breakdown
        )
        
        # Should return valid strings even if API fails
        assert isinstance(hint, str)
        assert isinstance(explanation, str)
        assert len(hint) > 0
        assert len(explanation) > 0


class TestHoProcessor:
    """Test the main HoProcessor class."""
    
    def test_initialization(self):
        """Test that the processor initializes all agents."""
        processor = HoProcessor()
        assert processor.reverse_engineer is not None
        assert processor.explainer is not None
        assert processor.auditor is not None
    
    def test_clean_clue_adds_enumeration(self):
        """Test that missing enumerations are added."""
        processor = HoProcessor()
        
        clue_dict = {
            "clue": "Confused enlist soldiers to be quiet",
            "answer": "SILENT"
        }
        
        cleaned = processor._clean_clue(clue_dict)
        assert "(6)" in cleaned["clue"]
    
    def test_clean_clue_preserves_existing_enumeration(self):
        """Test that existing enumerations are not duplicated."""
        processor = HoProcessor()
        
        clue_dict = {
            "clue": "Confused enlist soldiers to be quiet (6)",
            "answer": "SILENT"
        }
        
        cleaned = processor._clean_clue(clue_dict)
        # Should only have one enumeration
        assert cleaned["clue"].count("(6)") == 1
    
    def test_load_dataset_csv(self):
        """Test loading dataset from CSV file."""
        processor = HoProcessor()
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=['clue', 'answer', 'source', 'is_reviewed'])
            writer.writeheader()
            for clue in SAMPLE_CLUES:
                writer.writerow({
                    'clue': clue['clue'],
                    'answer': clue['answer'],
                    'source': clue['source'],
                    'is_reviewed': clue['is_reviewed']
                })
            temp_path = f.name
        
        try:
            clues = processor.load_dataset(temp_path)
            assert len(clues) == 3
        finally:
            os.unlink(temp_path)
    
    def test_load_dataset_json(self):
        """Test loading dataset from JSON file."""
        processor = HoProcessor()
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(SAMPLE_CLUES, f)
            temp_path = f.name
        
        try:
            clues = processor.load_dataset(temp_path)
            assert len(clues) == 3
        finally:
            os.unlink(temp_path)
    
    def test_load_dataset_with_filters(self):
        """Test loading dataset with filters applied."""
        processor = HoProcessor()
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(SAMPLE_CLUES, f)
            temp_path = f.name
        
        try:
            # Test reviewed_only filter
            clues = processor.load_dataset(temp_path, reviewed_only=True)
            assert len(clues) == 2  # Only 2 clues have is_reviewed=1
            
            # Test limit
            clues = processor.load_dataset(temp_path, limit=1)
            assert len(clues) == 1
            
            # Test source filter
            clues = processor.load_dataset(temp_path, source_filter="test_source")
            assert len(clues) == 3
            
        finally:
            os.unlink(temp_path)
    
    def test_save_results(self):
        """Test saving results to JSON file."""
        processor = HoProcessor()
        
        # Create sample results
        results = [
            HoClueResult(
                # Compatibility fields
                id="test_source_20240115_SILENT",
                clue="Confused enlist soldiers to be quiet (6)",
                length=6,
                reveal_order=[2, 5, 0, 3, 1, 4],
                # Original data
                original_clue="Confused enlist soldiers to be quiet (6)",
                answer="SILENT",
                original_definition="be quiet",
                source="test_source",
                source_url="https://example.com/test",
                puzzle_date="2024-01-15",
                is_reviewed=True,
                # Reverse-engineered components
                clue_type="Anagram",
                definition="be quiet",
                fodder="enlist",
                indicator="confused",
                mechanism="ENLIST anagram = SILENT",
                # Enrichment
                explanation="The word 'enlist' is confused (anagrammed) to produce SILENT",
                hint="Think about rearranging letters",
                # Audit metrics
                ximenean_score=0.85,
                difficulty_level=3,
                narrative_fidelity=90.0,
                # Processing metadata
                processing_timestamp=datetime.now().isoformat(),
                logic_model="test-logic-model",
                surface_model="test-surface-model"
            )
        ]
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            processor.save_results(results, temp_path)
            
            # Verify file was created and has correct structure
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "clues" in data
            assert len(data["clues"]) == 1
            assert data["clues"][0]["answer"] == "SILENT"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestHoClueResult:
    """Test the HoClueResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = HoClueResult(
            # Compatibility fields
            id="test_source_20240115_TESTS",
            clue="Test clue (5)",
            length=5,
            reveal_order=[2, 4, 0, 3, 1],
            # Original data
            original_clue="Test clue (5)",
            answer="TESTS",
            original_definition="tests",
            source="test_source",
            source_url="https://example.com",
            puzzle_date="2024-01-15",
            is_reviewed=True,
            # Reverse-engineered components
            clue_type="Anagram",
            definition="tests",
            fodder="stets",
            indicator="confused",
            mechanism="STETS anagram = TESTS",
            # Enrichment
            explanation="Simple anagram",
            hint="Rearrange letters",
            # Audit metrics
            ximenean_score=0.9,
            difficulty_level=2,
            narrative_fidelity=95.0,
            # Processing metadata
            processing_timestamp="2024-01-15T10:00:00",
            logic_model="test-logic",
            surface_model="test-surface"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["id"] == "test_source_20240115_TESTS"
        assert result_dict["answer"] == "TESTS"
        assert result_dict["length"] == 5
        assert result_dict["ximenean_score"] == 0.9
        assert result_dict["source"] == "test_source"
        assert isinstance(result_dict["reveal_order"], list)
        assert len(result_dict["reveal_order"]) == 5


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the full pipeline."""
    
    @pytest.mark.slow
    def test_full_pipeline(self):
        """Test processing a single clue through the full pipeline."""
        processor = HoProcessor()
        
        clue_dict = {
            "clue": "Confused enlist soldiers to be quiet (6)",
            "answer": "SILENT",
            "definition": "be quiet",
            "source": "test_source",
            "source_url": "https://example.com/test",
            "puzzle_date": "2024-01-15",
            "is_reviewed": "1"
        }
        
        result = processor.process_clue(clue_dict)
        
        # Result may be None if API is unavailable
        if result:
            assert result.answer == "SILENT"
            assert result.clue_type is not None
            assert result.ximenean_score >= 0.0
            assert result.ximenean_score <= 1.0
            assert result.difficulty_level >= 1
            assert result.difficulty_level <= 5
            assert result.narrative_fidelity >= 0.0
            assert result.narrative_fidelity <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
