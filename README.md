# Cryptic Crossword Clue Generator

A Python-based system for generating Ximenean standard cryptic crossword clues using the Portkey AI Gateway and Claude 3.5 Sonnet.

## 🚀 Quick Start

**Want to generate clues right now?** See **[docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md)** for the fastest way to get started.

```bash
# Generate 10 valid clues in ~3-5 minutes
python main.py
# Choose option 2, enter: 10
```

## Project Structure

```
clues/
├── main.py              # Orchestrator: Batch processing with mechanical-first pipeline
├── setter_agent.py      # Phase 1: LLM-based clue generation (two-step)
├── mechanic.py          # Phase 2: Mechanical validators for clue types
├── solver_agent.py      # Phase 3: LLM-based clue solving
├── referee.py           # Phase 3: Answer comparison and quality judgment
├── auditor.py           # Phase 4: Ximenean fairness and directional auditor
├── explanation_agent.py # Phase 6: User-friendly hints and breakdowns
├── word_selector.py     # Phase 5: Automated word selection engine
├── word_pool_loader.py  # Phase 5: Modular word pool loader with usage tracking
├── ingest_archive.py    # Phase 5: CSV/JSON word database ingestion tool
├── requirements.txt     # Python dependencies
├── .env.template        # Environment configuration template
│
├── word_pools/          # Modular word pool directory
│   └── seed_words.json  # 80 validated words with recommended clue types
│
├── docs/                # Documentation
│   ├── HOW_TO_RUN.md    # Quick start guide
│   ├── QUICKSTART.md    # Alternative quick start
│   ├── architecture.md  # System design documentation
│   ├── spec.md          # Functional requirements
│   ├── todo.md          # Implementation roadmap
│   ├── VERIFICATION.md  # Verification and test results
│   └── *.md             # Implementation summaries and phase documentation
│
└── tests/               # Test suite
    ├── test_config.py   # Test path configuration helper
    ├── test_mechanic.py # Unit tests for Mechanic validators (25 tests)
    ├── test_auditor.py  # Unit tests for Auditor (8 tests)
    ├── test_setter.py   # Unit tests for Setter Agent
    ├── test_word_selector.py # Unit tests for Word Selector (13 tests)
    ├── test_word_pool_loader.py # Unit tests for Word Pool Loader
    ├── test_explanation_integration.py # Unit tests for Explanation Agent
    ├── test_integration*.py # Integration tests
    └── demo_*.py        # Demo scripts
```

## Setup

### 1. Create Virtual Environment (Optional but Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
`. venv/Scripts/activate`
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Set your Portkey API Key in `.env`:
   ```
   PORTKEY_API_KEY=your_actual_key_here
   ```

## Testing

### Run Unit Tests (No Network Required)

Tests JSON parsing logic and response handling without requiring API connectivity:

```bash
python test_setter.py
```

Expected output:
```
✓ Direct JSON parsing test passed
✓ Markdown JSON parsing test passed
✓ Embedded JSON parsing test passed
✓ Metadata enrichment test passed
✓ Invalid JSON error handling test passed

All tests passed! ✓
```

### Run the Setter Agent (Requires API Access)

```bash
python setter_agent.py
```

This will attempt to generate an example cryptic clue for the word "LISTEN" using the "Hidden Word" clue type.

**Note:** If you receive a timeout error, verify:
- ✓ `PORTKEY_API_KEY` environment variable is set correctly in `.env`
- ✓ Network connectivity to `https://eu.aigw.galileo.roche.com/v1` is available
- ✓ API key has appropriate permissions

## Usage

### Recommended: Clue Factory with Mechanical-First Pipeline

```python
from main import factory_run

# Generate 20 valid clues automatically
# Uses seed_words.json with optimized type matching
results = factory_run(
    target_count=20,        # Number of PASSED clues to generate
    batch_size=10,          # Words per batch
    max_concurrent=5,       # Parallel API calls
    use_seed_words=True     # Use validated seed words (recommended)
)

# Results are saved to: final_clues_output.json
```

