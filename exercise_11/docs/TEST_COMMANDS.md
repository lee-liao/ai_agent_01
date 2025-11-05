# Test Commands Reference

## Running Snapshot Pattern Tests

Test file: `tests/test_prompts.py`
Test function: `test_snapshot_patterns_match`

### Basic command:
```bash
cd exercise_11/backend
pytest tests/test_prompts.py::test_snapshot_patterns_match -v
```

### With detailed output:
```bash
cd exercise_11/backend
pytest tests/test_prompts.py::test_snapshot_patterns_match -v -s
```

### Run all tests in test_prompts.py:
```bash
cd exercise_11/backend
pytest tests/test_prompts.py -v
```

### Notes:
- Requires `OPENAI_API_KEY` environment variable to be set
- Will call OpenAI API (costs money)
- Uses `@pytest.mark.asyncio` decorator for async support
- Tests pattern matching against LLM responses from `tests/snapshots/prompt_responses.json`

---

## Running Prompt Version Change Tests

Test file: `tests/test_prompt_version_changes.py`

### Run all version change tests:
```bash
cd exercise_11/backend
pytest tests/test_prompt_version_changes.py -v
```

### Run specific tests:
```bash
# Test 1: Valid filenames
cd exercise_11/backend
pytest tests/test_prompt_version_changes.py::test_prompt_files_have_valid_filenames -v

# Test 2: Version consistency
cd exercise_11/backend
pytest tests/test_prompt_version_changes.py::test_prompt_filename_version_matches_json_version -v

# Test 3: Changelog update requirement
cd exercise_11/backend
pytest tests/test_prompt_version_changes.py::test_changelog_updated_when_prompts_change -v
```

### Notes:
- Requires git history (compares `HEAD~1` to `HEAD`)
- Tests will be **skipped** if:
  - Git history is unavailable (shallow clone, no git)
  - No prompt files were changed in the commit
- These tests validate prompt version changes in CI/CD pipeline

---

## Running Both Test Suites

### Run all tests:
```bash
cd exercise_11/backend
pytest tests/ -v
```

### Run with coverage:
```bash
cd exercise_11/backend
pytest tests/ -v --cov=app --cov-report=html
```

---

## Prerequisites

### Install dependencies:
```bash
cd exercise_11/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### Set environment variables (for snapshot tests):
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

### Or use .env file:
Make sure `exercise_11/backend/.env` contains:
```env
OPENAI_API_KEY=your-api-key-here
```
