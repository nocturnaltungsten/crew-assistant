# Technical Stack & Framework Inventory

## Core Language & Runtime

* **Python 3.10+**: primary language
* **Virtual Environment**: `venv` or `poetry`
* **Shell**: Fish/Bash (Mac-native)

## Local LLM Engine

* **LM Studio**

  * Models: Mistral, Dolphin, Codestral, etc.
  * OpenAI-compatible API
  * URL: `http://localhost:1234/v1/chat/completions`

## Agent Framework

* **CrewAI**

  * Multi-agent orchestration
  * Planning, memory, and execution loops
  * Human-in-the-loop support

## Optional Agentic Layer

* **LangGraph** (for DAG-like agent workflows)
* **ModelContextProtocol (MCP)** for modular/edge distributed systems

## Task Memory + RAG

* **LlamaIndex (modular)**

  * `llama-index-core`
  * `llama-index-readers-file`
  * `llama-index-embeddings-huggingface`
* **Chroma** (or lightweight JSON/SQLite fallback)

## CLI + Orchestration

* `make` or `Justfile` for task scripting
* `dotenv` or native Mac keychain for secrets

## Developer Tooling

* **VSCode**

  * Extensions:

    * Python
    * Jupyter
    * Black Formatter
    * Privy (agent control panel)
* **Terminal tools**:

  * `starship`, `atuin`, `zoxide`

## Utilities

* `jq`, `curl`, `httpie`, `fd`, `ripgrep`
* `graphviz` for flowcharts/architecture diagrams

## Docs & Search Aggregation

* GitHub README + `/docs` scraper
* Optional: Embed for local semantic search
* Output formats: `.md`, `.pdf`, `.json`, `.html`

## APIs & Endpoints

* OpenAI-style interface via LM Studio
* Optional hooks for:

  * Claude (Anthropic)
  * Ollama local fallback
  * File I/O (read/write/exec)



# Manual link dump

https://lmstudio.ai/docs/app/api/tools

https://github.com/crewAIInc/crewAI
https://github.com/Fosowl/agenticSeek
Anthropic – Building Effective Agents blog: https://www.anthropic.com/engineering/building-effective-agents

Anthropic – Extended Thinking with Claude: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

Privy VSCode Extension – AI Agent Dev Tools: https://marketplace.visualstudio.com/items?itemName=privy.privy-vscode

Crew AI Crash Course (step‑by‑step): https://alejandro-ao.com/crew-ai-crash-course-step-by-step/

CrewAI Examples Repository: https://github.com/crewAIInc/crewAI-examples/tree/main

Datastax – Local AI with Ollama + Agents: https://datastax.medium.com/unlocking-local-ai-using-ollama-with-agents-34604790e55b

Datastax – LangFlow for Local AI Flow: https://www.datastax.com/products/langflow?utm_medium=byline&utm_campaign=local-ai-using-ollama-with-agents&utm_source=medium

Ollama-and-Agents (premthomas): https://github.com/premthomas/Ollama-and-Agents

CrewAI for local agents with Ollama (tutorial): https://medium.com/@indradumnabanerjee/crewai-for-local-ai-agents-with-ollama-a-hands-on-tutorial-for-local-ai-agents-a59b6ba32fd1

Analytics Vidhya – Build Multi‑Agent System: https://www.analyticsvidhya.com/blog/2024/09/build-multi-agent-system/

Reddit – CrewAI “confused between MCP server and crewAI”: https://www.reddit.com/r/crewai/comments/1kp9w3d/confused_between_mcp_server_and_crewai_when_to/

LinkedIn – CrewAI, MCP & Distributed Intelligence: https://www.linkedin.com/pulse/crewai-mcp-new-era-distributed-intelligence-edge-rob-olson-fgxcc

Medium – Refactoring CrewAI App to MCP: https://medium.com/@manavg/refactoring-a-crewai-app-to-mcp-a-journey-to-modular-agentic-systems-4e0e6df47ea0

ModelContextProtocol Quickstart (client/server + SDK):

Client: https://modelcontextprotocol.io/quickstart/client#building-mcp-clients

Server: https://modelcontextprotocol.io/quickstart/server

Python SDK: https://github.com/modelcontextprotocol/python-sdk

AG2.ai – Multi‑Agent Platform: https://ag2.ai/

🔍 Additional High-Value References
Ollama (local LLM host): https://ollama.ai/

LM Studio (local LLM GUI): https://lmstudio.ai/

CrewAI MCP Architecture Overview: (Add specific blog or repo link if found)

Anthropic Developer Docs: https://docs.anthropic.com/

ModelContextProtocol (official): https://modelcontextprotocol.io/



---

This document should be saved as `TECH_STACK.md` in the root project directory and updated as new tools/modules are added. All docs aggregation scripts will reference this list to determine scrape targets.
