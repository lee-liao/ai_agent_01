"""
Prompt versioning and loading module.

Supports loading versioned prompts from JSON files with caching and validation.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Cache for loaded prompts
_prompt_cache: Dict[str, Dict] = {}


def get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    # Navigate from backend/app/ to exercise_11/prompts/
    backend_dir = Path(__file__).parent.parent.parent
    prompts_dir = backend_dir / "prompts"
    return prompts_dir


def load_prompt(version: Optional[str] = None) -> Dict:
    """
    Load a prompt version from JSON file.
    
    Args:
        version: Prompt version (e.g., "1", "1.0.0", "v1"). 
                 If None, loads the latest version.
    
    Returns:
        Dictionary with prompt data including 'template' key
    
    Raises:
        FileNotFoundError: If prompt file not found
        ValueError: If prompt structure is invalid
    """
    prompts_dir = get_prompts_dir()
    
    # Determine which version to load
    if version is None:
        # Load from environment variable or default to latest
        version = os.getenv("PROMPT_VERSION", "latest")
    
    # Normalize version string
    if version == "latest":
        # Find the highest version number
        version = _find_latest_version(prompts_dir)
    elif version.startswith("v"):
        version = version[1:]  # Remove "v" prefix
    
    # Check cache first
    cache_key = f"v{version}"
    if cache_key in _prompt_cache:
        logger.debug(f"Using cached prompt version {cache_key}")
        return _prompt_cache[cache_key]
    
    # Load prompt file
    prompt_file = prompts_dir / f"child_coach_v{version}.json"
    if not prompt_file.exists():
        # Try with version as-is (e.g., "1.0.0")
        prompt_file = prompts_dir / f"child_coach_{version}.json"
        if not prompt_file.exists():
            # Fallback to v1 if version not found
            logger.warning(f"Prompt version {version} not found, falling back to v1")
            prompt_file = prompts_dir / "child_coach_v1.json"
            if not prompt_file.exists():
                raise FileNotFoundError(
                    f"Prompt file not found: {prompt_file}. "
                    f"Available prompts: {list(prompts_dir.glob('child_coach_*.json'))}"
                )
    
    # Load and validate prompt
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    # Validate structure
    required_keys = ["version", "template"]
    for key in required_keys:
        if key not in prompt_data:
            raise ValueError(
                f"Invalid prompt structure: missing required key '{key}' in {prompt_file}"
            )
    
    # Cache the loaded prompt
    _prompt_cache[cache_key] = prompt_data
    
    logger.info(f"Loaded prompt version {prompt_data.get('version', version)} from {prompt_file.name}")
    
    return prompt_data


def _find_latest_version(prompts_dir: Path) -> str:
    """
    Find the latest version number from prompt files.
    
    Returns:
        Latest version number as string (e.g., "1", "2")
    """
    prompt_files = list(prompts_dir.glob("child_coach_v*.json"))
    
    if not prompt_files:
        raise FileNotFoundError(f"No prompt files found in {prompts_dir}")
    
    # Extract version numbers and find the highest
    versions = []
    for file in prompt_files:
        # Extract version from filename: child_coach_v1.json -> "1"
        name = file.stem  # "child_coach_v1"
        if name.startswith("child_coach_v"):
            version_str = name.replace("child_coach_v", "")
            try:
                # Try to parse as integer (major version)
                versions.append((int(version_str.split(".")[0]), version_str))
            except ValueError:
                # If not numeric, use string comparison
                versions.append((0, version_str))
    
    if not versions:
        raise ValueError(f"Could not parse versions from prompt files in {prompts_dir}")
    
    # Sort by version number (descending) and return the highest
    versions.sort(key=lambda x: x[0], reverse=True)
    return versions[0][1]


def get_active_prompt_version() -> str:
    """
    Get the currently active prompt version.
    
    Returns:
        Version string (e.g., "1.0.0")
    """
    prompt = load_prompt()
    return prompt.get("version", "unknown")


def build_prompt_with_rag(question: str, rag_context: list, prompt_version: Optional[str] = None) -> list:
    """
    Build prompt messages including RAG context using versioned prompt template.
    
    This is a convenience function that combines prompt loading with RAG context.
    
    Args:
        question: Parent's question
        rag_context: List of retrieved documents with 'source', 'content', 'url'
        prompt_version: Optional prompt version to use (defaults to latest)
        
    Returns:
        List of message dicts for OpenAI API
    """
    # Load prompt template
    prompt_data = load_prompt(version=prompt_version)
    system_prompt = prompt_data["template"]
    
    # Add RAG context if available
    if rag_context:
        context_lines = []
        for doc in rag_context:
            source = doc.get('source', 'Unknown Source')
            content = doc.get('content', '')
            context_lines.append(f"Source: {source}\nContent: {content}")
        
        context_text = "\n\n".join(context_lines)
        system_prompt += f"\n\nResearch Context:\n{context_text}\n\nPlease reference these sources in your response."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    return messages
