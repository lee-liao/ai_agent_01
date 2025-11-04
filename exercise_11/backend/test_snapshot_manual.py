"""
Manual test script to see what happens when we call the LLM with snapshot test questions.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm import generate_advice_non_streaming


async def test_single_snapshot():
    """Test a single snapshot question."""
    # Load snapshots
    snapshots_file = Path(__file__).parent / "tests" / "snapshots" / "prompt_responses.json"
    
    with open(snapshots_file, 'r') as f:
        snapshots = json.load(f)
    
    # Get the first test case
    snapshot = snapshots["snapshots"][0]
    
    print("=" * 80)
    print(f"Test: {snapshot['test_name']}")
    print(f"Input: {snapshot['input']}")
    print(f"Expected patterns: {snapshot['expected_patterns']}")
    print(f"Should NOT contain: {snapshot['should_not_contain']}")
    print("=" * 80)
    print("\nCalling LLM...\n")
    
    # Call LLM
    response = await generate_advice_non_streaming(
        question=snapshot["input"],
        rag_context=[],
        session_id="test_manual"
    )
    
    print("LLM Response:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print("\n")
    
    # Check patterns
    response_lower = response.lower()
    
    print("Pattern Check Results:")
    print("-" * 80)
    
    # Check expected patterns
    print("\n✅ Expected patterns:")
    missing = []
    for pattern in snapshot["expected_patterns"]:
        if pattern.lower() in response_lower:
            print(f"  ✓ Found: '{pattern}'")
        else:
            print(f"  ✗ Missing: '{pattern}'")
            missing.append(pattern)
    
    # Check forbidden patterns
    print("\n❌ Forbidden patterns:")
    forbidden_found = []
    for forbidden in snapshot["should_not_contain"]:
        if forbidden.lower() in response_lower:
            print(f"  ✗ Found forbidden: '{forbidden}'")
            forbidden_found.append(forbidden)
        else:
            print(f"  ✓ Not present: '{forbidden}'")
    
    print("\n" + "=" * 80)
    if missing:
        print(f"❌ TEST WOULD FAIL: Missing {len(missing)} expected pattern(s)")
    elif forbidden_found:
        print(f"❌ TEST WOULD FAIL: Found {len(forbidden_found)} forbidden pattern(s)")
    else:
        print("✅ TEST WOULD PASS: All patterns validated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_single_snapshot())
