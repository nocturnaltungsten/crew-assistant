# Agent Base Classes
# Adapted from basic-agent project for crew coordination

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from providers import BaseProvider, ChatMessage


@dataclass
class AgentConfig:
    """Configuration for crew agents."""

    # Agent identity
    role: str
    goal: str
    backstory: str

    # Behavior settings
    max_execution_time: int = 300  # seconds
    max_tokens: int = 1000
    temperature: float = 0.7
    verbose: bool = True

    # Memory settings
    memory_enabled: bool = True
    memory_context_limit: int = 5

    # Tool settings
    tools_enabled: bool = True
    allowed_tools: list[str] = field(default_factory=list)


@dataclass
class TaskDelegationData:
    """Task delegation information for adaptive workflows."""
    
    complexity_assessment: int  # 1-10 scale
    delegation_instructions: str
    expected_subtasks: list[str] = field(default_factory=list)
    context_target_range: tuple[int, int] = (1000, 4000)  # (min_tokens, max_tokens)
    expected_cycles: int = 1  # Predicted execution cycles
    priority_level: str = "standard"  # "fast", "standard", "capable"


@dataclass
class TaskContext:
    """Context passed to agents during task execution."""

    task_description: str
    expected_output: str
    previous_results: list[str] = field(default_factory=list)
    memory_context: str = ""
    user_input: str = ""
    
    # NEW: Optional delegation data for adaptive workflows (BACKWARD COMPATIBLE)
    delegation_data: Optional[TaskDelegationData] = None

    def to_prompt(self) -> str:
        """
        Convert context to prompt format.
        BACKWARD COMPATIBLE: Existing behavior preserved when delegation_data is None.
        """
        prompt_parts = [
            f"Task: {self.task_description}",
            f"Expected Output: {self.expected_output}"
        ]

        if self.user_input:
            prompt_parts.insert(0, f"User Request: {self.user_input}")

        if self.previous_results:
            prompt_parts.append("Previous Results:")
            for i, result in enumerate(self.previous_results):
                prompt_parts.append(f"{i+1}. {result}")

        if self.memory_context:
            prompt_parts.append(f"Memory Context: {self.memory_context}")

        # NEW: Add delegation context for adaptive workflows
        if self.delegation_data:
            prompt_parts.append(self._format_delegation_context())

        return "\n\n".join(prompt_parts)
    
    def _format_delegation_context(self) -> str:
        """
        NEW: Format delegation data for prompt inclusion.
        Part of unified prompt engine foundation.
        """
        if not self.delegation_data:
            return ""
        
        delegation_parts = [
            "Delegation Context:",
            f"  Complexity Level: {self.delegation_data.complexity_assessment}/10",
            f"  Instructions: {self.delegation_data.delegation_instructions}",
            f"  Expected Cycles: {self.delegation_data.expected_cycles}",
            f"  Context Target: {self.delegation_data.context_target_range[0]}-{self.delegation_data.context_target_range[1]} tokens",
            f"  Performance Tier: {self.delegation_data.priority_level}"
        ]
        
        if self.delegation_data.expected_subtasks:
            delegation_parts.append("  Expected Subtasks:")
            for i, subtask in enumerate(self.delegation_data.expected_subtasks):
                delegation_parts.append(f"    {i+1}. {subtask}")
        
        return "\n".join(delegation_parts)


@dataclass
class AgentResult:
    """Result from agent execution."""

    content: str
    agent_role: str
    execution_time: float
    tokens_used: int | None = None
    success: bool = True
    error_message: str | None = None

    def __str__(self) -> str:
        return self.content


class BaseAgent(ABC):
    """Abstract base class for crew agents."""

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        config: AgentConfig
    ):
        """Initialize agent with provider and configuration."""
        self.provider = provider
        self.model = model
        self.config = config
        self.execution_count = 0

        # Memory manager (if basic-agent compatible)
        self.memory = None  # Will implement if needed

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def execute_task(self, context: TaskContext) -> AgentResult:
        """Execute a task with given context."""
        import time
        start_time = time.time()

        try:
            # Build messages
            messages = []

            # Add system prompt
            system_prompt = self.get_system_prompt()
            messages.append(ChatMessage(role="system", content=system_prompt))

            # Add task context as user message
            task_prompt = context.to_prompt()
            messages.append(ChatMessage(role="user", content=task_prompt))

            # Execute via provider
            response = self.provider.chat(
                messages=messages,
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            execution_time = time.time() - start_time
            self.execution_count += 1

            if self.config.verbose:
                print(f"🤖 {self.config.role} completed task in {execution_time:.2f}s")

            return AgentResult(
                content=response.content,
                agent_role=self.config.role,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent {self.config.role} failed: {str(e)}"

            if self.config.verbose:
                print(f"❌ {error_msg}")

            return AgentResult(
                content="",
                agent_role=self.config.role,
                execution_time=execution_time,
                success=False,
                error_message=error_msg
            )

    @property
    def role(self) -> str:
        """Get agent role."""
        return self.config.role

    @property
    def stats(self) -> dict[str, Any]:
        """Get agent execution statistics."""
        return {
            "role": self.config.role,
            "executions": self.execution_count,
            "model": self.model,
            "provider": self.provider.name
        }


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class TaskExecutionError(AgentError):
    """Raised when task execution fails."""
    pass


class ConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass
