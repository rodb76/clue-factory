# Minimalist Lie Logic - Classic Ximenean Economy

**Date:** February 11, 2026  
**Status:** ✅ Complete

## Philosophy

The **Minimalist Lie** is the art of crafting cryptic clues with maximum deception using minimum words. Every word must earn its place by serving either:
1. **Mechanical purpose** (definition, fodder, indicator)
2. **Thematic necessity** (essential for plausible surface deception)

Classic Ximenean economy eliminates literary flourishes and verbose connectors in favor of lean, elegant constructions where the surface reading is both misleading and grammatically sound.

## Implementation Summary

### Setter Agent Updates (`setter_agent.py`)

Enhanced the surface generation prompt with three key principles:

#### 1. The Minimalist Mandate
```
Start with ONLY: Definition + Fodder + Indicator
Add words ONLY if required for plausible, deceptive narrative (Thematic Necessity Test)
```

#### 2. Grammatical Integrity
- Avoid literal connectors like "gives", "plus", "becomes"
- Prefer grammatical links (possessives: 's, gerunds: -ing)
- Surface must read as coherent English

#### 3. Gold Standard Examples Added

**Anagram - DORMITORY:**
```
"Confused dirty room (9)"
Perfect 1:1 ratio - no filler words needed
```

**Reversal - REGAL:**
```
"Majestic lager returned (5)"
Zero filler - surface implies drink sent back, cryptic reverses letters
```

**Hidden Word:**
```
"How illusionist disguises a dead giveaway? (4)"
"disguises" serves as both indicator AND thematic anchor
```

**Charade:**
```
"Stronghold's right to be candid (10)"
Possessive 's acts as grammatical link (has)
```

### Auditor Updates (`auditor.py`)

#### Enhanced Filler Check
Now references MINIMALIST LIE terminology:
```python
"[FAIL] Too many connectors (3): becomes, gives, with. 
MINIMALIST LIE: Use at most 2 connectors. 
Build with Definition + Fodder + Indicator first."
```

```python
"[FAIL] Filler words detected: carefully, perhaps, result. 
These words fail the THEMATIC NECESSITY TEST. 
Every word must be definition, fodder, indicator, or essential thematic connector."
```

#### Refined Indicator Grammar Check
Position-aware and type-aware grammar validation:

- **Past participles BEFORE fodder:** ACCEPTABLE (attributive use)
  - ✅ "Confused dirty room" - classic style
  
- **Past participles AFTER fodder:**
  - ❌ FAIL for Anagrams (predicative = wrong)
  - ✅ PASS for Reversals (natural for type)
  - ✅ Example: "lager returned" acceptable for reversal

#### Updated Noun Indicators List
Removed ambiguous words that serve as imperative verbs:
- ❌ Removed: "mix", "scramble" (can be imperatives)
- ✅ Kept: "anagram", "medley", "salad", "mixture", "hash", "chaos", "mess", "jumble", "tangle"

**Rationale:** "Mix listen" uses "mix" as imperative verb (command), not noun.

## Test Results

Created comprehensive test suite ([tests/test_minimalist_lie.py](../tests/test_minimalist_lie.py)):

### Gold Standard Tests ✅
1. **DORMITORY** - "Confused dirty room"
   - Perfect 1:1 ratio (def + fodder + indicator only)
   - **Score:** 100% (all 6 checks passed)

2. **REGAL** - "Majestic lager returned"
   - Zero filler, grammatically perfect
   - **Score:** 100% (all 6 checks passed)

### Negative Tests (Correctly Failing) ✅
3. **Excessive Connectors** - "Listen mixed gives quiet result with becomes silence"
   - **Failed:** 3 connectors (max is 2)
   - **Score:** 66.7% ❌

4. **Non-Essential Words** - "Perhaps listen carefully disturbed for quiet result"
   - **Failed:** "perhaps", "carefully", "result" fail Thematic Necessity Test
   - **Score:** 66.7% ❌

### Minimalist Pass Test ✅
5. **Ideal Economy** - "Mix listen for quiet"
   - 1 connector ("for"), imperative indicator ("mix")
   - **Score:** 100% ✅

## Comparison: Before vs. After

### Before (Lenient Style)
```
Clue: "Perhaps when you become confused with listen it gives quite a silent result"
- Multiple filler words: "perhaps", "when", "you", "quite", "a", "result"
- 4 connectors: "become", "with", "it", "gives"
- Verbose, literary
- Fairness: ~50% (fails filler check)
```

### After (MINIMALIST LIE)
```
Clue: "Mix listen for quiet"
- No filler words
- 1 connector: "for"
- Grammatically tight, imperative indicator
- Fairness: 100% (passes all checks)
```

## The Six Audit Checks

All clues must pass 6 checks for 100% fairness:

1. **Direction Check** - No down-only indicators
2. **Double Duty Check** - Definition/wordplay separation (LLM)
3. **Indicator Fairness** - No noun indicators for anagrams
4. **Fodder Presence** - Exact fodder physically in clue
5. **Filler Check** - Max 2 connectors, no non-essential words
6. **Grammar Check** - Imperative indicators (position/type aware)

## Allowed Connectors (Max 2)

Standard Ximenean structural words:
- is, for, gives, from, at, becomes, to, in, of, with

**Preferred alternatives:**
- Use grammatical constructions instead:
  - Possessive: "'s" instead of "has"
  - Gerund: "-ing" for action
  - Direct juxtaposition when possible

## Usage Guidelines

### For Setter Agent
1. Always start: `Definition + Fodder + Indicator`
2. Test: Does this form a plausible sentence?
3. If NO: Add minimum words for thematic coherence
4. Avoid: "gives", "plus", "becomes" (use grammar instead)
5. Target: 0-1 connectors ideal, 2 maximum

### For Auditor
- Fodder must be physically present (no synonyms)
- Max 2 connectors allowed
- Imperative indicators preferred for anagrams
- Past participles acceptable before fodder (attributive)
- Type-specific rules (reversals get more flexibility)

## Examples of Acceptable Constructions

### Zero Connectors (Ideal)
- "Confused dirty room" → DORMITORY
- "Majestic lager returned" → REGAL

### One Connector (Good)
- "Mix listen for quiet" → SILENT
- "Stronghold's right to be candid" → FORTHRIGHT (using 's)

### Two Connectors (Maximum)
- "Broken listen in quiet place" → SILENT + location
  - Connectors: "in", optional liaison

## Technical Details

### Files Modified
1. **setter_agent.py**
   - Updated system prompt with MINIMALIST LIE principles
   - Added Gold Standard examples to few-shot learning
   - Enhanced user prompt with thematic necessity requirement

2. **auditor.py**
   - Refined `_check_filler_words()` feedback messages
   - Completely rewrote `_check_indicator_grammar()` for position/type awareness
   - Updated `NOUN_INDICATORS` to remove imperative-capable words

3. **tests/test_minimalist_lie.py** (NEW)
   - 5 comprehensive test functions
   - Validates gold standards, negative cases, edge cases
   - Total runtime: ~30 seconds (10 API calls)

### Backward Compatibility
- ✅ All existing tests still pass
- ✅ Old clues continue to work (lenient → strict is additive)
- ✅ AuditResult structure unchanged

## Impact on Pipeline

### Expected Changes
- **Initial Pass Rate:** May decrease 10-20% (stricter validation)
- **Final Quality:** Significantly improved elegance and economy
- **Fairness Scores:** More clues achieving 100% (fewer 66-83% scores)
- **Regeneration:** Setter learns from audit feedback to produce tighter clues

### Success Metrics
- Average words per clue: ↓ 15-20%
- Fairness score distribution: Shift toward 100%
- Connector usage: ↓ 50% (from 3-4 to 1-2)
- Filler word frequency: ↓ 80%

## Next Steps

1. **Monitor Production:** Track success rates in factory_run()
2. **Collect Data:** Analyze which clue types need adjustment
3. **Iterate Examples:** Refine few-shot examples if patterns emerge
4. **User Feedback:** Validate that minimalist clues are still solvable

## Philosophy Statement

> "The best cryptic clue is like a perfect crime: every element has a purpose, nothing is wasted, and the deception is complete. The Minimalist Lie achieves maximum misdirection with minimum means, honoring the Ximenean principle that economy enhances elegance."

## References

- Classic Ximenean standards (Ximenes, Azed tradition)
- Don Manley's "Chambers Crossword Manual"
- The Guardian crossword style guide
- Times Crossword Society guidelines

---

**Summary:** MINIMALIST LIE logic enforces classic Ximenean economy by building clues from essential components only (def + fodder + indicator), adding words solely for thematic necessity, and preferring grammatical links over literal connectors. Result: Cleaner, fairer, more elegant cryptic clues.
