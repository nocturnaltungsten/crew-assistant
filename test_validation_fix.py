#!/usr/bin/env python3
"""
Quick test to verify validation fixes are working
"""

import sys
import os

# Add project root to path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import create_crew_engine


def test_validation_improvements():
    """Test validation with simple tasks and override phrases."""
    print("🧪 Testing Validation Improvements")
    print("="*50)
    
    # Set up crew engine
    try:
        engine = create_crew_engine(
            provider='lmstudio',
            model='deepseek/deepseek-r1-0528-qwen3-8b',
            verbose=True
        )
        print("✅ Crew engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test cases that should now pass validation
    test_cases = [
        ("Simple task (should be approved)", "Create a basic sorting algorithm"),
        ("Simple task with details", "Write a Python function to calculate factorial"),
        ("Override phrase", "Build a password manager - JUST BUILD IT"),
        ("Vague but with override", "Make something cool - do the best you can"),
        ("Should still be rejected", "Build something"),
    ]
    
    results = []
    
    for description, task in test_cases:
        print(f"\n🎯 Testing: {description}")
        print(f"   Task: {task}")
        
        try:
            result = engine.execute_task(task)
            
            if hasattr(result, 'status'):
                status = result.status.value
            else:
                status = "unknown"
            
            success = result.success
            final_output = str(getattr(result, 'final_output', ''))
            
            # Determine if validation passed
            validation_passed = "approved" in final_output.lower() or success
            
            print(f"   Status: {status}")
            print(f"   Success: {success}")
            print(f"   Validation: {'✅ PASSED' if validation_passed else '❌ REJECTED'}")
            
            results.append({
                "description": description,
                "task": task,
                "validation_passed": validation_passed,
                "success": success,
                "status": status
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "description": description,
                "task": task,
                "validation_passed": False,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*50)
    print("📊 VALIDATION TEST SUMMARY")
    print("="*50)
    
    for result in results:
        status_icon = "✅" if result.get("validation_passed") else "❌"
        print(f"{status_icon} {result['description']}")
        print(f"   {result['task']}")
        if result.get("error"):
            print(f"   Error: {result['error']}")
        print()
    
    # Analysis
    passed = sum(1 for r in results if r.get("validation_passed"))
    total = len(results)
    
    print(f"Validation Pass Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= 3:  # Expect simple tasks + overrides to pass
        print("🎉 Validation improvements are working!")
    else:
        print("⚠️  Validation still too strict - needs more tuning")


if __name__ == "__main__":
    test_validation_improvements()