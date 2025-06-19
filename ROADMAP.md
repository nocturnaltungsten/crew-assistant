# Project Roadmap: Agentic Assistant System

## Phase 0 – Smoke Check

* ☑ Clarify philosophy: "Build an agent system to *teach CS through an engaging, useful project*."
* ☑ Clean environment (AutoGen nuked)
* ☑ Choose platform: **CrewAI**
* ☑ Identify constraints: must support **local LLM** (LM Studio preferred), offline execution, learnable structure

## Phase 1 – Groundwork

### 1.1. Architecture Plan

* Define system architecture:

  * Core agent loop
  * Multi-agent coordination
  * Context/Memory management
  * LLM abstraction layer (LM Studio bridge)
* Save in markdown and diagram form

### 1.2. Technology Inventory

* Document all:

  * Languages (Python 3.10+)
  * Runtimes (venv, poetry, Docker)
  * Agent frameworks (CrewAI)
  * Local LLM interface (LM Studio)
  * Embedding/RAG (LlamaIndex, Chroma optional)
  * Orchestration tools (AutoGen alt: CrewAI-native, LangGraph optional)
  * Dev tools: VSCode + recommended extensions

### 1.3. Documentation Aggregator

* Build script:

  * Accept list of GitHub repos, docs URLs
  * Crawl README, /docs, wiki, API refs
  * Save as local Markdown/HTML files for offline search
  * Optional: full-text embedding for LLM ingestion

## Phase 2 – Bootstrapping

### 2.1. Minimum Viable Crew

* Create 3-agent system:

  * **Commander** (you): issues objectives
  * **Planner Agent**: breaks tasks into subtasks
  * **Dev Agent**: executes subtasks with LLM
* Basic context sharing + persistence
* Output to local file/terminal

### 2.2. Dev Cycle Structure

* TDD where feasible
* Inline beginner-friendly CS commentary
* All scripts runnable with `python3 main.py`
* Automate:

  * Setup (bootstrap shell script)
  * Update (pull latest docs, models)

## Phase 3 – Context Engine & Intelligence

* Develop Context Engine:

  * Central JSON/SQLite store for:

    * prompt/task summaries
    * output logs
    * project state
  * Provide context to agents per cycle

## Phase 4 – Expand Capabilities

* Add:

  * RAG module (docs, filesystem)
  * Local voice/speech IO (optional)
  * Multimodal inputs (images/audio)
  * Secure file access & task execution

## Phase 5 – Final Polish

* Build .dmg GUI installer (as requested)
* Optionally split into MCP-compliant modules
* Export to reusable template repo

---

This document is to be stored as `ROADMAP.md` in the root of your project directory. All future development should reference it for alignment. Next step: the Tech Stack + Inventory doc.
