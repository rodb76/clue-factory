"""
Explanation Agent: Generate user-friendly hints and breakdowns.

This module implements Phase 6 functionality to create conversational
explanations of cryptic clues, including progressive hints and full
step-by-step breakdowns.
"""

import os
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

from portkey_ai import Portkey

# Configure logging
# Note: logging.basicConfig() should only be called in the main entry point (main.py)
# to avoid duplicate handlers when modules are imported
logger = logging.getLogger(__name__)


@dataclass
class ExplanationResult:
    """Result from generating explanations."""
    
    hints: Dict[str, str]
    full_breakdown: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hints": self.hints,
            "full_breakdown": self.full_breakdown
        }


class ExplanationAgent:
    """
    Explanation Agent for generating user-friendly hints and breakdowns.
    
    Uses SURFACE_MODEL_ID (Haiku) for conversational style generation.
    """
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    SURFACE_MODEL_ID = os.getenv("SURFACE_MODEL_ID", os.getenv("MODEL_ID"))
    
    def __init__(self, timeout: float = 30.0):
        """Initialize the Explanation Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "PORTKEY_API_KEY environment variable not set. "
                "Please set it before initializing the Explanation Agent."
            )
        
        self.client = Portkey(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            timeout=timeout
        )
        
        logger.info(f"ExplanationAgent initialized with SURFACE_MODEL_ID: {self.SURFACE_MODEL_ID}")
    
    def generate_explanation(
        self,
        clue: str,
        answer: str,
        clue_type: str,
        definition: str,
        wordplay_parts: Dict
    ) -> ExplanationResult:
        """
        Generate conversational hints and full breakdown for a clue.
        
        Args:
            clue: The complete clue text.
            answer: The answer word.
            clue_type: Type of clue (e.g., "Hidden Word", "Anagram").
            definition: The definition part of the clue.
            wordplay_parts: Dict containing fodder, indicator, mechanism, etc.
        
        Returns:
            ExplanationResult with hints and full breakdown.
        """
        
        system_prompt = """You are a friendly cryptic crossword instructor helping users understand clues.
You create conversational explanations that feel natural and educational, not mechanical.

Your tone should be warm and encouraging, like a teacher revealing secrets to an eager student.
Use phrases like "Notice how...", "The key here is...", "Watch out for...", etc.

You will generate THREE progressive hints and ONE full breakdown."""

        # Build context about wordplay parts
        wordplay_context = json.dumps(wordplay_parts, indent=2)
        
        user_prompt = f"""Generate explanations for this cryptic clue:

CLUE: "{clue}"
ANSWER: {answer}
TYPE: {clue_type}
DEFINITION: "{definition}"
WORDPLAY DETAILS:
{wordplay_context}

Return ONLY JSON (no other text) with this structure:
{{
    "hints": {{
        "indicators": "Conversational hint about the indicator's function and what operation it signals",
        "fodder": "Conversational hint about the raw materials and letters being used",
        "definition": "Conversational hint that MUST quote the exact definition text '{definition}' from the clue - never provide dictionary definitions or paraphrases"
    }},
    "full_breakdown": "A complete step-by-step walk-through explaining how the wordplay mechanically produces the answer, written in a warm educational tone."
}}

CRITICAL RULE FOR DEFINITION HINTS:
- ALWAYS use the EXACT text "{definition}" from the clue when discussing the definition
- DO NOT provide dictionary definitions like "case" or "sheath" unless those exact words appear in the clue
- Quote the definition substring directly: "Our definition here is '{definition}'"

EXAMPLE STYLE for "How illusionist disguises a dead giveaway?" (Answer: WILL):
{{
    "hints": {{
        "indicators": "This clue's indicator is 'disguises', and it's a hidden word indicator that tells us the answer is concealed somewhere in the nearby text. Hidden word clues are like treasure hunts - the letters are right there in front of you!",
        "fodder": "This clue's fodder is 'How illusionist'. We'll use these letters as our raw material. Remember, in hidden word clues, the answer is spelled out consecutively within the fodder - no anagramming needed!",
        "definition": "Our definition here is 'a dead giveaway' and our answer will be a word that matches that meaning. Think about what 'a dead giveaway' might refer to in legal or formal contexts - something left behind with instructions."
    }},
    "full_breakdown": "Let's crack this clue step by step! First, notice 'disguises' - that's our hidden word indicator, telling us the answer is concealed somewhere. Looking at 'How illusionist', we need to find consecutive letters that spell our answer. If we look carefully: 'ho**W ILL**usionist' - there it is! W-I-L-L hidden in plain sight. And 'a dead giveaway?' is our definition, which cleverly refers to a legal WILL (something literally given away after death). The surface reading makes you think of magic tricks, but the wordplay is hiding the real treasure!"
}}

