# API Reference

This document provides a comprehensive reference for the Crew Assistant APIs and interfaces.

## Agent System

### Agent Definition

All agents are built using the CrewAI framework and follow a consistent pattern:

```python
from crewai import Agent

agent_name = Agent(
    role='Role Name',
    goal='Agent-specific goal',
    backstory='Agent background/personality',
    allow_delegation=True,  # Whether agent can delegate tasks
    use_system_prompt=False,  # Whether to use system prompts
    verbose=True  # Enable verbose output
)
```

### Available Agents

#### UX Agent (`agents/ux.py`)
- **Role**: User Experience Agent
- **Purpose**: Primary interface for user interactions
- **Capabilities**: Chat interface, task complexity evaluation, delegation decisions
- **Delegation**: Enabled

#### Planner Agent (`agents/planner.py`)
- **Role**: Strategic Planner
- **Purpose**: Breaking down complex tasks into actionable subtasks
- **Capabilities**: Task decomposition, dependency analysis, planning
- **Delegation**: Enabled

#### Dev Agent (`agents/dev.py`)
- **Role**: Development Specialist
- **Purpose**: Technical implementation and code generation
- **Capabilities**: Code implementation, testing, technical analysis
- **Delegation**: Disabled

#### Reviewer Agent (`agents/reviewer.py`)
- **Role**: Quality Assessment Specialist
- **Purpose**: Comprehensive quality evaluation with numeric ratings
- **Capabilities**: 1-10 scale rating across 5 criteria (completeness, quality, clarity, feasibility, alignment)
- **Delegation**: Disabled
- **Output**: Structured numeric ratings for analytics (non-blocking)

### Agent Registry

#### Dynamic Discovery
```python
from core.agent_registry import discover_agents

agents = discover_agents()
# Returns: Dict[str, Agent] mapping role names to agent instances
```

#### Static Registry
```python
from agents import AGENT_REGISTRY

# Predefined agent mapping
AGENT_REGISTRY = {
    "UX": ux,
    "Planner": planner,
    "Developer": dev,
    "Reviewer": reviewer,
}
```

## Context Engine

### Memory Store

The memory store manages persistent conversation history.

```python
from core.context_engine.memory_store import MemoryStore

memory = MemoryStore()

# Save interaction
memory.save(
    agent="UX",
    input_summary="User asked about Python",
    output_summary="Explained Python basics",
    task_id="optional-task-id"
)

# Retrieve recent memories
recent = memory.recent(agent="UX", count=5)
# Returns: List[Dict] with timestamp, agent, summaries

# Load all memories
all_memories = memory.load_all()
```

### Fact Store

The fact store manages learned facts and knowledge.

```python
from core.context_engine.fact_store import FactStore

facts = FactStore()

# Store a fact
facts.set("user_name", "John Doe")
facts.set("favorite_language", "Python")

# Retrieve facts
name = facts.get("user_name")
all_facts = facts.all()

# Get formatted facts
facts_text = facts.as_text()
```

### Context Types

```python
from core.context_engine.context_types import ContextEntry
from dataclasses import dataclass
from typing import Optional

@dataclass
class ContextEntry:
    timestamp: str
    agent: str
    input_summary: str
    output_summary: str
    task_id: Optional[str] = None
```

### Context Injection

```python
from core.context_engine.inject_context import ContextInjector

injector = ContextInjector()

# Get context for an agent
context = injector.get_context(agent="UX", max_items=5)
# Returns formatted context string combining recent memories and facts
```

### Context Router

```python
from core.context_engine.context_router import RoutingAction, route_context_event

# Route a context event
action = route_context_event({
    "type": "user_input",
    "content": "Hello world",
    "agent": "UX"
})

# Actions: IGNORE, LOG, QUEUE_FOR_SUMMARY, EMBED
```

## Configuration System

### Settings Class

```python
from crew_assistant.config import Settings

settings = Settings()

# API Configuration
settings.openai_api_base  # "http://localhost:1234/v1"
settings.openai_api_key   # "not-needed-for-local"
settings.openai_api_model # "microsoft/phi-4-mini-reasoning"
settings.lm_timeout       # 60

# Storage Configuration
settings.memory_dir       # Path("memory/memory_store")
settings.facts_dir        # Path("memory/facts")
settings.snapshots_dir    # Path("snapshots")
settings.crew_runs_dir    # Path("crew_runs")

# Agent Configuration
settings.agent_verbose    # True
settings.max_memory_entries  # 1000
```

### Environment Variables

Configure via `.env` file:

```bash
# API Settings
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=not-needed-for-local
OPENAI_API_MODEL=your-model-name
LM_TIMEOUT=60

# Storage Settings
MEMORY_DIR=./memory/memory_store
FACTS_DIR=./memory/facts
MAX_MEMORY_ENTRIES=1000

# Agent Settings
AGENT_VERBOSE=true
```

## Utility Functions

### Model Selection