**Pipeline Features:**
- ✅ Two-step generation (mechanical draft → surface polish)
- ✅ Fail-fast with 3 retries on mechanical validation
- ✅ Type affinity matching (anagram-friendly words → anagrams)
- ✅ Automatic word selection from 80 validated seeds
- ✅ Full QC: Mechanical → Solver → Referee → Auditor

### Alternative: Basic Single Clue Generation

```python
from setter_agent import SetterAgent

# Initialize the agent
setter = SetterAgent()

# Generate a clue (old method - no validation)
clue = setter.generate_cryptic_clue(
    answer="SILENT",
    clue_type="Anagram"
)

print(clue)
```

### Validating Generated Clues

```python
from setter_agent import SetterAgent
from mechanic import validate_clue_complete

# Generate a clue
setter = SetterAgent()
clue = setter.generate_cryptic_clue("SILENT", "Anagram")

# Validate the clue
all_valid, results = validate_clue_complete(clue, enumeration="(6)")

for check_name, result in results.items():
    print(f"{check_name}: {result.message}")

# Check if passed all validations
if all_valid:
    print("✓ Clue is mechanically valid!")
```

### Supported Clue Types

- **Anagrams:** Rearranging letters with a valid indicator
- **Hidden Words:** Embedding the answer within the clue text
- **Charades:** Joining individually clued words or letters
- **Containers/Inclusions:** Placing one word inside another
- **Reversals:** Reading a word backward with directional indicators
- **Homophones:** Words that sound like the answer
- **Double Definitions:** Two separate definitions of the same word
- **&lit (All-in-one):** Entire clue serves as both definition and wordplay

## Output Format

The `generate_cryptic_clue()` function returns a JSON object:

```json
{
  "clue": "The complete clue surface reading",
  "definition": "The definition part of the clue",
  "wordplay_parts": {
    "type": "Clue type",
    "fodder": "The letters/words being manipulated",
    "indicator": "The word indicating the wordplay",
    "mechanism": "How the wordplay works"
  },
  "explanation": "Step-by-step breakdown",
  "type": "Anagram",
  "answer": "ANSWER"
}
```

## API Implementation

The Setter Agent uses the Portkey AI Gateway with the following configuration:

- **Base URL:** `https://eu.aigw.galileo.roche.com/v1`
- **Model:** `@vertex-ai-1/anthropic.claude-sonnet-4-5@20250929`
- **API Key:** Loaded from `PORTKEY_API_KEY` environment variable
- **Timeout:** 30 seconds (configurable)

### API Call Structure

```python
response = client.chat.completions.create(
    model=MODEL_ID,
    max_tokens=500,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)
```

### Response Parsing

The implementation includes robust JSON parsing that handles:
- ✓ Direct JSON responses
- ✓ JSON wrapped in markdown code blocks (``
`  ` ... ` `` `)
- ✓ JSON embedded within surrounding text
- ✓ Fallback error handling with clear messages

## Mechanical Validation (Phase 2)

The Mechanic module (`mechanic.py`) provides programmatic validation for cryptic clue types:

### Validators Implemented

1. **Anagram Validator** - Verifies `sorted(fodder) == sorted(answer)`
2. **Hidden Word Validator** - Checks if answer is present within fodder
3. **Charade Validator** - Confirms parts concatenate to answer
4. **Container Validator** - Validates insertion of one word into another
5. **Reversal Validator** - Checks if word reversed equals answer
6. **Length Validator** - Ensures answer matches enumeration (e.g., "(6)" or "(3,4)")

### Special Cases

- **Homophones**, **Double Definitions**, and **&lit** clues return `True` with a warning flag (`requires_llm: true`) since they require semantic/phonetic reasoning beyond string matching.

### Running Mechanic Tests

```bash
# Run unit tests (25 tests)
python test_mechanic.py

# Run standalone validation examples
python mechanic.py
```

**Example Output:**
```
Testing: Anagram Test
  ✓ Length: Length matches: 6
  ✓ Wordplay: Valid anagram: 'listen' → 'SILENT'

Testing: Hidden Word Test
  ✓ Length: Length matches: 6
  ✓ Wordplay: Valid hidden word: 'LISTEN' found in 'Silent listener'
```

## Adversarial Loop (Phase 3)

