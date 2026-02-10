# Tests Directory

This directory contains all test files for the Cryptic Crossword Clue Generator project.

## Running Tests

All tests can be run from the project root directory:

```bash
# Run a specific test
python tests/test_mechanic.py

# Run integration tests
python tests/test_explanation_integration.py
python tests/test_integration_mechanical_first.py

# Run validation tests
python tests/test_definition_hardening.py
```

## Test Categories

### Unit Tests
- `test_mechanic.py` - Mechanical validation tests (25 tests)
- `test_auditor.py` - Ximenean auditor tests (8 tests)
- `test_setter.py` - Setter agent tests
- `test_word_selector.py` - Word selection tests (13 tests)
- `test_word_pool_loader.py` - Word pool loader tests
- `test_explanation_integration.py` - Explanation agent tests

### Integration Tests
- `test_integration.py` - Setter + Mechanic integration
- `test_integration_mechanical_first.py` - Full pipeline tests (10 tests)
- `test_phase3.py` - Phase 3 component tests (17 tests)

### Validation Tests
- `test_definition_hardening.py` - Definition exactness validation
- `test_definition_validation.py` - Definition validation logic
- `test_double_duty_fix.py` - Double duty hallucination fixes
- `test_auditor_parser_fix.py` - Auditor parser hardening
- `test_hardened_logic.py` - Hardened parsing tests
- `test_parser_hardening.py` - JSON parser robustness

### Verification Scripts
- `verify_all_improvements.py` - Comprehensive improvement verification
- `verify_setter_fix.py` - Setter agent verification

### Demo Scripts
- `demo_mechanical_first.py` - Mechanical-first pipeline demo (no API calls)
- `HARDENED_LOGIC_DEMO.py` - Hardened logic demonstrations
- `REFINED_LOGIC_DEMO.py` - Refined logic demonstrations

## Test Configuration

All tests import `test_config.py` which sets up the Python path to allow importing from the parent directory where the main source code resides.

## Adding New Tests

When creating new test files:

1. Import `test_config` at the top:
   ```python
   import test_config
   from module_name import ClassName
   ```

2. Run tests from the project root:
   ```bash
   python tests/your_new_test.py
   ```

3. For file paths in tests, use relative paths from project root:
   ```python
   import os
   path = os.path.join('..', 'word_pools', 'seed_words.json')
   ```