```python
from utils.model_selector import (
    get_available_models,
    test_model_compatibility,
    select_model
)

# Get available models
models = get_available_models()
# Returns: List[Dict[str, str]] with model info

# Test model compatibility
is_compatible, message = test_model_compatibility("model-name")

# Interactive model selection
selected_model = select_model()
```

### Fact Learning

```python
from utils.fact_learning import learn_fact_if_possible, build_memory_context

# Learn facts from text
fact_result = learn_fact_if_possible(
    "My name is John and I love Python programming"
)
# Returns: Dict with extracted facts

# Build context from memory
context = build_memory_context(
    memory_dir="memory/memory_store",
    limit=10
)
# Returns: Formatted context string
```

### UX Shell

```python
from utils.ux_shell import run_ux_shell

# Run interactive shell
run_ux_shell(raw_mode=False)
```

## Exception Handling

### Exception Hierarchy

```python
from crew_assistant.exceptions import (
    CrewAssistantError,
    ConfigurationError,
    ModelError,
    MemoryError,
    AgentError,
    TaskError,
    ContextError
)

try:
    # Risky operation
    result = some_operation()
except ConfigurationError as e:
    # Handle configuration issues
    logger.error(f"Configuration error: {e}")
except ModelError as e:
    # Handle model-related issues
    logger.error(f"Model error: {e}")
```

## Main Workflow Functions

### Core Workflow

```python
from crew_agents import (
    handle_user_input_with_ux,
    execute_crew_delegation,
    call_llm
)

# Handle user input with UX agent
response, should_delegate = handle_user_input_with_ux(
    user_input="Build a web scraper",
    memory=memory_store
)

# Execute crew delegation
if should_delegate:
    result = execute_crew_delegation(
        user_input="Build a web scraper",
        memory=memory_store,
        deliverables_dir="./deliverables"
    )

# Direct LLM call
response = call_llm("What is Python?")
```

## Extension Points

### Adding New Agents

1. Create new agent file in `agents/` directory:

```python
# agents/researcher.py
from crewai import Agent

researcher = Agent(
    role="Research Specialist",
    goal="Gather and analyze information from various sources",
    backstory="Expert researcher with strong analytical skills",
    allow_delegation=True,
    verbose=True
)
```

2. Agent will be automatically discovered by the registry

### Adding Tools to Agents

```python
from crewai.tools import tool

@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for information."""
    # Implementation
    return search_results

# Add to agent
agent = Agent(
    role="Researcher",
    goal="Research information",
    backstory="Research expert",
    tools=[web_search],  # Add tools here
    verbose=True
)
```

### Custom Context Strategies

```python
from core.context_engine.context_router import ContextRouter

class CustomContextRouter(ContextRouter):
    def route_context_event(self, event):
        # Custom routing logic
        if event.get("type") == "special_case":
            return RoutingAction.EMBED
        return super().route_context_event(event)
```

### Custom Storage Backends

```python
from core.context_engine.memory_store import MemoryStore

class DatabaseMemoryStore(MemoryStore):
    def __init__(self, db_path):
        self.db_path = db_path
        # Initialize database connection
    
    def save(self, agent, input_summary, output_summary, task_id=None):
        # Custom database save logic
        pass
    
    def recent(self, agent=None, count=5):
        # Custom database query logic
        pass
```

## Types and Interfaces

### Agent Interface

Agents must implement the CrewAI Agent interface:

```python
from crewai import Agent
from typing import List, Optional

class CustomAgent(Agent):
    role: str
    goal: str
    backstory: str
    tools: Optional[List] = None
    allow_delegation: bool = True
    verbose: bool = True
```

### Memory Interface

```python
from typing import List, Dict, Optional

class MemoryInterface:
    def save(self, agent: str, input_summary: str, 
             output_summary: str, task_id: Optional[str] = None) -> None:
        pass
    
    def recent(self, agent: Optional[str] = None, count: int = 5) -> List[Dict]:
        pass
    
    def load_all(self) -> List[Dict]:
        pass
```

### Context Interface

```python
from typing import Dict, Any

class ContextInterface:
    def get_context(self, agent: str = "UX", max_items: int = 5) -> str:
        pass
    
    def inject_context(self, prompt: str, agent: str) -> str:
        pass
```

## Error Handling Patterns

### Standard Error Handling

```python
from loguru import logger
from crew_assistant.exceptions import MemoryError

try:
    memory.save(agent="UX", input_summary="test", output_summary="test")
except MemoryError as e:
    logger.error(f"Memory operation failed: {e}")
    # Handle gracefully
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Validation Patterns

```python
from pydantic import BaseModel, validator

class TaskRequest(BaseModel):
    task_description: str
    agent: str
    priority: int = 1
    
    @validator('task_description')
    def validate_description(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Task description cannot be empty')
        return v
```

This API reference provides the foundation for understanding and extending the Crew Assistant system. For more detailed implementation examples, see the `examples/` directory.