Phase 3 implements a complete quality assurance pipeline where generated clues are tested by an independent Solver Agent and judged by a Referee.

### Components

#### 1. Solver Agent (`solver_agent.py`)

The Solver attempts to solve cryptic clues without knowing the answer, mimicking a real solver's experience:

```python
from solver_agent import SolverAgent

solver = SolverAgent()
solution = solver.solve_clue(
    clue_text="Quietly listen to storyteller (6)",
    enumeration="(6)"
)

print(solution)
# Output:
# {
#   "answer": "SILENT",
#   "reasoning": "Step-by-step solving process...",
#   "confidence": "high",
#   "clue_type": "Charade",
#   "definition_part": "Quietly",
#   "wordplay_part": "listen to storyteller"
# }
```

#### 2. Referee Logic (`referee.py`)

The Referee compares the Setter's intended answer with the Solver's solution using normalized text comparison and similarity metrics:

```python
from referee import referee, RefereeResult

result = referee(
    original_answer="SILENT",
    solver_answer="SILENT",
    reasoning="Solver's step-by-step reasoning",
    strict=True  # Use strict mode (default)
)

print(f"Passed: {result.passed}")
print(f"Similarity: {result.similarity_score:.1%}")
print(f"Feedback: {result.feedback}")
```

**Similarity Thresholds:**
- **Strict Mode** (default): 100% exact match required
- **Lenient Mode**: 90% similarity threshold (catches near-misses)

**Features:**
- Case-insensitive comparison
- Whitespace normalization
- Length mismatch detection
- Detailed feedback messages

#### 3. Batch Orchestrator (`main.py`)

Process multiple clues in parallel through the complete pipeline:

```python
from main import process_batch_async, generate_report
import asyncio

# Define word-type pairs to generate
word_pairs = [
    ("SILENT", "Anagram"),
    ("LISTEN", "Hidden Word"),
    ("PARTRIDGE", "Container"),
    ("STAR", "Reversal")
]

# Process batch with async/await
results = asyncio.run(process_batch_async(
    word_pairs,
    max_concurrent=5  # Process up to 5 clues simultaneously
))

# Generate summary report
report = generate_report(results)
print(report)
```

**Pipeline Stages:**
1. **Generate** - Setter creates clue using LLM
2. **Validate** - Mechanic checks wordplay mechanics
3. **Solve** - Solver attempts to find answer
4. **Judge** - Referee compares answers and assigns Pass/Fail

**Output Format:**

```json
[
  {
    "word": "SILENT",
    "clue_type": "Anagram",
    "status": "passed",
    "clue": "Listen quietly (6)",
    "setter_answer": "SILENT",
    "solver_answer": "SILENT",
    "validation_passed": true,
    "similarity": 1.0,
    "feedback": "Perfect match"
  }
]
```

### Running Phase 3 Tests

```bash
# Run Referee unit tests (17 tests)
python test_phase3.py

# Run standalone Referee demo
python referee.py

# Run full integration (requires API access)
python main.py
```

**Example Test Output:**
```
Test Case: Exact Match
  Original: SILENT
  Solver:   SILENT
  ✓ PASSED (100.0% similarity)

Test Case: Anagram Confusion
  Original: SILENT
  Solver:   LISTEN
  ✗ FAILED (50.0% similarity)
  Feedback: Some similarity - solver may have partially understood
```

### Windows Compatibility

The orchestrator automatically configures the asyncio event loop for Windows:

```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

This prevents `NotImplementedError` on Windows when using async batch processing.

## Windows Compatibility

The orchestrator automatically configures the asyncio event loop for Windows:

```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

This prevents `NotImplementedError` on Windows when using async batch processing.

## Ximenean Audit (Phase 4)

Phase 4 adds fairness and technical auditing to ensure generated clues meet Ximenean standards.

### Components

#### Auditor (`auditor.py`)

The Auditor performs three critical checks on every generated clue:

```python
from auditor import XimeneanAuditor

auditor = XimeneanAuditor()

# Audit a clue after it passes mechanical and adversarial tests
audit_result = auditor.audit_clue(clue_json)

if audit_result.passed:
    print(f"Clue fairness: {audit_result.fairness_score:.0%}")
else:
    print(f"Failed: {audit_result.direction_feedback}")
    if audit_result.refinement_suggestion:
        print(f"Consider: {audit_result.refinement_suggestion}")
```

