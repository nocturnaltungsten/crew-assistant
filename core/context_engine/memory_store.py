# === memory_store.py ===
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

MEMORY_DIR = "memory/memory_store"
os.makedirs(MEMORY_DIR, exist_ok=True)


class MemoryStore:
    def __init__(self):
        self.store: List[Dict] = []

    def save(self, agent: str, input_summary: str, output_summary: str, task_id: Optional[str] = None):
        """
        Save a memory snapshot.
        """
        memory_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "task_id": str(task_id) if task_id else None,
            "input_summary": input_summary,
            "output_summary": output_summary,
        }
        self.store.append(memory_entry)

        # Save individual file (timestamped for redundancy)
        safe_ts = memory_entry['timestamp'].replace(":", "-")
        filename = f"{safe_ts}__{agent}.json"

        with open(os.path.join(MEMORY_DIR, filename), "w") as f:
            json.dump(memory_entry, f, indent=2)

    def load_all(self) -> List[Dict]:
        """
        Load all stored memory entries.
        """
        return self.store
