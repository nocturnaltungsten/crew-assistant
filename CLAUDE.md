# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Dependency Management
- Install dependencies: `uv sync`
- Activate environment: `./activate.sh` (shell script for Fish compatibility)

### Running the Application
- Main entry point: `python crew_agents.py`
- UX shell mode: `python crew_agents.py --ux`
- Interactive model selection: `python crew_agents.py --select-model`
- Raw UX output: `python crew_agents.py --ux --raw`

### Testing
- Run all tests: `python -m unittest discover`
- Run specific test: `python -m unittest tests/test_agents.py`

### Code Quality
- Lint code: `ruff check` (available via dev dependencies)
- Type check: `mypy` (available via dev dependencies)

## Architecture Overview

This is a **CrewAI-based multi-agent AI framework** that orchestrates task delegation between specialized agents using local LLMs through LM Studio.

### Core Components

#### Agent System (`agents/`)
- **Planner**: Strategic task breakdown agent (`agents/planner.py`)
- **Dev**: Implementation-focused agent (`agents/dev.py`) 
- **Commander**: Evaluation and critique agent (`agents/commander.py`)
- **Agent Registry**: Dynamic agent discovery system (`core/agent_registry.py`)

#### Context Engine (`core/context_engine/`)
- **Memory Store**: Persistent memory with JSON file storage (`memory_store.py`)
- **Context Router**: Event routing and filtering logic (`context_router.py`)
- **Fact Store & Summary Queue**: Context processing components

#### Crew Orchestration
- `crew_agents.py`: Main orchestration script with CLI options and task flow
- `utils/`: Utility modules extracted from experimental features
  - `model_selector.py`: Interactive LM Studio model selection
  - `ux_shell.py`: Conversational UX interface with memory integration
  - `fact_learning.py`: Regex-based fact extraction and memory context building

### Key Architectural Patterns

1. **Local-First AI**: All LLM calls go through LM Studio at `localhost:1234/v1`
2. **Memory Persistence**: Each agent interaction is logged to `memory/memory_store/` as timestamped JSON files
3. **Task Chaining**: Sequential task execution with agent delegation (Planner → Dev → Commander)
4. **Dynamic Agent Discovery**: Runtime detection of agents via reflection on `agents/` directory
5. **Snapshot Logging**: Full crew run results saved to `snapshots/` directory

### Environment Configuration

- Uses `.env` file for LM Studio API configuration
- Default model: `microsoft/phi-4-mini-reasoning` (configurable via `OPENAI_API_MODEL`)
- Expects LM Studio running on `http://localhost:1234/v1`

### Memory System

The context engine maintains persistent memory across runs:
- Individual agent memories stored as JSON files with timestamps
- Context routing filters trivial events and queues long content for summarization
- Memory retrieval supports agent-specific and recent entry queries