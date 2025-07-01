# Repository Directory Structure

## Overview

This document outlines the professional directory structure implemented for the Crew Assistant project.

## Root Structure

```
crew-assistant/
├── src/crew_assistant/          # Main application package
├── tests/                       # Complete testing suite
├── docs/                        # All documentation
├── run.py                       # Development convenience script
├── pyproject.toml              # Project configuration
├── README.md                   # Project overview
└── CLAUDE.md                   # Claude Code instructions
```

## Source Code (`src/crew_assistant/`)

```
src/crew_assistant/
├── __main__.py                 # CLI entry point
├── __init__.py                 # Package initialization
├── config.py                   # Configuration management
├── exceptions.py               # Custom exceptions
├── agents/                     # Agent implementations
│   ├── base.py                # Base agent classes
│   ├── ux.py                  # User experience agent
│   ├── planner.py             # Strategic planning agent
│   ├── dev.py                 # Development agent
│   ├── reviewer.py            # Quality validation agent
│   ├── commander.py           # Executive oversight agent
│   └── registry.py            # Agent factory and discovery
├── providers/                  # AI provider integrations
│   ├── base.py                # Provider base classes
│   ├── lmstudio.py            # LM Studio provider
│   ├── ollama.py              # Ollama provider
│   └── registry.py            # Provider registry and routing
├── core/                       # Core orchestration engine
│   ├── crew_engine.py         # Main orchestration logic
│   ├── agent_registry.py      # Agent management
│   └── context_engine/        # Memory and context management
│       ├── context_router.py  # Context routing logic
│       ├── fact_store.py      # Fact storage system
│       ├── memory_store.py    # Memory management
│       └── ...
├── workflows/                  # Workflow definitions
│   ├── base.py                # Workflow base classes
│   └── sequential.py          # Sequential workflow implementation
├── ui/                         # User interfaces
│   ├── shell.py               # Interactive shell
│   └── setup.py               # Provider setup interface
└── utils/                      # Utilities and helpers
    ├── model_selector.py      # Model selection utilities
    ├── testing_config.py      # Testing configuration
    └── ...
```

## Testing Structure (`tests/`)

```
tests/
├── unit/                       # Fast unit tests
│   ├── test_config.py         # Configuration tests
│   ├── test_context_router.py # Context routing tests
│   └── ...
├── integration/                # Component integration tests
│   ├── test_crew_workflow.py  # Workflow integration tests
│   ├── test_real_providers.py # Provider integration tests
│   └── ...
├── system/                     # End-to-end system tests
│   └── test_end_to_end.py     # Complete system tests
├── long_duration/              # Extended workflow testing
│   ├── long_duration_crew_test.py  # Comprehensive workflow tests
│   └── long_duration_test.py       # Extended testing scenarios
├── fixtures/                   # Test data and configuration
│   └── crew_test_tasks.py     # Test task definitions
├── logs/                       # Test execution logs
│   ├── crew_workflow_*/       # Workflow test logs
│   └── long_duration_*/       # Long duration test logs
├── run_crew_test_throttled.sh # Throttled test runner
└── run_throttled_test.sh      # Alternative test runner
```

## Documentation (`docs/`)

```
docs/
├── ARCHITECTURE.md             # System architecture documentation
├── API.md                      # API reference documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── ROADMAP.md                  # Project roadmap
├── TESTING_STATUS.md           # Current testing status
├── README_CREW_WORKFLOW_TEST.md # Workflow testing guide
└── README_LONG_DURATION_TEST.md # Long duration testing guide
```

## Running the Application

### Production Use
```bash
# Install and run as package
uv sync
uv run python -m crew_assistant

# Or use the convenience script
uv run python run.py
```

### Development Commands
```bash
# Run tests
uv run python -m pytest tests/ -v

# Run specific test categories
uv run python -m pytest -m unit        # Unit tests only
uv run python -m pytest -m integration # Integration tests
uv run python -m pytest -m system      # System tests

# Run long duration tests
python tests/long_duration/long_duration_crew_test.py 4

# Code quality
uv run ruff format .                    # Format code
uv run ruff check .                     # Check code quality
uv run mypy src/crew_assistant/         # Type checking
```

## Key Benefits of This Structure

1. **Professional Standards**: Follows Python packaging best practices
2. **Clear Separation**: Source code, tests, and docs are well organized
3. **Scalability**: Easy to add new components without clutter
4. **Testability**: Comprehensive testing structure with clear categories
5. **Documentation**: Centralized documentation for easy maintenance
6. **CLI Integration**: Proper package structure with console script entry point

## Import Patterns

- **Relative imports within package**: `from ..providers import BaseProvider`
- **External imports**: Standard absolute imports for third-party packages
- **Test imports**: `from src.crew_assistant.core import create_crew_engine`

This structure ensures the codebase is maintainable, professional, and ready for production deployment.