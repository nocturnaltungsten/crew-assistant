# Experimental Features Audit

This document captures the purpose and functionality of experimental files before cleanup.

## File Analysis

### `/crew_assistant/crew_agents.py`
**Purpose**: Simplified dynamic agent discovery approach
- Uses `core.agent_registry.discover_agents()` for runtime agent detection
- Cleaner, more minimal than root version (39 lines vs 138 lines)
- Same task flow but without memory persistence or detailed logging
- **Decision**: Root version is more feature-complete, remove this

### `/crew_assistant/wrap_crew_run.py`
**Purpose**: CLI wrapper with UX mode and model selection
- **Key Features**:
  - Interactive UX shell mode (`--ux` flag)
  - Dynamic model selection from LM Studio API
  - Conversation logging to `crew_runs/`
  - Plain English responses (no markdown formatting)
  - Subprocess delegation to main crew_agents.py
- **Value**: UX shell interaction and model selection are useful features
- **Decision**: Extract model selection utility, consider integrating UX mode

### `/crew_assistant/ux_loop.py`
**Purpose**: Conversational AI with fact learning and memory context
- **Key Features**:
  - Persistent fact learning via regex patterns (names, preferences)
  - Memory context injection (last 10 interactions)
  - Session logging with chat history
  - Fact storage integration
- **Value**: Fact learning and conversational memory are advanced features
- **Decision**: Preserve fact learning patterns, memory context injection

### `/crew_assistant/select_model.py`
**Purpose**: Dynamic model selection utility
- Queries LM Studio `/models` endpoint
- Interactive CLI model picker
- Environment variable management
- **Decision**: Useful utility, preserve as standalone function

### `/crew_assistant/test_context.py`  
**Purpose**: Context engine testing
- File appears to be empty in current state
- Likely was used for context system development
- **Decision**: Remove (empty file)

### `/crew_assistant/main.py`
**Purpose**: Unknown (empty file)
- **Decision**: Remove

## Valuable Features to Preserve

1. **Model Selection**: Dynamic LM Studio model picker
2. **UX Shell Mode**: Interactive conversational interface
3. **Fact Learning**: Regex-based fact extraction and storage
4. **Memory Context**: Injection of recent interactions into prompts
5. **Session Logging**: Structured chat session persistence

## Cleanup Strategy

1. Keep root `/crew_agents.py` as canonical entry point
2. Extract useful utilities (model selection, fact learning patterns)
3. Consider adding UX mode as optional flag to main entry point
4. Remove duplicate/empty files
5. Clean up accumulated memory files
6. Remove downloaded external documentation