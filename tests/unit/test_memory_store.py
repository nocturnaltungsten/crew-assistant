"""Unit tests for memory store functionality."""

import json

from core.context_engine.memory_store import MemoryStore


class TestMemoryStore:
    """Test the MemoryStore class."""

    def test_initialization(self, test_settings):
        """Test memory store initialization."""
        memory_store = MemoryStore()
        assert memory_store.store == []

    def test_save_memory_entry(self, test_settings, sample_memory_entry):
        """Test saving a memory entry."""
        memory_store = MemoryStore()

        memory_store.save(
            agent="TestAgent",
            input_summary="Test input",
            output_summary="Test output",
            task_id="test-task-123",
        )

        assert len(memory_store.store) == 1
        entry = memory_store.store[0]

        assert entry["agent"] == "TestAgent"
        assert entry["input_summary"] == "Test input"
        assert entry["output_summary"] == "Test output"
        assert entry["task_id"] == "test-task-123"
        assert "id" in entry
        assert "timestamp" in entry

    def test_save_without_task_id(self, test_settings):
        """Test saving memory entry without task_id."""
        memory_store = MemoryStore()

        memory_store.save(
            agent="TestAgent", input_summary="Test input", output_summary="Test output"
        )

        entry = memory_store.store[0]
        assert entry["task_id"] is None

    def test_save_creates_file(self, test_settings):
        """Test that save creates a JSON file."""
        memory_store = MemoryStore()

        memory_store.save(
            agent="TestAgent", input_summary="Test input", output_summary="Test output"
        )

        # Check that a file was created
        memory_dir = test_settings.memory_dir
        files = list(memory_dir.glob("*.json"))
        assert len(files) == 1

        # Check file contents
        with open(files[0]) as f:
            data = json.load(f)
            assert data["agent"] == "TestAgent"

    def test_load_all(self, test_settings):
        """Test loading all memory entries."""
        memory_store = MemoryStore()

        # Add some entries
        memory_store.save("Agent1", "Input1", "Output1")
        memory_store.save("Agent2", "Input2", "Output2")

        all_entries = memory_store.load_all()
        assert len(all_entries) == 2
        assert all_entries[0]["agent"] == "Agent1"
        assert all_entries[1]["agent"] == "Agent2"

    def test_recent_entries(self, test_settings):
        """Test retrieving recent entries."""
        memory_store = MemoryStore()

        # Create some test files
        memory_dir = test_settings.memory_dir
        for i in range(10):
            file_path = memory_dir / f"2025-06-27T14-00-{i:02d}__Agent{i}.json"
            entry = {
                "id": f"test-{i}",
                "timestamp": f"2025-06-27T14:00:{i:02d}",
                "agent": f"Agent{i}",
                "input_summary": f"Input {i}",
                "output_summary": f"Output {i}",
            }
            with open(file_path, "w") as f:
                json.dump(entry, f)

        # Test retrieving recent entries
        recent = memory_store.recent(count=5)
        assert len(recent) == 5

        # Should be in reverse chronological order (most recent first)
        assert recent[0]["agent"] == "Agent9"
        assert recent[4]["agent"] == "Agent5"

    def test_recent_entries_filtered_by_agent(self, test_settings):
        """Test retrieving recent entries filtered by agent."""
        memory_store = MemoryStore()
        memory_dir = test_settings.memory_dir

        # Create mixed agent files
        agents = ["AgentA", "AgentB", "AgentA", "AgentB", "AgentA"]
        for i, agent in enumerate(agents):
            file_path = memory_dir / f"2025-06-27T14-00-{i:02d}__{agent}.json"
            entry = {
                "id": f"test-{i}",
                "timestamp": f"2025-06-27T14:00:{i:02d}",
                "agent": agent,
                "input_summary": f"Input {i}",
                "output_summary": f"Output {i}",
            }
            with open(file_path, "w") as f:
                json.dump(entry, f)

        # Test filtering by agent
        agent_a_entries = memory_store.recent(agent="AgentA", count=10)
        assert len(agent_a_entries) == 3
        assert all(entry["agent"] == "AgentA" for entry in agent_a_entries)

    def test_recent_entries_with_corrupted_file(self, test_settings):
        """Test that corrupted files are skipped."""
        memory_store = MemoryStore()
        memory_dir = test_settings.memory_dir

        # Create a valid file
        valid_file = memory_dir / "2025-06-27T14-00-01__ValidAgent.json"
        valid_entry = {
            "id": "valid-1",
            "agent": "ValidAgent",
            "input_summary": "Valid input",
            "output_summary": "Valid output",
        }
        with open(valid_file, "w") as f:
            json.dump(valid_entry, f)

        # Create a corrupted file
        corrupted_file = memory_dir / "2025-06-27T14-00-02__CorruptedAgent.json"
        with open(corrupted_file, "w") as f:
            f.write("invalid json content {")

        # Should only return valid entries
        recent = memory_store.recent(count=10)
        assert len(recent) == 1
        assert recent[0]["agent"] == "ValidAgent"
