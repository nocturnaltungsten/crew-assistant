# 🛣️ Project ROADMAP: CrewAI-Based Local Assistant

## 🧭 Core Philosophy & Goals

> **"Build an AI system that teaches CS through a useful, modular, and extensible project."**

- ⚙️ Use agentic workflows to mirror real-world system design
- 🧠 Teach coding, architecture, and AI via real project structure
- 🔐 Run *entirely locally* using LM Studio or similar LLM host
- 🪞 Maintain prompt transparency, agent introspectability, and traceable memory

---

## ✅ Phase 0 – Smoke Check & Ground Rules

- ☑ Platform selected: **CrewAI** (with optional LangGraph/MCP)
- ☑ SOPs written: snapshot tools, `.gitignore`, modular file structure
- ☑ Tech inventory documented (`TECH_STACK.md`)
- ☑ GitHub repo deployed: [`crew-assistant`](https://github.com/nocturnaltungsten/crew-assistant)

---

## 🔧 Phase 1 – Groundwork

### 1.1. Minimum Viable Crew
- ☑ `Commander`: human UX interface (chat, CLI, future GUI)
- ☑ `PlannerAgent`: breaks goals into subtasks
- ☑ `DevAgent`: executes subtasks and returns results
- ☑ Core context engine prototype functional

### 1.2. File Structure & Dev Ergonomics
- ☑ `/agents/`, `/tasks/`, `/core/`, `/snapshots/`
- ☑ `.gitignore` ignores local-only tools like `fetch_docs.py`
- ☑ Fish shell tools and snapshot automation in place

### 1.3. Docs & Knowledge Aggregator (Local)
- ☑ Manual fetch tool for scraping docs/READMEs into `/docs/`
- ⏳ Optional embed & search via LlamaIndex (future)

---

## 🧠 Phase 2 – Context Engine & Memory Core

### 2.1. Core Memory Store (MVP)
- ☑ Input/output summaries stored to JSON file
- ☑ Logging agent, task, timestamp, prompt/output
- ⏳ Validate persistence across sessions
- ⏳ Add per-task summaries + agent metadata

### 2.2. Context Injection
- ⏳ Feed memory summaries into next agent prompt
- ⏳ Filter based on task relevance and agent

---

## 🧱 Phase 3 – Modular Scalability Foundation

### 3.1. Inference Manager
- ⏳ Central gatekeeper controls LLM access
- ⏳ Priority system: `urgency * importance`
- ⏳ Light-weight model for UX agent = always first
- ⏳ Task queue with async inference routing

### 3.2. Agent/Team-Specific Memory
- ⏳ Add vector stores per agent/team
- ⏳ Knowledge scraping agents for docs, APIs, tools
- ⏳ Agents return relevance scores per chunk to improve search

### 3.3. Prompt Observability & Control
- ⏳ Agent config files in `/configs/agent_prompts/`
- ⏳ Template override & versioning
- ⏳ Logging of prompt + final output for audit/debug

---

## 🚀 Phase 4 – Expansion & UX Polish

### 4.1. Multimodal Input
- ⏳ Audio, image, and file processing agents
- ⏳ Transcription (Whisper), vision (local CLIP, etc.)

### 4.2. Task Execution Agents
- ⏳ File I/O, subprocess, shell runners
- ⏳ Guardrails for safety (e.g. sandbox execution)

### 4.3. Interactive UX Layer
- ⏳ Web dashboard or `.app` GUI
- ⏳ Drag-and-drop .dmg installer
- ⏳ Real-time log viewer + memory browser

---

## 📦 Phase 5 – Template & Reusability

- ⏳ Split into reusable agentic assistant template repo
- ⏳ Add examples for other domains (data analysis, writing tutor)
- ⏳ Document for onboarding new devs/contributors

---

## 📍Next Tasks

| Task | Status |
|------|--------|
| `.gitignore` cleanup | ✅ |
| Snapshot tooling | ✅ |
| Modular memory store | ✅ MVP |
| Prioritized inference manager | ⏳ |
| Agent memory router | ⏳ |
| Prompt config + override system | ⏳ |
| Feed memory into agents | ⏳ |

---

> 💡 **Reminder**: This roadmap evolves. Each phase expands capabilities **without breaking ergonomics or stability.**

---

