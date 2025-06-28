from dataclasses import dataclass


@dataclass
class ContextEntry:
    timestamp: str
    agent: str
    input_summary: str
    output_summary: str
    task_id: str | None = None
