"""Configuration management for Crew Assistant."""

import os
from pathlib import Path

from loguru import logger
from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation."""

    # API Configuration
    ai_provider: str = Field(default="lm_studio", description="AI provider: lm_studio or ollama")
    openai_api_base: str = Field(
        default="http://localhost:1234/v1", description="Base URL for OpenAI-compatible API"
    )
    openai_api_key: str = Field(
        default="not-needed-for-local", description="API key (not needed for local providers)"
    )
    openai_api_model: str = Field(
        default="microsoft/phi-4-mini-reasoning", description="Default model to use"
    )
    lm_timeout: int = Field(default=60, ge=1, le=600, description="LLM request timeout in seconds")

    # Application Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Storage Configuration
    base_dir: Path = Field(
        default_factory=lambda: Path.cwd(), description="Base directory for the application"
    )
    memory_dir: Path = Field(
        default_factory=lambda: Path("memory/memory_store"),
        description="Directory for memory storage",
    )
    facts_dir: Path = Field(
        default_factory=lambda: Path("memory/facts"), description="Directory for fact storage"
    )
    snapshots_dir: Path = Field(
        default_factory=lambda: Path("snapshots"), description="Directory for run snapshots"
    )
    crew_runs_dir: Path = Field(
        default_factory=lambda: Path("crew_runs"), description="Directory for crew run logs"
    )

    # Agent Configuration
    agent_verbose: bool = Field(default=True, description="Enable agent verbose output")
    max_memory_entries: int = Field(
        default=1000, ge=10, le=10000, description="Maximum memory entries to keep"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @model_validator(mode="after")
    def resolve_paths(self):
        """Resolve relative paths against base_dir."""
        path_fields = ["memory_dir", "facts_dir", "snapshots_dir", "crew_runs_dir"]

        for field_name in path_fields:
            path = getattr(self, field_name)
            if not isinstance(path, Path):
                path = Path(path)

            if not path.is_absolute():
                path = self.base_dir / path

            object.__setattr__(self, field_name, path)

        return self

    def create_directories(self) -> None:
        """Create necessary directories."""
        directories = [
            self.memory_dir,
            self.facts_dir,
            self.snapshots_dir,
            self.crew_runs_dir,
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()

        # Configure logging
        logger.remove()  # Remove default handler
        logger.add(
            lambda msg: print(msg, end=""),  # Print to stdout
            level=_settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>",
            colorize=True,
        )

        logger.info(f"Crew Assistant v{os.getenv('CREW_ASSISTANT_VERSION', '0.2.0')} initialized")
        logger.debug(f"Configuration: {_settings.dict(exclude={'openai_api_key'})}")

    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None
