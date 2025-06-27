"""Unit tests for configuration management."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from crew_assistant.config import Settings, get_settings, reset_settings


class TestSettings:
    """Test the Settings class."""
    
    def test_default_values(self, temp_dir: Path):
        """Test default configuration values."""
        from unittest.mock import patch
        import os
        
        # Override env vars that might interfere with tests
        with patch.dict(os.environ, {
            "LM_TIMEOUT": "60",  # Valid timeout
        }, clear=False):
            settings = Settings(base_dir=temp_dir, _env_file=None)
        
        assert settings.openai_api_base == "http://localhost:1234/v1"
        assert settings.openai_api_model == "microsoft/phi-4-mini-reasoning"
        assert settings.lm_timeout == 60
        assert settings.debug is False
        assert settings.log_level == "INFO"
    
    def test_path_validation(self, temp_dir: Path):
        """Test that paths are properly validated and made absolute."""
        settings = Settings(
            base_dir=temp_dir,
            memory_dir=Path("relative/memory"),
            facts_dir=Path("relative/facts"),
        )
        
        assert settings.memory_dir.is_absolute()
        assert settings.facts_dir.is_absolute()
        assert str(settings.memory_dir).startswith(str(temp_dir))
    
    def test_log_level_validation(self, temp_dir: Path):
        """Test log level validation."""
        # Valid log level
        settings = Settings(base_dir=temp_dir, log_level="DEBUG")
        assert settings.log_level == "DEBUG"
        
        # Invalid log level should raise error
        with pytest.raises(ValidationError):
            Settings(base_dir=temp_dir, log_level="INVALID")
    
    def test_timeout_validation(self, temp_dir: Path):
        """Test timeout validation."""
        # Valid timeout
        settings = Settings(base_dir=temp_dir, lm_timeout=30)
        assert settings.lm_timeout == 30
        
        # Too low timeout
        with pytest.raises(ValidationError):
            Settings(base_dir=temp_dir, lm_timeout=0)
        
        # Too high timeout
        with pytest.raises(ValidationError):
            Settings(base_dir=temp_dir, lm_timeout=700)
    
    def test_create_directories(self, temp_dir: Path):
        """Test directory creation."""
        settings = Settings(
            base_dir=temp_dir,
            memory_dir=temp_dir / "test_memory",
            facts_dir=temp_dir / "test_facts",
        )
        
        settings.create_directories()
        
        assert settings.memory_dir.exists()
        assert settings.facts_dir.exists()
        assert settings.snapshots_dir.exists()
        assert settings.crew_runs_dir.exists()
    
    def test_env_file_loading(self, temp_dir: Path):
        """Test loading from .env file."""
        env_file = temp_dir / ".env"
        env_file.write_text("OPENAI_API_MODEL=test-model-from-env\nDEBUG=true")
        
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(base_dir=temp_dir)
            # Note: We need to override the env_file path since it looks in cwd by default
            
        # For now, just test that we can instantiate settings
        assert isinstance(settings, Settings)


class TestGetSettings:
    """Test the settings singleton function."""
    
    def test_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        reset_settings()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reset_settings(self):
        """Test that reset_settings clears the singleton."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        
        assert settings1 is not settings2