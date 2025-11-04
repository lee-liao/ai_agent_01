# Prompt Version Changelog

This document tracks all changes to system prompts used in the Child Growth Assistant.

## Version 1.0.0 (2025-01-01)

**Author**: Development Team

**Changes**:
- Updated date field to 2025-01-01 (test change for validation)

---

## Version 1.0.0 (2024-01-01)

**Author**: Development Team

**Initial Release**

- Created initial parenting coach system prompt
- Includes guidelines for warm, empathetic responses
- Supports RAG context integration
- Emphasizes evidence-based advice with citations
- Includes scope boundaries (no medical/legal/therapy advice)

**Template Structure**:
- System prompt with role definition
- Guidelines for response style
- RAG context integration format
- Citation requirements

---

## How to Add a New Version

When making changes to the system prompt, follow these steps:

### Step 1: Create a New Prompt File
1. Copy the current prompt JSON file (e.g., `child_coach_v1.json`)
2. Create a new file with the incremented version number (e.g., `child_coach_v2.json`)
3. Save it in the same directory as the existing prompt files

### Step 2: Make Your Changes
- Edit the new JSON file with your prompt modifications
- Test the new prompt to ensure it works as expected
- Update any references or metadata within the JSON file if needed

### Step 3: Update the Changelog
Add a new version entry at the **top** of this changelog (after the heading but before older versions) with the following structure:

```markdown
## Version X.Y.Z (YYYY-MM-DD)

**Author**: Your Name or Team Name

**Summary**: Brief one-line description of the changes

**Changes**:
- List specific changes made
- Explain what was modified
- Include reasoning for significant changes
- Note any breaking changes or new features

**Migration Notes** (if applicable):
- Any instructions for users/developers when upgrading
- Configuration changes required
- Deprecations or removals
```

### Step 4: Update Version References
- Update any configuration files that reference the prompt version
- Update tests or documentation that mention specific versions
- Update the active version being used in the application (see below)

### Step 5: Review and Test
- Review all changes for consistency
- Test the new prompt version thoroughly
- Ensure backward compatibility or document breaking changes

## Active Prompt Version Configuration

The active prompt version is controlled by the `PROMPT_VERSION` environment variable in the `.env` file located at `exercise_11/backend/.env`.

**Location**: `exercise_11/backend/.env`

**Configuration**:
```env
PROMPT_VERSION=1
```

**Behavior**:
- If `PROMPT_VERSION` is set, that specific version will be used (e.g., `PROMPT_VERSION=1` loads `child_coach_v1.json`)
- If `PROMPT_VERSION` is not set or set to `"latest"`, the system automatically uses the highest version number found in the prompts directory
- Version can be specified as `"1"`, `"1.0.0"`, `"v1"`, or `"latest"`

**Implementation Details**:
- The prompt version is loaded in `exercise_11/backend/app/prompts.py` by the `load_prompt()` function
- The active version is logged on application startup in `exercise_11/backend/app/main.py`
- To check the currently active version, look at the application logs on startup or call the `get_active_prompt_version()` function

**To Change the Active Version**:
1. Edit `exercise_11/backend/.env`
2. Set `PROMPT_VERSION=<version_number>` (e.g., `PROMPT_VERSION=2`)
3. Restart the backend application

## CI Validation

The CI pipeline (`.github/workflows/exercise_11_ci.yml`) automatically validates prompt changes on every commit and pull request. The validation ensures:

**What is Checked**:
1. **Filename-Content Consistency**: For any changed prompt file (`child_coach_v*.json`):
   - Extracts version number from filename (e.g., `child_coach_v2.json` → version `"2"`)
   - Verifies that the JSON `"version"` field matches the filename version
   - The JSON version must start with the filename version number (e.g., filename `v2` matches JSON `"2.0.0"`)

2. **Changelog Requirement**: If any prompt files are changed, the `CHANGELOG.md` must also be updated in the same commit

**What is NOT Checked**:
- ❌ Whether the version actually incremented from previous versions
- ❌ Whether it's a new file vs. modified existing file
- ❌ Semantic versioning compliance (MAJOR.MINOR.PATCH format)
- ❌ Content quality or correctness of prompt changes

**Validation Failure**:
If validation fails, the CI job will:
- Show specific error messages for each issue
- Provide guidance on how to fix the problems
- Block the commit/PR from merging until fixed

**Best Practice**:
- Always create a new version file when making changes (don't modify existing versions)
- Update the changelog with detailed information about your changes
- Test the new prompt before committing

## Version Format

Versions follow semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes to prompt structure or behavior
- **MINOR**: New features or significant improvements
- **PATCH**: Minor adjustments or fixes
