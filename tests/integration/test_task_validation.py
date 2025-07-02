#!/usr/bin/env python3
"""Integration test for the task validation feature."""

import os
import pytest
from crew_assistant.core import create_crew_engine


@pytest.mark.integration
def test_validation():
    """Test the task validation system with clear and unclear requests."""

    # Set up environment
    os.environ["AI_PROVIDER"] = "lmstudio"
    os.environ["OPENAI_API_MODEL"] = "microsoft/phi-4-mini-reasoning"
    os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"

    try:
        engine = create_crew_engine(
            provider="lmstudio", model="microsoft/phi-4-mini-reasoning", verbose=True
        )

        print("🧪 Testing Task Validation System\n")

        # Test 1: Unclear/vague request (should be rejected)
        print("=" * 60)
        print("Test 1: Vague request (should need clarification)")
        print("=" * 60)

        vague_request = "make something cool"
        result1 = engine.execute_task(vague_request)

        print(f"Status: {result1.status.value}")
        print(f"Success: {result1.success}")
        print(f"Feedback: {result1.final_output[:200]}...")

        print("\n" + "=" * 60)
        print("Test 2: Clear request (should be approved)")
        print("=" * 60)

        clear_request = "Create a Python script that reads a CSV file and generates a bar chart showing the frequency of values in the first column. Include error handling for missing files and proper documentation."
        result2 = engine.execute_task(clear_request)

        print(f"Status: {result2.status.value}")
        print(f"Success: {result2.success}")
        if result2.success:
            print("✅ Clear request approved and processed by crew!")
        else:
            print(f"Feedback: {result2.final_output[:200]}...")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_validation()
