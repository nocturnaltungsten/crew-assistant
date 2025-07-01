#!/usr/bin/env python3
"""
Quick test to verify the crew workflow test system works
"""

import asyncio
import sys
import os

# Add project root to path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from long_duration_crew_test import LongDurationCrewTester
from crew_test_tasks import get_task_bank, get_random_task


async def quick_test():
    """Run a quick 2-minute test to verify system works."""
    print("🧪 Quick Crew System Test (2 minutes)")
    print("="*50)
    
    # Test task bank
    print("📝 Testing task bank...")
    task_bank = get_task_bank()
    print(f"   Task categories: {len(task_bank)}")
    total_tasks = sum(len(tasks) for tasks in task_bank.values())
    print(f"   Total tasks: {total_tasks}")
    
    # Show some examples
    for category in ["simple", "vague", "vague_override"]:
        example = get_random_task(category)
        print(f"   {category}: {example[:60]}...")
    
    print("\n🚀 Starting 2-minute crew workflow test...")
    
    # Run 2-minute test
    tester = LongDurationCrewTester(duration_hours=2/60)  # 2 minutes
    await tester.run()
    
    print("✅ Quick test completed!")


if __name__ == "__main__":
    asyncio.run(quick_test())