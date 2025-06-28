# 🧠 Crew Assistant: Local Multi-Agent AI Framework

## Overview

Crew Assistant is a local-first AI orchestration platform built with [CrewAI](https://github.com/joaomdmoura/crewAI) to manage complex task flows through structured agent collaboration. It leverages local large language models (LLMs) through [LM Studio](https://lmstudio.ai) and provides a foundation for a scalable, agentic operating system tailored for developers, entrepreneurs, and knowledge workers.

This repository represents a complete, running implementation of:

* ✅ End-to-end working CrewAI task pipeline
* ✅ Local model inference using `qwen/qwen3-32b` via LM Studio
* ✅ Multi-agent delegation with `Planner`, `Dev`, and `Commander` agents
* ✅ Secure `.env` configuration for LM Studio-compatible OpenAI API endpoints
* ✅ Shell compatibility with Fish and Python 3.13+ venv activation
* ✅ Internal recursive task delegation with live progress summaries

---

## 🧪 Example Use Case

**Educational Curriculum Designer**

* **Planner**: Breaks down the goal of building a CS curriculum into smaller subtasks
* **Dev**: Generates project-based learning modules in Python using web frameworks
* **Commander**: Reviews, critiques, and dynamically assigns deeper subtasks

All interactions occur via a local LLM API, ensuring privacy and offline capability.

---

## 🚀 Quickstart

Requires [UV](https://docs.astral.sh/uv/getting-started/installation/#creating-a-python-script)

```bash
# Clone the repo
git clone https://github.com/nocturnaltungsten/crew-assistant.git
cd crew-assistant

# Install dependencies
uv sync
./activate.sh  # Fish shell compatible activation

# Add your local LM Studio key
cp .env.example .env
# (Edit .env to include your API key and base URL)

# Default: CrewAI UX shell mode
python crew_agents.py

# Interactive model selection with compatibility checking
python crew_agents.py --select-model

# Full crew workflow
python crew_agents.py --crew
```

---

## 🤖 Architecture

```
crew-assistant/
├── agents/               # Agent definitions
│   ├── planner.py       # Task breakdown and planning
│   ├── dev.py           # Code implementation  
│   ├── commander.py     # Review and evaluation
│   └── ux.py            # User interaction and delegation
├── core/                 # Core engine
│   ├── agent_registry.py
│   └── context_engine/
│       ├── memory_store.py
│       ├── context_router.py
│       └── fact_store.py
├── utils/                # Utilities
│   ├── model_selector.py
│   ├── ux_shell.py
│   └── fact_learning.py
├── crew_agents.py        # Main entry point
├── deliverables/         # Crew workflow outputs
├── crew_runs/            # UX shell session logs
├── memory/               # Persistent memory
│   ├── memory_store/
│   └── archive/
└── pyproject.toml        # Dependencies
```

### Workflow Modes

**UX Shell Mode** (default): Single UX agent for conversational interaction with memory and fact learning.

**Crew Workflow Mode** (`--crew`): Interactive multi-agent workflow:
1. **UX Agent** handles user chat and determines task complexity
2. **Auto-delegation** to crew for complex tasks:
   - **Planner** breaks down requirements
   - **Dev** implements solutions  
   - **Commander** reviews and provides next steps
3. **Deliverables** saved to `deliverables/` directory
4. **Session logging** with full conversation history

---

## 🔐 Security & Privacy

* No cloud inference. All LLM calls happen through LM Studio on `localhost:1234`
* `.env` is gitignored and required for clean API key management
* No telemetry, no API calls beyond localhost

---

## 📜 License

MIT. Built for learning, not production-grade use (yet). Contributions and forks welcome.

---

## 🙏 Acknowledgments

Multi-shot vibe-coded by [@nocturnaltungsten](https://github.com/nocturnaltungsten), with near-zero dev skills or understanding. Guidance from local model assistance.

> This repo exists as a learning exercise and is entirely experimental. Not recommended for use, quality not guaranteed
