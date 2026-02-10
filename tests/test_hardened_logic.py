import test_config
"""
Test hardened Solver reasoning and Auditor fairness.
Verifies all four improvements requested by the user.
"""

import sys
import inspect
import json

print("\n" + "="*70)
print("TEST: HARDENED SOLVER REASONING & AUDITOR FAIRNESS")
print("="*70 + "\n")

# Test 1: Solver Step 0 - Hidden Word Priority
print("TEST 1: Solver System Prompt - Step 0 Hidden Word Priority")
print("-" * 60)
try:
    from solver_agent import SolverAgent
    source = inspect.getsource(SolverAgent.solve_clue)
    
    has_step_0 = "MANDATORY STEP 0" in source or "0." in source
    has_hidden_check = "look for a hidden word" in source
    has_physically_written = "physically written inside" in source
    has_check_before = "BEFORE trying complex wordplay" in source
    
    print(f"  Step 0 present: {'✓' if has_step_0 else '✗'}")
    print(f"  Hidden word check instruction: {'✓' if has_hidden_check else '✗'}")
    print(f"  'Physically written' phrase: {'✓' if has_physically_written else '✗'}")
    print(f"  Check before complex wordplay: {'✓' if has_check_before else '✗'}")
    
    if all([has_step_0, has_hidden_check, has_physically_written, has_check_before]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 2: Solver Sound-Alike Constraint
print("TEST 2: Solver System Prompt - Sound-Alike Constraint")
print("-" * 60)
try:
    source = inspect.getsource(SolverAgent.solve_clue)
    
    has_step_7 = "7." in source or "SOUND-ALIKE CONSTRAINT" in source
    has_sound_alike_example = "WAIL/WHALE" in source or "sound-alikes" in source
    has_choose_definition = "choose the one that matches the DEFINITION" in source
    has_synonym_requirement = "must be a synonym of the definition" in source
    
    print(f"  Step 7 or Sound-Alike Constraint: {'✓' if has_step_7 else '✗'}")
    print(f"  Sound-alike example (WAIL/WHALE): {'✓' if has_sound_alike_example else '✗'}")
    print(f"  Choose based on definition: {'✓' if has_choose_definition else '✗'}")
    print(f"  Synonym requirement: {'✓' if has_synonym_requirement else '✗'}")
    
    if all([has_step_7, has_sound_alike_example, has_choose_definition, has_synonym_requirement]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 3: Auditor Refined Double Duty Check
print("TEST 3: Auditor Double Duty Check - Synonym Exemption")
print("-" * 60)
try:
    from auditor import XimeneanAuditor
    source = inspect.getsource(XimeneanAuditor._check_double_duty_with_llm)
    
    has_important_note = "IMPORTANT" in source or "Do NOT flag" in source
    has_standard_synonym = "standard synonym for the definition" in source
    has_indicator_only = "WORDPLAY INDICATOR" in source
    has_example_clarification = "mixed" in source and "hidden" in source
    
    print(f"  IMPORTANT note present: {'✓' if has_important_note else '✗'}")
    print(f"  Standard synonym exemption: {'✓' if has_standard_synonym else '✗'}")
    print(f"  Only flag wordplay indicators: {'✓' if has_indicator_only else '✗'}")
    print(f"  Example clarification: {'✓' if has_example_clarification else '✗'}")
    
    if all([has_important_note, has_standard_synonym, has_indicator_only, has_example_clarification]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 4: Setter Hidden Word Instructions
print("TEST 4: Setter Hidden Word - Non-Suspicious Words")
print("-" * 60)
try:
    from setter_agent import SetterAgent
    source = inspect.getsource(SetterAgent.generate_wordplay_only)
    
    has_hidden_word_note = "Hidden Word" in source
    has_common_words = "common, non-suspicious words" in source
    has_betray_example = "BETRAY" in source or "alphabet ray" in source
    has_avoid_obvious = "less obvious" in source or "non-suspicious" in source
    
    print(f"  Hidden Word rule present: {'✓' if has_hidden_word_note else '✗'}")
    print(f"  Common, non-suspicious instruction: {'✓' if has_common_words else '✗'}")
    print(f"  BETRAY example: {'✓' if has_betray_example else '✗'}")
    print(f"  Avoid obvious phrasing: {'✓' if has_avoid_obvious else '✗'}")
    
    if all([has_hidden_word_note, has_common_words, has_betray_example, has_avoid_obvious]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 5: JSON Parser Hardening (Solver)
print("TEST 5: Solver JSON Parser - Truncation Handling")
print("-" * 60)
try:
    source = inspect.getsource(SolverAgent._parse_json_response)
    
    has_last_block_note = "LAST" in source
    has_truncation_note = "truncation" in source or "truncated" in source
    has_regex_pattern = "json_pattern" in source
    has_reversed_iteration = "reversed" in source
    
    print(f"  Notes about LAST block: {'✓' if has_last_block_note else '✗'}")
    print(f"  Truncation handling mentioned: {'✓' if has_truncation_note else '✗'}")
    print(f"  Regex pattern for JSON objects: {'✓' if has_regex_pattern else '✗'}")
    print(f"  Reversed iteration (last to first): {'✓' if has_reversed_iteration else '✗'}")
    
    # Functional test with truncated JSON
    test_truncated = '{"reasoning": "First...", "answer": "TEST", "confidence": "High"} and then some extra'
    try:
        result = SolverAgent._parse_json_response(test_truncated)
        truncation_works = result.get("answer") == "TEST"
    except:
        truncation_works = False
    
    print(f"  Functional test (truncated JSON): {'✓' if truncation_works else '✗'}")
    
    if all([has_last_block_note, has_truncation_note, has_regex_pattern, has_reversed_iteration, truncation_works]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 6: JSON Parser - Multiple Blocks (corrections)
print("TEST 6: JSON Parser - Handle Multiple Correction Blocks")
print("-" * 60)
try:
    # Test with multiple JSON blocks (LLM corrections)
    test_multiple = '''```json
{"answer": "WRONG"}
```
Wait, let me reconsider...
```json
{"answer": "CORRECT", "confidence": "High"}
```'''
    
    result = SolverAgent._parse_json_response(test_multiple)
    takes_last = result.get("answer") == "CORRECT"
    
    print(f"  Takes LAST JSON block: {'✓ CORRECT' if takes_last else '✗ WRONG'}")
    
    if takes_last:
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Final Summary
print("="*70)
print("ALL TESTS PASSED ✓")
print("="*70)
print("\nHardening Summary:")
print("  1. Solver: Added Step 0 - Check for hidden words FIRST")
print("  2. Solver: Added Step 7 - Sound-alike constraint (choose definition match)")
print("  3. Auditor: Refined Double Duty - Exempt standard synonyms")
print("  4. Setter: Hidden Word instruction - Use non-suspicious common words")
print("  5. Solver: Hardened JSON parser - Handles truncation & corrections")
print("\nExpected Impact:")
print("  • Solver finds hidden words immediately (no overthinking)")
print("  • Solver chooses correct sound-alike based on definition")
print("  • Auditor stops flagging valid definition synonyms")
print("  • Hidden word clues less obvious to solvers")
print("  • JSON parsing handles truncated/corrected responses")
print("\n" + "="*70 + "\n")

