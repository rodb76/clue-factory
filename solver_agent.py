"""
Solver Agent: Attempts to solve cryptic clues using LLM reasoning.

This module implements the "Solver" component of the adversarial loop.
It receives only the clue text and enumeration, and attempts to solve it
using step-by-step cryptic crossword reasoning.
"""

import asyncio
import sys
import os
import json
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

# Fix: Force Windows to use the correct event loop policy
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

from portkey_ai import Portkey


class SolverAgent:
    """
    Solver Agent responsible for solving cryptic crossword clues.
    
    Uses Portkey AI Gateway to communicate with Claude 3.5 Sonnet.
    Receives only the clue text and enumeration - no answer provided.
    """
    
    # Configuration constants (same as Setter)
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    # Use logic model for careful reasoning in solving
    MODEL_ID = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))
    
    def __init__(self, timeout: float = 45.0):
        """
        Initialize the Solver Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 45.0).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "PORTKEY_API_KEY environment variable not set. "
                "Please set it before initializing the Solver Agent."
            )
        
        # Initialize Portkey client with explicit base_url and api_key
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        logger.info(f"Solver Agent initialized with model: {self.MODEL_ID} [LOGIC tier]")
    
    def solve_clue(self, clue_text: str, enumeration: str) -> Dict:
        """
        Attempt to solve a cryptic crossword clue.
        
        Args:
            clue_text: The clue text (e.g., "Confused listen").
            enumeration: The letter count (e.g., "(6)" or "(3,4)").
        
        Returns:
            A dictionary containing:
            - answer: The proposed solution
            - reasoning: Step-by-step solving process
            - confidence: High/Medium/Low confidence level
            - clue_type: Identified clue type (if determined)
            - definition_part: Identified definition
            - wordplay_part: Identified wordplay
        
        Raises:
            ValueError: If the API response is invalid or JSON parsing fails.
            Exception: If the API call fails.
        """
        
        system_prompt = """You are an expert cryptic crossword solver. You solve clues using systematic step-by-step reasoning.

When solving a clue, follow these steps:
0. MANDATORY STEP 0: First, look for a hidden word. If the answer is physically written inside the clue text itself (consecutive letters spanning words), that is almost certainly the solution. Check this BEFORE trying complex wordplay.
   IMPORTANT: If the enumeration is (5) and you find a 5-letter word hidden consecutively in the clue letters, that IS the answer. Do not suggest synonyms that don't fit the wordplay - the hidden word must match the enumeration EXACTLY.
1. Identify the DEFINITION (usually at start or end)
2. Identify any INDICATORS (words suggesting wordplay type)
3. Identify the WORDPLAY mechanism (anagram, hidden word, charade, etc.)
4. Work through the wordplay mechanically
5. Verify the answer matches both definition and wordplay
6. FINAL CHECK: Before outputting the answer, identify which part of the clue is the 'Straight Definition.' The final answer MUST be a synonym of that definition. If your proposed answer is just a rearrangement of the wordplay letters but doesn't match the definition, it is WRONG.
7. SOUND-ALIKE CONSTRAINT: If you find two sound-alikes (e.g., WAIL/WHALE), choose the one that matches the DEFINITION given in the surface. The answer must be a synonym of the definition, not just phonetically similar.

CRITICAL: Your response must contain NOTHING but the JSON object. Do not include introductory text like 'I will solve this...' or concluding thoughts. Start with '{' and end with '}'. No preamble, no explanation outside the JSON.

WARNING: Any text outside the JSON brackets is a SYSTEM-BREAKING ERROR. If you write "Let me analyze..." before the JSON, the system will CRASH. Output ONLY the JSON object, nothing else."""

        user_prompt = f"""Solve this cryptic crossword clue:

Clue: "{clue_text}"
Enumeration: {enumeration}

Think step-by-step through the solving process, then provide your answer.

IMPORTANT: The answer must be a SYNONYM of the DEFINITION, not a repetition of the wordplay fodder.
For example, if the wordplay is an anagram of 'enlist', the answer is 'SILENT' (meaning quiet), not 'ENLIST'.
The definition tells you WHAT the answer means, the wordplay tells you HOW to get the letters.

CRITICAL: DO NOT EXPLAIN YOUR STEPS OUTSIDE THE JSON. PROVIDE ONLY THE JSON. If you include any text outside the JSON block, the system will fail. Start your response with '{{' immediately.

