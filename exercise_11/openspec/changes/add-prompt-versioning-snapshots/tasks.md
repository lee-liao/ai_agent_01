# Implementation Tasks

## 1. Prompt Structure
- [x] 1.1 Create `prompts/child_coach_v1.json` with system prompt
- [x] 1.2 Include version number, author, date, description
- [x] 1.3 Define prompt template with variables
- [x] 1.4 Add example user messages and expected responses
- [x] 1.5 Create `prompts/CHANGELOG.md`

## 2. Prompt Loader
- [x] 2.1 Create `backend/app/prompts.py` module
- [x] 2.2 Implement `load_prompt(version)` function
- [x] 2.3 Default to latest version if not specified
- [x] 2.4 Cache loaded prompts
- [x] 2.5 Validate prompt structure on load

## 3. Snapshot Tests
- [x] 3.1 Create `tests/snapshots/prompt_responses.json`
- [x] 3.2 Store expected outputs for sample inputs with `expected_patterns` and `should_not_contain`
- [x] 3.3 Implement `tests/test_prompts.py` with `test_snapshot_patterns_match()`
- [x] 3.4 Implement flexible pattern matching (exact phrase, keyword-based, regex for citations)
- [x] 3.5 Call LLM with test inputs and validate responses against patterns
- [x] 3.6 Handle async LLM calls with `@pytest.mark.asyncio`

## 4. Version Check CI Job
- [x] 4.1 Implement prompt version validation as pytest tests (`test_prompt_version_changes.py`)
- [x] 4.2 Detect changes in `prompts/child_coach_v*.json` files using git diff
- [x] 4.3 Extract version numbers from changed files (filename and JSON content)
- [x] 4.4 Validate filename matches JSON version field
- [x] 4.5 Require CHANGELOG.md update when prompts change
- [x] 4.6 Integrate tests into `test-backend` CI job (with `fetch-depth: 0` for git history)

## 5. Runtime Version Selection
- [x] 5.1 Add environment variable `PROMPT_VERSION` in `.env` file
- [x] 5.2 Load specified version on startup (via load_prompt)
- [x] 5.3 Log active prompt version (in main.py startup)
- [x] 5.4 Support fallback to v1 if version not found
- [x] 5.5 Document version selection in `CHANGELOG.md` (Active Prompt Version Configuration section)
- [x] 5.6 Document test commands in `exercise_11/docs/TEST_COMMANDS.md`

## 6. Additional Improvements
- [x] 6.1 Fixed datetime deprecation warnings (use `timezone.utc` instead of `datetime.utcnow()`)
- [x] 6.2 Tested prompt version validation (without and with changelog scenarios)
- [x] 6.3 Verified CI compatibility (git available, fetch-depth: 0 configured)

---

## Implementation Summary

### Key Features Implemented

1. **Prompt Versioning System**
   - JSON-based prompt files with version metadata
   - Version loader with caching and fallback support
   - Environment variable configuration (`PROMPT_VERSION`)
   - Comprehensive changelog documentation

2. **Snapshot Testing**
   - Pattern-based validation (not exact matching)
   - Flexible keyword matching for concepts
   - Citation detection via regex
   - Async LLM integration with pytest-asyncio

3. **CI/CD Validation**
   - Pytest-based tests for prompt version changes
   - Git-based change detection (`HEAD~1` to `HEAD`)
   - Filename-version consistency validation
   - Changelog requirement enforcement

### Test Coverage

- **Snapshot Pattern Tests**: `tests/test_prompts.py::test_snapshot_patterns_match`
  - Validates LLM responses against expected patterns
  - Tests both positive (expected patterns) and negative (forbidden patterns)
  
- **Version Change Tests**: `tests/test_prompt_version_changes.py`
  - `test_prompt_files_have_valid_filenames`
  - `test_prompt_filename_version_matches_json_version`
  - `test_changelog_updated_when_prompts_change`

### Files Created/Modified

**New Files:**
- `exercise_11/prompts/child_coach_v1.json` - Initial prompt version
- `exercise_11/prompts/CHANGELOG.md` - Version history and documentation
- `exercise_11/backend/app/prompts.py` - Prompt loader module
- `exercise_11/backend/tests/test_prompts.py` - Prompt and snapshot tests
- `exercise_11/backend/tests/test_prompt_version_changes.py` - Version validation tests
- `exercise_11/backend/tests/snapshots/prompt_responses.json` - Snapshot test data
- `exercise_11/docs/TEST_COMMANDS.md` - Test execution guide

**Modified Files:**
- `exercise_11/billing/ledger.py` - Fixed datetime deprecation warnings
- `.github/workflows/exercise_11_ci.yml` - Integrated version tests into test-backend job
- `exercise_11/backend/.env` - Added PROMPT_VERSION configuration

### Validation Results

✅ All tests passing:
- Snapshot pattern tests: **PASSED** (validates LLM responses)
- Version change tests: **PASSED** (validates prompt version consistency)
- Tested scenarios: without changelog (fails) and with changelog (passes)

✅ CI/CD Ready:
- Git history available in GitHub Actions
- Tests integrated into existing CI pipeline
- Proper error messages for validation failures

