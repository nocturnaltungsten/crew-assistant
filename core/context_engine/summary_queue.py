"""
summary_queue.py

Efficient queue for routing long content chunks to summarization modules.
Buffers routed events, manages queue size, and handles periodic flush to disk or processing pipeline.
Location: core/context_engine/
"""

import os
import json
import uuid
import datetime
from typing import List, Dict, Optional

# === Constants ===
SUMMARY_QUEUE_DIR = "memory/summary_queue"
os.makedirs(SUMMARY_QUEUE_DIR, exist_ok=True)


class SummaryQueue:
    def __init__(self, flush_limit: int = 5):
        """
        Create a new summary queue.

        :param flush_limit: Number of items before auto-flush.
        """
        self.queue: List[Dict] = []
        self.flush_limit = flush_limit

    def add(self, content: str, source: str, metadata: Optional[Dict] = None):
        """
        Add a content block to the queue.

        :param content: Raw content to be summarized.
        :param source: Identifier for the content origin (e.g. "DevAgent", "task123").
        :param metadata: Optional metadata (timestamp, type, tags, etc).
        """
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "source": source,
            "content": content.strip(),
            "metadata": metadata or {}
        }
        self.queue.append(entry)

        if len(self.queue) >= self.flush_limit:
            self.flush()

    def flush(self):
        """Flush the current queue to a timestamped JSONL file."""
        if not self.queue:
            return

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = os.path.join(SUMMARY_QUEUE_DIR, f"summary_batch__{timestamp}.jsonl")

        with open(filename, "w") as f:
            for entry in self.queue:
                f.write(json.dumps(entry) + "\n")

        print(f"📤 Summary queue flushed to: {filename} ({len(self.queue)} items)")
        self.queue.clear()

    def pending(self) -> int:
        """Return the number of items currently in the queue."""
        return len(self.queue)