Your response MUST be valid JSON (and ONLY JSON) with exactly this structure:
{{
    "reasoning": "Step-by-step explanation (max 50 words): First, I identify... Then I notice... The wordplay works as...",
    "definition_part": "The part of the clue that is the straight definition",
    "wordplay_part": "The part that contains the wordplay",
    "clue_type": "Anagram|Hidden Word|Charade|Container|Reversal|Homophone|Double Definition|&lit|Unknown",
    "answer": "YOUR ANSWER IN CAPITALS",
    "confidence": "High|Medium|Low"
}}

IMPORTANT: Keep your reasoning concise (max 50 words) to ensure the JSON does not get truncated.

Return ONLY the JSON. Do not include 'I'll solve this' or any Step 0 preamble text inside or outside the JSON block."""

        try:
            logger.info(f"Solving clue: '{clue_text}' {enumeration}")
            
            # Make API request using the Portkey client
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=800,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            
            logger.info(f"API response received")
            
            # Extract the text content from the response
            if not response.choices or len(response.choices) == 0:
                raise ValueError("Empty response from API")
            
            choice = response.choices[0]
            
            # Try different ways to access the content
            response_text = None
            
            if hasattr(choice, 'text') and isinstance(choice.text, str):
                response_text = choice.text
            elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                msg_content = choice.message.content
                if isinstance(msg_content, str):
                    response_text = msg_content
                elif isinstance(msg_content, dict):
                    response_text = msg_content.get('text', '')
                elif isinstance(msg_content, (list, tuple)) and len(msg_content) > 0:
                    first_item = msg_content[0]
                    if isinstance(first_item, dict):
                        response_text = first_item.get('text', str(first_item))
                    else:
                        response_text = str(first_item)
                else:
                    # Try to convert iterator/complex type to list
                    try:
                        msg_list = list(msg_content)
                        if msg_list and isinstance(msg_list[0], dict):
                            response_text = msg_list[0].get('text', '')
                        elif msg_list:
                            response_text = str(msg_list[0])
                    except:
                        response_text = str(msg_content)
            
            if not response_text:
                raise ValueError("Could not extract response text from API response")
            
            logger.debug(f"Response text extracted (first 100 chars): {response_text[:100] if len(response_text) > 100 else response_text}")
            
            # Parse JSON response
            solution_json = self._parse_json_response(response_text)
            
            # Add metadata
            solution_json["clue"] = clue_text
            solution_json["enumeration"] = enumeration
            
            logger.info(f"Solution proposed: {solution_json.get('answer', 'UNKNOWN')}")
            return solution_json
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON in API response: {e}") from e
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "connecttimeout" in error_msg:
                logger.error(
                    f"API request timed out. The Portkey endpoint may be unreachable. "
                    f"Check your network connectivity and API key configuration."
                )
            logger.error(f"API call failed: {e}")
            raise
    
    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        """
        Parse JSON from the model response, handling potential formatting issues.
        Extracts content between FIRST '{' and LAST '}' for maximum robustness.
        
        Args:
            response_text: The raw text response from the API.
        
        Returns:
            Parsed JSON as a dictionary.
        
        Raises:
            ValueError: If JSON parsing fails.
        """
        response_text = response_text.strip()
        
        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON if wrapped in markdown code blocks
        # Find ALL code blocks and try the LAST valid one (handles corrections and truncation)
        if "```" in response_text:
            code_blocks = []
            parts = response_text.split("```")
            
            # Collect all potential JSON blocks (odd indices are inside code blocks)
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                # Remove language specifier if present
                if block.startswith("json"):
                    block = block[4:].strip()
                code_blocks.append(block)
            
            # Try parsing from last to first (most recent correction)
            for block in reversed(code_blocks):
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue
        
        # Robust extraction: Find FIRST '{' and LAST '}' and extract that substring
        # This handles preamble text and trailing thoughts
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_substring = response_text[first_brace:last_brace + 1]
            try:
                return json.loads(json_substring)
            except json.JSONDecodeError:
                pass
        
        # If all else fails, raise error
        raise ValueError(f"Could not parse JSON from response: {response_text[:200]}...")


def main():
    """Example usage of the Solver Agent."""
    
    try:
        # Initialize the Solver Agent
        solver = SolverAgent(timeout=60.0)
        
        # Example: Solve a clue
        example_clue = "Confused listen"
        example_enumeration = "(6)"
        
        print(f"\n{'='*60}")
        print(f"Attempting to solve cryptic clue:")
        print(f"Clue: {example_clue}")
        print(f"Enumeration: {example_enumeration}")
        print(f"{'='*60}\n")
        
        solution = solver.solve_clue(example_clue, example_enumeration)
        
        print("Solver's Solution:")
        print(json.dumps(solution, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
