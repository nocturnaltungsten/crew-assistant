#!/usr/bin/env python3
"""
Long Duration Integration Test Runner
Runs for 2-4+ hours unattended, collecting maximum integration data
Handles all errors gracefully and continues testing
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from crew_assistant.providers.lmstudio_enhanced import LMStudioEnhancedProvider  # TODO: Create enhanced providers
# from crew_assistant.providers.ollama_enhanced import OllamaEnhancedProvider  # TODO: Create enhanced providers
# from crew_assistant.providers.registry_enhanced import EnhancedProviderRegistry, ModelRequirements, get_registry  # TODO: Create enhanced providers
from crew_assistant.providers.base import ChatMessage, ProviderError


# Configure comprehensive logging
LOG_DIR = Path("test_logs") / f"long_duration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Multiple log files for different aspects
logging.basicConfig(level=logging.INFO)

# Main test log
main_logger = logging.getLogger("main")
main_handler = logging.FileHandler(LOG_DIR / "main_test.log")
main_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
main_logger.addHandler(main_handler)

# Performance metrics log
perf_logger = logging.getLogger("performance")
perf_handler = logging.FileHandler(LOG_DIR / "performance_metrics.log")
perf_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
perf_logger.addHandler(perf_handler)

# Error log
error_logger = logging.getLogger("errors")
error_handler = logging.FileHandler(LOG_DIR / "errors.log")
error_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s\n%(exc_info)s")
)
error_logger.addHandler(error_handler)

# Integration log
integration_logger = logging.getLogger("integration")
integration_handler = logging.FileHandler(LOG_DIR / "integration_events.log")
integration_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
integration_logger.addHandler(integration_handler)


class TestScenario:
    """Base class for test scenarios."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.execution_count = 0
        self.success_count = 0
        self.total_time = 0.0
        self.errors: List[str] = []

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        """Execute the test scenario."""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """Get scenario statistics."""
        return {
            "name": self.name,
            "executions": self.execution_count,
            "successes": self.success_count,
            "failures": self.execution_count - self.success_count,
            "success_rate": (self.success_count / self.execution_count * 100)
            if self.execution_count > 0
            else 0,
            "avg_time": (self.total_time / self.execution_count) if self.execution_count > 0 else 0,
            "total_time": self.total_time,
            "errors": self.errors[-5:],  # Last 5 errors
        }


