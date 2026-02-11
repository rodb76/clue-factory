# Workshop Agent Documentation

## Overview

The Workshop Agent is a post-processing tool that analyzes completed cryptic clues and suggests improvements for underperforming ones while preserving excellent clues.

## Features

### 1. Quality Classification

Clues are classified into three categories based on their scores:

- **EXCELLENT** (kept as-is):
  - Narrative Fidelity ≥ 90%
  - Ximenean Score ≥ 0.9

- **GOOD** (possibly suggest word swap):
  - Narrative Fidelity ≥ 80%
  - Ximenean Score ≥ 0.8

- **NEEDS_WORK** (suggest alternative mechanism):
  - Below the good thresholds

### 2. Suggestion Types

#### Keep As-Is
For excellent clues with high scores. No changes suggested.

**Example:**
```
Original: "Majestic lager returned" (REGAL)
Scores: narrative: 100%, ximenean: 1.0
→ KEEP AS-IS: Excellent quality
```

#### Alternative Mechanism
For clues with low scores. Suggests a different cryptic mechanism that might work better for the word.

**Example:**
```
Original: "Hear with L, I, S, T, E, N" (LISTEN)
Scores: narrative: 40%, ximenean: 0.5
→ ALTERNATIVE MECHANISM: Homophone
  Reason: "The word LISTEN has excellent homophone potential..."
```

#### Word Swap
For clues with good surface quality but a suboptimal answer word. Suggests a better-fitting word.

**Example:**
```
Original: "Breathing condition from maths mixed" (ASTHMA)
Scores: narrative: 85%, ximenean: 0.85
→ WORD SWAP: MATHS
  Reason: "The anagram surface works beautifully for MATHS..."
```

## Usage

### Basic Usage

```bash
python workshop.py
```

This processes `final_clues_output.json` and creates `workshopped_clues.json`.

### Custom Input/Output

```bash
python workshop.py -i my_clues.json -o my_workshop_results.json
```

### Command-Line Options

- `-i, --input`: Input JSON file with generated clues (default: `final_clues_output.json`)
- `-o, --output`: Output JSON file for workshop suggestions (default: `workshopped_clues.json`)

## Output Format

The output JSON contains:

```json
{
  "metadata": {
    "workshop_date": "2026-02-11T15:42:30",
    "input_file": "final_clues_output.json",
    "original_metadata": { ... },
    "statistics": {
      "total_clues": 5,
      "kept_as_is": 3,
      "alternative_mechanism_suggested": 1,
      "word_swap_suggested": 1,
      "improvement_rate": "40.0%"
    }
  },
  "suggestions": [
    {
      "original_word": "REGAL",
      "original_clue": "Majestic lager returned",
      "original_type": "Reversal",
      "suggestion_type": "keep_as_is",
      "reason": "Excellent quality - narrative: 100%, ximenean: 1.00",
      "scores": {
        "narrative_fidelity": 100.0,
        "ximenean_score": 1.0
      }
    },
    {
      "original_word": "LISTEN",
      "original_clue": "Hear with L, I, S, T, E, N",
      "original_type": "Charade",
      "suggestion_type": "alternative_mechanism",
      "reason": "Low narrative fidelity (40%)",
      "alternative_mechanism": {
        "type": "Homophone",
        "explanation": "The word LISTEN has excellent homophone potential with 'LISSEN'..."
      },
      "scores": {
        "narrative_fidelity": 40.0,
        "ximenean_score": 0.5
      }
    }
  ]
}
```

## Integration with Main Pipeline

### Option 1: Standalone Mode (Current)

Run workshop after clue generation is complete:

```bash
python main.py  # Generate clues → final_clues_output.json
python workshop.py  # Analyze and suggest improvements → workshopped_clues.json
```

### Option 2: Integrated Mode (Future Enhancement)

Add to `main.py`:

```python
from workshop import WorkshopAgent

# After generating clues...
workshop = WorkshopAgent()
workshop.workshop_batch(
    input_file="final_clues_output.json",
    output_file="workshopped_clues.json"
)
```

## Quality Thresholds

The workshop agent uses these thresholds to make decisions:

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| Narrative Fidelity | ≥ 90% | ≥ 80% | < 80% |
| Ximenean Score | ≥ 0.9 | ≥ 0.8 | < 0.8 |

## LLM Analysis

The workshop agent uses Claude Sonnet 4.5 (Logic Tier) for:

1. **Alternative Mechanism Suggestions**
   - Analyzes word structure (length, letter patterns)
   - Checks reversibility (does reversed word = real word?)
   - Evaluates anagram potential
   - Considers hidden word and double definition options

2. **Word Swap Suggestions**
   - Finds words with similar letter patterns
   - Prioritizes thematic fit with surface reading
   - Suggests more common/accessible vocabulary
   - Maintains the same cryptic mechanism

## Testing

Run the test suite:

```bash
python tests/test_workshop.py
```

This verifies:
- Excellent clues are preserved
- Low-quality clues get alternative mechanism suggestions
- Word swap suggestions work correctly
- All quality thresholds are respected

## Statistics

After running the workshop agent, you'll see:

```
======================================================================
WORKSHOP COMPLETE
======================================================================
Total clues analyzed: 5
Keep as is: 3 (60.0%)
Alternative mechanism: 1 (20.0%)
Word swap: 1 (20.0%)

Results saved to: workshopped_clues.json
======================================================================
```

## Philosophy

**"Don't workshop perfection."**

The workshop agent follows a conservative approach:
- Excellent clues (90%+ scores) are always preserved
- Only clues with clear quality issues receive suggestions
- All suggestions are advisory, not mandatory
- The goal is continuous improvement, not universal revision
