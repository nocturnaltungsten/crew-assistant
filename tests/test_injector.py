from crew_assistant.context.inject import ContextInjector
from crew_assistant.context.memory import MemoryStore
from crew_assistant.context.facts import FactStore


def test_context_build(tmp_path, monkeypatch):
    mem_dir = tmp_path / "mem"
    mem_dir.mkdir()
    monkeypatch.setattr("crew_assistant.context.memory.MEMORY_DIR", str(mem_dir))
    mem = MemoryStore()
    mem.save("UX", "hi", "there")

    facts_file = tmp_path / "facts.json"
    monkeypatch.setattr("crew_assistant.context.facts.FACT_FILE", str(facts_file))
    facts = FactStore()
    facts.set("name", "Avery")

    inj = ContextInjector(memory=mem, factstore=facts)
    text = inj.get_context("UX", max_items=1)
    assert "Avery" in text
    assert "hi" in text
