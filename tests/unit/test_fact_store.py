"""Unit tests for fact store functionality."""

import json
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from core.context_engine.fact_store import FactStore


class TestFactStore:
    """Test the FactStore class."""

    def test_initialization(self, temp_dir: Path):
        """Test fact store initialization."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        assert fact_store.facts_file == facts_file
        assert fact_store.facts == {}

    def test_set_and_get_fact(self, temp_dir: Path):
        """Test setting and getting facts."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        # Set a fact
        fact_store.set("user_name", "Alice")
        assert fact_store.get("user_name") == "Alice"

        # Get non-existent fact
        assert fact_store.get("non_existent") is None

        # Get with default
        assert fact_store.get("non_existent", "default") == "default"

    def test_all_facts(self, temp_dir: Path):
        """Test getting all facts."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("name", "Alice")
        fact_store.set("age", "30")
        fact_store.set("city", "New York")

        all_facts = fact_store.all()
        expected = {"name": "Alice", "age": "30", "city": "New York"}
        assert all_facts == expected

    def test_as_text(self, temp_dir: Path):
        """Test text representation of facts."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        # Empty facts
        assert fact_store.as_text() == ""

        # With facts
        fact_store.set("name", "Alice")
        fact_store.set("hobby", "painting")

        text = fact_store.as_text()
        assert "name: Alice" in text
        assert "hobby: painting" in text

    def test_save_facts(self, temp_dir: Path):
        """Test saving facts to file."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("name", "Bob")
        fact_store.set("language", "Python")
        fact_store.save()

        # Check file was created and contains correct data
        assert facts_file.exists()
        with open(facts_file) as f:
            saved_data = json.load(f)

        expected = {"name": "Bob", "language": "Python"}
        assert saved_data == expected

    def test_load_facts_existing_file(self, temp_dir: Path):
        """Test loading facts from existing file."""
        facts_file = temp_dir / "facts.json"

        # Create a facts file
        facts_data = {"user": "Charlie", "skill": "JavaScript"}
        with open(facts_file, "w") as f:
            json.dump(facts_data, f)

        # Load facts
        fact_store = FactStore(facts_file=facts_file)
        fact_store.load()

        assert fact_store.get("user") == "Charlie"
        assert fact_store.get("skill") == "JavaScript"

    def test_load_facts_nonexistent_file(self, temp_dir: Path):
        """Test loading facts when file doesn't exist."""
        facts_file = temp_dir / "nonexistent.json"
        fact_store = FactStore(facts_file=facts_file)

        # Should not raise error
        fact_store.load()
        assert fact_store.facts == {}

    def test_load_facts_corrupted_file(self, temp_dir: Path):
        """Test loading facts from corrupted file."""
        facts_file = temp_dir / "corrupted.json"

        # Create corrupted JSON file
        with open(facts_file, "w") as f:
            f.write("{ invalid json")

        fact_store = FactStore(facts_file=facts_file)

        # Should handle corrupted file gracefully
        fact_store.load()
        assert fact_store.facts == {}

    def test_overwrite_fact(self, temp_dir: Path):
        """Test overwriting existing facts."""
        facts_file = temp_dir / "facts.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("status", "beginner")
        assert fact_store.get("status") == "beginner"

        fact_store.set("status", "expert")
        assert fact_store.get("status") == "expert"

    def test_persistence_across_instances(self, temp_dir: Path):
        """Test that facts persist across FactStore instances."""
        facts_file = temp_dir / "persistent.json"

        # First instance
        fact_store1 = FactStore(facts_file=facts_file)
        fact_store1.set("persistent_fact", "this should persist")
        fact_store1.save()

        # Second instance
        fact_store2 = FactStore(facts_file=facts_file)
        fact_store2.load()

        assert fact_store2.get("persistent_fact") == "this should persist"

    def test_unicode_handling(self, temp_dir: Path):
        """Test handling of unicode characters in facts."""
        facts_file = temp_dir / "unicode.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("emoji", "😀🎉")
        fact_store.set("unicode", "café naïve résumé")
        fact_store.save()

        # Reload and verify
        fact_store2 = FactStore(facts_file=facts_file)
        fact_store2.load()

        assert fact_store2.get("emoji") == "😀🎉"
        assert fact_store2.get("unicode") == "café naïve résumé"

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_save_permission_error(self, mock_file, temp_dir: Path):
        """Test handling of permission errors during save."""
        facts_file = temp_dir / "no_permission.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("test", "value")

        # Should handle permission error gracefully
        with pytest.raises(PermissionError):
            fact_store.save()

    def test_case_sensitive_keys(self, temp_dir: Path):
        """Test that fact keys are case sensitive."""
        facts_file = temp_dir / "case_test.json"
        fact_store = FactStore(facts_file=facts_file)

        fact_store.set("Name", "Alice")
        fact_store.set("name", "Bob")

        assert fact_store.get("Name") == "Alice"
        assert fact_store.get("name") == "Bob"
        assert len(fact_store.all()) == 2
