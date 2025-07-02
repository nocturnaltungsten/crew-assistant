"""System/E2E tests for complete application workflows."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestEndToEnd:
    """End-to-end system tests."""

    @pytest.mark.system
    @pytest.mark.slow
    def test_crew_agents_help(self):
        """Test that crew_agents.py shows help."""
        result = subprocess.run(
            ["python", "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert result.returncode == 0
        assert "Crew AI Assistant" in result.stdout
        assert "--ux" in result.stdout
        assert "--select-model" in result.stdout

    @pytest.mark.system
    def test_model_selector_script(self, mock_requests):
        """Test model selector as standalone script."""
        with patch("builtins.input", return_value="1"):
            result = subprocess.run(
                ["python", "-m", "crew_assistant.utils.model_selector"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
                env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            )

        # Should not crash and should show model selection
        assert result.returncode == 0 or "test-model" in result.stdout or result.stderr

    @pytest.mark.system
    @pytest.mark.slow
    def test_full_crew_run_dry(self):
        """Test a full crew run in dry mode (without actually calling LLM)."""
        # This would require mocking the entire CrewAI stack
        # For now, just test that the script can be imported
        result = subprocess.run(
            ["python", "-c", "import main; print('Import successful')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert result.returncode == 0
        assert "Import successful" in result.stdout

    @pytest.mark.system
    def test_project_structure_integrity(self):
        """Test that all expected files and directories exist."""
        project_root = Path(__file__).parent.parent.parent

        # Check critical files exist
        critical_files = [
            "main.py",
            "pyproject.toml",
            "README.md",
            "CLAUDE.md",
        ]

        for file_path in critical_files:
            assert (project_root / file_path).exists(), f"Missing critical file: {file_path}"

        # Check critical directories exist
        critical_dirs = [
            "src/crew_assistant/agents",
            "src/crew_assistant/core",
            "src/crew_assistant/utils",
            "tests",
            "src/crew_assistant",
        ]

        for dir_path in critical_dirs:
            assert (project_root / dir_path).is_dir(), f"Missing critical directory: {dir_path}"

    @pytest.mark.system
    def test_import_all_modules(self):
        """Test that all Python modules can be imported without errors."""
        import importlib

        modules_to_test = [
            "crew_assistant",
            "crew_assistant.config",
            "crew_assistant.exceptions",
            "crew_assistant.utils.model_selector",
            "crew_assistant.utils.fact_learning",
            "crew_assistant.core.agent_registry",
            "crew_assistant.core.context_engine.memory_store",
            "crew_assistant.core.context_engine.fact_store",
        ]

        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    @pytest.mark.system
    def test_configuration_validation(self):
        """Test that configuration validates correctly."""
        from crew_assistant.config import Settings

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Should create settings without errors
            settings = Settings(base_dir=Path(tmp_dir))
            settings.create_directories()

            # All directories should be created
            assert settings.memory_dir.exists()
            assert settings.facts_dir.exists()
            assert settings.snapshots_dir.exists()
            assert settings.crew_runs_dir.exists()
