import json
from crew_assistant.context import memory
from crew_assistant.context.memory import MemoryStore


def test_save_and_recent(tmp_path, monkeypatch):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    monkeypatch.setattr(memory, "MEMORY_DIR", str(data_dir))
    store = MemoryStore()
    store.save("Tester", "hello", "world")

    recent = store.recent()
    assert len(recent) == 1
    assert recent[0]["agent"] == "Tester"
