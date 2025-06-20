from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ContextEntry:
    timestamp: str
    agent: str
    input_summary: str
    output_summary: str
    task_id: Optional[str] = None