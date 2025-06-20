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
. .venv/bin/activate.fish  # for Fish shell

# Add your local LM Studio key
cp .env.example .env
# (Edit .env to include your API key and base URL)

# Run the main crew
python crew_agents.py
```

---

## 🤖 Architecture

```
crew-assistant/
├── agents/
│   ├── planner.py
│   ├── dev.py
│   └── commander.py
├── tasks/
│   └── curriculum_task.py
├── crew_agents.py        # Entrypoint script
├── .env                  # API config (excluded from repo)
├── requirements.txt      # Python dependencies
```

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

Multi-shot vibe-coded by [@nocturnaltungsten](https://github.com/nocturnaltungsten), with near-zero dev skills or understanding. Guidance from ChatGPT.

> This repo exists as a learning exercise and is entirely experimental. Not recommended for use, quality not guaranteed
