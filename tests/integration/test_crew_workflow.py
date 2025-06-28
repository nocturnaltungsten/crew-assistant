"""Integration tests for crew workflow."""

import json
from unittest.mock import patch

import pytest

from crew_assistant.config import Settings


class TestCrewWorkflow:
    """Test complete crew workflow integration."""

    @pytest.mark.integration
    def test_memory_persistence_workflow(self, test_settings: Settings, mock_crewai):
        """Test that crew runs properly persist memory."""
        from core.context_engine.memory_store import MemoryStore

        memory_store = MemoryStore()

        # Simulate a crew run saving memory
        memory_store.save(
            agent="TestAgent",
            input_summary="Test task description",
            output_summary="Test task result",
            task_id="integration-test-123"
        )

        # Verify memory was saved to disk
        memory_files = list(test_settings.memory_dir.glob("*.json"))
        assert len(memory_files) == 1

        # Verify file contents
        with open(memory_files[0]) as f:
            data = json.load(f)
            assert data["agent"] == "TestAgent"
            assert data["task_id"] == "integration-test-123"

        # Test loading memory back
        recent_entries = memory_store.recent(count=1)
        assert len(recent_entries) == 1
        assert recent_entries[0]["agent"] == "TestAgent"

    @pytest.mark.integration
    def test_agent_registry_discovery(self, test_settings: Settings):
        """Test agent registry can discover agents."""
        from core.agent_registry import discover_agents

        # This will test the actual agent discovery
        agents = discover_agents()

        # Should find the actual agents defined in agents/
        expected_roles = {"Planner", "Dev", "Commander", "UX"}
        found_roles = set(agents.keys())

        # At minimum should find some agents
        assert len(agents) > 0
        # Check if expected agents are found (may vary based on actual agent files)
        assert found_roles.intersection(expected_roles)

    @pytest.mark.integration
    def test_fact_learning_integration(self, test_settings: Settings):
        """Test fact learning and storage integration."""
        from core.context_engine.fact_store import FactStore
        from utils.fact_learning import learn_fact_if_possible

        fact_store = FactStore()

        # Test learning facts from text
        test_text = "My name is John Doe and I prefer Python programming"
        facts = learn_fact_if_possible(test_text, fact_store)

        assert "name" in facts
        assert facts["name"] == "John Doe"
        assert "preferred_python" in facts

        # Verify facts are persisted
        all_facts = fact_store.all()
        assert "name" in all_facts
        assert all_facts["name"] == "John Doe"

    @pytest.mark.integration
    def test_model_selector_integration(self, test_settings: Settings, mock_requests):
        """Test model selector with mocked API."""
        from utils.model_selector import select_model

        with patch("builtins.input", return_value="1"):
            result = select_model()

        assert result == "test-model-1"

        # Verify environment is updated
        import os
        assert os.environ.get("OPENAI_API_MODEL") == "test-model-1"
