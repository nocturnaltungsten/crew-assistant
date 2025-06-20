# 🧠 System Architecture Audit — Crew Assistant

## ✅ Implemented

### Agents
- **Planner**: Decomposes goals into subtasks — operational
- **Dev**: Implements subtasks — operational
- **Commander**: Reviews outputs and assigns next steps — functional

### Core Modules
- `summary_queue.py` (✅): Buffers task outputs, flushes to JSONL batches
- `select_model.py` (✅): Allows dynamic switching of LLM backends
- `wrap_crew_run.py` (⚠️ Partially wired): Orchestrates crew runs (needs summary queue hook)
- `crew_agents.py` (✅): Agent instantiation + configuration
- `fetch_docs.py` (✅): Optional reader for local content/doc scraping

### Logs + Metadata
- `crew_runs/*.json`: CrewAI execution logs with task→agent→output mappings
- `sys_arch_audit.md`: This file, updated with module state
- `snapshots/`: Directory created (⚠️ unused; awaiting MemoryStore patch)
- `context_log.json`: High-level summaries of task I/O per cycle (used by context engine)

---

## ⚠️ Known Issues

| Module             | Issue                                                       | Status     |
|--------------------|-------------------------------------------------------------|------------|
| `MemoryStore`      | `.save()` method missing — causes fatal crash               | 🛠️ Blocking |
| `wrap_crew_run.py` | Not currently pushing task output into `SummaryQueue`       | 🧩 Missing  |
| `summary_queue.py` | No integration with downstream summarizer                   | 🔜 Deferred |
| `select_model.py`  | Not actively used in agent pipeline yet                     | ✅ Ready    |

---

## 🧩 On Deck (Next Subtasks)

| Task ID | Subtask                                    | Status    | Notes                                   |
|---------|---------------------------------------------|-----------|-----------------------------------------|
| T001    | Wire `SummaryQueue.add()` after each agent output | 🟡 Pending | Needs edit in `wrap_crew_run.py`       |
| T002    | Implement dummy `MemoryStore.save()`       | 🟡 Pending | Prevents run crash                      |
| T003    | Write flush processor: summarize `*.jsonl` batches | 🔜 Planned  | Enables long-term memory summary       |
| T004    | Hook `select_model.py` into agent startup  | 🔜 Planned  | For runtime model switching             |
| T005    | Snapshot per-agent task + output           | 🔜 Planned  | Store JSON dumps into `snapshots/` dir |

---