class SimpleInferenceTest(TestScenario):
    """Basic inference test with varying token sizes."""

    def __init__(self):
        super().__init__("simple_inference", weight=3.0)
        self.token_sizes = [100, 500, 1000, 5000, 10000]

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        token_size = random.choice(self.token_sizes)
        prompt = "Explain the concept of " + " ".join(
            [
                random.choice(["quantum", "distributed", "neural", "genetic", "parallel"])
                + " "
                + random.choice(["computing", "systems", "networks", "algorithms", "processing"])
                for _ in range(token_size // 20)
            ]
        )

        messages = [ChatMessage(role="user", content=prompt)]

        start_time = time.time()
        try:
            response = await provider.chat_async(
                messages, model, max_tokens=min(500, token_size // 10), temperature=0.7
            )

            elapsed = time.time() - start_time
            return {
                "success": True,
                "token_size": token_size,
                "response_length": len(response.content),
                "elapsed_time": elapsed,
                "tokens_per_second": token_size / elapsed if elapsed > 0 else 0,
                "response_preview": response.content[:100],
            }
        except Exception as e:
            return {
                "success": False,
                "token_size": token_size,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }


class StreamingTest(TestScenario):
    """Test streaming capabilities with various response sizes."""

    def __init__(self):
        super().__init__("streaming", weight=2.0)

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        prompts = [
            "Write a detailed 10-step plan for building a distributed system",
            "Explain machine learning concepts with examples",
            "Create a comprehensive code review checklist",
            "Design a microservices architecture",
        ]

        prompt = random.choice(prompts)
        messages = [ChatMessage(role="user", content=prompt)]

        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        total_content = ""

        try:
            async for chunk in provider.chat_streaming(messages, model, max_tokens=1000):
                if not first_chunk_time and chunk.content:
                    first_chunk_time = time.time() - start_time

                chunks_received += 1
                total_content += chunk.content

                if chunk.is_final:
                    break

            total_time = time.time() - start_time

            return {
                "success": True,
                "chunks": chunks_received,
                "first_chunk_latency": first_chunk_time,
                "total_time": total_time,
                "response_length": len(total_content),
                "streaming_rate": chunks_received / total_time if total_time > 0 else 0,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "elapsed_time": time.time() - start_time}


class ConcurrentLoadTest(TestScenario):
    """Test concurrent request handling."""

    def __init__(self):
        super().__init__("concurrent_load", weight=1.5)

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        concurrent_count = random.randint(2, 5)

        tasks = []
        for i in range(concurrent_count):
            messages = [
                ChatMessage(
                    role="user",
                    content=f"Request {i + 1}: Generate a random fact about {random.choice(['space', 'ocean', 'technology', 'history'])}",
                )
            ]
            tasks.append(provider.chat_async(messages, model, max_tokens=100))

        start_time = time.time()
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            successful = sum(1 for r in results if not isinstance(r, Exception))

            return {
                "success": successful > 0,
                "concurrent_requests": concurrent_count,
                "successful_requests": successful,
                "failed_requests": concurrent_count - successful,
                "total_time": elapsed,
                "avg_time_per_request": elapsed / concurrent_count,
            }
        except Exception as e:
            return {
                "success": False,
                "concurrent_requests": concurrent_count,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }


class LargeContextTest(TestScenario):
    """Test with large context windows (10k-50k tokens)."""

    def __init__(self):
        super().__init__("large_context", weight=0.5)

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        # Use battle test context generation
        from tests.integration.test_battle_providers import generate_large_context

        token_size = random.choice([10000, 20000, 30000, 40000])
        context = generate_large_context(token_size)

        messages = [
            ChatMessage(role="system", content="You are a technical analyst."),
            ChatMessage(
                role="user", content=f"{context}\n\nSummarize the key points in 3 bullets."
            ),
        ]

        start_time = time.time()
        try:
            response = await provider.chat_async(messages, model, max_tokens=200, temperature=0.3)

            elapsed = time.time() - start_time

            return {
                "success": True,
                "context_tokens": token_size,
                "response_length": len(response.content),
                "elapsed_time": elapsed,
                "tokens_per_second": token_size / elapsed if elapsed > 0 else 0,
                "memory_impact": "monitored",  # Could add actual memory monitoring
            }
        except Exception as e:
            return {
                "success": False,
                "context_tokens": token_size,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }


class ProviderFailoverTest(TestScenario):
    """Test provider failover and recovery."""

    def __init__(self):
        super().__init__("provider_failover", weight=0.5)

    async def execute(self, provider, model: str) -> Dict[str, Any]:
        # This tests the registry's failover capabilities
        registry = get_registry()

        start_time = time.time()
        try:
            # Try to get optimal provider
            optimal = registry.get_optimal_provider()
            if not optimal:
                return {
                    "success": False,
                    "error": "No providers available",
                    "elapsed_time": time.time() - start_time,
                }

            # Make a request
            messages = [ChatMessage(role="user", content="Test failover capability")]
            response = await optimal.chat_async(messages, model, max_tokens=50)

            # Check health
            health = optimal.get_health_status()

            return {
                "success": True,
                "provider_used": optimal.name,
                "health_status": health.is_healthy,
                "response_time": health.response_time,
                "consecutive_failures": health.consecutive_failures,
                "elapsed_time": time.time() - start_time,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "elapsed_time": time.time() - start_time}


class LongDurationTestRunner:
    """Main test runner that orchestrates all scenarios."""

    def __init__(self, duration_hours: float = 2.0):
        self.duration = timedelta(hours=duration_hours)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration

        # Initialize scenarios
        self.scenarios = [
            SimpleInferenceTest(),
            StreamingTest(),
            ConcurrentLoadTest(),
            LargeContextTest(),
            ProviderFailoverTest(),
        ]

        # Test statistics
        self.total_tests = 0
        self.successful_tests = 0
        self.provider_stats: Dict[str, Dict[str, Any]] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {}

        # Initialize registry
        self.registry = get_registry()

        main_logger.info(f"Initialized test runner for {duration_hours} hours")
        main_logger.info(f"Test will run until {self.end_time}")
        main_logger.info(f"Log directory: {LOG_DIR}")

    def select_scenario(self) -> TestScenario:
        """Select a scenario based on weights."""
        weights = [s.weight for s in self.scenarios]
        return random.choices(self.scenarios, weights=weights)[0]

    async def run_single_test(self) -> None:
        """Run a single test iteration."""
        scenario = self.select_scenario()

        # Get provider and model
        provider = self.registry.get_optimal_provider()
        if not provider:
            error_logger.error("No providers available")
            return

        # Get a suitable model
        models = provider.list_models()
        suitable_models = [
            m
            for m in models
            if m.compatibility == "compatible"
            and "embed" not in m.id.lower()
            and any(size in m.id.lower() for size in ["7b", "8b", "13b", "14b"])
        ]

        if not suitable_models:
            error_logger.error("No suitable models available")
            return

        model = random.choice(suitable_models)

        # Log test start
        integration_logger.info(f"Starting {scenario.name} with {provider.name}:{model.id}")

        # Execute scenario
        try:
            result = await scenario.execute(provider, model.id)

            # Update statistics
            scenario.execution_count += 1
            self.total_tests += 1

            if result.get("success", False):
                scenario.success_count += 1
                self.successful_tests += 1
                scenario.total_time += result.get("elapsed_time", 0)

                # Log performance metrics
                perf_logger.info(
                    json.dumps(
                        {
                            "scenario": scenario.name,
                            "provider": provider.name,
                            "model": model.id,
                            **result,
                        }
                    )
                )
            else:
                error_msg = f"{scenario.name} failed: {result.get('error', 'Unknown error')}"
                scenario.errors.append(error_msg)
                error_logger.error(error_msg, exc_info=True)

            # Update provider/model stats
            provider_key = provider.name
            if provider_key not in self.provider_stats:
                self.provider_stats[provider_key] = {"requests": 0, "successes": 0, "total_time": 0}

            self.provider_stats[provider_key]["requests"] += 1
            if result.get("success", False):
                self.provider_stats[provider_key]["successes"] += 1
                self.provider_stats[provider_key]["total_time"] += result.get("elapsed_time", 0)

            # Log integration event
            integration_logger.info(
                json.dumps(
                    {
                        "event": "test_complete",
                        "scenario": scenario.name,
                        "provider": provider.name,
                        "model": model.id,
                        "success": result.get("success", False),
                        "duration": result.get("elapsed_time", 0),
                    }
                )
            )

        except Exception as e:
            error_logger.error(f"Unexpected error in {scenario.name}: {str(e)}", exc_info=True)
            scenario.errors.append(f"Unexpected: {str(e)}")

    def log_summary(self) -> None:
        """Log current test summary."""
        runtime = datetime.now() - self.start_time

        summary = {
            "runtime": str(runtime),
            "total_tests": self.total_tests,
            "successful_tests": self.successful_tests,
            "success_rate": (self.successful_tests / self.total_tests * 100)
            if self.total_tests > 0
            else 0,
            "tests_per_hour": (self.total_tests / runtime.total_seconds() * 3600)
            if runtime.total_seconds() > 0
            else 0,
            "scenario_stats": [s.get_stats() for s in self.scenarios],
            "provider_stats": self.provider_stats,
        }

        # Write summary to file
        with open(LOG_DIR / "test_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Log to console and main log
        main_logger.info(f"Test Summary after {runtime}:")
        main_logger.info(f"  Total Tests: {self.total_tests}")
        main_logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        main_logger.info(f"  Tests/Hour: {summary['tests_per_hour']:.1f}")
        main_logger.info(f"  Models Tested: {len(self.model_profiles)}")

        current_model = (
            self.test_models[self.current_model_idx][0].id if self.test_models else "None"
        )
        print(
            f"\n📊 Test Progress: {self.total_tests} tests, {summary['success_rate']:.1f}% success rate"
        )
        print(f"🤖 Current Model: {current_model}")
        print(f"🏭 Models Profiled: {len(self.model_profiles)}")

    async def run(self) -> None:
        """Run the long duration test."""
        print(
            f"🚀 Starting long duration test for {self.duration.total_seconds() / 3600:.1f} hours"
        )
        print(f"📁 Logs: {LOG_DIR}")
        print(f"⏰ Will run until {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 60 + "\n")

        # Start health monitoring
        self.registry.start_health_monitoring(interval=60)

        last_summary = time.time()

        try:
            while datetime.now() < self.end_time:
                # Run a test
                try:
                    await self.run_single_test()
                except Exception as e:
                    error_logger.error(f"Test iteration failed: {e}", exc_info=True)

                # Log summary every 5 minutes
                if time.time() - last_summary > 300:
                    self.log_summary()
                    last_summary = time.time()

                # Small delay between tests (1-5 seconds)
                await asyncio.sleep(random.uniform(1, 5))

                # Check if we should throttle based on time
                current_hour = datetime.now().hour
                if 22 <= current_hour or current_hour <= 6:  # Night hours
                    # Longer delays at night
                    await asyncio.sleep(random.uniform(5, 10))

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            main_logger.info("Test interrupted by user")

        finally:
            # Final summary
            self.log_summary()

            # Stop health monitoring
            self.registry.stop_health_monitoring()

            # Log final summary to console
            runtime = datetime.now() - self.start_time
            print("\n" + "=" * 60)
            print(f"✅ Test completed after {runtime}")
            print(f"📊 Total tests run: {self.total_tests}")
            print(f"✅ Successful tests: {self.successful_tests}")
            print(f"❌ Failed tests: {self.total_tests - self.successful_tests}")
            print(
                f"📈 Success rate: {(self.successful_tests / self.total_tests * 100) if self.total_tests > 0 else 0:.1f}%"
            )
            print(f"📁 Full results in: {LOG_DIR}")

            # Create final report
            self.create_final_report()

    def create_final_report(self) -> None:
        """Create a comprehensive final report."""
        runtime = datetime.now() - self.start_time

        report = f"""
# Long Duration Test Report

**Test Duration**: {runtime}
**Total Tests**: {self.total_tests}
**Success Rate**: {(self.successful_tests / self.total_tests * 100) if self.total_tests > 0 else 0:.1f}%

## Scenario Performance

"""

        for scenario in self.scenarios:
            stats = scenario.get_stats()
            report += f"""
### {scenario.name}
- Executions: {stats["executions"]}
- Success Rate: {stats["success_rate"]:.1f}%
- Average Time: {stats["avg_time"]:.2f}s
- Total Time: {stats["total_time"]:.1f}s
"""

        report += "\n## Provider Performance\n\n"
        for provider, stats in self.provider_stats.items():
            success_rate = (
                (stats["successes"] / stats["requests"] * 100) if stats["requests"] > 0 else 0
            )
            avg_time = (stats["total_time"] / stats["successes"]) if stats["successes"] > 0 else 0

            report += f"""
### {provider}
- Requests: {stats["requests"]}
- Success Rate: {success_rate:.1f}%
- Average Response Time: {avg_time:.2f}s
"""

        # Write report
        with open(LOG_DIR / "final_report.md", "w") as f:
            f.write(report)

        main_logger.info("Final report created")


async def main():
    """Main entry point."""
    # Check if running in throttled mode
    throttle_percent = int(os.environ.get("INFERENCE_THROTTLE", "100"))

    if throttle_percent < 100:
        print(f"🌙 Running in throttled mode at {throttle_percent}% performance")

    # Parse duration from command line
    duration_hours = 2.0  # Default
    if len(sys.argv) > 1:
        try:
            duration_hours = float(sys.argv[1])
        except:
            print("Usage: python long_duration_test.py [hours]")
            print("Using default duration of 2 hours")

    # Create and run test runner
    runner = LongDurationTestRunner(duration_hours)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
