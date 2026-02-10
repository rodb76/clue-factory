 **Task: Initialize Custom Portkey Integration for Cryptic Crossword Generator**
 **Goal:** Create a Python script for the "Setter Agent" using the `portkey-ai` SDK.
 **Connection Details:**
 * **API Key:** Load from environment variable `PORTKEY_API_KEY`.
 * **Base URL:** `https://eu.aigw.galileo.roche.com/v1`
 * **Model ID:** `@vertex-ai-1/anthropic.claude-sonnet-4-5@20250929`
 
 
 **Requirements:**
 1. **Setup:** Use `from portkey_ai import Portkey`. Initialize the client passing `api_key` and `base_url` explicitly. Do **not** use a `virtual_key` parameter.
 2. **Function:** Create `generate_cryptic_clue(answer: str, clue_type: str)`.
 3. **Prompting:** Instruct the model (using the specific `MODEL_ID` provided) to act as a Ximenean cryptic setter. It must return a JSON object containing:
 * `clue`: The final surface reading.
 * `definition`: The "straight" part of the clue.
 * `wordplay_parts`: Breakdown of components (fodder/indicators).
 * `explanation`: Mechanical breakdown following the "Definition + Wordplay = Answer" equation.
 
 4. **Validation:** Implement a basic JSON parser for the response and include error handling for the API call.


 ---
 **Phase 2:**

**Task: Create Mechanical Validator for Cryptic Clues**
**Goal:** Write a Python module `mechanic.py` that contains validation functions for the 8 core cryptic clue types.
**Requirements:**
 1. **Anagram Validator:** A function that takes `fodder` and `answer` and returns `True` if `sorted(fodder.replace(" ", "").lower()) == sorted(answer.lower())`.
 2. **Hidden Word Validator:** A function that checks if the `answer` string is physically present within the `fodder` string (ignoring spaces/case).
 3. **Charade Validator:** A function that verifies if the concatenated `wordplay_parts` (e.g., PART + RIDGE) equals the `answer`.
 4. **Container Validator:** A function that checks if `Word A` placed inside `Word B` matches the `answer`.
 5. **Integration:** Create a main function `validate_clue(clue_json)` that routes the clue to the correct validator based on the `type` field.
 
 
 **Note:** For now, if a type is "Double Definition" or "Cryptic Definition," just return `True` with a warning, as these require LLM reasoning rather than string matching.

 ### Phase 3: The Adversarial Loop

 **Task: Build Adversarial Solver and Orchestrator for Batch Processing**
 **Goal:** Create a system that generates a batch of 20 clues, validates them mechanically, and then uses a separate "Solver Agent" to verify solvability.
 **Connection Details:** Use the same Portkey setup as `setter_agent.py` (Base URL, API Key, and Model ID).
 **Requirements:**
 1. **Batch Logic:** Update the script to take a list of words. Use `asyncio` or `threading` to generate clues in parallel to speed up the process.
 2. **Solver Agent:** Create a function `solve_clue(clue_text, enumeration)`.
 * **Prompting:** Instruct the model to act as an expert cryptic solver. Provide *only* the clue text and the letter count (e.g., "5").
 * **Thinking:** Require the model to output its reasoning (identifying the definition and parsing the wordplay) before providing the final answer in a JSON field.
 
 
 3. **The Referee:** Write a comparison function `referee(original_answer, solver_answer)`.
 * If they match: Mark the clue as **PASSED**.
 * If they differ or the solver fails: Mark as **FAILED** and include the solver's reasoning to help the setter improve.
 
 
 4. **Integration:** Combine `setter_agent.py`, `mechanic.py`, and the new solver logic into a single `main.py` flow.
 
 
 **Output:** The final result should be a JSON list of passed clues ready for Phase 6 (Extended Explanations).


 ### Phase4

 **Task: Create Ximenean Auditor and Integrate into Orchestrator**
 **Goal:** Create a new module `auditor.py` that specifically checks for "fair play" and technical correctness according to Ximenean standards.
 **Requirements:**
 1. **Indicator Validator:** Create a function `validate_indicators(clue_json)` that checks the "indicator" field against a list of valid cryptic indicators (e.g., ensuring a noun isn't used as an anagram indicator).
 2. **Double Duty Check:** Use the LLM to analyze the `clue`, `definition`, and `wordplay_parts`. It must flag if any word in the clue is being used for both the definition and wordplay.
 3. **Surface Polisher:** Create a function `refine_surface(clue_json)` where, if a clue passes all other tests but has a clunky surface (like "Hear from hostile entries"), the LLM suggests three more deceptive "cryptic masks" while keeping the wordplay identical.
 4. **Integration:** Update `main.py` to include a `Step 5: Ximenean Audit`. If the audit fails (e.g., illegal indicator), the clue should be sent back for a single regeneration attempt.
   
 **Specific Check:** Ensure that "Across" clues do not use "Down" indicators (like "rising" or "on top of") and vice-versa. 
 
 **Connection Details:** Use the existing Portkey setup and `MODEL_ID`.
