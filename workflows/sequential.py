# Sequential Workflow Implementation
# Research → Plan → Develop → Review workflow with feedback loops


from agents.base import AgentResult, BaseAgent

from .base import BaseWorkflow, TaskContext, WorkflowStep


class SequentialWorkflow(BaseWorkflow):
    """Sequential workflow: Researcher → Planner → Developer → Reviewer with quality gates."""

    def __init__(self, agents: dict[str, BaseAgent], **kwargs):
        """Initialize sequential workflow."""
        required_agents = {"Researcher", "Planner", "Developer", "Reviewer"}
        available_agents = set(agents.keys())

        if not required_agents.issubset(available_agents):
            missing = required_agents - available_agents
            raise ValueError(f"Missing required agents: {missing}")

        super().__init__(agents, **kwargs)

    def define_steps(self, user_request: str) -> list[WorkflowStep]:
        """Define the sequential workflow steps."""
        return [
            WorkflowStep(
                agent_role="Researcher",
                task_description=f"Research and analyze the requirements for: {user_request}",
                expected_output="Comprehensive research report with technical requirements, best practices, and recommendations"
            ),
            WorkflowStep(
                agent_role="Planner",
                task_description="Create detailed implementation plan based on research findings",
                expected_output="Step-by-step implementation plan with clear tasks and dependencies"
            ),
            WorkflowStep(
                agent_role="Developer",
                task_description="Implement the solution according to the research and plan",
                expected_output="Complete working implementation with code, documentation, and usage instructions"
            ),
            WorkflowStep(
                agent_role="Reviewer",
                task_description="Review and validate the complete deliverable against requirements",
                expected_output="Quality assessment with ACCEPT/NEEDS_REVISION/REJECT decision and specific feedback"
            )
        ]

    def build_context(self, step: WorkflowStep, previous_results: list[AgentResult]) -> TaskContext:
        """Build context for each agent based on previous results."""
        context = TaskContext(
            task_description=step.task_description,
            expected_output=step.expected_output,
            previous_results=[result.content for result in previous_results if result.success]
        )

        # Add role-specific context
        if step.agent_role == "Researcher":
            # Researcher gets the raw user request
            pass

        elif step.agent_role == "Planner":
            # Planner gets research findings
            if previous_results:
                research_result = previous_results[0]  # Researcher is first
                context.task_description = f"""Create a detailed implementation plan based on this research:

RESEARCH FINDINGS:
{research_result.content}

PLANNING TASK:
{step.task_description}

Provide a clear, actionable plan that the development team can follow."""

        elif step.agent_role == "Developer":
            # Developer gets both research and plan
            if len(previous_results) >= 2:
                research_result = previous_results[0]
                plan_result = previous_results[1]
                context.task_description = f"""Implement the solution based on this research and plan:

RESEARCH FINDINGS:
{research_result.content}

IMPLEMENTATION PLAN:
{plan_result.content}

DEVELOPMENT TASK:
{step.task_description}

Create a complete, working implementation that follows the research recommendations and plan."""

        elif step.agent_role == "Reviewer":
            # Reviewer gets everything for validation
            if len(previous_results) >= 3:
                research_result = previous_results[0]
                plan_result = previous_results[1]
                dev_result = previous_results[2]

                context.task_description = f"""Review and validate this complete deliverable:

ORIGINAL REQUIREMENTS:
{context.user_input}

RESEARCH FINDINGS:
{research_result.content}

IMPLEMENTATION PLAN:
{plan_result.content}

DEVELOPER DELIVERABLE:
{dev_result.content}

REVIEW TASK:
{step.task_description}

Evaluate against requirements and make ACCEPT/NEEDS_REVISION/REJECT decision."""

        return context

    def _compile_final_output(self, steps: list[WorkflowStep]) -> str:
        """Compile final output focusing on the accepted deliverable."""
        # Find the final reviewer decision
        reviewer_step = next((step for step in reversed(steps) if step.agent_role == "Reviewer"), None)

        if reviewer_step and reviewer_step.result and "**DECISION: ACCEPT**" in reviewer_step.result.content:
            # Get the developer output that was accepted
            dev_step = next((step for step in reversed(steps) if step.agent_role == "Developer"), None)

            if dev_step and dev_step.result:
                return f"""# ✅ Completed Project Deliverable

{dev_step.result.content}

---

## 🔍 Quality Review Summary
{reviewer_step.result.content}

---
*Generated by enhanced 4-agent crew workflow*
*Research → Plan → Develop → Review with quality gates*"""

        # Fallback to standard compilation
        return super()._compile_final_output(steps)
