🧠 Core Language & Runtime

Python 3.10+ – Primary language

Poetry – Dependency + env manager (pyproject.toml) (use venv only for quick prototyping)

Fish Shell – Default scripting (Bash-compatible)

🧱 Base Architecture

CrewAI – Lightweight multi-agent orchestration

Task/goal loops with role-specific agents

Sequential or manager-delegation process types

ModelContextProtocol (MCP) – For future: composable distributed agent modules

LangGraph (optional) – For flow-based multi-agent DAGs

🤖 LLM Inference Layer

LM Studio (local default)

OpenAI-compatible server: http://localhost:1234/v1

Supports: Mistral, Dolphin, Codestral, DeepSeek, etc.

Ollama (fallback) – Simple model runner for low-config local deployment

Supported APIs (optional)

OpenAI

Claude (Anthropic)

Together.ai / Groq / DeepSeek

🧩 Embeddings + Retrieval (RAG)

LlamaIndex (modular setup)

llama-index-core

llama-index-readers-file

llama-index-embeddings-huggingface

Lite Store Options

JSON store (default)

SQLite (local memory prototype)

Chroma (for future clustering/semantic ops)

🛠 Developer Environment

Editor: VS Code

Extensions:

Python

Jupyter

Black Formatter

Privy (CrewAI GUI)

Terminal Stack:

starship – Prompt

atuin – Shell history

zoxide – Smart directory nav

📁 Project Utilities

Orchestration Scripts

make or just – Command aliases

dotenv – Config loading

Toolchain

jq, fd, ripgrep, httpie, graphviz

Snapshot System

Modular ZIP snapshot + part splitter

Smoke-break initiated .zip logging

📚 Documentation / Scraper

GitHub doc fetcher script:

Crawls /docs, README.md, etc. from listed URLs

Outputs .md for local review, .html for browser dump

Embed-ready output for RAG pipeline

Export format: .md, .json, .html, .pdf

🌐 API Adapters + Routing

OpenAI-compatible (LM Studio)

Future Expandable Hooks

Internal voice-to-text

File I/O

System commands (with agent permissions)

🧪 Optional Components (R&D Phase)

LangGraph (advanced agent DAG routing)

CrewAI Flows (logic-based reactive loops)

MCP Mesh (for edge/distributed extensions)

Langchain-style tools (as standalone subprocesses)

🔗 High-Value Links

CrewAI GitHub

CrewAI Examples

ModelContextProtocol SDK

LM Studio

Ollama

Anthropic – Effective Agents

CrewAI Crash Course

Datastax: Agents + Ollama

LangFlow (Visual DAG Builder)

Privy VS Code Tool

AG2.ai

