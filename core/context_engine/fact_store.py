# === FILE: core/context_engine/fact_store.py ===

import json
import os

FACTS_DIR = "memory/facts"
os.makedirs(FACTS_DIR, exist_ok=True)

FACT_FILE = os.path.join(FACTS_DIR, "user_facts.json")


class FactStore:
    def __init__(self) -> None:
        self.facts: dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.isfile(FACT_FILE):
            with open(FACT_FILE) as f:
                self.facts = json.load(f)

    def save(self):
        with open(FACT_FILE, "w") as f:
            json.dump(self.facts, f, indent=2)

    def set(self, key: str, value: str):
        self.facts[key] = value
        self.save()

    def get(self, key: str) -> str:
        return self.facts.get(key, "")

    def as_text(self) -> str:
        if not self.facts:
            return "(no known facts)"
        return "\n".join([f"- {k}: {v}" for k, v in self.facts.items()])

    def all(self) -> dict[str, str]:
        return self.facts
