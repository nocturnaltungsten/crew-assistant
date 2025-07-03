# === FILE: core/context_engine/inject_context.py ===

from .fact_store import FactStore
from .memory_store import MemoryStore


class ContextInjector:
    def __init__(
        self, memory: MemoryStore | None = None, factstore: FactStore | None = None
    ) -> None:
        self.memory = memory or MemoryStore()
        self.facts = factstore or FactStore()

    def get_context(self, agent: str = "UX", max_items: int = 5) -> str:
        """
        Build a context block containing recent memory and known facts.
        """
        recent = self.memory.recent(agent=agent, count=max_items)

        context_lines = ["Here is your latest memory:"]

        for item in recent:
            input_summary = item.get("input_summary", "").strip()
            output_summary = item.get("output_summary", "").strip()

            line = f"[{agent}] {input_summary}: {output_summary}"
            context_lines.append(line)

        fact_block = self.facts.as_text()
        if fact_block:
            context_lines.append("\nCurrent known facts:")
            context_lines.append(fact_block)

        return "\n".join(context_lines)