**Three Audit Flags:**

1. **Direction Check** - Ensures clue is stand-alone horizontal
   - Blocks down-only indicators: "rising", "lifted", "climbing", "up", "upwards", "skyward", "mounting", "ascending", "overhead", "over", "underneath", "atop", etc.
   - Prevents vertical-only wordplay in stand-alone format

2. **Double Duty Check** - Uses LLM to verify definition and wordplay are discrete
   - Ensures no word serves both as definition AND wordplay component
   - Example violation: "Quiet **times** around the **clock**" if "times" is both definition and wordplay
   - Returns `True` if no violations detected

3. **Indicator Fairness Check** - Contextual indicator validation
   - For anagrams: flags noun indicators (e.g., "jumble", "salad", "hash")
   - Ximeneans prefer verb indicators (e.g., "mixed", "scrambled", "rearranged")
   - May be extended for other clue types

**Fairness Score:**
- Calculated as: (direction_pass + double_duty_pass + fairness_pass) / 3
- Range: 0.0 (all failed) to 1.0 (all passed)

### Pipeline Integration with Regeneration

The complete pipeline now has 5 steps:

```
Step 1: Generate clue (Setter)
  ↓
Step 2: Validate mechanically (Mechanic)
  ↓
Step 3: Solve clue (Solver)
  ↓
Step 4: Judge result (Referee)
  ↓
Step 5: Audit for fairness (Auditor)
  ↓ [If audit fails]
Regenerate with Feedback
  ↓
[Up to 1 attempt, then FAIL]
```

**ClueResult Extended:**

```json
{
  "word": "SILENT",
  "clue": "Quietly listen (6)",
  "passed": true,
  "audit": {
    "passed": true,
    "direction_check": true,
    "double_duty_check": true,
    "indicator_fairness_check": true,
    "fairness_score": 1.0,
    "refinement_suggestion": null
  },
  "regeneration_attempts": 0
}
```

### Running Phase 4

```bash
# Run Auditor unit tests (8 tests)
python test_auditor.py

# Run standalone Auditor demo
python auditor.py

# Run complete pipeline with audit (includes regeneration)
python main.py
```

### Directional Blocklist

The auditor maintains a comprehensive list of down-only indicators:

```python
DIRECTIONAL_BLOCKLIST = {
    "rising", "lifted", "climbing", "up", "upwards",
    "skyward", "mounting", "ascending", "on", "supports",
    "overhead", "over", "underneath", "atop",
    "climbing up", "going up", "comes up", "rises", "lifts", "climbs"
}
```

These terms should never appear in stand-alone horizontal clues.

## Clue Factory (Phase 5)

Phase 5 introduces automated word selection and continuous clue generation until a target count is reached.

### Word Selector (`word_selector.py`)

Automatically selects words from a curated pool:

```python
from word_selector import WordSelector

# Initialize with length constraints
selector = WordSelector(min_length=4, max_length=10)

# Select 10 random words with assigned clue types
word_pairs = selector.select_words(10, avoid_recent=True)

for word, clue_type in word_pairs:
    print(f"{word} → {clue_type}")
```

**Features:**
- Built-in curated word list (149 words, 4-10 letters)
- NLTK corpus support (automatically downloads if available)
- Custom word list loading from file
- Intelligent clue type assignment based on word characteristics
- Duplicate avoidance (tracks recently used words)

**Word Pool Characteristics:**
- Length: 4-10 letters
- All uppercase, alphabetic only
- Filters out obscure words with unusual letter patterns
- Variety across different lengths

### Factory Run (`factory_run()`)

Continuous clue generation until target is met:

```python
from main import factory_run

# Generate 20 validated clues
factory_run(
    target_count=20,
    batch_size=10,
    max_concurrent=5,
    output_file="final_clues_output.json"
)
```

**How It Works:**

1. **Word Selection** - Automatically pulls words from pool
2. **Batch Processing** - Processes 10 words in parallel per batch
3. **Quality Loop** - Continues until target count of PASSED clues reached
4. **Auto-Retry** - Failed clues are discarded, new words selected
5. **Persistence** - Only PASSED clues saved to output file

