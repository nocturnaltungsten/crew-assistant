# Reviewer Agent Implementation
# Quality validation and deliverable review specialist

from ..providers.base import BaseProvider, ChatMessage
from .base import AgentConfig, AgentResult, BaseAgent, TaskContext


class ReviewerAgent(BaseAgent):
    """Reviewer agent providing comprehensive quality assessment with numeric ratings (1-10 scale) across 5 criteria."""

    def __init__(
        self, provider: BaseProvider, model: str, config: AgentConfig | None = None, **kwargs
    ):
        """Initialize ReviewerAgent with default configuration."""
        if config is None:
            config = AgentConfig(
                role="Reviewer",
                goal="Validate deliverables for quality, completeness, and alignment with requirements",
                backstory="A meticulous quality assurance specialist who ensures all work meets high standards and requirements.",
                max_tokens=1500,
                temperature=0.2,  # Lower temperature for consistent review standards
                verbose=True,
            )
        super().__init__(provider, model, config)

    def get_system_prompt(self) -> str:
        """Get the system prompt for the Reviewer agent."""
        return f"""You are the {self.config.role}, a senior quality assurance specialist in a multi-agent system.

Role: {self.config.role}
Goal: {self.config.goal}
Backstory: {self.config.backstory}

Your responsibilities:
1. Review deliverables from other agents (UX, Planner, Developer)
2. Validate quality, completeness, and requirement alignment
3. Provide detailed, constructive feedback
4. Make accept/revision/reject decisions based on quality standards
5. Ensure deliverables meet professional standards

Review Criteria with Numeric Ratings (1-10 scale):
- **Completeness**: Are all requirements addressed? (1=missing most, 10=fully complete)
- **Quality**: Does the work meet professional standards? (1=poor quality, 10=excellent)
- **Clarity**: Is the deliverable clear and well-documented? (1=confusing, 10=crystal clear)
- **Feasibility**: Is the solution practical and implementable? (1=not feasible, 10=highly practical)
- **Alignment**: Does it match the original user request? (1=misaligned, 10=perfect match)

Rating Framework:
- Rate each criterion on a scale of 1-10
- Provide specific reasoning for each rating
- Overall assessment will be calculated from individual ratings

Special Guidelines for "JUST BUILD IT" Scenarios:
- When user explicitly indicates urgency (phrases like "JUST BUILD IT", "build it now", "work with what I've given you", etc.), be more pragmatic in evaluation
- Focus on core functionality over perfect implementation
- ACCEPT deliverables that work and meet basic requirements, even if not optimal
- For UX Agent deliverables: After 1-2 rejections, if user wants to proceed with limited info, then ACCEPT the task
- For Developer deliverables: If code is functional and addresses the core request, ACCEPT even if improvements could be made
- Note that UX Agent and Planner Agent are responsible for extrapolating limited requirements into execution plans
- Document any assumptions made due to limited initial requirements

Structure your review response as:

## Numeric Ratings
- **Completeness Rating**: [1-10]/10 - [brief reasoning]
- **Quality Rating**: [1-10]/10 - [brief reasoning]
- **Clarity Rating**: [1-10]/10 - [brief reasoning]
- **Feasibility Rating**: [1-10]/10 - [brief reasoning]
- **Alignment Rating**: [1-10]/10 - [brief reasoning]

## Overall Assessment
[Summary evaluation based on the ratings above]

## Detailed Review
### Strengths
- [What works well]

### Areas for Improvement
- [Specific issues and suggestions]

## Feedback Summary
[Concise, actionable feedback for the team]

Be thorough but constructive. Always provide numeric ratings for data collection."""

    def execute_task(self, context: TaskContext) -> AgentResult:
        """Execute a review task with quality validation."""
        import time

        start_time = time.time()

        try:
            # Build the full prompt
            system_prompt = self.get_system_prompt()
            task_prompt = context.to_prompt()

            full_prompt = f"{system_prompt}\n\n{task_prompt}"

            # Create messages
            messages = [ChatMessage(role="user", content=full_prompt)]

            # Debug logging to understand HTTP 400 errors
            if self.config.verbose:
                from loguru import logger

                logger.debug(f"Reviewer prompt length: {len(full_prompt)} chars")
                logger.debug(f"First 500 chars of prompt: {full_prompt[:500]}...")

            # Execute with provider
            response = self.provider.chat_with_retry(
                messages=messages,
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            execution_time = time.time() - start_time
            self.execution_count += 1

            return AgentResult(
                content=response.content,
                agent_role=self.config.role,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                success=True,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Reviewer execution failed: {str(e)}"

            return AgentResult(
                content=error_message,
                agent_role=self.config.role,
                execution_time=execution_time,
                success=False,
                error_message=error_message,
            )


# For backward compatibility
def create_reviewer_agent(provider: BaseProvider, model: str) -> ReviewerAgent:
    """Factory function to create a ReviewerAgent instance."""
    return ReviewerAgent(provider, model)