Now generate explanations for the provided clue using this conversational, educational style."""

        try:
            logger.info(f"Generating explanation for '{answer}' [Model: SURFACE]")
            
            response = self.client.chat.completions.create(
                model=self.SURFACE_MODEL_ID,
                max_tokens=800,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract response text
            response_text = self._extract_response_text(response)
            
            # Log for debugging
            logger.debug(f"Raw response_text type: {type(response_text)}")
            logger.debug(f"Raw response_text: {str(response_text)[:200]}")
            
            if not response_text:
                logger.error("Empty response from ExplanationAgent")
                return self._create_fallback_explanation(clue, answer, clue_type, definition, wordplay_parts)
            
            # Parse JSON
            explanation_json = self._parse_json_response(response_text)
            
            if not explanation_json:
                logger.error(f"Failed to parse explanation JSON: {response_text[:200]}")
                return self._create_fallback_explanation(clue, answer, clue_type, definition, wordplay_parts)
            
            # Validate structure
            if "hints" not in explanation_json or "full_breakdown" not in explanation_json:
                logger.warning("Incomplete explanation structure, using fallback")
                return self._create_fallback_explanation(clue, answer, clue_type, definition, wordplay_parts)
            
            hints = explanation_json["hints"]
            if not all(key in hints for key in ["indicators", "fodder", "definition"]):
                logger.warning("Missing hint keys, supplementing")
                hints.setdefault("indicators", "The indicator signals the wordplay operation.")
                hints.setdefault("fodder", "The fodder provides the raw letters for wordplay.")
                hints.setdefault("definition", f"Our definition is '{definition}' which points to the answer {answer}.")
            
            # Validate that definition hint references the exact definition text from the clue
            if definition and definition.lower() not in hints["definition"].lower():
                logger.warning(f"Definition hint missing exact text '{definition}', correcting...")
                # Prepend the exact definition reference
                hints["definition"] = f"Our definition here is '{definition}'. " + hints["definition"]
            
            return ExplanationResult(
                hints=hints,
                full_breakdown=explanation_json["full_breakdown"]
            )
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._create_fallback_explanation(clue, answer, clue_type, definition, wordplay_parts)
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Portkey response (handles multiple formats)."""
        try:
            # Format 1: response.choices[0].message.content (OpenAI format)
            if hasattr(response, 'choices') and response.choices:
                # Handle list or ValidatorIterator
                choices = list(response.choices) if hasattr(response.choices, '__iter__') else [response.choices]
                if choices:
                    if hasattr(choices[0], 'message'):
                        content = choices[0].message.content
                        # Handle ValidatorIterator or list in content
                        if hasattr(content, '__iter__') and not isinstance(content, str):
                            content_list = list(content)
                            if content_list:
                                # Check if it's a dict with 'text' key (Anthropic format)
                                if isinstance(content_list[0], dict) and 'text' in content_list[0]:
                                    return content_list[0]['text']
                                elif hasattr(content_list[0], 'text'):
                                    return content_list[0].text
                                return str(content_list[0])
                            return ""
                        return content
                    elif hasattr(choices[0], 'text'):
                        return choices[0].text
            
            # Format 2: response.content (Anthropic format)
            if hasattr(response, 'content'):
                content = response.content
                # Handle ValidatorIterator or list
                if hasattr(content, '__iter__') and not isinstance(content, str):
                    content_list = list(content)
                    if content_list:
                        # Check if it's a dict with 'text' key (Anthropic format)
                        if isinstance(content_list[0], dict) and 'text' in content_list[0]:
                            return content_list[0]['text']
                        elif hasattr(content_list[0], 'text'):
                            return content_list[0].text
                        return str(content_list[0])
                    return ""
                elif isinstance(content, str):
                    return content
            
            # Format 3: Direct string
            if isinstance(response, str):
                return response
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            return ""
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from response text, handling various formats."""
        
        # Handle dict response with 'text' key (Anthropic format)
        if isinstance(text, dict) and 'text' in text:
            text = text['text']
        
        # Handle string
        if not isinstance(text, str):
            text = str(text)
        
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        if text.startswith('```'):
            text = text[3:]  # Remove ```
        if text.endswith('```'):
            text = text[:-3]  # Remove trailing ```
        text = text.strip()
        
        try:
            # Try direct parsing first
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting JSON block from text
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            return None
    
    def _create_fallback_explanation(
        self,
        clue: str,
        answer: str,
        clue_type: str,
        definition: str,
        wordplay_parts: Dict
    ) -> ExplanationResult:
        """Create a basic explanation when LLM generation fails."""
        
        indicator = wordplay_parts.get("indicator", "the indicator")
        fodder = wordplay_parts.get("fodder", "the wordplay material")
        mechanism = wordplay_parts.get("mechanism", "the wordplay operation")
        
        hints = {
            "indicators": f"This {clue_type} clue uses '{indicator}' as its indicator, which signals how to manipulate the letters.",
            "fodder": f"The wordplay uses '{fodder}' as its raw material for the {clue_type.lower()} operation.",
            "definition": f"The definition '{definition}' points to the answer {answer}."
        }
        
        full_breakdown = f"""This clue uses a {clue_type} structure. The definition is "{definition}", which means {answer}. The wordplay mechanism is: {mechanism}. The indicator "{indicator}" signals this operation, and working with the fodder "{fodder}", we arrive at the answer {answer}."""
        
        return ExplanationResult(
            hints=hints,
            full_breakdown=full_breakdown
        )


if __name__ == "__main__":
    """Test the Explanation Agent with a sample clue."""
    
    print("\n" + "="*80)
    print("EXPLANATION AGENT TEST")
    print("="*80 + "\n")
    
    agent = ExplanationAgent()
    
    # Test with example clue
    result = agent.generate_explanation(
        clue="How illusionist disguises a dead giveaway?",
        answer="WILL",
        clue_type="Hidden Word",
        definition="a dead giveaway",
        wordplay_parts={
            "type": "Hidden Word",
            "fodder": "How illusionist",
            "indicator": "disguises",
            "mechanism": "hidden in 'ho[W ILL]usionist'"
        }
    )
    
    print("Hints:")
    print("-" * 80)
    print(f"\nIndicators: {result.hints['indicators']}")
    print(f"\nFodder: {result.hints['fodder']}")
    print(f"\nDefinition: {result.hints['definition']}")
    
    print("\n" + "="*80)
    print("Full Breakdown:")
    print("-" * 80)
    print(result.full_breakdown)
    print("\n" + "="*80)
