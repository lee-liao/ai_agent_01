# Implementation Tasks

## 1. Prompt Structure
- [ ] 1.1 Create `prompts/child_coach_v1.json` with system prompt
- [ ] 1.2 Include version number, author, date, description
- [ ] 1.3 Define prompt template with variables
- [ ] 1.4 Add example user messages and expected responses
- [ ] 1.5 Create `prompts/CHANGELOG.md`

## 2. Prompt Loader
- [ ] 2.1 Create `backend/app/prompts.py` module
- [ ] 2.2 Implement `load_prompt(version)` function
- [ ] 2.3 Default to latest version if not specified
- [ ] 2.4 Cache loaded prompts
- [ ] 2.5 Validate prompt structure on load

## 3. Snapshot Tests
- [ ] 3.1 Create `tests/snapshots/prompt_responses.json`
- [ ] 3.2 Store expected outputs for sample inputs
- [ ] 3.3 Implement `tests/test_prompts.py`
- [ ] 3.4 Compare actual vs snapshot outputs
- [ ] 3.5 Provide diff when snapshots don't match

## 4. Version Check CI Job
- [ ] 4.1 Add `check-prompt-version` job to CI
- [ ] 4.2 Detect changes in `prompts/*.json` files
- [ ] 4.3 Extract version numbers from changed files
- [ ] 4.4 Fail if version not incremented
- [ ] 4.5 Require CHANGELOG update

## 5. Runtime Version Selection
- [ ] 5.1 Add environment variable `PROMPT_VERSION`
- [ ] 5.2 Load specified version on startup
- [ ] 5.3 Log active prompt version
- [ ] 5.4 Support fallback to v1 if version not found
- [ ] 5.5 Document version selection in README

