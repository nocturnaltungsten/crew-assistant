from crew_assistant.context.facts import FactStore


def test_set_and_get(tmp_path, monkeypatch):
    facts_file = tmp_path / "facts.json"
    monkeypatch.setattr("crew_assistant.context.facts.FACT_FILE", str(facts_file))
    store = FactStore()
    store.set("name", "Avery")
    assert store.get("name") == "Avery"