**Output Format (`final_clues_output.json`):**

```json
{
  "metadata": {
    "generated_at": "2026-02-09T18:40:00",
    "target_count": 20,
    "total_attempts": 35,
    "success_rate": "57.1%",
    "total_time_seconds": 450.2,
    "batches_processed": 4
  },
  "clues": [
    {
      "word": "LISTEN",
      "clue_type": "Anagram",
      "clue": "Be quiet about twisted nets (6)",
      "passed": true,
      "audit": {
        "passed": true,
        "fairness_score": 1.0
      }
    }
  ]
}
```

### Running Phase 5

```bash
# Run word selector tests (13 tests)
python test_word_selector.py

# Run word selector standalone
python word_selector.py

# Run Clue Factory (interactive)
python main.py
# Select mode: 2 (Clue Factory Mode)
# Enter target: 20
```

**Interactive Mode:**
```
Select mode:
  1. Fixed Batch Mode (10 predefined words)
  2. Clue Factory Mode (automated word selection until target reached)

Enter choice (1 or 2, default=2): 2

How many valid clues to generate? (default=20): 20
```

The factory will:
- Process batches of 10 words in parallel
- Display real-time progress (e.g., "Progress: 15/20 clues validated")
- Show batch statistics (pass rate, time per batch)
- Save final results to `final_clues_output.json`

### Performance Metrics

**Typical Results:**
- Success rate: 40-60% (varies by word difficulty)
- Time per clue: 15-30 seconds
- 20 clues: ~8-12 minutes total
- Batches processed: 3-5 (for 20 clues)

## Configuration Details

## Error Handling & Features

The Setter Agent implementation includes:

- **Environment Validation:** Checks for missing API key before initialization
- **JSON Parsing:** Robust handling of various response formats
- **Timeout Management:** Configurable request timeouts with clear error messages
- **Logging:** INFO and DEBUG level logging for troubleshooting (enable with `logging.debug()`)
- **Windows Compatibility:** Automatic event loop policy handling for Windows systems
- **Graceful Degradation:** Meaningful error messages for network and API issues

## Prompting Strategy

The system uses a two-part prompt structure:

**System Prompt:** Instructs the model to act as a Ximenean cryptic setter following strict standards (definition + fair wordplay + nothing else).

**User Prompt:** Specifies the target answer, clue type, and enforces JSON-only response format with exact structure requirements.

The model is instructed to return a JSON object with:
- `clue`: The complete surface reading
- `definition`: The "straight" part of the clue
- `wordplay_parts`: Component breakdown (fodder, indicator, mechanism)
- `explanation`: Step-by-step mechanical breakdown
- `is_fair`: Boolean flag indicating if the clue follows Ximenean standards

## Modular Word Pool System

### Overview

The system supports loading words from multiple JSON files in the `word_pools/` directory. This allows you to:
- Organize words by source (original seeds, external archives, custom lists)
- Track which dataset each word came from
- Scale your word pool by adding new files
- Prioritize underused words for variety

### Word Pool Structure

Place JSON files in the `word_pools/` directory with this format:

```json
{
  "anagram_friendly": ["LISTEN", "SILENT", "ENLIST"],
  "charade_friendly": ["PARTRIDGE", "FARMING"],
  "hidden_word_friendly": ["AORTA", "SCONE", "THECA"],
  "container_friendly": ["PAINT", "VOICE"],
  "reversal_friendly": ["REGAL", "STOPS"],
  "homophone_friendly": ["BEAR", "PARE"],
  "double_def_friendly": ["BLIND", "POLISH"],
  "standard_utility": ["ELAPSED", "DRIVERS"]
}
```

### Ingesting External Databases

Use the `ingest_archive.py` script to process external cryptic crossword databases:

**CSV Format:**
```bash
python ingest_archive.py archive.csv --output word_pools/george_ho_archive.json
```

Expected CSV columns:
- `answer`: The crossword answer (will be cleaned and uppercased)
- `type`: The clue type (will be normalized to standard format)

