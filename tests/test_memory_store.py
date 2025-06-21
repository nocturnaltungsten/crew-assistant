from core.context_engine.memory_store import MemoryStore

def test_save_and_recent(tmp_path, monkeypatch):
    monkeypatch.setattr('core.context_engine.memory_store.MEMORY_DIR', tmp_path)
    store = MemoryStore()
    store.save('Agent', 'input', 'output')
    recent = store.recent()
    assert len(recent) == 1
    entry = recent[0]
    assert entry.agent == 'Agent'
    assert entry.input_summary == 'input'
    assert entry.output_summary == 'output'
