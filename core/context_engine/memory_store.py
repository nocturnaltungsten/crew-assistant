# === memory_store.py ===
import os
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

MEMORY_DIR = "memory/memory_store"
os.makedirs(MEMORY_DIR, exist_ok=True)


@dataclass
class MemoryEntry:
    id: str
    timestamp: str
    agent: str
    input_summary: str
    output_summary: str
    task_id: Optional[str] = None

class MemoryStore:
    def __init__(self) -> None:
        self.store: list[MemoryEntry] = []

    def save(self, agent: str, input_summary: str, output_summary: str, task_id: Optional[str] = None) -> MemoryEntry:
        """Convenience wrapper to create and persist a :class:`MemoryEntry`."""
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            agent=agent,
            input_summary=input_summary,
            output_summary=output_summary,
            task_id=str(task_id) if task_id else None,
        )
        self.save_entry(entry)
        return entry

    def save_entry(self, entry: MemoryEntry) -> None:
        """Persist a pre-created :class:`MemoryEntry`."""
        self.store.append(entry)

        safe_ts = entry.timestamp.replace(":", "-")
        filename = f"{safe_ts}__{entry.agent}.json"

        with open(os.path.join(MEMORY_DIR, filename), "w") as f:
            json.dump(asdict(entry), f, indent=2)

    def load_all(self) -> List[MemoryEntry]:
        """Return all entries stored during this session."""
        return list(self.store)

    def recent(self, agent: Optional[str] = None, count: int = 5) -> List[MemoryEntry]:
        """Return the most recent persisted entries from disk."""
        entries: List[MemoryEntry] = []
        files = sorted(os.listdir(MEMORY_DIR), reverse=True)
        for f in files:
            try:
                with open(os.path.join(MEMORY_DIR, f)) as file:
                    data = json.load(file)
                    if agent is None or data.get("agent") == agent:
                        entries.append(MemoryEntry(**data))
            except Exception:
                continue
            if len(entries) >= count:
                break
        return entries

    def latest(self, count: int = 1) -> List[MemoryEntry]:
        """Helper to fetch the newest ``count`` entries."""
        return self.recent(count=count)
