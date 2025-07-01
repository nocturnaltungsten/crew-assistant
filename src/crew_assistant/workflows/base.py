# Workflow Base Classes
# Orchestration engine for multi-agent workflows

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..agents.base import AgentResult, BaseAgent, TaskContext


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    NEEDS_CLARIFICATION = "needs_clarification"


class ReviewDecision(Enum):
    """Review decision types."""

    ACCEPT = "ACCEPT"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECT = "REJECT"


@dataclass
class WorkflowStep:
    """Individual step in workflow execution."""

    agent_role: str
    task_description: str
    expected_output: str
    result: AgentResult | None = None
    iteration: int = 1
    max_iterations: int = 3


@dataclass
class ValidationResult:
    """Result of task specification validation."""

    approved: bool
    feedback: str
    suggestions: list[str] | None = None


@dataclass
class ReviewRatings:
    """Numeric ratings from reviewer evaluation."""

    completeness: int = 0
    quality: int = 0
    clarity: int = 0
    feasibility: int = 0
    alignment: int = 0

    @property
    def average_rating(self) -> float:
        """Calculate average rating across all criteria."""
        ratings = [self.completeness, self.quality, self.clarity, self.feasibility, self.alignment]
        valid_ratings = [r for r in ratings if r > 0]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0.0


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""

    status: WorkflowStatus
    steps: list[WorkflowStep]
    final_output: str
    total_execution_time: float
    iterations_count: int
    success: bool
    error_message: str | None = None
    review_ratings: ReviewRatings | None = None

    def get_step_results(self) -> dict[str, str]:
        """Get results by agent role."""
        return {step.agent_role: step.result.content if step.result else "" for step in self.steps}


