"""
summary_queue.py

Efficient, pluggable queue for routing long-form content (e.g. agent outputs, logs)
to summarization modules or persistent memory systems. Buffers routed events,
auto-flushes on limit, and supports hooks into external archiving systems.

Location: core/context_engine/
"""

import os
import json
import uuid
import datetime
from typing import List, Dict, Optional, Callable

# === CONFIG ===
SUMMARY_QUEUE_DIR = "memory/summary_queue"
os.makedirs(SUMMARY_QUEUE_DIR, exist_ok=True)


class SummaryQueue:
    def __init__(self, flush_limit: int = 5, on_flush: Optional[Callable[[List[Dict]], None]] = None):
        """
        Initialize a new summary queue.

        Args:
            flush_limit (int): Number of entries before triggering flush.
            on_flush (callable): Optional callback for flushed data (e.g. to archive).
        """
        self.queue: List[Dict] = []
        self.flush_limit = flush_limit
        self.on_flush = on_flush

    def add(self, content: str, source: str, metadata: Optional[Dict] = None):
        """
        Add a content entry to the queue.

        Args:
            content (str): Raw content to store.
            source (str): Origin identifier (e.g., "DevAgent", "task123").
            metadata (dict, optional): Additional metadata for context or tracing.
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
        """
        Flush the queue to disk and optionally to an external callback.

        - Writes current queue to a timestamped .jsonl file in memory/summary_queue
        - Calls `on_flush(entries)` if provided
        """
        if not self.queue:
            return

        flushed = self.queue.copy()
        self.queue.clear()

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = os.path.join(SUMMARY_QUEUE_DIR, f"summary_batch__{timestamp}.jsonl")

        try:
            with open(filename, "w") as f:
                for entry in flushed:
                    f.write(json.dumps(entry) + "\n")
            print(f"📤 Flushed {len(flushed)} summaries → {filename}")
        except Exception as e:
            print(f"❌ Error while flushing summary queue to disk: {e}")

        if self.on_flush:
            try:
                self.on_flush(flushed)
            except Exception as e:
                print(f"⚠️  on_flush callback raised exception: {e}")

    def pending(self) -> int:
        """Returns the number of unflushed entries in the queue."""
        return len(self.queue)
