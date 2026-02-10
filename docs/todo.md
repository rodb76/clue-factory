## todo.md: Implementation Roadmap

### Phase 1: Setup & Generation

* [x] Initialize Portkey client with base_url and api_key.
* [x] Draft the **Setter Prompt** using the knowledge base (defining the 8 main clue types).
* [x] Implement JSON response parsing and error handling.

### Phase 2: Mechanical Validation

* [x] Create `mechanic.py` with string-matching logic.
* [x] Add "Length Check" to ensure the clue matches the provided (enumeration).
* [x] Implement validators for Anagrams (set logic).
* [x] Implement validators for Hidden Words (string searching).
* [x] Implement validators for Charades/Inclusions (string concatenation).
* [x] Implement validators for Containers (insertion logic).
* [x] Implement validators for Reversals (string reversal).
* [x] Create main `validate_clue()` routing function.
* [x] Add unit tests for all validators (25 tests passing).

### Phase 3: The Adversarial Loop

* [x] Implement solver_agent.py with step-by-step reasoning logic.

* [x] Create parallel orchestrator for 20+ clues (main.py with async batch processing).

* [x] Implement Referee logic for Pass/Fail reporting (determine if a clue passes or needs a "Redo" instruction for the Setter.).

* [x] Add unit tests for Referee (17 tests passing). 

### Phase 4: Ximenean Audit & Quality Refinement

* [x] Implement `auditor.py` for directional and fairness checks.
* [x] Implement "Direction Check" using DIRECTIONAL_BLOCKLIST (down-only indicators).
* [x] Implement "Double Duty Check" using LLM to verify definition and wordplay are discrete.
* [x] Implement "Indicator Fairness Check" (noun indicators on anagrams).
* [x] Implement "Surface Polish" refinement suggestions.
* [x] Integrate Auditor into `main.py` as Step 5 of the pipeline.
* [x] Add regeneration logic: If audit fails, attempt to regenerate with feedback (max 1 attempt).
* [x] Update ClueResult with audit_result and regeneration_count fields.

### Phase 5: Automated Word Selection Engine & The "Clue Factory" Loop
**Task 5.1: Automated Word Selection Engine**
* [x] Integrate a word source (built-in word list with 149 words, NLTK support available).
* [x] Implement `WordSelector` class to filter words between 4 and 10 letters.
* [x] Add intelligent clue type assignment based on word characteristics.

**Task 5.2: The "Clue Factory" Loop**
* [x] Create `factory_run()` function in `main.py` that runs until N clues pass all QC stages.
* [x] Implement batch processing with parallel execution (10 words per batch).
* [x] Add automatic word selection from pool with avoid-duplicate logic.
* [x] Save only PASSED clues to `final_clues_output.json`.
* [x] Add unit tests for WordSelector (13 tests passing).

**Task 5.3: Mechanical First Generation**
[ ] Update the Setter Agent to produce a "Raw wordplay draft" first.

**Task 5.4: Word-to-Type Affinity**
[ ] Create a logic gate that assigns "Hidden Word" to short words and "Anagram" to high-vowel words.

**Task 5.5: Error-Informed Regeneration**
[ ] If mechanic.py fails, feed the specific letter mismatch back to the AI (e.g., "You are missing an 'S' in your fodder") to force a correction.

**Task 5.6: Dataset Integration**

[x] Create word_pool_loader.py with seed_words.json.

[x] Implement Two-Step Generation (Mechanical Draft -> Surface Polish).

[x] Integrate specific retry logic for mechanical failures.

**Phase 5.7: Harden Solver & Auditor Logic**
* [x] Apply "Synonym Anchor" to Solver (Step 0 hidden word priority + Step 7 sound-alike constraint).
* [x] Implement "Fodder Immunity" in Auditor (refined Double Duty check).
* [x] Update JSON parser for truncated strings (last complete block extraction).
* [x] Add Hidden Word non-suspicious instructions to Setter.

**Phase 5.8: Hardened Parsing & Audit Refinement**
* [x] Implement `\b` word boundaries in Auditor blocklist.
* [x] Force "JSON-only" output in Solver Agent system prompt.
* [x] Implement robust `{...}` substring extraction in all agent parsers (first/last brace method).
* [x] Add character-by-character check instruction for Hidden Word fodder in Setter.
* [x] Make Auditor Double Duty check more lenient (separate words OK).
* [x] Add unit tests for parser hardening (6 tests passing).

**Phase 5.9: Modular Word Scaling**

* [x] Create ./word_pools/ directory structure.
* [x] Implement modular file scanning in word_pool_loader.py.
* [x] Add metadata tracking (source field) for each word.
* [x] Implement usage-based prioritization (least-used words first).
* [x] Build ingest_archive.py to process external cryptic databases.

### Phase 6: Hints & Explanations Generation

* [x] Create a final agent to produce user-friendly "Hint" (oblique) and "Explanation" (full breakdown) outputs.


### Phase 7: Explanations & Style Extension
* [ ] Create YouTube transcript extraction script.
* [ ] **Task 7.1: Structural Mapping** - Use an LLM to analyze `transcript_JAGbz18gYHk.txt` and identify the "Explanation Architecture" (e.g., Intro -> Surface Deception -> Definition Reveal -> Wordplay Mechanical Breakdown -> Final "Aha!" Moment).
* [ ] **Task 7.2: Style Enrichment** - Extract specific linguistic flourishes from transcripts (e.g., how the speaker uses words like "dastardly," "equation," or "fair play").
* [ ] **Task 7.3: Few-Shot Prompting** - Integrate the mapped architecture into `explainer_prompt.md` as few-shot examples.
* [ ] **Task 7.4: Human-in-the-loop (HITL) Review** - Test the Explainer on a validated clue and verify it matches the reference video's tone.

### Phase 8: Scaling (Optional)
* [ ] Add keyword-based auto-detection to ingest_archive.py to categorize clues without a 'type' column.
* [ ] Update WordPoolLoader to perform modular directory scanning for all *.json files in ./word_pools/.
