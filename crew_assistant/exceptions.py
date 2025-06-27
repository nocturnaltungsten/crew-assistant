"""Custom exceptions for Crew Assistant."""


class CrewAssistantError(Exception):
    """Base exception for Crew Assistant."""
    pass


class ConfigurationError(CrewAssistantError):
    """Configuration related errors."""
    pass


class ModelError(CrewAssistantError):
    """Model selection and API errors."""
    pass


class MemoryError(CrewAssistantError):
    """Memory storage and retrieval errors."""
    pass


class AgentError(CrewAssistantError):
    """Agent instantiation and execution errors."""
    pass


class TaskError(CrewAssistantError):
    """Task definition and execution errors."""
    pass


class ContextError(CrewAssistantError):
    """Context engine errors."""
    pass