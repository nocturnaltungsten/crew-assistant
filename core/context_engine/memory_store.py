import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from core.context_engine.context_types import ContextEntry


class MemoryStore:
    def __init__(self, storage_path: str = "memory/context_log.json"):
        self.path = Path(storage_path)

        # Ensure parent directories exist
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty JSON file if it doesn't exist
        if not self.path.exists():
            self.path.write_text("[]")

    def save_entry(
        self,
        agent: str,
        input_summary: str,
        output_summary: str,
        task_id: Optional[str] = None,
    ):
        entry = ContextEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            input_summary=input_summary,
            output_summary=output_summary,
            task_id=task_id,
        )

        # Load existing entries
        existing = self.load_entries()

        # Add new one and write back
        existing.append(entry.__dict__)
        self.path.write_text(json.dumps(existing, indent=2))

    def load_entries(self) -> List[dict]:
        try:
            return json.loads(self.path.read_text())
        except Exception as e:
            print(f"⚠️ Failed to load memory entries: {e}")
            return []

    def latest(self, count: int = 1) -> List[dict]:
        return self.load_entries()[-count:]
