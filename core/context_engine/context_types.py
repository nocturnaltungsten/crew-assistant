from dataclasses import dataclass
from typing import Optional


@dataclass
class ContextEntry:
    """Single memory entry used by the context engine."""

    timestamp: str
    agent: str
    input_summary: str
    output_summary: str
    task_id: Optional[str] = None
