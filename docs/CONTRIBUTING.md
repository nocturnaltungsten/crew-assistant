# Development Guidelines

This document provides guidelines for developing and maintaining the Crew Assistant project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) package manager
- [LM Studio](https://lmstudio.ai/) for local LLM inference
- Git

### Installation

1. **Install dependencies**:
   ```bash
   uv sync --group dev
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Verify installation**:
   ```bash
   python crew_agents.py --help
   ```

## Development Workflow

### Running Quality Checks

Before committing, run:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy crew_assistant/ core/ utils/ agents/

# Run tests
uv run pytest tests/ -v
```

## Code Standards

### Python Style Guide

- Follow PEP 8 with 100-character line length
- Use type hints for all function signatures
- Prefer f-strings for string formatting

### Type Hints

All new code must include type hints:

```python
from typing import List, Optional, Dict, Any

def process_memories(
    memories: List[Dict[str, Any]], 
    max_items: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Process and filter memories.
    
    Args:
        memories: List of memory dictionaries
        max_items: Maximum number of items to return
        
    Returns:
        Filtered list of memories
    """
    # Implementation
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> bool:
    """Short description of function.
    
    Longer description if needed, explaining the purpose
    and any important details about the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> complex_function("test", 42)
        True
    """
```

### Error Handling

- Use specific exceptions from `crew_assistant/exceptions.py`
- Always include helpful error messages
- Log errors appropriately using loguru

```python
from loguru import logger
from crew_assistant.exceptions import MemoryStoreError

try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise MemoryStoreError(f"Cannot process memory: {e}") from e
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/          # Test individual components
├── integration/   # Test component interactions
└── system/        # Test end-to-end workflows
```

### Writing Tests

1. **Use descriptive test names**:
   ```python
   def test_memory_store_saves_entry_with_timestamp():
       # not test_save()
   ```

2. **Follow AAA pattern**:
   ```python
   def test_fact_extraction():
       # Arrange
       extractor = FactExtractor()
       text = "Python was created by Guido van Rossum"
       
       # Act
       facts = extractor.extract(text)
       
       # Assert
       assert len(facts) == 1
       assert facts[0]["key"] == "Python creator"
   ```

3. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def memory_store(tmp_path):
       return MemoryStore(base_path=tmp_path)
   ```

4. **Mark test categories**:
   ```python
   @pytest.mark.unit
   def test_unit_functionality():
       pass
       
   @pytest.mark.integration
   @pytest.mark.slow
   def test_integration_scenario():
       pass
   ```

### Test Coverage

Run coverage report:
```bash
uv run pytest --cov=crew_assistant --cov-report=html
```

## Adding New Features

### Adding a New Agent

1. Create new file in `agents/` directory:
   ```python
   # agents/researcher.py
   from crewai import Agent
   
   researcher = Agent(
       role="Research Specialist",
       goal="Gather and analyze information",
       backstory="Expert in research and analysis",
       tools=[],  # Add relevant tools
       verbose=True,
       allow_delegation=True
   )
   ```

2. Agent will be automatically discovered by the registry

3. Add tests in `tests/unit/test_agents.py`

### Adding a New Tool

1. Implement tool following CrewAI interface:
   ```python
   from crewai.tools import tool
   
   @tool("search_web")
   def search_web(query: str) -> str:
       """Search the web for information."""
       # Implementation
   ```

2. Add to relevant agent's tool list

3. Write tests for the tool

### Adding Context Strategies

1. Extend `ContextRouter`:
   ```python
   class CustomContextRouter(ContextRouter):
       def route_context(self, agent_role: str) -> Dict:
           # Custom routing logic
   ```

2. Register in configuration

3. Test thoroughly

## Project Structure

```
crew-assistant/
├── agents/               # Agent definitions
│   ├── planner.py       # Task breakdown and planning
│   ├── dev.py           # Code implementation  
│   ├── commander.py     # Review and evaluation
│   └── ux.py            # User interaction and delegation
├── core/                # Core engine
│   ├── agent_registry.py
│   └── context_engine/
│       ├── memory_store.py
│       ├── context_router.py
│       └── fact_store.py
├── utils/               # Utilities
│   ├── model_selector.py
│   ├── ux_shell.py
│   └── fact_learning.py
├── tests/               # Test suite
├── crew_agents.py       # Main entry point
└── pyproject.toml       # Dependencies
```