#!/usr/bin/env python3
"""
Long Duration Crew Workflow Test Runner
Tests the entire multi-agent system with varying task complexity and specificity
Runs for 2-4+ hours unattended, collecting comprehensive workflow performance data
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
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crew_assistant.core import create_crew_engine
from crew_assistant.providers.lmstudio import LMStudioProvider
from tests.fixtures.crew_test_tasks import get_task_bank

# Configure comprehensive logging
LOG_DIR = Path("test_logs") / f"crew_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Multiple log files for different aspects
logging.basicConfig(level=logging.INFO)

# Main test log
main_logger = logging.getLogger("crew_main")
main_handler = logging.FileHandler(LOG_DIR / "main_test.log")
main_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
main_logger.addHandler(main_handler)

# Workflow performance log
workflow_logger = logging.getLogger("workflow")
workflow_handler = logging.FileHandler(LOG_DIR / "workflow_performance.log")
workflow_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
workflow_logger.addHandler(workflow_handler)

# Agent performance log
agent_logger = logging.getLogger("agents")
agent_handler = logging.FileHandler(LOG_DIR / "agent_performance.log")
agent_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
agent_logger.addHandler(agent_handler)

# Task complexity analysis log
complexity_logger = logging.getLogger("complexity")
complexity_handler = logging.FileHandler(LOG_DIR / "task_complexity.log")
complexity_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
complexity_logger.addHandler(complexity_handler)

# Error log
error_logger = logging.getLogger("errors")
error_handler = logging.FileHandler(LOG_DIR / "errors.log")
error_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s\n%(exc_info)s")
)
error_logger.addHandler(error_handler)


class TaskComplexity:
    """Task complexity levels for systematic testing."""

    TRIVIAL = {
        "level": "trivial",
        "description": "Single-step, clear requests",
        "weight": 3.0,
        "examples": [
            "What is Python?",
            "List 5 programming languages",
            "Explain what a variable is",
            "Define REST API",
            "What is Git?",
        ],
    }

    SIMPLE = {
        "level": "simple",
        "description": "Clear requests with basic implementation",
        "weight": 3.0,
        "examples": [
            "Write a Python function to calculate factorial",
            "Create a simple HTML contact form",
            "Write a bash script to backup files",
            "Create a basic calculator in Python",
            "Write SQL to find top 5 customers",
        ],
    }

    MODERATE = {
        "level": "moderate",
        "description": "Multi-step projects with clear requirements",
        "weight": 2.5,
        "examples": [
            "Build a REST API for a todo app with authentication",
            "Create a web scraper that saves data to CSV",
            "Build a chat application using WebSockets",
            "Design a database schema for an e-commerce site",
            "Create a CI/CD pipeline for a Python project",
        ],
    }

    COMPLEX = {
        "level": "complex",
        "description": "Multi-component systems requiring planning",
        "weight": 2.0,
        "examples": [
            "Build a microservices architecture for user management with Docker",
            "Create a real-time analytics dashboard with React and Python backend",
            "Design and implement a distributed caching system",
            "Build a machine learning pipeline for text classification",
            "Create a full-stack e-commerce platform with payment integration",
        ],
    }

    VAGUE = {
        "level": "vague",
        "description": "Ambiguous requests requiring interpretation",
        "weight": 1.5,
        "examples": [
            "Make something cool",
            "Build an app",
            "Create a system for managing stuff",
            "I need something automated",
            "Build a game",
            "Make it better",
            "Fix this problem",
            "Optimize performance",
        ],
    }

    VAGUE_WITH_OVERRIDE = {
        "level": "vague_override",
        "description": "Vague requests with 'JUST BUILD IT' directive",
        "weight": 2.0,
        "examples": [
            "Make something cool - JUST BUILD IT",
            "Build an app. Do your best with what I've given you",
            "Create a system for managing stuff. Just build it the best you can",
            "I need something automated - work with what I've told you",
            "Build a game - JUST BUILD IT",
            "Make it better - proceed anyway",
        ],
    }


class CrewWorkflowTest:
    """Test scenario for crew workflow execution."""

    def __init__(self, name: str, complexity_level: dict, weight: float = 1.0):
        self.name = name
        self.complexity_level = complexity_level
        self.weight = weight
        self.execution_count = 0
        self.success_count = 0
        self.total_time = 0.0
        self.validation_approvals = 0
        self.validation_rejections = 0
        self.workflow_completions = 0
        self.agent_failures = 0
        self.errors: list[str] = []
        self.task_results: list[dict] = []

    async def execute(self, crew_engine, task_prompt: str) -> dict[str, Any]:
        """Execute a crew workflow test."""
        start_time = time.time()
        self.execution_count += 1

        try:
            main_logger.info(
                f"Executing {self.complexity_level['level']} task: {task_prompt[:100]}..."
            )

            # Execute the crew workflow
            result = crew_engine.execute_task(task_prompt)

            execution_time = time.time() - start_time
            self.total_time += execution_time

            # Analyze the result
            analysis = self._analyze_result(result, execution_time, task_prompt)
            self.task_results.append(analysis)

            if result.success:
                self.success_count += 1
                if hasattr(result, "iterations") and result.iterations > 0:
                    self.workflow_completions += 1
            else:
                error_msg = f"Task failed: {getattr(result, 'error_message', 'Unknown error')}"
                self.errors.append(error_msg)
                error_logger.error(f"Crew workflow failed: {error_msg}")

            # Log detailed workflow performance
            workflow_logger.info(
                json.dumps(
                    {
                        "complexity": self.complexity_level["level"],
                        "task": task_prompt[:200],
                        "success": result.success,
                        "execution_time": execution_time,
                        "status": getattr(result, "status", {}).value
                        if hasattr(result, "status")
                        else "unknown",
                        "iterations": getattr(result, "iterations", 0),
                        "steps_completed": len(getattr(result, "workflow_steps", [])),
                        "validation_approved": "approved"
                        in str(getattr(result, "final_output", "")).lower(),
                    }
                )
            )

            return analysis

        except Exception as e:
            execution_time = time.time() - start_time
            self.total_time += execution_time
            error_msg = f"Exception during execution: {str(e)}"
            self.errors.append(error_msg)
            error_logger.error(f"Crew test exception: {traceback.format_exc()}")

            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "complexity": self.complexity_level["level"],
            }

    def _analyze_result(self, result, execution_time: float, task_prompt: str) -> dict[str, Any]:
        """Analyze crew workflow result for insights."""
        analysis = {
            "task_prompt": task_prompt,
            "complexity": self.complexity_level["level"],
            "success": result.success,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
        }

        # Extract workflow-specific metrics
        if hasattr(result, "status"):
            analysis["status"] = result.status.value

        if hasattr(result, "iterations"):
            analysis["iterations"] = result.iterations

        if hasattr(result, "workflow_steps"):
            analysis["steps_completed"] = len(result.workflow_steps)
            analysis["agent_performances"] = []

            for step in result.workflow_steps:
                if hasattr(step, "result") and step.result:
                    agent_perf = {
                        "agent": step.agent_role,
                        "success": step.result.success,
                        "execution_time": step.result.execution_time,
                        "tokens_used": getattr(step.result, "tokens_used", 0),
                    }
                    analysis["agent_performances"].append(agent_perf)

                    # Log individual agent performance
                    agent_logger.info(
                        json.dumps(
                            {
                                "agent": step.agent_role,
                                "task_complexity": self.complexity_level["level"],
                                "success": step.result.success,
                                "execution_time": step.result.execution_time,
                                "tokens_used": getattr(step.result, "tokens_used", 0),
                                "task_snippet": task_prompt[:50],
                            }
                        )
                    )

        # Check for validation behavior
        final_output = str(getattr(result, "final_output", ""))
        if "needs clarification" in final_output.lower():
            self.validation_rejections += 1
            analysis["validation_result"] = "rejected"
        elif "approved" in final_output.lower() or result.success:
            self.validation_approvals += 1
            analysis["validation_result"] = "approved"

        # Log complexity analysis
        complexity_logger.info(
            json.dumps(
                {
                    "complexity_level": self.complexity_level["level"],
                    "task_length": len(task_prompt),
                    "has_just_build_it": "just build" in task_prompt.lower(),
                    "validation_result": analysis.get("validation_result", "unknown"),
                    "workflow_completed": result.success,
                    "execution_time": execution_time,
                    "iterations_required": getattr(result, "iterations", 0),
                }
            )
        )

        return analysis

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive test statistics."""
        return {
            "name": self.name,
            "complexity_level": self.complexity_level["level"],
            "executions": self.execution_count,
            "successes": self.success_count,
            "failures": self.execution_count - self.success_count,
            "success_rate": (self.success_count / self.execution_count * 100)
            if self.execution_count > 0
            else 0,
            "avg_time": (self.total_time / self.execution_count) if self.execution_count > 0 else 0,
            "total_time": self.total_time,
            "validation_approvals": self.validation_approvals,
            "validation_rejections": self.validation_rejections,
            "validation_approval_rate": (self.validation_approvals / self.execution_count * 100)
            if self.execution_count > 0
            else 0,
            "workflow_completions": self.workflow_completions,
            "workflow_completion_rate": (self.workflow_completions / self.execution_count * 100)
            if self.execution_count > 0
            else 0,
            "recent_errors": self.errors[-3:],
            "task_results": self.task_results[-5:],  # Last 5 detailed results
        }


