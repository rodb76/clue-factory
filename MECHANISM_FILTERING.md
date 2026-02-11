# Mechanism Filtering Feature

## Overview
Mechanism filtering allows users to specify required clue types for a clue generation run, ensuring that only specific cryptic mechanisms are used.

## Implementation Date
February 11, 2026

## Problem Statement
Previously, the clue factory would generate clues using any available mechanism. Users needed a way to:
1. **Focus on specific clue types** for targeted practice or testing
2. **Prevent "Path of Least Resistance"** where the AI defaults to easier mechanisms
3. **Explicitly inject clue types** into the Logic Tier for precise control

## Solution: Required Types Parameter

### 1. Parameter Addition
Added `required_types` parameter to `factory_run()`:

```python
def factory_run(
    target_count: int = 20,
    batch_size: int = 10,
    max_concurrent: int = 5,
    output_file: str = "final_clues_output.json",
    use_seed_words: bool = True,
    required_types: Optional[List[str]] = None  # NEW
) -> List[ClueResult]:
```

**Values:**
- `None` or empty list: All clue types allowed (default behavior)
- `["Charade"]`: Only Charade clues
- `["Charade", "Container"]`: Only Charade or Container clues
- Any combination of: Anagram, Charade, Hidden Word, Container, Reversal, Homophone, Double Definition

### 2. Filter Logic
When `required_types` is specified, word selection is filtered:

```python
if required_types:
    # MECHANISM FILTER: Only select words matching required types
    # Distribute evenly across required types
    types_cycle = required_types * (current_batch_size // len(required_types) + 1)
    
    for clue_type in types_cycle[:current_batch_size]:
        seed_result = word_loader.get_specific_type_seed(clue_type, avoid_duplicates=True)
        if seed_result:
            word_type_pairs.append(seed_result)
```

**How it works:**
1. Creates a cycling list of required types (e.g., `[Charade, Container, Charade, Container, ...]`)
2. Selects words matching each type in sequence
3. Ensures even distribution across required types
4. Uses `get_specific_type_seed()` for type-specific selection

### 3. Mechanism Injection
The clue type is explicitly passed to the Setter Agent:

```python
result = process_single_clue_sync(
    word,
    clue_type,  # ← Explicitly passed
    setter,
    solver,
    auditor,
    ...
)
```

This prevents the Logic Tier from defaulting to easier mechanisms.

### 4. Filter Logging
When filter is active, an INFO message is logged:

```python
if required_types:
    logger.info(f"Batch Filter Active: Only processing {required_types}")
    print(f"\n*** MECHANISM FILTER ACTIVE ***")
    print(f"Only generating: {', '.join(required_types)}")
```

**Example output:**
```
2026-02-11 14:30:00,123 - __main__ - INFO - Batch Filter Active: Only processing ['Charade', 'Container']

*** MECHANISM FILTER ACTIVE ***
Only generating: Charade, Container
```

## Usage Examples

### Command Line Interface
When running `python main.py` and selecting Factory mode:

```
Select mode:
  1. Fixed Batch Mode (10 predefined words)
  2. Clue Factory Mode (automated word selection until target reached)

Enter choice (1 or 2, default=2): 2

How many valid clues to generate? (default=20): 10

Mechanism Filter (optional):
Available types: Anagram, Charade, Hidden Word, Container, Reversal, Homophone, Double Definition
Examples: 'Charade,Container' or 'Anagram' or leave blank for all types

Filter by clue types (comma-separated, or Enter for all): Charade,Container
Filter activated: Charade, Container
```

### Programmatic Usage

**Example 1: Generate only Charades**
```python
from main import factory_run

results = factory_run(
    target_count=10,
    batch_size=5,
    required_types=["Charade"]
)
```

**Example 2: Generate Charades and Containers**
```python
results = factory_run(
    target_count=20,
    batch_size=10,
    required_types=["Charade", "Container"]
)
```

**Example 3: No filter (all types)**
```python
results = factory_run(
    target_count=20,
    batch_size=10,
    required_types=None  # or omit parameter
)
```

## Test Results

### Test Suite: test_mechanism_filter.py

**Test 1: Filter for Charades only** ✅
```
Required types: ['Charade']

1. PIANIST    → Charade
2. BITTERN    → Charade
3. DALLAS     → Charade
4. DETRACT    → Charade
5. HANDSOME   → Charade

✓ SUCCESS: All 5 words are Charades
```

**Test 2: Filter for Charade and Container** ✅
```
Required types: ['Charade', 'Container']

1. FORGET      → Charade
2. ERNEST      → Container
3. FORTHRIGHT  → Charade
4. HURRICANE   → Container
5. BAPTISM     → Charade
6. VICTORIAN   → Container

✓ SUCCESS: All 6 words are Charade or Container
```

**Test 3: Mechanism Injection** ✅
- Verified clue_type is explicitly passed to setter
- Prevents "Path of Least Resistance" defaults

**Test 4: Filter Logging** ✅
- Verified INFO log message when filter is active
- Clear user feedback in console output

## Word Pool Requirements

**For filtering to work, you must use seed_words.json:**
- `use_seed_words=True` (default)
- Word pool files must have type categorization

**WordSelector fallback:**
- If `required_types` is specified but `use_seed_words=False`, a warning is logged:
  ```
  WordSelector doesn't support type filtering. Use seed_words.json for mechanism filtering.
  ```

## Current Word Pool Statistics

From test run (284 word-type pairs across 4 seed files):
```
Type distribution:
  Anagram             :  40 words
  Charade             :  45 words
  Container           :  47 words
  Double Definition   :  38 words
  Hidden Word         :  39 words
  Homophone           :  38 words
  Reversal            :  37 words
```

Good distribution ensures filters have sufficient words to work with.

## Benefits

1. **Targeted Practice**: Focus on specific clue types for learning or testing
2. **Quality Control**: Avoid mechanisms that historically have lower success rates
3. **Explicit Control**: Force specific mechanisms rather than relying on AI defaults
4. **Even Distribution**: Cycling ensures balanced type selection
5. **Pool Management**: Uses `get_specific_type_seed()` for efficient filtering

## Integration with Existing Pipeline

Mechanism filtering integrates seamlessly with:
- ✅ **Mechanical-First Generation**: Filter works with wordplay validation
- ✅ **Solver Pipeline**: No changes needed
- ✅ **Auditor Checks**: All 8 checks still applied
- ✅ **Phase 10 Metrics**: Ximenean score, difficulty, narrative fidelity calculated
- ✅ **Explanation Generation**: Hints and breakdowns still generated

## Future Enhancements

Potential improvements:
1. **CLI arguments**: Add `--types` flag for command-line control
2. **Type weighting**: Allow percentage distribution (e.g., 70% Charade, 30% Container)
3. **Dynamic filtering**: Adjust filter based on success rates
4. **Type combinations**: Filter for clues that could use multiple mechanisms
5. **Difficulty-based filtering**: Filter by clue difficulty level (Phase 10 metrics)

## References
- [word_pool_loader.py](../word_pool_loader.py): `get_specific_type_seed()` method
- [main.py](../main.py): `factory_run()` function with filtering logic
- [test_mechanism_filter.py](../tests/test_mechanism_filter.py): Test suite demonstrating feature
