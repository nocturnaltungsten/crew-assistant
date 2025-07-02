# Agent Base Classes
# Adapted from basic-agent project for crew coordination

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..providers import BaseProvider, ChatMessage


from typing import Any
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    result: Any
    error: str | None = None


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
    max_tool_calls: int = 5  # Maximum tool calls per execution
    tool_call_timeout: int = 30  # Timeout per tool call in seconds


@dataclass
class TaskContext:
    """Context passed to agents during task execution."""

    task_description: str
    expected_output: str
    previous_results: list[str] = field(default_factory=list)
    memory_context: str = ""
    user_input: str = ""

    def to_prompt(self) -> str:
        """Convert context to prompt format."""
        prompt_parts = [
            f"Task: {self.task_description}",
            f"Expected Output: {self.expected_output}",
        ]

        if self.user_input:
            prompt_parts.insert(0, f"User Request: {self.user_input}")

        if self.previous_results:
            prompt_parts.append("Previous Results:")
            for i, result in enumerate(self.previous_results):
                prompt_parts.append(f"{i + 1}. {result}")

        if self.memory_context:
            prompt_parts.append(f"Memory Context: {self.memory_context}")

        return "\n\n".join(prompt_parts)


@dataclass
class AgentResult:
    """Result from agent execution."""

    content: str
    agent_role: str
    execution_time: float
    tokens_used: int | None = None
    success: bool = True
    error_message: str | None = None
    tool_calls_executed: list["ToolResult"] = field(default_factory=list)
    tool_call_count: int = 0

    def __str__(self) -> str:
        return self.content


