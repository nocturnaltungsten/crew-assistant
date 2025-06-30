# Workflow Base Classes
# Orchestration engine for multi-agent workflows

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from agents.base import AgentResult, BaseAgent, TaskContext


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
class WorkflowResult:
    """Complete workflow execution result."""
    status: WorkflowStatus
    steps: list[WorkflowStep]
    final_output: str
    total_execution_time: float
    iterations_count: int
    success: bool
    error_message: str | None = None

    def get_step_results(self) -> dict[str, str]:
        """Get results by agent role."""
        return {
            step.agent_role: step.result.content if step.result else ""
            for step in self.steps
        }


class BaseWorkflow(ABC):
    """Abstract base class for workflow orchestration."""

    def __init__(self, agents: dict[str, BaseAgent], max_iterations: int = 3):
        """Initialize workflow with agents."""
        self.agents = agents
        self.max_iterations = max_iterations
        self.execution_history: list[WorkflowResult] = []

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
                        success=True
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
                        error_message="Quality standards not met after maximum iterations"
                    )

                iteration += 1
                print(f"🔄 Iteration {iteration-1} requires revision, continuing...")

            # Max iterations reached
            execution_time = time.time() - start_time
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps=steps,
                final_output="Maximum iterations reached without acceptance",
                total_execution_time=execution_time,
                iterations_count=self.max_iterations,
                success=False,
                error_message=f"Failed to meet quality standards within {self.max_iterations} iterations"
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
                error_message=f"Workflow execution error: {str(e)}"
            )

    def _execute_step(self, step: WorkflowStep, previous_results: list[AgentResult], user_request: str) -> AgentResult:
        """Execute a single workflow step."""
        agent = self.agents.get(step.agent_role)
        if not agent:
            raise ValueError(f"Agent '{step.agent_role}' not found")

        context = self.build_context(step, previous_results)
        context.user_input = user_request

        print(f"🤖 Executing {step.agent_role}...")
        return agent.execute_task(context)

    def _evaluate_workflow(self, steps: list[WorkflowStep], iteration: int) -> WorkflowStatus:
        """Evaluate workflow and determine if it should continue."""
        # Find reviewer step
        reviewer_step = next((step for step in steps if step.agent_role == "Reviewer"), None)

        if not reviewer_step or not reviewer_step.result:
            return WorkflowStatus.FAILED

        review_content = reviewer_step.result.content

        # Parse reviewer decision
        if "**DECISION: ACCEPT**" in review_content:
            return WorkflowStatus.COMPLETED
        elif "**DECISION: NEEDS_REVISION**" in review_content and iteration < self.max_iterations:
            return WorkflowStatus.NEEDS_REVISION
        elif "**DECISION: REJECT**" in review_content:
            return WorkflowStatus.FAILED
        else:
            # Default behavior based on iteration
            return WorkflowStatus.NEEDS_REVISION if iteration < self.max_iterations else WorkflowStatus.FAILED

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
            "success_rate": sum(1 for r in self.execution_history if r.success) / len(self.execution_history) if self.execution_history else 0,
            "average_iterations": sum(r.iterations_count for r in self.execution_history) / len(self.execution_history) if self.execution_history else 0,
            "average_execution_time": sum(r.total_execution_time for r in self.execution_history) / len(self.execution_history) if self.execution_history else 0
        }
