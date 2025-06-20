# 🧠 CrewAI System Architecture Audit & Modularity Review

## 🔍 Smoke Break: Philosophy & SOP Check
- **Primary Objective**: Build an autonomous agent system capable of performing complex, multi-stage tasks with minimal supervision. The "teach CS through a project" mission is a use-case of the system, not its core objective.
- **Core Principle**: Never scale a mistake. Each feature must align with long-term goals before implementation.
- **Engineering Values**: Modularity, transparency, traceability, testability, and ergonomics for both user and developer.

---

## 🧱 Current Core System Architecture

### 🧩 Modules
- `agents/`: agent definitions and agent runners
- `tasks/`: task generators and planners
- `core/context_engine/`: memory store, context router, and summary queue (modularized)
- `wrap_crew_run.py`: agent run wrapper with model selection and snapshotting
- `crew_agents.py`: orchestrates agent runs
- `fetch_docs.py`: local-only dev tooling (ignored in Git)

### 🔄 Core Loop
1. User (Commander) inputs high-level objective
2. Planner breaks into subtasks
3. DevAgent (and others) execute subtasks
4. Outputs are written to memory store
5. Router dispatches context to appropriate queues
6. SummaryQueue triages and queues items for LLM summarization
7. Summaries are committed to memory store
8. Next cycle begins with updated context

---

## 🛠 Audit: Support for Future Features

### A) 🔁 **Resource Prioritization & LLM Inference Throttling**
**Goal**: Implement a dynamic, task-aware prioritization system for LLM requests.

**Requirements:**
- Central gatekeeper for LLM access
- Task/Agent priority matrix (urgency * importance)
- Agent-side urgency overrides (for critical-path ops)
- Light model always gets front-of-line access for UX
- Modular backend capable of:
  - Queueing inference requests
  - Evaluating current load / model availability
  - Routing tasks intelligently

**Architecture Support (✅ / ⚠️ / ❌):**
- Modular memory storage: ✅
- Agent metadata routing: ⚠️ (needs abstraction layer)
- Inference broker logic: ❌
- Async/queue-ready request model: ❌

**Action**: Add `inference_manager.py` skeleton with task prioritization queue (future).

---

### B) 🧠 **Modular Agent Memory & Search System**
**Goal**: Agent- or team-specific vector databases with full knowledge scraping and semantic retrieval.

**Requirements:**
- Vector store per agent/team
- Embedding strategy abstraction layer
- Context engine decides what gets embedded & where
- Doc scraper/indexer agent
- Hybrid keyword+semantic search

**Architecture Support:**
- LlamaIndex integration: ✅
- Custom vector routing: ⚠️ (requires indexing abstraction)
- Scalable doc ingestion: ⚠️ (fetch_docs script exists)
- Separate stores per team: ❌ (needs orchestration)

**Action**: Plan for `knowledge_manager.py` or `agent_memory_router.py`

---

### C) 🧾 **Prompt Observability & Agent Control**
**Goal**: Full prompt visibility, version control, and override capability for each agent

**Requirements:**
- Config files or override UIs per agent
- Prompt templates stored, editable, documented
- Central audit log of messages (debug + review)

**Architecture Support:**
- Hardcoded agents: ⚠️ (minimal customization)
- Prompt template storage: ❌
- Logging via context engine: ✅ (WIP)

**Action**: Add `/configs/agent_prompts/` and logging decorator

---

### D) 📬 **Context Engine with Smart Queueing (New)**
**Goal**: Modular pipeline to filter, triage, and summarize relevant context before LLM use.

**Modules Deployed:**
- `memory_store.py`: persistent memory with JSON log backend ✅
- `context_router.py`: triage and dispatch context to summary queues ✅
- `summary_queue.py`: staging buffer for incoming context prior to summarization ✅

**Key Features:**
- Summary queue accepts structured memory entries
- Only relevant or unsummarized items sent to LLM
- Can be extended to support prioritization, deduplication, TTL expiration
- All modules lightweight and agent-agnostic

**Next Up:**
- `summary_runner.py`: process queue and generate summaries ✅
- Integrate summary_runner into `wrap_crew_run.py` ✅
- Trigger LLM summarization only when needed ✅

---

## 🧭 Updated ROADMAP Sneak Peek (for regen)

**NEW PHASE: Architecture Scalability Foundation**
- ✅ Add modular context engine w/ router and summary queue
- ✅ Build `summary_runner.py` to finalize context summarization pipeline
- 🔜 Build Inference Manager: prioritize LLM access
- 🔜 Modular Memory: add agent/team-specific vector stores
- 🔜 PromptControl Module: configure & audit agent prompts

### 🔁 Recap
| Feature | Supported Now? | Action |
|--------|----------------|--------|
| Inference Prioritization | ❌ | Scaffold inference_manager.py |
| Agent-Specific Memory | ⚠️ | Build modular memory router |
| Prompt Observability | ⚠️ | Config & log audit tooling |
| Context Engine (router + queue) | ✅ | Integrated into full loop |
| SummaryRunner | ✅ | Live and working |

**Next Step:** Evaluate context log growth and identify scaling thresholds. Begin modularizing long-term memory system and LLM load-balancing logic.