**JSON Format:**
```bash
python ingest_archive.py archive.json --format json
```

Expected JSON format:
```json
[
  {"answer": "LISTEN", "type": "Anagram"},
  {"answer": "AORTA", "type": "Hidden Word"}
]
```

**Options:**
```bash
--output, -o          Output file path (default: word_pools/external_archive.json)
--format, -f          Input format: csv, json, auto (default: auto)
--answer-column       CSV column name for answers (default: answer)
--type-column         CSV column name for clue types (default: type)
```

**Supported Clue Type Aliases:**
The ingestor recognizes various naming conventions:
- Anagram: `anagram`, `ana`, `anag`
- Hidden Word: `hidden`, `hidden word`, `hid`
- Charade: `charade`, `char`
- Container: `container`, `cont`, `insertion`
- Reversal: `reversal`, `rev`
- Homophone: `homophone`, `homo`
- Double Definition: `double`, `double def`, `dd`

**Data Cleaning:**
- Converts to UPPERCASE
- Removes punctuation, hyphens, spaces
- Filters to 4-10 letter words
- Removes duplicates
- Skips invalid entries

### Usage-Based Prioritization

The `WordPoolLoader` automatically prioritizes words that have been used fewer times:

```python
from word_pool_loader import WordPoolLoader

loader = WordPoolLoader()  # Loads all *.json files from word_pools/

# Get a word - automatically picks from least-used words
word, clue_type = loader.get_random_seed(avoid_duplicates=True)

# View statistics
stats = loader.get_pool_stats()
print(f"Total words: {stats['unique_words']}")
print(f"Source distribution: {stats['source_distribution']}")
print(f"Usage stats: {stats['usage_stats']}")
```

**Benefits:**
- Words used less often get higher priority
- Ensures variety across clue generation sessions
- Tracks usage per word across multiple runs
- Prevents over-reliance on easy words

### Example Workflow

1. **Start with seed words:**
   ```bash
   # seed_words.json already in word_pools/
   python main.py  # Uses 80 validated seed words
   ```

2. **Add external archive:**
   ```bash
   # Ingest George Ho's archive
   python ingest_archive.py george_ho_archive.csv

   # Now system uses both seed_words.json AND external_archive.json
   python main.py  # Now has 200+ words available
   ```

3. **Add custom word list:**
   ```bash
   # Create word_pools/my_custom_words.json
   # System automatically loads it
   python main.py  # Now has 300+ words available
   ```

4. **Monitor usage:**
   ```python
   from word_pool_loader import WordPoolLoader
   loader = WordPoolLoader()
   stats = loader.get_pool_stats()
   
   # See which sources contributed words
   print(stats['source_distribution'])
   # {'seed_words.json': 80, 'external_archive.json': 150, 'my_custom_words.json': 70}
   
   # See which words have been used most
   print(stats['usage_stats'])
   # {'LISTEN': 3, 'AORTA': 2, 'PAINT': 1, ...}
   ```

## Next Steps

Phase 1 (Setup & Generation), Phase 2 (Mechanical Validation), Phase 3 (Adversarial Loop), Phase 4 (Ximenean Audit), and Phase 5 (Clue Factory) are complete!

**Completed Phases:**
- ✓ Phase 1: Portkey integration, Setter Agent
- ✓ Phase 2: Mechanical validators (6 types)
- ✓ Phase 3: Solver Agent, Referee logic, batch orchestrator
- ✓ Phase 4: Ximenean Auditor with regeneration loop
- ✓ Phase 5: Word Selector and Clue Factory with automated generation

**Upcoming phases:**
1. **Phase 6: Hints & Explanations** - Generate user-friendly explanations
2. **Phase 7: Style Extension** - Extract and apply explanation styles from reference materials

**Phase 5 Status:**
- ✓ WordSelector with intelligent clue type assignment
- ✓ Built-in word pool (149 words) + NLTK support
- ✓ Factory loop with continuous generation until target reached
- ✓ Batch processing (10 words in parallel)
- ✓ Persistence to JSON (only PASSED clues saved)
- ✓ Unit tests for WordSelector (13 tests passing)

See [todo.md](todo.md) for the complete implementation roadmap.
