## architecture.md: System Design

The system will operate as a **Sequential Agent Chain** orchestrated in Python.

### 1. Component Roles

* 
**The Setter (Generator):** Picks a target word (from a provided wordlist or theme)  and generates a clue. It outputs a JSON object containing the clue, type, definition, wordplay breakdown, and indicator.


* **The Mechanic (Validator):** A Python script that performs non-LLM checks.
* *Example:* If Type="Anagram", it checks if `sorted(fodder) == sorted(answer)`.


* **The Solver (QC Agent):** Receives *only* the clue and the enumeration. It attempts to parse it and provide a solution.


* **The Referee (Reviewer):** Compares the Setter’s intent with the Solver’s results. It flags ambiguities (e.g., if the Solver finds a different valid answer) or "unfair" clues where the wordplay is too loose.

**Directional Constraints:**
**Standalone Horizontal Rule:** To ensure fairness for clues presented in isolation, the system must only use indicators valid for an **Across** or **Generic** grid orientation.
* **Blocked Logic:** Reversals like "rising," "mounting," or "upwards" and positional charades like "A on B" (where A is above B) are prohibited.
* **Supported Logic:** Horizontal reversals like "going west" or "to the left" and generic terms like "back," "around," or "reverse" are allowed.

**Word Selection & Batching**:

**Clue Factory Logic:** Instead of fixed lists, the system pulls from a `seed_dictionary`.
* **Type Matching:** The system should intelligently match words to types (e.g., short words for "Hidden Word", words with common letters for "Anagrams").
* **Persistence:** Valid clues are saved to a `clue_bank.json`, while failures are logged to a `tuning_corpus.json` to help refine future prompts.
We are adding a **Heuristic Selection** layer to the orchestrator:

* 
**Seed Prioritization:** The system will select words from `seed_words.json` based on the specific wordplay type they are known to support (e.g., using "REMIT" for a Reversal).


* 
**Mechanical Sandbox:** The Setter must provide a valid mechanical string (fodder) *before* the polisher attempts to write a "story" for the surface reading.


* 
**Historical Validation:** The Auditor will cross-reference the output to ensure it follows the "Equation" of Definition + Wordplay = Answer.
 


### 2. Tech Stack

* **Language:** Python 3.10+
* **LLM Gateway:** Portkey (for routing to models like Claude 3.5 Sonnet or GPT-4o)
* **Data Structures:** JSON for inter-agent communication.

### Connectivity Configuration
- **Gateway:** Portkey AI Gateway (Custom Roche Endpoint)
- **Base URL:** `https://eu.aigw.galileo.roche.com/v1`
- **Model ID:** `@vertex-ai-1/anthropic.claude-sonnet-4-5@20250929`
- **Authentication:** Direct Portkey API Key (No virtual keys used)
