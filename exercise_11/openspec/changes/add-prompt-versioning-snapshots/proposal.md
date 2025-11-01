# Add Prompt Versioning & Snapshots

## Why
Prompts are critical to AI behavior. Versioning ensures changes are tracked, tested, and reversible. Snapshot tests catch unintended prompt changes that could degrade response quality.

## What Changes
- Create `prompts/child_coach_vX.json` for versioned prompts
- Implement `tests/snapshots/` for prompt snapshot tests
- Create prompt changelog document
- CI fails if prompts change without version bump
- Support loading specific prompt versions at runtime

## Impact
- Affected specs: New capability `prompt-versioning`
- Affected code:
  - `prompts/child_coach_v1.json` - Prompt templates
  - `prompts/CHANGELOG.md` - Version history
  - `backend/app/prompts.py` - Prompt loader
  - `tests/snapshots/prompt_responses.json` - Expected outputs
  - `tests/test_prompts.py` - Snapshot tests
  - `.github/workflows/ci.yml` - Version check job

