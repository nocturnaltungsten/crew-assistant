# Project Integration Plan

## Current State

### 🚀 **Crew Project** (`feature/tool-integration` branch)
**Location**: `/Users/ahughes/dev/crew` (main development)
**Copy**: `integration-workspace/crew/`

**Key Features**:
- ✅ Modular agent system (removed CrewAI dependency)
- ✅ Enhanced 4-agent workflow: Researcher → Planner → Developer → Reviewer  
- ✅ Quality gates with feedback loops and rejection capability
- ✅ Provider abstraction (LM Studio + Ollama support)
- ✅ Session logging and memory persistence
- ✅ Fixed memory storage + increased timeouts
- ❌ **No tools currently integrated**

**Architecture**:
```
crew/
├── agents/           # Enhanced agents with base classes
├── providers/        # AI provider abstraction  
├── workflows/        # Sequential workflow engine
├── core/            # Context engine + memory
├── ui/              # Shell interface
└── main.py          # Entry point
```

### 🛠️ **Basic-Agent Project** (`feature/crew-integration` branch)
**Location**: `/Users/ahughes/dev/basic-agent` (tools source)
**Copy**: `integration-workspace/basic-agent/`

**Key Features**:
- ✅ **Rich tool ecosystem** (file ops, terminal, web search)
- ✅ Memory management system
- ✅ Safety framework
- ✅ Model configuration system
- ✅ Well-tested tool implementations

**Tool Inventory**:
```
src/tools/
├── base.py              # Tool base classes
├── file_operations.py   # File system tools
├── terminal.py          # Shell execution tools  
└── web_search.py        # Web search capabilities
```

## Integration Strategy

### 🎯 **Goal**: Merge basic-agent's tool system into crew's modular architecture

### 📋 **Integration Steps**:

1. **Tool System Migration**
   - [ ] Copy `src/tools/` from basic-agent to crew
   - [ ] Adapt tool base classes to crew's provider pattern
   - [ ] Update agent base classes to support tool execution

2. **Agent Enhancement**
   - [ ] Extend `BaseAgent` with tool calling capabilities
   - [ ] Add tool-specific agents (e.g., `DeveloperAgent` with file/terminal tools)
   - [ ] Update workflow to handle tool results

3. **Safety Integration**
   - [ ] Port safety framework from basic-agent
   - [ ] Add tool usage validation
   - [ ] Implement permission controls

4. **Memory Unification**
   - [ ] Merge memory systems (crew's context engine + basic-agent's memory)
   - [ ] Ensure tool usage is logged in memory
   - [ ] Maintain context across tool calls

5. **Configuration Harmonization**
   - [ ] Unify model configuration systems
   - [ ] Merge environment management
   - [ ] Standardize on single pyproject.toml

### 🔗 **Integration Points**

| Component | Crew | Basic-Agent | Integration Strategy |
|-----------|------|-------------|---------------------|
| **Agents** | Enhanced 4-agent crew | Single configurable agent | Extend crew agents with tool capabilities |
| **Tools** | None | File, Terminal, Web | Port all tools to crew architecture |
| **Memory** | Context engine | Simple memory system | Merge into unified memory system |
| **Providers** | LM Studio + Ollama | OpenAI-compatible | Keep crew's provider abstraction |
| **Workflows** | Sequential with quality gates | Linear execution | Keep crew's enhanced workflow |
| **Safety** | None | Safety framework | Port safety framework |

### 🚦 **Next Actions**

1. **Immediate**: Explore tool integration by porting one tool (e.g., file_operations) to crew
2. **Short-term**: Create tool-enabled developer agent
3. **Medium-term**: Full integration with safety and unified memory
4. **Long-term**: Deploy as single unified agent platform

### 📁 **Workspace Structure**
```
integration-workspace/
├── crew/           # Enhanced crew system (target)
├── basic-agent/    # Tool system source
└── INTEGRATION_PLAN.md  # This document
```

Both projects are now on feature branches and copied to the shared workspace for safe experimentation!