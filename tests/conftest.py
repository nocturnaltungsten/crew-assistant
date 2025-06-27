"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import pytest
from loguru import logger

from crew_assistant.config import Settings, reset_settings


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration for each test."""
    logger.remove()  # Remove all handlers
    logger.add(lambda msg: None, level="CRITICAL")  # Suppress logs in tests
    yield
    logger.remove()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Generator[Settings, None, None]:
    """Create test settings with temporary directories."""
    import os
    from unittest.mock import patch
    
    reset_settings()  # Reset singleton
    
    # Override problematic env vars for testing
    with patch.dict(os.environ, {
        "LM_TIMEOUT": "5",
        "OPENAI_API_MODEL": "test-model",
    }, clear=False):
        settings = Settings(
            base_dir=temp_dir,
            memory_dir=temp_dir / "memory" / "memory_store",
            facts_dir=temp_dir / "memory" / "facts", 
            snapshots_dir=temp_dir / "snapshots",
            crew_runs_dir=temp_dir / "crew_runs",
            debug=True,
            log_level="DEBUG",
            _env_file=None,  # Don't load .env in tests
        )
        
        settings.create_directories()
        yield settings
    
    reset_settings()  # Clean up


@pytest.fixture
def mock_requests():
    """Mock requests module for API testing."""
    import requests
    
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {"id": "test-model-1"},
            {"id": "test-model-2"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    
    original_get = requests.get
    requests.get = Mock(return_value=mock_response)
    
    yield mock_response
    
    requests.get = original_get


@pytest.fixture
def mock_crewai():
    """Mock CrewAI components for testing."""
    from unittest.mock import patch
    
    mock_agent = Mock()
    mock_agent.role = "TestAgent"
    mock_agent.__class__.__name__ = "TestAgent"
    
    mock_task = Mock()
    mock_task.id = "test-task-123"
    mock_task.output.content = "Test output"
    
    mock_crew = Mock()
    mock_crew.kickoff.return_value = "Test crew result"
    mock_crew.tasks = [mock_task]
    
    with patch("crewai.Agent", return_value=mock_agent), \
         patch("crewai.Task", return_value=mock_task), \
         patch("crewai.Crew", return_value=mock_crew):
        yield {
            "agent": mock_agent,
            "task": mock_task, 
            "crew": mock_crew,
        }


@pytest.fixture
def sample_memory_entry():
    """Sample memory entry for testing."""
    return {
        "id": "test-memory-123",
        "timestamp": "2025-06-27T14:00:00.000000",
        "agent": "TestAgent",
        "task_id": "test-task-123",
        "input_summary": "Test input",
        "output_summary": "Test output",
    }


@pytest.fixture
def sample_facts():
    """Sample facts for testing."""
    return {
        "name": "Test User",
        "preferred_language": "python",
        "project_type": "ai_assistant",
    }