class LongDurationCrewTester:
    """Main test runner for crew workflow system."""

    def __init__(self, duration_hours: float = 4.0):
        self.duration_hours = duration_hours
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=duration_hours)

        # Initialize test scenarios
        self.scenarios = [
            CrewWorkflowTest(
                "Trivial Tasks", TaskComplexity.TRIVIAL, TaskComplexity.TRIVIAL["weight"]
            ),
            CrewWorkflowTest(
                "Simple Tasks", TaskComplexity.SIMPLE, TaskComplexity.SIMPLE["weight"]
            ),
            CrewWorkflowTest(
                "Moderate Tasks", TaskComplexity.MODERATE, TaskComplexity.MODERATE["weight"]
            ),
            CrewWorkflowTest(
                "Complex Tasks", TaskComplexity.COMPLEX, TaskComplexity.COMPLEX["weight"]
            ),
            CrewWorkflowTest("Vague Tasks", TaskComplexity.VAGUE, TaskComplexity.VAGUE["weight"]),
            CrewWorkflowTest(
                "Vague Override Tasks",
                TaskComplexity.VAGUE_WITH_OVERRIDE,
                TaskComplexity.VAGUE_WITH_OVERRIDE["weight"],
            ),
        ]

        self.total_tests = 0
        self.total_successes = 0
        self.current_model = None
        self.crew_engine = None
        self.models_tested = []
        self.last_summary_time = datetime.now()

        main_logger.info(f"Initialized crew tester for {duration_hours} hours")
        main_logger.info(f"Target end time: {self.end_time}")

    def setup_crew_engine(self, provider_name: str, model: str) -> bool:
        """Set up crew engine with specified provider and model."""
        try:
            main_logger.info(f"Setting up crew engine with {provider_name}:{model}")

            self.crew_engine = create_crew_engine(provider=provider_name, model=model, verbose=True)

            self.current_model = f"{provider_name}:{model}"

            if model not in self.models_tested:
                self.models_tested.append(model)

            main_logger.info(f"Successfully initialized crew engine with {self.current_model}")
            return True

        except Exception as e:
            error_logger.error(f"Failed to setup crew engine with {provider_name}:{model}: {e}")
            return False

    def auto_select_lm_studio_model(self) -> str | None:
        """Automatically select best available LM Studio model."""
        try:
            config = {"base_url": "http://localhost:1234/v1", "api_key": "not-needed-for-local"}
            provider = LMStudioProvider(config)
            models = provider.list_models()

            if not models:
                main_logger.warning("No models available in LM Studio")
                return None

            # Prefer models that are likely to work well for crew workflows
            preferred_patterns = ["qwen", "llama", "mistral", "deepseek", "phi", "gemma"]

            # Extract model names from ModelInfo objects
            model_names = [m.id if hasattr(m, "id") else str(m) for m in models]

            # Filter out embedding models
            chat_models = [
                m for m in model_names if "embed" not in m.lower() and "embedding" not in m.lower()
            ]

            # Try to find a preferred model
            for pattern in preferred_patterns:
                for model in chat_models:
                    if pattern in model.lower():
                        main_logger.info(f"Auto-selected model: {model}")
                        return model

            # Fallback to first available chat model
            if chat_models:
                model = chat_models[0]
                main_logger.info(f"Fallback selected model: {model}")
                return model

            return None

        except Exception as e:
            error_logger.error(f"Failed to auto-select LM Studio model: {e}")
            return None

    def should_continue(self) -> bool:
        """Check if testing should continue."""
        return datetime.now() < self.end_time

    def select_random_task(self, scenario: CrewWorkflowTest) -> str:
        """Select a random task from the scenario's complexity level."""
        # Use extended task bank if available
        try:
            extended_tasks = get_task_bank()
            level = scenario.complexity_level["level"]
            if level in extended_tasks:
                return random.choice(extended_tasks[level])
        except:
            pass

        # Fallback to original examples
        return random.choice(scenario.complexity_level["examples"])

    def calculate_scenario_weights(self) -> list[float]:
        """Calculate normalized weights for scenario selection."""
        weights = [scenario.weight for scenario in self.scenarios]
        total_weight = sum(weights)
        return [w / total_weight for w in weights]

    async def run_test_cycle(self):
        """Run a single test cycle."""
        # Select scenario based on weights
        weights = self.calculate_scenario_weights()
        scenario = random.choices(self.scenarios, weights=weights)[0]

        # Select random task from scenario
        task_prompt = self.select_random_task(scenario)

        # Execute the test
        result = await scenario.execute(self.crew_engine, task_prompt)

        self.total_tests += 1
        if result.get("success", False):
            self.total_successes += 1

        # Log summary every 5 minutes
        if datetime.now() - self.last_summary_time > timedelta(minutes=5):
            await self.log_summary()
            self.last_summary_time = datetime.now()

    async def log_summary(self):
        """Log current test summary."""
        elapsed = datetime.now() - self.start_time
        remaining = self.end_time - datetime.now()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_hours": elapsed.total_seconds() / 3600,
            "remaining_hours": remaining.total_seconds() / 3600,
            "total_tests": self.total_tests,
            "total_successes": self.total_successes,
            "overall_success_rate": (self.total_successes / self.total_tests * 100)
            if self.total_tests > 0
            else 0,
            "current_model": self.current_model,
            "models_tested": len(self.models_tested),
            "scenarios": [scenario.get_stats() for scenario in self.scenarios],
        }

        # Save summary to file
        with open(LOG_DIR / "test_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        main_logger.info(
            f"SUMMARY: {self.total_tests} tests, {self.total_successes} successes "
            f"({summary['overall_success_rate']:.1f}%) in {elapsed}"
        )

        # Print to console
        print(f"\n{'=' * 60}")
        print("🧪 CREW WORKFLOW TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"⏱️  Elapsed: {elapsed} | Remaining: {remaining}")
        print(
            f"📊 Tests: {self.total_tests} | Successes: {self.total_successes} ({summary['overall_success_rate']:.1f}%)"
        )
        print(f"🤖 Current Model: {self.current_model}")
        print("📈 Scenarios tested:")
        for scenario in self.scenarios:
            stats = scenario.get_stats()
            print(
                f"   {stats['complexity_level']:12} | {stats['executions']:3} tests | {stats['success_rate']:5.1f}% success"
            )
        print(f"{'=' * 60}\n")

    async def run(self):
        """Run the long duration test."""
        main_logger.info("Starting long duration crew workflow test")

        # Auto-select LM Studio model
        model = self.auto_select_lm_studio_model()
        if not model:
            main_logger.error("Failed to find suitable model, aborting test")
            return

        # Setup crew engine
        if not self.setup_crew_engine("lmstudio", model):
            main_logger.error("Failed to setup crew engine, aborting test")
            return

        print(f"\n🚀 Starting {self.duration_hours}h crew workflow test with {model}")
        print(f"📁 Logs: {LOG_DIR}")
        print(f"⏰ End time: {self.end_time.strftime('%H:%M:%S')}")

        try:
            while self.should_continue():
                try:
                    await self.run_test_cycle()

                    # Random delay between tests (1-5 seconds)
                    await asyncio.sleep(random.uniform(1, 5))

                except KeyboardInterrupt:
                    main_logger.info("Test interrupted by user")
                    break
                except Exception:
                    error_logger.error(f"Test cycle error: {traceback.format_exc()}")
                    await asyncio.sleep(5)  # Brief pause on error

        finally:
            await self.generate_final_report()

    async def generate_final_report(self):
        """Generate comprehensive final report."""
        elapsed = datetime.now() - self.start_time

        report = {
            "test_run_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_hours": elapsed.total_seconds() / 3600,
                "planned_duration": self.duration_hours,
                "total_tests": self.total_tests,
                "total_successes": self.total_successes,
                "overall_success_rate": (self.total_successes / self.total_tests * 100)
                if self.total_tests > 0
                else 0,
                "models_tested": self.models_tested,
                "current_model": self.current_model,
            },
            "scenario_results": [scenario.get_stats() for scenario in self.scenarios],
            "insights": self._generate_insights(),
        }

        # Save JSON report
        with open(LOG_DIR / "final_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Generate markdown report
        markdown_report = self._generate_markdown_report(report)
        with open(LOG_DIR / "final_report.md", "w") as f:
            f.write(markdown_report)

        main_logger.info("Final report generated")
        print(f"\n📋 Final report saved to: {LOG_DIR}/final_report.md")

    def _generate_insights(self) -> dict[str, Any]:
        """Generate insights from test results."""
        insights = {
            "validation_patterns": {},
            "complexity_performance": {},
            "workflow_efficiency": {},
            "recommendations": [],
        }

        # Analyze validation patterns
        for scenario in self.scenarios:
            if scenario.execution_count > 0:
                approval_rate = scenario.validation_approvals / scenario.execution_count * 100
                insights["validation_patterns"][scenario.complexity_level["level"]] = {
                    "approval_rate": approval_rate,
                    "avg_time": scenario.total_time / scenario.execution_count,
                    "success_rate": scenario.success_count / scenario.execution_count * 100,
                }

        # Generate recommendations based on patterns
        if insights["validation_patterns"]:
            vague_approval = (
                insights["validation_patterns"].get("vague", {}).get("approval_rate", 0)
            )
            vague_override_approval = (
                insights["validation_patterns"].get("vague_override", {}).get("approval_rate", 0)
            )

            if vague_override_approval > vague_approval + 20:
                insights["recommendations"].append(
                    "JUST BUILD IT directive effectively improves vague task acceptance rate"
                )

            simple_success = (
                insights["validation_patterns"].get("simple", {}).get("success_rate", 0)
            )
            complex_success = (
                insights["validation_patterns"].get("complex", {}).get("success_rate", 0)
            )

            if simple_success > complex_success + 30:
                insights["recommendations"].append(
                    "Consider breaking down complex tasks into simpler subtasks for better success rates"
                )

        return insights

    def _generate_markdown_report(self, report: dict[str, Any]) -> str:
        """Generate markdown final report."""
        md = f"""# Crew Workflow Long Duration Test Report

## 📊 Test Run Summary
- **Duration**: {report["test_run_summary"]["duration_hours"]:.2f} hours
- **Total Tests**: {report["test_run_summary"]["total_tests"]}
- **Success Rate**: {report["test_run_summary"]["overall_success_rate"]:.1f}%
- **Model**: {report["test_run_summary"]["current_model"]}

## 🎯 Scenario Results

| Complexity | Tests | Success Rate | Avg Time | Validation Approval |
|-----------|-------|--------------|----------|-------------------|
"""

        for scenario in report["scenario_results"]:
            md += f"| {scenario['complexity_level']} | {scenario['executions']} | {scenario['success_rate']:.1f}% | {scenario['avg_time']:.2f}s | {scenario.get('validation_approval_rate', 0):.1f}% |\n"

        md += """
## 🔍 Key Insights

### Validation Patterns
"""

        for level, data in report["insights"]["validation_patterns"].items():
            md += f"- **{level.title()}**: {data['approval_rate']:.1f}% approval rate, {data['success_rate']:.1f}% success rate\n"

        md += """
### Recommendations
"""

        for rec in report["insights"]["recommendations"]:
            md += f"- {rec}\n"

        md += f"""
## 📁 Log Files
- Main Test Log: `main_test.log`
- Workflow Performance: `workflow_performance.log`
- Agent Performance: `agent_performance.log`
- Task Complexity Analysis: `task_complexity.log`
- Error Log: `errors.log`

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        return md


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Long Duration Crew Workflow Test")
    parser.add_argument(
        "duration", type=float, default=4.0, nargs="?", help="Test duration in hours (default: 4.0)"
    )
    args = parser.parse_args()

    tester = LongDurationCrewTester(args.duration)
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