class BaseWorkflow(ABC):
    """Abstract base class for workflow orchestration."""

    def __init__(self, agents: dict[str, BaseAgent], max_iterations: int = 3):
        """Initialize workflow with agents."""
        self.agents = agents
        self.max_iterations = max_iterations
        self.execution_history: list[WorkflowResult] = []
        self._reviewer_failure_count = 0  # Track reviewer failures across iterations
        self._current_ratings: ReviewRatings | None = None  # Store ratings from current iteration

    @abstractmethod
    def define_steps(self, user_request: str) -> list[WorkflowStep]:
        """Define workflow steps for the given request."""
        pass

    @abstractmethod
    def build_context(self, step: WorkflowStep, previous_results: list[AgentResult]) -> TaskContext:
        """Build context for agent execution."""
        pass

    def execute(self, user_request: str) -> WorkflowResult:
        """Execute the complete workflow with feedback loops."""
        start_time = time.time()

        try:
            steps = self.define_steps(user_request)
            iteration = 1

            while iteration <= self.max_iterations:
                print(f"🔄 Workflow iteration {iteration}")

                # Execute all steps
                step_results = []
                for step in steps:
                    result = self._execute_step(step, step_results, user_request)
                    step.result = result
                    step.iteration = iteration
                    step_results.append(result)

                # Check if workflow should continue or terminate
                decision = self._evaluate_workflow(steps, iteration)

                if decision == WorkflowStatus.COMPLETED:
                    execution_time = time.time() - start_time
                    return WorkflowResult(
                        status=WorkflowStatus.COMPLETED,
                        steps=steps,
                        final_output=self._compile_final_output(steps),
                        total_execution_time=execution_time,
                        iterations_count=iteration,
                        success=True,
                        review_ratings=self._current_ratings,
                    )
                elif decision == WorkflowStatus.FAILED:
                    execution_time = time.time() - start_time
                    return WorkflowResult(
                        status=WorkflowStatus.FAILED,
                        steps=steps,
                        final_output="Workflow failed after multiple iterations",
                        total_execution_time=execution_time,
                        iterations_count=iteration,
                        success=False,
                        error_message="Quality standards not met after maximum iterations",
                    )

                iteration += 1
                print(f"🔄 Iteration {iteration - 1} requires revision, continuing...")

            # Max iterations reached
            execution_time = time.time() - start_time
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps=steps,
                final_output="Maximum iterations reached without acceptance",
                total_execution_time=execution_time,
                iterations_count=self.max_iterations,
                success=False,
                error_message=f"Failed to meet quality standards within {self.max_iterations} iterations",
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps=[],
                final_output="",
                total_execution_time=execution_time,
                iterations_count=1,
                success=False,
                error_message=f"Workflow execution error: {str(e)}",
            )

    def _execute_step(
        self, step: WorkflowStep, previous_results: list[AgentResult], user_request: str
    ) -> AgentResult:
        """Execute a single workflow step."""
        agent = self.agents.get(step.agent_role)
        if not agent:
            raise ValueError(f"Agent '{step.agent_role}' not found")

        context = self.build_context(step, previous_results)
        context.user_input = user_request

        print(f"🤖 Executing {step.agent_role}...")
        result = agent.execute_task(context)

        # With numeric ratings system, reviewer failures don't block workflow
        # Just return the actual result (success or failure) for analytics
        return result

    def _evaluate_workflow(self, steps: list[WorkflowStep], iteration: int) -> WorkflowStatus:
        """Evaluate workflow and collect quality ratings. Always returns COMPLETED for non-blocking execution."""
        # Find reviewer step
        reviewer_step = next((step for step in steps if step.agent_role == "Reviewer"), None)

        if reviewer_step and reviewer_step.result and reviewer_step.result.success:
            # Parse numeric ratings from reviewer output
            ratings = self._parse_numeric_ratings(reviewer_step.result.content)
            self._current_ratings = ratings
        else:
            # Reviewer failed or missing - create empty ratings for consistency
            self._current_ratings = ReviewRatings()
            if reviewer_step:
                print("⚠️ Reviewer failed - proceeding without quality ratings")

        # With numeric ratings system, workflow always proceeds to completion
        # Ratings are for analytics and feedback, not blocking execution
        return WorkflowStatus.COMPLETED

    def _parse_numeric_ratings(self, review_content: str) -> ReviewRatings:
        """Parse numeric ratings (1-10 scale) from reviewer output using regex patterns."""
        import re

        ratings = ReviewRatings()

        # Pattern to match "**Rating Name**: X/10" format
        rating_patterns = {
            "completeness": r"\*\*Completeness Rating\*\*:\s*(\d+)/10",
            "quality": r"\*\*Quality Rating\*\*:\s*(\d+)/10",
            "clarity": r"\*\*Clarity Rating\*\*:\s*(\d+)/10",
            "feasibility": r"\*\*Feasibility Rating\*\*:\s*(\d+)/10",
            "alignment": r"\*\*Alignment Rating\*\*:\s*(\d+)/10",
        }

        for field_name, pattern in rating_patterns.items():
            match = re.search(pattern, review_content, re.IGNORECASE)
            if match:
                try:
                    rating_value = int(match.group(1))
                    # Validate rating is in 1-10 range
                    if 1 <= rating_value <= 10:
                        setattr(ratings, field_name, rating_value)
                except (ValueError, IndexError):
                    pass  # Keep default value of 0 for invalid ratings

        return ratings

    def _compile_final_output(self, steps: list[WorkflowStep]) -> str:
        """Compile final output from all workflow steps."""
        output_parts = []

        for step in steps:
            if step.result and step.result.success:
                output_parts.append(f"## {step.agent_role} Output\n{step.result.content}\n")

        return "\n".join(output_parts)

    @property
    def stats(self) -> dict[str, Any]:
        """Get workflow execution statistics."""
        return {
            "total_executions": len(self.execution_history),
            "success_rate": sum(1 for r in self.execution_history if r.success)
            / len(self.execution_history)
            if self.execution_history
            else 0,
            "average_iterations": sum(r.iterations_count for r in self.execution_history)
            / len(self.execution_history)
            if self.execution_history
            else 0,
            "average_execution_time": sum(r.total_execution_time for r in self.execution_history)
            / len(self.execution_history)
            if self.execution_history
            else 0,
        }
