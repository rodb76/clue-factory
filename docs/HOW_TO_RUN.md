# How to Run the Clue Generator Pipeline

## Quick Answer: Generate Valid Clues Right Now

### Option 1: Interactive Mode (Easiest)
```bash
python main.py
```
Then:
1. Choose option **2** (Clue Factory Mode)
2. Enter target count (e.g., `10` for 10 valid clues)
3. Wait for results (saved to `final_clues_output.json`)

### Option 2: Command Line (Fastest)
```bash
# Generate 10 valid clues
python -c "from main import factory_run; factory_run(target_count=10)"
```

### Option 3: Python Script (Most Control)
```python
from main import factory_run

# Generate 20 valid clues using the mechanical-first pipeline
results = factory_run(
    target_count=20,         # How many valid clues you want
    batch_size=10,           # Process 10 words at a time
    max_concurrent=5,        # Run 5 API calls in parallel
    use_seed_words=True      # Use validated seed words (recommended)
)

# Results automatically saved to final_clues_output.json
print(f"Generated {len(results)} valid clues!")
```

## What Happens During Execution

### The Mechanical-First Pipeline

```
For each word in seed_words.json:
  
  1. Generate Mechanical Draft (API call #1)
     └─> Returns: fodder, indicator, mechanism
  
  2. Validate Mechanically (local, fast)
     ├─> If PASS: Continue to step 3
     └─> If FAIL: Retry up to 3 times with feedback
         └─> Still failing? Discard word, get next seed
  
  3. Generate Surface Polish (API call #2)
     └─> Creates natural-reading clue from validated wordplay
  
  4. Solve Clue (API call #3)
     └─> Solver attempts to find the answer
  
  5. Judge Result (local)
     └─> Referee compares solver's answer to actual answer
  
  6. Audit for Fairness (API call #4)
     └─> Checks Ximenean standards
  
  7. Final Decision
     ├─> ALL PASS: Add to output file ✅
     └─> ANY FAIL: Discard, continue to next word ❌

Repeat until target_count valid clues are generated
```

## Expected Output

### Console Output
```
================================================================================
CLUE FACTORY: Generating 10 Valid Cryptic Clues
================================================================================

Word pool loaded from seed_words.json: 80 words
Type distribution:
  Anagram             :  14 words
  Charade             :  11 words
  Container           :  10 words
  [...]
Batch size: 10 words
Target: 10 PASSED clues
Pipeline: Mechanical Draft → Validate → Surface Polish → Solve → Judge → Audit

Batch 1: Processing 10 candidates...
Progress: 0/10 clues validated
✓ SUCCESS: LISTEN (1/10)
✓ SUCCESS: SILENT (2/10)
[...]

================================================================================
CLUE FACTORY COMPLETE
================================================================================
Total time: 245.3 seconds (4.1 minutes)
Total attempts: 18
Successful clues: 10
Success rate: 55.6%
Average time per clue: 24.5 seconds

✓ 10 validated clues saved to: final_clues_output.json
```

### Output File (final_clues_output.json)
```json
{
  "metadata": {
    "generated_at": "2026-02-10T09:30:15.123456",
    "target_count": 10,
    "total_attempts": 18,
    "success_rate": "55.6%",
    "total_time_seconds": 245.3
  },
  "clues": [
    {
      "word": "LISTEN",
      "clue_type": "Hidden Word",
      "clue": "Pay attention to hostile entries",
      "definition": "Pay attention",
      "explanation": "[Pay attention] is the definition. [hostile ENtries] contains LISTEN.",
      "passed": true,
      "mechanical_valid": true,
      "solver_answer": "LISTEN",
      "audit": {
        "passed": true,
        "fairness_score": 0.95
      }
    }
  ]
}
```

## Timing Expectations

- **Single clue generation**: ~15-30 seconds
  - 1-3 mechanical draft attempts: 5-15 seconds
  - Surface polish: 3-5 seconds
  - Solver: 5-8 seconds
  - Auditor: 2-4 seconds

- **Batch of 10 clues**: ~3-5 minutes
  - Depends on success rate and parallel execution

- **Target of 20 clues**: ~6-10 minutes
  - With ~50% success rate, needs ~40 attempts

## Troubleshooting

### "PORTKEY_API_KEY not set"
```bash
# Make sure .env file exists with your API key
cp .env.template .env
# Edit .env and add: PORTKEY_API_KEY=your_actual_key_here
```

### "TimeoutError" or "Connection refused"
- Check network connectivity to `https://eu.aigw.galileo.roche.com/v1`
- Increase timeout: `factory_run(target_count=10)` uses 60s default
- Try running with lower `max_concurrent` (less parallel load)

### "Word pool exhausted"
- The pipeline will automatically reset the used words tracker
- If seeing this repeatedly, consider increasing `batch_size` or lowering `target_count`

### Low Success Rate (<30%)
- This is expected! The pipeline is strict
- Mechanical-first helps, but some words are harder than others
- The system automatically tries more words until target is reached

## Advanced Options

### Use General Word Pool Instead of Seed Words
```python
factory_run(
    target_count=10,
    use_seed_words=False  # Uses WordSelector with built-in/NLTK words
)
```

### Sequential Processing (Easier to Debug)
```python
from main import process_batch_sync

word_type_pairs = [
    ("LISTEN", "Hidden Word"),
    ("SILENT", "Anagram"),
    ("STAR", "Reversal")
]

results = process_batch_sync(word_type_pairs)
```

### Single Word Processing
```python
from main import process_single_clue_sync
from setter_agent import SetterAgent
from solver_agent import SolverAgent
from auditor import XimeneanAuditor

setter = SetterAgent()
solver = SolverAgent()
auditor = XimeneanAuditor()

result = process_single_clue_sync(
    word="LISTEN",
    clue_type="Hidden Word",
    setter=setter,
    solver=solver,
    auditor=auditor
)

if result.passed:
    print(f"✓ Success: {result.clue_json['clue']}")
else:
    print(f"✗ Failed: {result.error}")
```

## Summary

**Simplest command to get started:**
```bash
python main.py
# Choose option 2
# Enter: 10
# Wait ~3-5 minutes
# Check final_clues_output.json
```

**Results include:**
- ✅ Mechanically validated wordplay
- ✅ Solvable by independent AI
- ✅ Referee-approved answers
- ✅ Ximenean fairness audit passed
- ✅ Ready for use in cryptic crosswords!
