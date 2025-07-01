# === memory_store.py ===
import json
import os
import uuid
from datetime import datetime
from typing import Any

MEMORY_DIR = "memory/memory_store"
os.makedirs(MEMORY_DIR, exist_ok=True)


class MemoryStore:
    def __init__(self) -> None:
        self.store: list[dict] = []

    def save(self, agent: str, input_summary: str, output_summary: str, task_id: str | None = None):
        """
        Save a memory snapshot.
        """
        memory_entry: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "task_id": str(task_id) if task_id else None,
            "input_summary": input_summary,
            "output_summary": output_summary,
        }
        self.store.append(memory_entry)

        # Save individual file (timestamped for redundancy)
        safe_ts = memory_entry["timestamp"].replace(":", "-")
        filename = f"{safe_ts}__{agent}.json"

        with open(os.path.join(MEMORY_DIR, filename), "w") as f:
            json.dump(memory_entry, f, indent=2)

    def load_all(self) -> list[dict]:
        """
        Load all stored memory entries.
        """
        return self.store

    def recent(self, agent: str | None = None, count: int = 5) -> list[dict]:
        """
        Returns the N most recent memory entries, optionally filtered by agent.
        """
        entries = []
        files = sorted(os.listdir(MEMORY_DIR), reverse=True)
        for f in files:
            try:
                with open(os.path.join(MEMORY_DIR, f)) as file:
                    entry = json.load(file)
                    if agent is None or entry.get("agent") == agent:
                        entries.append(entry)
            except Exception:
                continue
            if len(entries) >= count:
                break
        return entries
