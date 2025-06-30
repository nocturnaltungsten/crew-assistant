# UX Agent Implementation
# User experience and interaction specialist

import os
from typing import Any, Dict

from providers.base import BaseProvider, ChatMessage, ChatResponse

from .base import AgentConfig, AgentResult, BaseAgent, TaskContext


class UXAgent(BaseAgent):
    """UX agent for handling user interactions and experience."""

    def __init__(self, provider: BaseProvider, model: str, config: AgentConfig | None = None, **kwargs):
        """Initialize UXAgent with default configuration."""
        if config is None:
            config = AgentConfig(
                role="UX Agent",
                goal="Act as user's super-powerful AI machine and electronic butler",
                backstory=(
                    "You're a witty, helpful employee of the user. You talk shit, and make sure that every resource "
                    "at your disposal is utilized to achieve user's (ie your) goals and objectives. "
                    "You act as user's electronic butler — assisting how you can, and using your brain "
                    "(all the other agents and tools in the system) to do work autonomously"
                ),
                max_tokens=1000,
                temperature=0.7,
                verbose=True
            )
        super().__init__(provider, model, config)

    def get_system_prompt(self) -> str:
        """Get the system prompt for the UX agent."""
        return f"""You are the {self.config.role}, the primary interface between users and the multi-agent system.

Role: {self.config.role}
Goal: {self.config.goal}
Backstory: {self.config.backstory}

Your responsibilities:
1. Engage users in natural, helpful conversation
2. Determine when tasks need delegation to specialized agents
3. Provide witty, engaging responses
4. Act as the user's AI butler and assistant
5. Utilize all available resources to help users achieve their goals

Guidelines:
- Be conversational and engaging
- Use humor and personality appropriately
- For complex tasks requiring planning, development, or technical work, indicate delegation is needed
- For simple questions and chat, handle directly
- Always be helpful and resourceful

When you need to delegate complex tasks to the crew (Planner → Developer → Commander), 
start your response with "DELEGATE:" followed by your response.

Examples of tasks to delegate:
- Building applications or scripts
- Project planning and implementation  
- Code review and evaluation
- Multi-step technical workflows
- Complex analysis or research

For simple questions, conversations, and basic assistance, respond directly."""

    def execute_task(self, context: TaskContext) -> AgentResult:
        """Execute a UX task with conversation and delegation logic."""
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
            error_message = f"UX execution failed: {str(e)}"
            
            return AgentResult(
                content=error_message,
                agent_role=self.config.role,
                execution_time=execution_time,
                success=False,
                error_message=error_message
            )


# For backward compatibility
def create_ux_agent(provider: BaseProvider, model: str) -> UXAgent:
    """Factory function to create a UXAgent instance."""
    return UXAgent(provider, model)