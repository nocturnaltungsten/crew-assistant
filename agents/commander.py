# Commander Agent Implementation
# Executive agent for review and evaluation

from typing import Any, Dict

from providers.base import BaseProvider, ChatMessage, ChatResponse

from .base import AgentConfig, AgentResult, BaseAgent, TaskContext


class CommanderAgent(BaseAgent):
    """Executive agent responsible for review, evaluation, and next steps."""

    def __init__(self, provider: BaseProvider, model: str, config: AgentConfig | None = None, **kwargs):
        """Initialize CommanderAgent with default configuration."""
        if config is None:
            config = AgentConfig(
                role="Commander",
                goal="Oversee the agent system and ensure proper planning and execution.",
                backstory="A seasoned systems architect who ensures agents work in harmony and quality standards are met.",
                max_tokens=1500,
                temperature=0.3,
                verbose=True
            )
        super().__init__(provider, model, config)

    def get_system_prompt(self) -> str:
        """Get the system prompt for the Commander agent."""
        return f"""You are the {self.config.role}, a senior executive agent in a multi-agent system.

Role: {self.config.role}
Goal: {self.config.goal}
Backstory: {self.config.backstory}

Your responsibilities:
1. Review work from other agents (Planner, Developer)
2. Evaluate quality and completeness
3. Provide constructive feedback and recommendations
4. Determine if work meets acceptance criteria
5. Suggest next steps and improvements

When reviewing work, structure your response as:

## Review Summary
[Brief overview of what was reviewed]

## Quality Assessment
[Evaluation of the work quality, completeness, and alignment with requirements]

## Feedback
[Specific, actionable feedback]

## Decision
**DECISION: [ACCEPT/NEEDS_REVISION/REJECT]**

## Next Steps
[Recommended actions and improvements]

Be thorough but constructive. Focus on helping the team deliver high-quality results."""

    def execute_task(self, context: TaskContext) -> AgentResult:
        """Execute a commander task with review and evaluation."""
        import time
        start_time = time.time()

        try:
            # Build the full prompt
            system_prompt = self.get_system_prompt()
            task_prompt = context.to_prompt()

            full_prompt = f"{system_prompt}\n\n{task_prompt}"

            # Create messages
            messages = [ChatMessage(role="user", content=full_prompt)]

            # Execute with provider
            response = self.provider.chat_with_retry(
                messages=messages,
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            execution_time = time.time() - start_time
            self.execution_count += 1

            return AgentResult(
                content=response.content,
                agent_role=self.config.role,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Commander execution failed: {str(e)}"
            
            return AgentResult(
                content=error_message,
                agent_role=self.config.role,
                execution_time=execution_time,
                success=False,
                error_message=error_message
            )


# For backward compatibility with old imports
def create_commander_agent(provider: BaseProvider, model: str) -> CommanderAgent:
    """Factory function to create a CommanderAgent instance."""
    return CommanderAgent(provider, model)