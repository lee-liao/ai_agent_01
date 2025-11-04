"""
Pytest tests for prompt version changes validation.

These tests validate that:
1. Changed prompt files have matching version numbers in filename and JSON content
2. CHANGELOG.md is updated when prompt files are changed

NOTE: These tests require git history and may be skipped if not available.
"""

import json
import re
import pytest
import subprocess
from pathlib import Path


def get_repo_paths():
    """Get paths relative to this test file."""
    tests_dir = Path(__file__).parent
    backend_dir = tests_dir.parent
    exercise_dir = backend_dir.parent
    repo_root = exercise_dir.parent
    prompts_dir = exercise_dir / "prompts"
    return repo_root, prompts_dir


def get_changed_files(repo_root):
    """
    Get list of changed files between HEAD~1 and HEAD.
    
    Returns:
        List of changed file paths, or None if git history unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root
        )
        changed_files = result.stdout.strip().split("\n")
        return [f for f in changed_files if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or shallow clone
        return None


@pytest.fixture
def changed_files():
    """Fixture that provides changed files, skipping if git history unavailable."""
    repo_root, _ = get_repo_paths()
    files = get_changed_files(repo_root)
    if files is None:
        pytest.skip("Git history not available (shallow clone or no git)")
    return files


def test_prompt_files_have_valid_filenames(changed_files):
    """Test that changed prompt files follow the naming convention."""
    repo_root, _ = get_repo_paths()
    errors = []
    
    prompt_changes = [
        f for f in changed_files 
        if "prompts/child_coach_" in f and f.endswith(".json")
    ]
    
    if not prompt_changes:
        pytest.skip("No prompt files changed in this commit")
    
    for changed_file in prompt_changes:
        file_path = repo_root / changed_file if changed_file.startswith("exercise_11/") else repo_root / "exercise_11" / changed_file
        
        if not file_path.exists():
            continue  # File deleted, skip
        
        match = re.search(r'child_coach_v(\d+)\.json', file_path.name)
        assert match is not None, (
            f"Invalid prompt filename: {file_path.name} "
            f"(should be child_coach_vX.json)"
        )


def test_prompt_filename_version_matches_json_version(changed_files):
    """Test that prompt file versions in filename match JSON version field."""
    repo_root, prompts_dir = get_repo_paths()
    errors = []
    
    prompt_changes = [
        f for f in changed_files 
        if "prompts/child_coach_" in f and f.endswith(".json")
    ]
    
    if not prompt_changes:
        pytest.skip("No prompt files changed in this commit")
    
    for changed_file in prompt_changes:
        file_path = repo_root / changed_file if changed_file.startswith("exercise_11/") else repo_root / "exercise_11" / changed_file
        
        if not file_path.exists():
            continue  # File deleted, skip
        
        # Extract version from filename
        match = re.search(r'child_coach_v(\d+)\.json', file_path.name)
        if not match:
            continue  # Already checked in test_prompt_files_have_valid_filenames
        
        file_version = int(match.group(1))
        
        # Load JSON and check version
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        json_version = prompt_data.get("version", "")
        assert json_version.startswith(str(file_version)), (
            f"Version mismatch in {file_path.name}: "
            f"filename version is v{file_version} but JSON version is {json_version}"
        )


def test_changelog_updated_when_prompts_change(changed_files):
    """Test that CHANGELOG.md is updated when prompt files change."""
    prompt_changes = [
        f for f in changed_files 
        if "prompts/child_coach_" in f and f.endswith(".json")
    ]
    
    if not prompt_changes:
        pytest.skip("No prompt files changed in this commit")
    
    changelog_updated = any("CHANGELOG.md" in f for f in changed_files)
    
    assert changelog_updated, (
        "Prompt files changed but CHANGELOG.md was not updated. "
        "Please document the changes in prompts/CHANGELOG.md"
    )
