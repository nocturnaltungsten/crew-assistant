# Tool System for Agent Capabilities
# Foundational classes for tool calling and execution

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolCallStatus(Enum):
    """Status of tool call execution."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # For when tool call was partially successful
    SKIPPED = "skipped"  # For when tool call was skipped due to safety/validation


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str  # 'string', 'number', 'boolean', 'array', 'object'
    description: str
    required: bool = True
    default: Any = None
    enum_values: list[str] | None = None  # For restricted string values


@dataclass
class ToolDefinition:
    """Complete definition of a tool for LLM consumption."""

    name: str
    description: str
    parameters: list[ToolParameter]

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop_def = {"type": param.type, "description": param.description}

            if param.enum_values:
                prop_def["enum"] = param.enum_values

            properties[param.name] = prop_def

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": properties, "required": required},
            },
        }


@dataclass
class ToolCall:
    """Represents a tool call request from the LLM."""

    tool_name: str
    parameters: dict[str, Any]
    raw_text: str = ""  # Original text that was parsed
    confidence: float = 1.0  # Parser confidence in the call (0-1)

    def __post_init__(self):
        """Validate tool call after initialization."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ToolResult:
    """Result of tool execution."""

    status: ToolCallStatus
    content: str = ""
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    @property
    def success(self) -> bool:
        """Check if tool call was successful."""
        return self.status == ToolCallStatus.SUCCESS

    def to_llm_message(self) -> str:
        """Format result for LLM consumption."""
        if self.success:
            return f"✅ Tool executed successfully:\n{self.content}"
        else:
            return f"❌ Tool execution failed: {self.error_message or 'Unknown error'}"


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self):
        self._definition: ToolDefinition | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (must be unique)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters definition."""
        pass

    @property
    def definition(self) -> ToolDefinition:
        """Get complete tool definition."""
        if self._definition is None:
            self._definition = ToolDefinition(
                name=self.name, description=self.description, parameters=self.parameters
            )
        return self._definition

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate parameters against tool definition.

        Returns:
            (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in parameters:
                return False, f"Missing required parameter: {param.name}"

            if param.name in parameters:
                value = parameters[param.name]

                # Basic type validation
                if param.type == "string" and not isinstance(value, str):
                    return False, f"Parameter {param.name} must be a string"
                elif param.type == "number" and not isinstance(value, int | float):
                    return False, f"Parameter {param.name} must be a number"
                elif param.type == "boolean" and not isinstance(value, bool):
                    return False, f"Parameter {param.name} must be a boolean"

                # Enum validation
                if param.enum_values and value not in param.enum_values:
                    return False, f"Parameter {param.name} must be one of: {param.enum_values}"

        return True, None

    def safe_execute(self, parameters: dict[str, Any]) -> ToolResult:
        """Execute tool with validation and error handling."""
        import time

        start_time = time.time()

        try:
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(parameters)
            if not is_valid:
                return ToolResult(
                    status=ToolCallStatus.ERROR,
                    error_message=f"Parameter validation failed: {error_msg}",
                    execution_time=time.time() - start_time,
                )

            # Execute tool
            result = self.execute(**parameters)
            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Tool execution failed: {str(e)}",
                execution_time=time.time() - start_time,
            )


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} is already registered")
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Get definitions for all registered tools."""
        return [tool.definition for tool in self._tools.values()]

    def get_openai_functions(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI function calling format."""
        return [tool.definition.to_openai_format() for tool in self._tools.values()]

    def fuzzy_match_tool(self, tool_name: str, threshold: float = 0.6) -> str | None:
        """Find closest matching tool name using fuzzy matching.

        Args:
            tool_name: The tool name to match
            threshold: Minimum similarity threshold (0-1)

        Returns:
            Best matching tool name or None
        """
        from difflib import SequenceMatcher

        best_match = None
        best_score = 0.0

        for registered_name in self._tools.keys():
            # Calculate similarity
            similarity = SequenceMatcher(None, tool_name.lower(), registered_name.lower()).ratio()

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = registered_name

        return best_match

    def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            Tool execution result
        """
        # First try exact match
        tool = self.get_tool(tool_call.tool_name)

        # If no exact match, try fuzzy matching
        if tool is None:
            fuzzy_match = self.fuzzy_match_tool(tool_call.tool_name)
            if fuzzy_match:
                tool = self.get_tool(fuzzy_match)
                # Update the tool call name for clarity
                tool_call.tool_name = fuzzy_match
                tool_call.confidence *= 0.8  # Reduce confidence for fuzzy matches

        if tool is None:
            available_tools = ", ".join(self.list_tools())
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Tool '{tool_call.tool_name}' not found. Available tools: {available_tools}",
            )

        return tool.safe_execute(tool_call.parameters)


# Global tool registry instance
default_registry = ToolRegistry()