class BaseAgent(ABC):
    """Abstract base class for crew agents."""

    def __init__(self, provider: BaseProvider, model: str, config: AgentConfig):
        """Initialize agent with provider and configuration."""
        self.provider = provider
        self.model = model
        self.config = config
        self.execution_count = 0

        # Memory manager (if basic-agent compatible)
        self.memory = None  # Will implement if needed

        # Tool system (imported here to avoid circular imports)
        self._tool_registry = None
        self._tool_parser = None

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    @property
    def tool_registry(self):
        """Get tool registry, initializing if needed."""
        if self._tool_registry is None:
            from .tools import default_registry

            self._tool_registry = default_registry
        return self._tool_registry

    @property
    def tool_parser(self):
        """Get tool parser, initializing if needed."""
        if self._tool_parser is None:
            from .tool_parser import ToolCallParser

            self._tool_parser = ToolCallParser(self.tool_registry)
        return self._tool_parser

    def get_tool_definitions_prompt(self) -> str:
        """Get comprehensive tool usage instructions."""
        if not self.config.tools_enabled:
            return ""

        tools = self.tool_registry.get_tool_definitions()
        if not tools:
            return ""

        prompt_parts = [
            "\n" + "=" * 60,
            "TOOL SYSTEM ARCHITECTURE",
            "=" * 60,
            "",
            "## 🎯 CORE PRINCIPLE",
            "You are an ACTION-ORIENTED AI assistant with FILE OPERATION capabilities.",
            "When users ask you to CREATE, SAVE, or WRITE files - DO IT IMMEDIATELY with tools.",
            "When users ask for information or explanations - respond normally.",
            "",
            "## 🧠 DECISION FRAMEWORK",
            "",
            "### When to USE tools (output JSON IMMEDIATELY):",
            "✅ User asks to create/make ANY script, file, or code",
            "✅ User wants to save/write content to disk",
            "✅ User mentions creating something that should be a file",
            "✅ User asks 'create a [anything]' - assume they want a file",
            "✅ User asks to read/open/view a specific file",
            "✅ User asks to list directory contents",
            "✅ Follow-up requests after showing code (assume they want it saved)",
            "",
            "### When to RESPOND normally (no tools):",
            "❌ User asks for information, explanations, advice",
            "❌ User asks 'how to' questions",
            "❌ User wants code examples or snippets",
            "❌ User asks about concepts, tutorials",
            "❌ General conversation and questions",
            "",
            "## 🔧 AVAILABLE TOOLS",
            "",
        ]

        # Add tool descriptions
        for tool in tools:
            tool_desc = [f"### {tool.name.upper()}", f"Purpose: {tool.description}", "Parameters:"]

            for param in tool.parameters:
                required_str = "REQUIRED" if param.required else "optional"
                default_str = (
                    f" (default: {param.default})" if not param.required and param.default else ""
                )
                tool_desc.append(
                    f"  • {param.name} ({param.type}) - {required_str}: {param.description}{default_str}"
                )

            prompt_parts.extend(tool_desc)
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "## 📋 TOOL USAGE PROTOCOL",
                "",
                "### Step 1: Classify the Request",
                "- Is this a FILE OPERATION? → Use tool",
                "- Is this a CONVERSATION? → Normal response",
                "",
                "### Step 2: If Using Tool, Format Response",
                "```json",
                '{"tool_name": "exact_tool_name", "parameters": {"param": "value"}}',
                "```",
                "",
                "### Step 3: Add Brief Confirmation",
                "Example: 'File created.' or 'Reading file...'",
                "",
                "## 🎭 BEHAVIORAL EXAMPLES",
                "",
                "### FILE OPERATIONS (Use Tools)",
                "",
                "User: 'Create a python script that prints hello world'",
                "Response:",
                "```json",
                '{"tool_name": "write_file", "parameters": {"file_path": "hello_world.py", "content": "print(\\"hello world\\")"}}',
                "```",
                "Created hello_world.py with the requested script.",
                "",
                "User: 'Create a more sophisticated script that does whatever you want'",
                "Response:",
                "```json",
                '{"tool_name": "write_file", "parameters": {"file_path": "weather_app.py", "content": "import random\\n\\ndef get_weather():\\n    weather = [\\"sunny\\", \\"cloudy\\", \\"rainy\\"]\\n    return random.choice(weather)\\n\\nprint(f\\"Today is {get_weather()}!\\")"}}}',
                "```",
                "Created weather_app.py - a simple weather simulator.",
                "",
                "User: 'What's in my config file?'",
                "Response:",
                "```json",
                '{"tool_name": "read_file", "parameters": {"file_path": "config.txt"}}',
                "```",
                "",
                "### NORMAL CONVERSATIONS (No Tools)",
                "",
                "User: 'How do I write a Python script?'",
                "Response: To write a Python script, create a .py file and use Python syntax...",
                "",
                "User: 'What's the syntax for print in Python?'",
                "Response: In Python, use print() function: print('hello world')",
                "",
                "User: 'Explain file operations'",
                "Response: File operations include reading, writing, creating files...",
                "",
                "## ⚠️ CRITICAL RULES",
                "",
                "1. **NEVER** use tools for explanations or code examples",
                "2. **ALWAYS** use tools for actual file create/read/write operations",
                "3. **ADAPT** parameters to the user's specific request",
                "4. **VALIDATE** that your chosen tool matches the user's intent",
                "5. **RESPOND** naturally for non-file-operation requests",
                "",
                "## 🚫 COMMON MISTAKES TO AVOID",
                "",
                "❌ Using write_file when user wants to see code",
                "❌ Using read_file when user asks how to read files",
                "❌ Adding invalid parameters to tools",
                "❌ Using tools for general questions about programming",
                "❌ Copying example values literally without adapting",
                "",
                "=" * 60,
                "",
            ]
        )

        return "\n".join(prompt_parts)

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed for this agent."""
        if not self.config.tools_enabled:
            return False

        # If no allowed_tools specified, all tools are allowed
        if not self.config.allowed_tools:
            return True

        return tool_name in self.config.allowed_tools

    def execute_tool_calls(self, response_text: str) -> list["ToolResult"]:
        """Parse and execute tool calls from LLM response."""
        if not self.config.tools_enabled:
            return []

        # Parse tool calls from response
        parse_result = self.tool_parser.parse(response_text)

        if self.config.verbose:
            if parse_result.tool_calls:
                print(f"🔍 Parser found {len(parse_result.tool_calls)} tool call(s)")
                for i, call in enumerate(parse_result.tool_calls):
                    print(f"  Call {i + 1}: {call.tool_name} with params {call.parameters}")
                    print(f"    Raw text: {call.raw_text[:100]}...")
                    print(f"    Confidence: {call.confidence:.2f}")
            else:
                print("🔍 Parser found no tool calls in response")
                print(f"    Response preview: {response_text[:200]}...")

            if parse_result.parse_errors:
                print(f"⚠️ Tool parsing issues: {parse_result.parse_errors}")

        # Execute tool calls
        tool_results = []
        for i, tool_call in enumerate(parse_result.tool_calls):
            if i >= self.config.max_tool_calls:
                if self.config.verbose:
                    print(f"⚠️ Maximum tool calls ({self.config.max_tool_calls}) reached")
                break

            # Check if tool is allowed
            if not self.is_tool_allowed(tool_call.tool_name):
                from .tools import ToolCallStatus, ToolResult

                result = ToolResult(
                    status=ToolCallStatus.ERROR,
                    error_message=f"Tool '{tool_call.tool_name}' is not allowed for this agent",
                )
                tool_results.append(result)
                continue

            # Execute tool
            if self.config.verbose:
                print(f"🔧 Executing tool: {tool_call.tool_name}")

            result = self.tool_registry.execute_tool(tool_call)
            tool_results.append(result)

            if self.config.verbose:
                if result.success:
                    print(f"✅ Tool {tool_call.tool_name} succeeded")
                else:
                    print(f"❌ Tool {tool_call.tool_name} failed: {result.error_message}")

        return tool_results

    def execute_task(self, context: TaskContext) -> AgentResult:
        """Execute a task with given context, including tool calling."""
        import time

        start_time = time.time()
        all_tool_results = []

        try:
            # Build messages
            messages = []

            # Add system prompt with tool definitions
            system_prompt = self.get_system_prompt()
            if self.config.tools_enabled:
                tool_prompt = self.get_tool_definitions_prompt()
                system_prompt += tool_prompt

            messages.append(ChatMessage(role="system", content=system_prompt))

            # Add task context as user message
            task_prompt = context.to_prompt()
            messages.append(ChatMessage(role="user", content=task_prompt))

            # Execute via provider
            response = self.provider.chat(
                messages=messages,
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Check for and execute tool calls
            tool_results = self.execute_tool_calls(response.content)
            all_tool_results.extend(tool_results)

            # If tools were executed, prepare final response
            final_content = response.content
            if tool_results:
                # Add tool results to the response
                tool_summary = "\n\n## Tool Execution Results:\n"
                for i, result in enumerate(tool_results, 1):
                    tool_summary += f"{i}. {result.to_llm_message()}\n"

                final_content += tool_summary

            execution_time = time.time() - start_time
            self.execution_count += 1

            if self.config.verbose:
                tool_count = len(all_tool_results)
                print(
                    f"🤖 {self.config.role} completed task in {execution_time:.2f}s (tools: {tool_count})"
                )

            return AgentResult(
                content=final_content,
                agent_role=self.config.role,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                success=True,
                tool_calls_executed=all_tool_results,
                tool_call_count=len(all_tool_results),
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
                error_message=error_msg,
                tool_calls_executed=all_tool_results,
                tool_call_count=len(all_tool_results),
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
            "provider": self.provider.name,
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
