# Quick Start Guide: Cryptic Clue Generator

## 🚀 Quick Commands

### Setup (One-time)
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.template .env
# Edit .env and add your PORTKEY_API_KEY
```

### Run Tests
```bash
# Test Setter Agent (Phase 1)
python test_setter.py

# Test Mechanic validators (Phase 2)
python test_mechanic.py

# Test Word Pool Loader (Phase 5.6)
python test_word_pool_loader.py

# Test Integration (Phase 5.6)
python test_integration_mechanical_first.py

# Run mechanic demo
python mechanic.py

# Demo the mechanical-first pipeline (no API calls)
python demo_mechanical_first.py
```

### Generate Valid Clues (Clue Factory)
```bash
# Generate 5 valid clues using the mechanical-first pipeline
python -c "from main import factory_run; factory_run(target_count=5, use_seed_words=True)"

# Generate 20 valid clues (default)
python main.py
# Select option 2 (Clue Factory Mode)
# Enter target count: 20
```

### Generate & Validate Single Clues
```bash
# Generate a single clue with Setter Agent
python setter_agent.py

# Or use Python directly:
python -c "from setter_agent import SetterAgent; s = SetterAgent(); print(s.generate_cryptic_clue('SILENT', 'Anagram'))"
```

## 📚 Code Examples

### Generate Valid Clues (Recommended - Mechanical-First Pipeline)
```python
from main import factory_run

# Generate 10 valid clues using seed words
results = factory_run(
    target_count=10,
    batch_size=5,
    max_concurrent=3,
    use_seed_words=True  # Uses seed_words.json (recommended)
)

# Print successful clues
for result in results:
    print(f"✓ {result.word}: {result.clue_json['clue']}")
```

### Generate a Single Clue (Basic)
```python
from setter_agent import SetterAgent

setter = SetterAgent()
clue = setter.generate_cryptic_clue("LISTEN", "Hidden Word")

print(f"Clue: {clue['clue']}")
print(f"Definition: {clue['definition']}")
print(f"Explanation: {clue['explanation']}")
```

### Mechanical-First Generation (Two-Step Process)
```python
from setter_agent import SetterAgent
from mechanic import validate_clue_complete

setter = SetterAgent()

# Step 1: Generate mechanical draft (wordplay only)
wordplay_data = setter.generate_wordplay_only("SILENT", "Anagram")

# Step 2: Validate mechanically
temp_clue = {
    "answer": "SILENT",
    "type": "Anagram",
    "wordplay_parts": wordplay_data.get("wordplay_parts", {})
}
all_valid, results = validate_clue_complete(temp_clue, "(6)")

if all_valid:
    # Step 3: Generate surface polish
    final_clue = setter.generate_surface_from_wordplay(wordplay_data, "SILENT")
    print(f"✓ Valid clue: {final_clue['clue']}")
else:
    print("✗ Mechanical validation failed")
```

### Validate a Clue
```python
from mechanic import validate_clue_complete

clue = {
    "answer": "SILENT",
    "type": "Anagram",
    "wordplay_parts": {"fodder": "listen"}
}

all_valid, results = validate_clue_complete(clue, "(6)")

for check, result in results.items():
    print(f"{check}: {'✓' if result else '✗'} {result.message}")
```

### Full Workflow (Generate + Validate)
```python
from setter_agent import SetterAgent
from mechanic import validate_clue_complete

# 1. Generate
setter = SetterAgent()
clue = setter.generate_cryptic_clue("PARTRIDGE", "Charade")

# 2. Validate
all_valid, results = validate_clue_complete(clue, "(9)")

# 3. Report
if all_valid:
    print(f"✓ Valid clue: {clue['clue']}")
else:
    print("✗ Validation failed")
    for check, result in results.items():
        if not result:
            print(f"  Failed: {result.message}")
```

## 🎯 Supported Clue Types

| Type | Example | Validator Status |
|------|---------|------------------|
| Anagram | "Confused listen" → SILENT | ✅ Implemented |
| Hidden Word | "Silent listener" → LISTEN | ✅ Implemented |
| Charade | "Part + Ridge" → PARTRIDGE | ✅ Implemented |
| Container | "IN in PAT" → PAINT | ✅ Implemented |
| Reversal | "STAR backwards" → RATS | ✅ Implemented |
| Homophone | "Sounds like WAIT" → WEIGHT | ⚠️ LLM required |
| Double Definition | "Tender (gentle/money)" → TENDER | ⚠️ LLM required |
| &lit | Entire clue = definition | ⚠️ LLM required |

## 📊 Project Status

### ✅ Phase 1: Setup & Generation
- Portkey client initialized
- Setter Agent implemented
- JSON parsing robust
- 5/5 tests passing

### ✅ Phase 2: Mechanical Validation
- 5 validators implemented
- Length checking added
- 25/25 tests passing
- Integration ready

### 🔄 Phase 3: Adversarial Loop (Next)
- Solver Agent (in progress)
- Referee Logic (planned)
- Parallel batching (planned)

## 🐛 Troubleshooting

### "PORTKEY_API_KEY not set"
```bash
# Create .env file from template
cp .env.template .env
# Edit .env and add your key
```

### "Request timed out"
- Check network connectivity to Portkey gateway
- Increase timeout: `SetterAgent(timeout=60.0)`
- Verify API key has permissions

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 📖 Documentation

- [README.md](README.md) - Full documentation
- [architecture.md](architecture.md) - System design
- [spec.md](spec.md) - Functional requirements
- [todo.md](todo.md) - Implementation roadmap
- [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) - Phase 2 details

## 🧪 Test Coverage

```
Setter Agent:   5 tests  ✓
Mechanic:      25 tests  ✓
Total:         30 tests  ✓
Success Rate:  100%
```

## 💡 Tips

1. **Start with simple clue types** (Anagram, Hidden Word)
2. **Always validate generated clues** before using
3. **Check the explanation field** to understand wordplay
4. **Use enumeration** for better validation
5. **Review logs** if validation fails

## 🔗 Quick Links

- [Portkey Documentation](https://docs.portkey.ai/)
- [Ximenean Standards](https://en.wikipedia.org/wiki/Ximenean_rules)
- [Cryptic Clue Types](https://en.wikipedia.org/wiki/Cryptic_crossword)

---

**Ready to generate cryptic clues!** 🎯

Start with: `python setter_agent.py`
