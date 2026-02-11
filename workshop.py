"""
Workshop Agent: Post-processing and refinement for generated clues.

This module analyzes completed clues from final_clues_output.json and:
1. Identifies clues with low narrative/quality scores
2. Suggests alternative mechanisms for problematic words
3. Proposes word swaps for high-quality surfaces with difficult words
4. Preserves excellent clues as-is (no unnecessary workshops)

Quality Thresholds:
- EXCELLENT: narrative_fidelity >= 90% AND ximenean_score >= 0.9
- GOOD: narrative_fidelity >= 80% AND ximenean_score >= 0.8
- NEEDS_WORK: Below these thresholds
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from portkey_ai import Portkey

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class WorkshopSuggestion:
    """Container for workshop suggestions."""
    
    original_word: str
    original_clue: str
    original_type: str
    suggestion_type: str  # "keep_as_is", "alternative_mechanism", "word_swap"
    reason: str
    
    # For alternative mechanism suggestions
    suggested_mechanism: Optional[str] = None
    mechanism_explanation: Optional[str] = None
    
    # For word swap suggestions
    suggested_word: Optional[str] = None
    word_swap_reason: Optional[str] = None
    
    # Scores
    original_narrative_fidelity: float = 100.0
    original_ximenean_score: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "original_word": self.original_word,
            "original_clue": self.original_clue,
            "original_type": self.original_type,
            "suggestion_type": self.suggestion_type,
            "reason": self.reason,
            "scores": {
                "narrative_fidelity": self.original_narrative_fidelity,
                "ximenean_score": self.original_ximenean_score
            }
        }
        
        if self.suggested_mechanism:
            result["alternative_mechanism"] = {
                "type": self.suggested_mechanism,
                "explanation": self.mechanism_explanation
            }
        
        if self.suggested_word:
            result["word_swap"] = {
                "new_word": self.suggested_word,
                "reason": self.word_swap_reason
            }
        
        return result


class WorkshopAgent:
    """Analyzes and suggests improvements for generated cryptic clues."""
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    MODEL_ID = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))
    
    # Quality thresholds
    EXCELLENT_NARRATIVE = 90.0
    EXCELLENT_XIMENEAN = 0.9
    GOOD_NARRATIVE = 80.0
    GOOD_XIMENEAN = 0.8
    
    def __init__(self, timeout: float = 45.0):
        """Initialize the Workshop Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 45.0).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "PORTKEY_API_KEY environment variable not set. "
                "Please set it before initializing the Workshop Agent."
            )
        
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        logger.info(f"Workshop Agent initialized with model: {self.MODEL_ID}")
    
    def _extract_response_text(self, response) -> str:
        """Extract text content from Portkey API response."""
        if not response.choices or len(response.choices) == 0:
            raise ValueError("Empty response from API")
        
        choice = response.choices[0]
        
        if hasattr(choice, 'text') and isinstance(choice.text, str):
            return choice.text
        elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            msg_content = choice.message.content
            if isinstance(msg_content, str):
                return msg_content
            elif isinstance(msg_content, dict):
                return msg_content.get('text', str(msg_content))
            elif isinstance(msg_content, (list, tuple)) and len(msg_content) > 0:
                return str(msg_content[0])
        
        raise ValueError("Could not extract response text from API response")
    
    def _is_excellent(self, clue_data: Dict) -> bool:
        """Check if a clue is excellent quality (no workshop needed)."""
        audit = clue_data.get("audit", {})
        narrative_fidelity = audit.get("narrative_fidelity", 100.0)
        ximenean_score = audit.get("ximenean_score", 1.0)
        
        return (narrative_fidelity >= self.EXCELLENT_NARRATIVE and 
                ximenean_score >= self.EXCELLENT_XIMENEAN)
    
    def _needs_work(self, clue_data: Dict) -> Tuple[bool, str]:
        """Determine if a clue needs workshop attention.
        
        Returns:
            (needs_work, reason)
        """
        audit = clue_data.get("audit", {})
        narrative_fidelity = audit.get("narrative_fidelity", 100.0)
        ximenean_score = audit.get("ximenean_score", 1.0)
        
        if narrative_fidelity < self.GOOD_NARRATIVE:
            return True, f"Low narrative fidelity ({narrative_fidelity:.0f}%)"
        
        if ximenean_score < self.GOOD_XIMENEAN:
            return True, f"Low Ximenean score ({ximenean_score:.2f})"
        
        return False, "Quality acceptable"
    
    def suggest_alternative_mechanism(
        self,
        word: str,
        original_clue: str,
        original_type: str,
        audit_feedback: Dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """Suggest an alternative cryptic mechanism for a problematic word.
        
        Args:
            word: The answer word.
            original_clue: The original clue text.
            original_type: The original clue type.
            audit_feedback: Complete audit feedback dictionary.
        
        Returns:
            (suggested_mechanism, explanation)
        """
        
        # Gather problem areas from audit
        problems = []
        if not audit_feedback.get("narrative_integrity_check", True):
            problems.append(audit_feedback.get("narrative_integrity_feedback", ""))
        if not audit_feedback.get("filler_check", True):
            problems.append(audit_feedback.get("filler_feedback", ""))
        if not audit_feedback.get("indicator_grammar_check", True):
            problems.append(audit_feedback.get("indicator_grammar_feedback", ""))
        
        problem_summary = " | ".join(problems) if problems else "Low quality scores"
        
        system_prompt = """You are a cryptic crossword expert analyzing problematic clues.
Your task is to suggest alternative mechanisms that might work better for difficult words.

Consider:
- Word length and structure (vowel/consonant patterns)
- Reversibility (does the word reversed = another real word?)
- Anagram potential (interesting letter combinations?)
- Hidden word potential (can it hide in common phrases?)
- Double definition potential (does the word have distinct meanings?)

Prioritize mechanisms that produce cleaner, more natural surface readings."""

        user_prompt = f"""Analyze this problematic clue and suggest a better mechanism:

ANSWER WORD: {word}
ORIGINAL CLUE: "{original_clue}"
ORIGINAL TYPE: {original_type}

PROBLEMS IDENTIFIED:
{problem_summary}

Suggest ONE alternative clue type that might work better for this word.
Consider the word's features:
- Length: {len(word)} letters
- Structure: {word}
- Reversed: {word[::-1]}

Available types: Anagram, Hidden Word, Charade, Container, Reversal, Homophone, Double Definition

Return ONLY JSON (no other text) with this structure:
{{
    "suggested_mechanism": "Name of clue type",
    "explanation": "Why this mechanism suits this word better (2-3 sentences)",
    "example_sketch": "Brief outline of how the mechanism would work"
}}"""

        try:
            logger.info(f"Analyzing alternative mechanisms for '{word}'...")
            
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = self._extract_response_text(response)
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                mechanism = result.get("suggested_mechanism", "")
                explanation = result.get("explanation", "") + "\n" + result.get("example_sketch", "")
                return mechanism, explanation
            
            return None, None
            
        except Exception as e:
            logger.error(f"Failed to suggest alternative mechanism: {e}")
            return None, None
    
    def suggest_word_swap(
        self,
        current_word: str,
        clue_surface: str,
        clue_type: str,
        wordplay_parts: Dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """Suggest a better-fitting word for a high-quality surface reading.
        
        This is useful when the clue construction is elegant but the answer word
        doesn't quite fit naturally.
        
        Args:
            current_word: The current answer word.
            clue_surface: The surface reading of the clue.
            clue_type: The clue type.
            wordplay_parts: The wordplay components.
        
        Returns:
            (suggested_word, reason)
        """
        
        fodder = wordplay_parts.get("fodder", "")
        indicator = wordplay_parts.get("indicator", "")
        mechanism = wordplay_parts.get("mechanism", "")
        
        system_prompt = """You are a cryptic crossword expert optimizing word selection.
Your task is to find a better answer word that fits an elegant clue construction.

Consider:
- Similar letter patterns (length, structure)
- Better thematic fit with the surface reading
- More common/accessible vocabulary
- Maintains the same cryptic mechanism"""

        user_prompt = f"""This clue has a good surface reading but the word might not be optimal:

CURRENT ANSWER: {current_word}
CLUE SURFACE: "{clue_surface}"
CLUE TYPE: {clue_type}

WORDPLAY COMPONENTS:
- Fodder: {fodder}
- Indicator: {indicator}
- Mechanism: {mechanism}

Suggest ONE alternative answer word that:
1. Has the same length ({len(current_word)} letters)
2. Can be produced by the same mechanism
3. Fits the surface reading more naturally
4. Is a more common/elegant choice

Return ONLY JSON (no other text) with this structure:
{{
    "suggested_word": "THE_NEW_WORD",
    "reason": "Why this word is a better fit (2-3 sentences)",
    "confidence": "High/Medium/Low"
}}

If NO better word exists, return:
{{
    "suggested_word": null,
    "reason": "Current word is optimal",
    "confidence": "N/A"
}}"""

        try:
            logger.info(f"Analyzing word swap alternatives for '{current_word}'...")
            
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = self._extract_response_text(response)
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                suggested = result.get("suggested_word")
                reason = result.get("reason", "")
                
                if suggested and suggested.upper() != current_word.upper():
                    return suggested.upper(), reason
            
            return None, None
            
        except Exception as e:
            logger.error(f"Failed to suggest word swap: {e}")
            return None, None
    
    def analyze_clue(self, clue_data: Dict) -> WorkshopSuggestion:
        """Analyze a single clue and generate workshop suggestions.
        
        Args:
            clue_data: Dictionary containing clue information and audit results.
        
        Returns:
            WorkshopSuggestion with analysis and recommendations.
        """
        word = clue_data.get("word", "UNKNOWN")
        clue_text = clue_data.get("clue", "")
        clue_type = clue_data.get("clue_type", "")
        audit = clue_data.get("audit", {})
        wordplay_parts = clue_data.get("wordplay_parts", {})
        
        narrative_fidelity = audit.get("narrative_fidelity", 100.0)
        ximenean_score = audit.get("ximenean_score", 1.0)
        
        # Case 1: Excellent quality - keep as is
        if self._is_excellent(clue_data):
            return WorkshopSuggestion(
                original_word=word,
                original_clue=clue_text,
                original_type=clue_type,
                suggestion_type="keep_as_is",
                reason=f"Excellent quality - narrative: {narrative_fidelity:.0f}%, ximenean: {ximenean_score:.2f}",
                original_narrative_fidelity=narrative_fidelity,
                original_ximenean_score=ximenean_score
            )
        
        # Case 2: Needs work - suggest alternative mechanism
        needs_work, work_reason = self._needs_work(clue_data)
        if needs_work:
            suggested_mech, mech_explanation = self.suggest_alternative_mechanism(
                word, clue_text, clue_type, audit
            )
            
            return WorkshopSuggestion(
                original_word=word,
                original_clue=clue_text,
                original_type=clue_type,
                suggestion_type="alternative_mechanism",
                reason=work_reason,
                suggested_mechanism=suggested_mech,
                mechanism_explanation=mech_explanation,
                original_narrative_fidelity=narrative_fidelity,
                original_ximenean_score=ximenean_score
            )
        
        # Case 3: Good quality but might benefit from word swap
        # (Only if surface is solid but word doesn't quite fit)
        if narrative_fidelity >= self.GOOD_NARRATIVE:
            suggested_word, swap_reason = self.suggest_word_swap(
                word, clue_text, clue_type, wordplay_parts
            )
            
            if suggested_word:
                return WorkshopSuggestion(
                    original_word=word,
                    original_clue=clue_text,
                    original_type=clue_type,
                    suggestion_type="word_swap",
                    reason="Surface quality is good - alternative word suggested",
                    suggested_word=suggested_word,
                    word_swap_reason=swap_reason,
                    original_narrative_fidelity=narrative_fidelity,
                    original_ximenean_score=ximenean_score
                )
        
        # Default: Keep as is (good enough)
        return WorkshopSuggestion(
            original_word=word,
            original_clue=clue_text,
            original_type=clue_type,
            suggestion_type="keep_as_is",
            reason=f"Quality acceptable - narrative: {narrative_fidelity:.0f}%, ximenean: {ximenean_score:.2f}",
            original_narrative_fidelity=narrative_fidelity,
            original_ximenean_score=ximenean_score
        )
    
    def workshop_batch(
        self,
        input_file: str = "final_clues_output.json",
        output_file: str = "workshopped_clues.json"
    ) -> Dict:
        """Process a batch of clues and generate workshop recommendations.
        
        Args:
            input_file: Path to input JSON file with generated clues.
            output_file: Path to output JSON file with workshop suggestions.
        
        Returns:
            Dictionary with workshop results and statistics.
        """
        
        logger.info(f"Loading clues from {input_file}...")
        
        # Load input file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return {"error": "Input file not found"}
        
        clues = data.get("clues", [])
        metadata = data.get("metadata", {})
        
        print(f"\nAnalyzing {len(clues)} clues...")
        print("-" * 70)
        
        logger.info(f"Analyzing {len(clues)} clues...")
        
        # Process each clue
        suggestions = []
        stats = {
            "keep_as_is": 0,
            "alternative_mechanism": 0,
            "word_swap": 0
        }
        
        for i, clue_data in enumerate(clues, 1):
            word = clue_data.get("word", "UNKNOWN")
            print(f"[{i}/{len(clues)}] {word}...", end=" ", flush=True)
            logger.info(f"[{i}/{len(clues)}] Analyzing {word}...")
            
            suggestion = self.analyze_clue(clue_data)
            suggestions.append(suggestion)
            stats[suggestion.suggestion_type] += 1
            
            # Print result with emoji indicator
            result_emoji = {
                "keep_as_is": "✓",
                "alternative_mechanism": "🔄",
                "word_swap": "🔀"
            }.get(suggestion.suggestion_type, "•")
            
            print(f"{result_emoji} {suggestion.suggestion_type.replace('_', ' ').upper()}")
            logger.info(f"  → {suggestion.suggestion_type.upper()}: {suggestion.reason}")
        
        # Generate output
        output_data = {
            "metadata": {
                "workshop_date": datetime.now().isoformat(),
                "input_file": input_file,
                "original_metadata": metadata,
                "statistics": {
                    "total_clues": len(clues),
                    "kept_as_is": stats["keep_as_is"],
                    "alternative_mechanism_suggested": stats["alternative_mechanism"],
                    "word_swap_suggested": stats["word_swap"],
                    "improvement_rate": f"{(stats['alternative_mechanism'] + stats['word_swap']) / len(clues) * 100:.1f}%"
                }
            },
            "suggestions": [s.to_dict() for s in suggestions]
        }
        
        # Save output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Print statistics to console (always visible to user)
        print("\n" + "="*70)
        print("WORKSHOP COMPLETE")
        print("="*70)
        print(f"\nStatistics:")
        print(f"  Total clues analyzed: {len(clues)}")
        print(f"  Keep as is: {stats['keep_as_is']} ({stats['keep_as_is']/len(clues)*100:.1f}%)")
        print(f"  Alternative mechanism: {stats['alternative_mechanism']} ({stats['alternative_mechanism']/len(clues)*100:.1f}%)")
        print(f"  Word swap: {stats['word_swap']} ({stats['word_swap']/len(clues)*100:.1f}%)")
        print(f"  Improvement rate: {(stats['alternative_mechanism'] + stats['word_swap']) / len(clues) * 100:.1f}%")
        print(f"\n✓ Results saved to: {output_file}")
        print("="*70 + "\n")
        
        # Also log for debugging
        logger.info(f"Workshop complete: {len(clues)} clues analyzed")
        logger.info(f"Results: {stats['keep_as_is']} kept, {stats['alternative_mechanism']} alternative, {stats['word_swap']} swap")
        
        return output_data


def main():
    """Main entry point for the Workshop Agent."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Workshop Agent: Analyze and improve generated cryptic clues"
    )
    parser.add_argument(
        "-i", "--input",
        default="final_clues_output.json",
        help="Input JSON file with generated clues (default: final_clues_output.json)"
    )
    parser.add_argument(
        "-o", "--output",
        default="workshopped_clues.json",
        help="Output JSON file for workshop suggestions (default: workshopped_clues.json)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("CRYPTIC CLUE WORKSHOP AGENT")
    print("="*70 + "\n")
    
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print()
    
    # Initialize workshop agent
    workshop = WorkshopAgent(timeout=60.0)
    
    # Process batch
    results = workshop.workshop_batch(
        input_file=args.input,
        output_file=args.output
    )
    
    if "error" in results:
        print(f"\n✗ Error: {results['error']}")
        sys.exit(1)
    
    print("\n✓ Workshop complete!")


if __name__ == "__main__":
    # Configure logging when running as standalone
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    main()
