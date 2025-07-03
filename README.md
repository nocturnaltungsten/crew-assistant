# 🧠 Crew Assistant: Experimental Multi-Agent Hobby Project v0.3.1

## ⚠️ Reality Check

**This is a hobby project**, not production software. It's an experimental attempt at building a multi-agent system that sometimes works when configured correctly. The code quality is amateur-level with many shortcuts, poor error handling, and questionable design decisions.

**What This Actually Is:**
* 🧑‍💻 **Hobby Experiment** - Weekend project quality code
* 🔧 **Basic LLM Integration** - Minimal error handling, fails often
* 🤖 **4-Agent Pipeline** - Sequential execution that sometimes completes
* 🏠 **Local LLM Support** - Works with LM Studio/Ollama (when they're running)
* 📊 **Number Ratings** - Replaced binary validation with 1-10 scores (untested)
* ⏱️ **Slow Performance** - 2-3 minutes per task (when it works)
* 🛠️ **Basic Tool Calling** - File operations only (experimental)

---

## 🎯 Agent Architecture

**Core 4-Agent System:**

* **🎨 UX Agent**: User experience specialist and interaction coordinator
* **📋 Planner Agent**: Strategic planning and task breakdown 
* **💻 Developer Agent**: Implementation and coding specialist with tool execution capabilities
* **🔍 Reviewer Agent**: Non-blocking quality assessment with numeric ratings (1-10 scale)

**Workflow Pattern:**
```
User Request → UX Analysis → Planning → Development (with Tools) → Quality Assessment (Non-blocking) → Delivery
```

**Tool Calling System (v0.3.1):**
- **Action-Oriented**: Agents execute actions immediately without seeking permission
- **Robust Parser**: Handles 8+ response formats (JSON, XML, function calls, natural language)
- **File Operations**: Safe read/write/list operations with validation
- **Extensible Framework**: Easy to add new tools through registry pattern
- **Error Recovery**: Graceful handling of malformed tool calls

**Numeric Rating Hack (v0.3.0):**
- **Always Completes**: Removed blocking validation (quality not guaranteed)
- **Completeness**: Random 1-10 score
- **Quality**: Another 1-10 score
- **Clarity**: Yet another 1-10 score
- **Feasibility**: More arbitrary numbers
- **Alignment**: Final random score
- **"Analytics"**: Saves JSON files to disk (no actual analysis)

---

## 🚀 Quick Start

### Prerequisites
- [UV Package Manager](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.11+
- [LM Studio](https://lmstudio.ai) or [Ollama](https://ollama.ai) running locally

### Installation
```bash
# Clone and setup
git clone https://github.com/nocturnaltungsten/crew-assistant.git
cd crew-assistant

# Install dependencies
uv sync

# Run interactive setup
uv run python run.py --setup

# Start the enhanced UX shell
uv run python run.py
```

### First Run
The system will automatically:
1. Detect available providers (LM Studio/Ollama)
2. List compatible models
3. Test your selected model
4. Launch the interactive shell

---

## 🛠️ Usage Modes

### Interactive Shell (Default)
```bash
uv run python run.py
```
Smart UX agent handles conversations and delegates complex tasks to the crew.

### Direct Crew Execution
```bash
uv run python run.py --crew "Build a web API for user management"
```
Bypass UX and run tasks directly through the full agent pipeline.

### Provider Setup
```bash
uv run python run.py --setup
```
Interactive provider and model configuration.

---

## 🚀 v0.3.0 Breakthrough: Revolutionary Numeric Ratings

**The Problem**: Traditional validation systems create binary ACCEPT/REJECT decisions that block workflow progress, leading to user frustration and failed tasks.

**The Solution**: Our revolutionary numeric ratings system provides comprehensive quality assessment without ever blocking workflow completion.

### Key Benefits:
- **100% Workflow Completion**: Every task completes successfully with quality insights
- **Rich Analytics**: 5-criteria assessment provides actionable improvement data
- **Non-Blocking Design**: Quality evaluation enhances rather than gates progress
- **Data-Driven Optimization**: Continuous improvement based on quality trends

### How It Works:
1. Tasks flow through all agents without interruption
2. Reviewer provides numeric ratings (1-10) across 5 criteria
3. Workflow always completes with deliverable + quality data
4. Analytics enable continuous system improvement

This breakthrough transforms multi-agent orchestration from a gatekeeping system to an insights-driven platform.

---

## 🏗️ Architecture

### Provider System
**Production-grade AI provider abstraction:**
- **Circuit Breakers**: Automatic failover and recovery
- **Connection Pooling**: Optimized for long conversations  
- **Intelligent Caching**: Response caching with TTL
- **Health Monitoring**: Real-time provider status
- **Load Balancing**: Optimal provider selection

### Memory Engine
**Persistent context management:**
- Session-based memory storage
- Fact learning and retrieval
- Context injection and routing
- Memory rotation and archival

### Workflow Engine
**Native orchestration system:**
- Sequential workflow execution
- Numeric quality assessment (no blocking)
- Task routing and delegation
- Execution context management
- Real-time quality analytics collection

---

## 📁 Project Structure

```
crew-assistant/
├── src/
│   └── crew_assistant/     # Main package
│       ├── agents/         # Native agent implementations
│       │   ├── base.py     # Base agent classes
│       │   ├── ux.py       # User experience agent
│       │   ├── planner.py  # Strategic planning agent
│       │   ├── dev.py      # Development agent
│       │   ├── reviewer.py # Quality validation agent
│       │   └── registry.py # Agent discovery and factory
│       ├── providers/      # AI provider integrations
│       │   ├── base.py     # Provider base classes
│       │   ├── lmstudio.py # LM Studio provider
│       │   ├── ollama.py   # Ollama provider
│       │   └── registry.py # Provider registry and routing
│       ├── core/           # Core orchestration engine
│       │   ├── crew_engine.py  # Main orchestration logic
│       │   └── context_engine/ # Memory and context management
│       ├── workflows/      # Workflow definitions
│       │   ├── base.py     # Workflow base classes
│       │   └── sequential.py   # Sequential workflow implementation
│       ├── ui/             # User interfaces
│       │   ├── shell.py    # Interactive shell
│       │   └── setup.py    # Provider setup interface
│       └── utils/          # Utilities and helpers
├── tests/                  # Comprehensive test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── system/            # End-to-end tests
│   └── long_duration/     # Performance and stress tests
├── run.py                  # Main entry point
└── pyproject.toml         # Project configuration
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Provider Configuration
AI_PROVIDER=lmstudio                    # or 'ollama'
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_MODEL=your-model-name

# Performance Settings
LM_TIMEOUT=60                           # Request timeout (seconds)
```

### Provider Settings
The system automatically detects and configures:
- **LM Studio**: `http://localhost:1234/v1` (default)
- **Ollama**: `http://localhost:11434/v1`

---

## 🚦 Performance

**Rough Numbers** (when it works):
- **Model Detection**: 15-500ms (varies)
- **Provider Response**: Usually fast (unless it fails)
- **Agent Execution**: 15-60s per agent (unpredictable)
- **Memory Operations**: Just file I/O
- **Concurrent Tasks**: Don't even try (not thread-safe)

---

## 🧪 Testing

```bash
# Run full test suite
uv run python -m pytest tests/ -v --cov=crew_assistant --cov-report=term-missing

# Run specific test categories
uv run python -m pytest -m unit        # Unit tests
uv run python -m pytest -m integration # Integration tests
uv run python -m pytest -m system      # System tests

# Performance benchmarks
uv run python -m pytest tests/integration/test_battle_providers.py -v
```

---

## 🧪 Testing

### Test Suite
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test categories
uv run python -m pytest tests/unit/        # Unit tests
uv run python -m pytest tests/integration/ # Integration tests  
uv run python -m pytest tests/system/      # End-to-end tests

# Run with coverage
uv run python -m pytest tests/ -v --cov=crew_assistant --cov-report=term-missing
```

### Long-Duration Testing
```bash
# These might work if you're lucky
python tests/long_duration/long_duration_crew_test.py 0.5
python tests/long_duration/long_duration_crew_test.py 4

# Hacky throttling script
bash run_crew_test_throttled.sh 6
```

**Test Framework Reality:**
- 139 tasks of varying quality
- Logs JSON files (no analysis tools)
- Numbers saved to disk
- "Performance benchmarking" = timestamps

---

## 📊 Performance (Highly Variable)

### Agent Times (When They Work)
- **UX Agent**: 10-30 seconds
- **Planner Agent**: 15-40 seconds
- **Developer Agent**: 20-60 seconds
- **Reviewer Agent**: 15-30 seconds
- **End-to-End**: 2-5 minutes (or timeout)

### "Quality" Metrics
- **Completion Rate**: 100% (but output quality varies wildly)
- **Quality Scores**: Random 1-10 numbers
- **Provider Reliability**: Works until it doesn't

### Resource Usage
- **Memory**: Who knows? Never profiled
- **CPU**: Single-threaded, blocks everything
- **Network**: Talks to local LLMs

---

## 🔄 Development Workflow

### Code Quality
```bash
# Format code
uv run ruff format .

# Check code quality
uv run ruff check .

# Type checking
uv run mypy src/crew_assistant/
```

### Adding Agents
1. Extend `BaseAgent` in `agents/`
2. Register in `agents/registry.py`
3. Add tests in `tests/unit/`

### Adding Providers
1. Extend `BaseProvider` in `providers/`
2. Register in `providers/registry.py`
3. Add integration tests

---

## 🤝 Contributing

Honestly, this codebase needs a complete rewrite. But if you want to contribute:

1. Lower your expectations
2. Fork the repository
3. Try not to make it worse
4. Add tests (they probably won't pass)
5. Submit a PR and hope for the best

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Local AI Providers**: [LM Studio](https://lmstudio.ai), [Ollama](https://ollama.ai)
- **Core Dependencies**: [Pydantic](https://pydantic.dev), [Loguru](https://loguru.readthedocs.io)
- **Development Tools**: [UV](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/), [Pytest](https://pytest.org)

---

## ⚠️ Known Issues

### Major Problems
- **No Real Error Handling**: Lots of `except Exception: pass`
- **Thread Safety**: Don't even think about concurrent execution
- **Memory Leaks**: Caches grow forever
- **Test Coverage**: Many tests fail without exact setup
- **Performance**: Wildly unpredictable execution times
- **Code Quality**: Amateur hour with lots of hacks

### What Barely Works
- Basic LLM integration (when providers are running)
- Sequential agent execution (sometimes)
- File operations (with minimal validation)
- JSON logging (no analysis tools)

### What Doesn't Work
- Proper error recovery
- Concurrent execution
- Real quality assessment
- Analytics (just saves files)
- Production deployment (don't even try)

---

## 📄 Version History

### v0.3.1 (2025-07-02) - Tool Calling Hack
- Added basic file operations (read/write/list)
- "Robust" parser (handles some malformed JSON)
- Agents sometimes take actions
- Fixed some MyPy errors

### v0.3.0 (2025-07-01) - Numeric Ratings Hack  
- Replaced binary validation with 1-10 numbers
- Everything completes now (quality not guaranteed)
- Removed CrewAI dependency
- Added JSON logging

### v0.1.0 - Original CrewAI Wrapper
- Basic CrewAI integration
- Worked sometimes

---

**Project Status**: 🤷 **Experimental Hobby Project** - Use at your own risk. This is not production software.