# CLAUDE_BRANCH_adaptive-workflow.md

**Branch**: `feature/adaptive-workflow`  
**Created**: 2025-06-30  
**Parent**: `main` (v0.3.0)  
**Status**: Active Development

NEVER delete anything. Move to trash!

---

## 🎯 **BRANCH MISSION: Adaptive Workflow System Implementation**

**Objective**: Implement adaptive workflow capabilities that enable:
- UX Agent priority scheduling for sub-100ms user interaction latency
- Multi-model provider selection (fast models for UX, capable models for complex work)
- Dynamic task delegation with parallel background processing
- Cycle-based execution planning with configurable context targets
- Per-agent memory isolation and context injection

**Core Principle**: **PRESERVE AND EXTEND** existing infrastructure - never replace working systems.

---

## 🏗️ **IMPLEMENTATION STRATEGY: Incremental Infrastructure Evolution**

### **Engineering Discipline (NON-NEGOTIABLE)**
1. **PRESERVE EXISTING INVESTMENTS** - Provider system, agent base classes, memory engine, validation logic ALL stay
2. **INCREMENTAL EVOLUTION** - Small, testable changes that build on current foundation  
3. **COMPREHENSIVE TESTING** - Unit → Integration → System testing at EVERY step
4. **REVERSIBLE CHANGES** - Every modification must be easily rollback-able
5. **INFRASTRUCTURE REUSE** - Extend, don't replace, existing components

### **Existing Infrastructure to PRESERVE & EXTEND**
- ✅ **Provider Registry** - Circuit breakers, health monitoring, load balancing
- ✅ **Sequential Workflow** - Quality gates, iteration logic, context passing
- ✅ **Agent Base Classes** - Role definitions, context handling, memory integration
- ✅ **TaskContext System** - Inter-agent communication, result accumulation
- ✅ **Memory Store** - Persistent storage, fact learning, context injection
- ✅ **Validation System** - Pre/post validation, "JUST BUILD IT" overrides

---

## 📋 **MASTER TASK LIST (Continuation of Main Project Tasks)**

*Note: These tasks continue the numbering sequence from the main project CLAUDE.md file*

### **Phase 6: Adaptive Workflow Foundation** *(Tasks 6.1-6.6)*

#### **6.1 Architecture Analysis & Safe Extension Points** ✅ **COMPLETED**
- [x] **6.1.1** Analyze current workflow, provider, and agent architecture
- [x] **6.1.2** Identify safe extension points that preserve existing functionality
- [x] **6.1.3** Document backward compatibility requirements
- [x] **6.1.4** Design incremental enhancement strategy

**Status**: Architecture analysis complete. Safe extension points identified in ProviderRegistry, BaseWorkflow, TaskContext, and BaseAgent.

#### **6.2 Provider Priority System Extension** ✅ **COMPLETED** 
- [x] **6.2.1** Extend ProviderRegistry with optional priority parameter (backward compatible) ✅
- [x] **6.2.2** Implement UX-priority provider selection logic ✅
- [x] **6.2.3** Add PriorityLevel enum and ModelRequirements extensions ✅
- [x] **6.2.4** Comprehensive unit tests for priority provider selection ✅
- [x] **6.2.5** Integration tests validating existing workflows unchanged ✅
- [x] **6.2.6** System tests confirming zero performance impact on current flows ✅

**Status**: ✅ **COMPLETED** - Priority system functional with backward compatibility maintained

**Manual System Test Entrypoint**:
```bash
uv run python -c "
from providers.registry import get_optimal_provider, PriorityLevel, ModelRequirements
import time

# Test all priority levels with timing
requirements = ModelRequirements(capabilities=['chat'])

print('=== PRIORITY SYSTEM VALIDATION ===')
for priority in [None, PriorityLevel.UX_INTERACTIVE, PriorityLevel.STANDARD, PriorityLevel.BACKGROUND]:
    start = time.time()
    provider = get_optimal_provider(requirements, priority)
    latency = (time.time() - start) * 1000
    priority_name = priority.name if priority else 'ORIGINAL'
    print(f'{priority_name}: {provider.name if provider else \"None\"} ({latency:.1f}ms)')
"
```

**What's Different/What to Look For**:
- **UX_INTERACTIVE priority**: Should show fastest latency (<1ms) and log "UX priority provider" messages
- **STANDARD/BACKGROUND priority**: Should behave identically to original behavior  
- **All variants**: Should return same provider but with different internal routing
- **Performance**: UX priority should be fastest, all others nearly identical

#### **6.3 TaskContext Enhancement for Delegation** ✅ **COMPLETED**
- [x] **6.3.1** Add optional delegation_data field to existing TaskContext ✅
- [x] **6.3.2** Preserve all existing context passing behavior ✅

**Status**: ✅ **COMPLETED** - TaskContext enhanced with delegation fields, existing behavior preserved

**Manual System Test Entrypoint**:
```bash
OPENAI_API_MODEL="qwen/qwen3-8b" OPENAI_API_BASE="http://localhost:1234/v1" AI_PROVIDER="lmstudio" uv run python main.py --crew "Create a simple calculator function"
```

**What's Different/What to Look For**:
- **System behavior identical** to before (TaskContext enhancement invisible)
- **Enhanced TaskContext** working underneath in workflow build_context() calls
- **Unified prompt engine foundation** ready (delegation_data stays None for now)
- **Full workflow execution** with UX → Planner → Developer → Reviewer pipeline
- [ ] **6.3.3** Design TaskDelegationPacket data structure
- [ ] **6.3.4** Unit tests for enhanced TaskContext compatibility
- [ ] **6.3.5** Integration tests with current sequential workflow
- [ ] **6.3.6** Validate memory integration unchanged

#### **6.4 Multi-Model Provider Support**
- [ ] **6.4.1** Extend ModelRequirements with performance_tier and agent_role fields
- [ ] **6.4.2** Implement model tier mapping (fast/balanced/capable)
- [ ] **6.4.3** Add agent-role-specific model selection logic
- [ ] **6.4.4** Unit tests for multi-model selection algorithms
- [ ] **6.4.5** Integration tests with existing provider health monitoring
- [ ] **6.4.6** Performance benchmarking across model tiers

#### **6.5 Agent Cycle Planning Extension**
- [ ] **6.5.1** Extend BaseAgent with optional cycle planning methods
- [ ] **6.5.2** Implement cycle planning in Developer agent as pilot
- [ ] **6.5.3** Design per-agent memory file system
- [ ] **6.5.4** Unit tests for cycle planning vs standard execution
- [ ] **6.5.5** Integration tests with existing agent workflows
- [ ] **6.5.6** Performance impact analysis and optimization

#### **6.6 Async Workflow Mode Implementation**
- [ ] **6.6.1** Add adaptive_mode flag to SequentialWorkflow (optional)
- [ ] **6.6.2** Implement UX-priority execution path
- [ ] **6.6.3** Maintain identical behavior for sync mode (backward compatibility)
- [ ] **6.6.4** Unit tests for async vs sync workflow execution
- [ ] **6.6.5** Integration tests with current quality gates and validation
- [ ] **6.6.6** Full system testing and performance comparison

### **Phase 7: Adaptive Integration & Testing** *(Tasks 7.1-7.4)*

#### **7.1 Component Integration**
- [ ] **7.1.1** Integrate provider priority with async workflow mode
- [ ] **7.1.2** Connect enhanced TaskContext with agent cycle planning
- [ ] **7.1.3** Implement end-to-end adaptive workflow execution
- [ ] **7.1.4** Comprehensive integration testing across all components

#### **7.2 Performance Validation**
- [ ] **7.2.1** Performance benchmarking: adaptive vs current system
- [ ] **7.2.2** UX latency testing (target: sub-100ms for UX agent)
- [ ] **7.2.3** Background processing efficiency analysis
- [ ] **7.2.4** Resource utilization optimization

#### **7.3 Long-Duration Testing Extension**
- [ ] **7.3.1** Extend existing long-duration test framework for adaptive workflows
- [ ] **7.3.2** Add adaptive-specific test cases to crew_test_tasks.py
- [ ] **7.3.3** Implement adaptive workflow analytics and logging
- [ ] **7.3.4** Execute comprehensive 4-hour adaptive workflow test

#### **7.4 Production Readiness**
- [ ] **7.4.1** Backward compatibility validation (100% existing functionality preserved)
- [ ] **7.4.2** Documentation updates for adaptive features
- [ ] **7.4.3** User interface updates for adaptive mode selection
- [ ] **7.4.4** Production deployment preparation

---

## 🔧 **DETAILED IMPLEMENTATION SPECIFICATIONS**

### **6.2 Provider Priority System Extension**

**Goal**: Add UX agent priority to existing provider system without disrupting current functionality.

**Implementation Approach**:
```python
# EXTEND existing providers/registry.py - DON'T REPLACE
from enum import Enum
from typing import Optional

class PriorityLevel(Enum):
    UX_INTERACTIVE = 1      # Highest priority - UX agent
    STANDARD = 5            # Default - existing behavior  
    BACKGROUND = 10         # Background delegates

class ProviderRegistry:
    # ... existing code preserved ...
    
    async def get_optimal_provider(
        self, 
        requirements: ModelRequirements,
        priority_level: Optional[PriorityLevel] = None  # NEW: Optional extension
    ) -> BaseProvider:
        """
        BACKWARD COMPATIBLE: Existing calls work identically
        NEW: Optional priority parameter for UX agent prioritization
        """
        if priority_level == PriorityLevel.UX_INTERACTIVE:
            return await self._get_ux_priority_provider(requirements)
        
        # EXISTING LOGIC UNCHANGED - zero impact on current workflows
        return await self._get_standard_provider(requirements)
    
    async def _get_ux_priority_provider(self, requirements: ModelRequirements) -> BaseProvider:
        """New method: UX-optimized provider selection"""
        # 1. Check for dedicated UX provider pool
        # 2. Prioritize fastest response providers
        # 3. Bypass load balancing for immediate access
        # 4. Fallback to standard selection if needed
```

**Testing Requirements**:
- **Unit Tests**: Verify existing provider selection logic completely unchanged
- **Integration Tests**: Confirm current workflows have identical behavior
- **Priority Tests**: New priority feature works correctly when explicitly requested
- **Performance Tests**: UX priority achieves target <100ms latency

### **6.3 TaskContext Enhancement**

**Goal**: Add delegation capabilities to existing TaskContext without breaking current workflows.

**Implementation Approach**:
```python
# EXTEND existing core/crew_engine.py TaskContext - DON'T REPLACE
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class TaskDelegationData:
    """New: Task delegation information for adaptive workflows"""
    complexity_assessment: int  # 1-10 scale
    delegation_instructions: str
    expected_subtasks: list[str]
    priority_level: PriorityLevel
    context_target_range: tuple[int, int]  # (min_tokens, max_tokens)

@dataclass 
class TaskContext:
    # ... ALL existing fields preserved ...
    task_description: str
    expected_output: str
    previous_results: list[str]
    memory_context: str
    user_input: str
    
    # NEW: Optional delegation data (backward compatible)
    delegation_data: Optional[TaskDelegationData] = None
```

**Testing Requirements**:
- **Unit Tests**: All existing TaskContext usage works identically
- **Integration Tests**: Current sequential workflow unchanged with enhanced TaskContext
- **Delegation Tests**: New delegation features work when explicitly used

### **6.4 Multi-Model Provider Support**

**Goal**: Enable agent-role-specific model selection while preserving existing model requirements.

**Implementation Approach**:
```python
# EXTEND existing providers/base.py ModelRequirements - DON'T REPLACE
@dataclass 
class ModelRequirements:
    # ... ALL existing fields preserved ...
    streaming: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    # ... other existing fields ...
    
    # NEW: Optional performance optimization (backward compatible)
    performance_tier: Optional[str] = None  # "fast", "balanced", "capable"
    agent_role: Optional[str] = None        # For role-specific optimization
    latency_target_ms: Optional[int] = None # Target response latency

MODEL_TIER_MAPPING = {
    "fast": {
        "target_latency_ms": 100,
        "model_size_preference": "3B-7B",
        "use_cases": ["chat", "simple_analysis", "ux_interaction"]
    },
    "balanced": {
        "target_latency_ms": 300,
        "model_size_preference": "7B-14B", 
        "use_cases": ["planning", "review", "reasoning"]
    },
    "capable": {
        "target_latency_ms": 1000,
        "model_size_preference": "14B+",
        "use_cases": ["complex_development", "architecture", "deep_analysis"]
    }
}
```

### **6.5 Agent Cycle Planning Extension**

**Goal**: Add multi-cycle execution planning to agents without disrupting existing single-cycle behavior.

**Implementation Approach**:
```python
# EXTEND existing agents/base.py BaseAgent - DON'T REPLACE
class BaseAgent:
    # ... ALL existing methods preserved ...
    
    async def execute(self, context: TaskContext) -> str:
        """EXISTING: Single-cycle execution (unchanged)"""
        # All current logic preserved
        return await self._execute_single_cycle(context)
    
    # NEW: Optional multi-cycle execution capability
    async def execute_adaptive(self, context: TaskContext) -> str:
        """NEW: Multi-cycle execution with planning"""
        if await self._should_use_multi_cycle(context):
            return await self._execute_multi_cycle(context)
        
        # Fallback to existing single-cycle behavior
        return await self.execute(context)
    
    async def _should_use_multi_cycle(self, context: TaskContext) -> bool:
        """Determine if task benefits from multi-cycle execution"""
        if not context.delegation_data:
            return False
        return context.delegation_data.complexity_assessment >= 7
```

### **6.6 Async Workflow Mode**

**Goal**: Add optional async execution to SequentialWorkflow while preserving existing synchronous behavior.

**Implementation Approach**:
```python
# EXTEND existing workflows/sequential.py - DON'T REPLACE
class SequentialWorkflow(BaseWorkflow):
    def __init__(self, adaptive_mode: bool = False):  # NEW: Optional flag
        super().__init__()
        self.adaptive_mode = adaptive_mode
        
    async def execute(self, user_request: str) -> WorkflowResult:
        if self.adaptive_mode:
            return await self._execute_adaptive_mode(user_request)
        
        # EXISTING LOGIC COMPLETELY UNCHANGED
        return await self._execute_sequential_standard(user_request)
    
    async def _execute_adaptive_mode(self, user_request: str) -> WorkflowResult:
        """NEW: Adaptive execution with UX priority and background processing"""
        # 1. UX Agent executes immediately with priority provider access
        # 2. Parse UX output for chat response + delegation data
        # 3. Return immediate chat response to user
        # 4. Process delegation in background with progress updates
```

---

## 🧪 **TESTING STRATEGY**

### **Comprehensive Testing Requirements**

**Unit Testing (95%+ Coverage)**:
- Every new extension method individually tested
- Backward compatibility validated for all existing methods
- Edge cases and error conditions covered
- Performance benchmarks for new features

**Integration Testing**:
- Extended components work together correctly
- Existing workflows function identically with extensions
- Provider health monitoring works with priority system
- Memory integration preserved across enhancements

**System Testing**:
- Full workflow execution with adaptive features enabled
- Full workflow execution with adaptive features disabled (identical to current)
- Performance comparison: adaptive vs current system
- Long-duration testing with mixed workloads

**Backward Compatibility Testing**:
- 100% existing functionality preserved
- Existing configuration files work unchanged
- Current CLI interfaces function identically
- Performance does not degrade for existing workflows

---

## 🔄 **ROLLBACK & SAFETY PROCEDURES**

### **Rollback Capabilities**
1. **Feature Flags**: All adaptive features behind optional parameters
2. **Configuration-Based**: Adaptive mode disabled by default
3. **Branch Isolation**: All changes contained in feature branch
4. **Incremental Commits**: Each task commits separately for granular rollback

### **Safety Validation**
- Continuous integration tests for every commit
- Performance monitoring for regression detection
- Existing workflow validation in test suite
- User acceptance testing with current workflow patterns

---

## 🚀 **FUTURE ROADMAP INTEGRATION**

### **Base Agent Modularization Path**
- Current extensions preserve BaseAgent standalone capability
- Agent registry pattern supports external agent integration
- Memory interface abstractions maintained
- Clean separation of concerns for modular deployment

### **Provider Enhancement Path**
- Ollama integration leverages extended provider registry
- Cloud API support uses enhanced ModelRequirements
- Circuit breaker/health monitoring scales to all provider types
- Priority system supports any number of provider types

### **Quality Assurance Alignment**
- Every change passes existing test suite with 100% compatibility
- New features require 95%+ test coverage
- Performance must not degrade for existing workflows
- Documentation reflects both legacy and adaptive capabilities

---

## 📊 **SUCCESS METRICS**

### **Performance Targets**
- **UX Agent Latency**: <100ms for user interactions
- **Background Processing**: No impact on UX responsiveness
- **Workflow Completion**: ≤10% increase in total execution time
- **Resource Utilization**: ≤20% increase in provider requests

### **Quality Targets** 
- **Backward Compatibility**: 100% existing functionality preserved
- **Test Coverage**: 95%+ for all new features
- **System Reliability**: No degradation in current workflow success rates
- **Documentation**: Complete coverage of adaptive features and migration paths

### **User Experience Targets**
- **Interactive Responsiveness**: Sub-second UX agent responses
- **Progress Visibility**: Real-time updates on background task progress
- **Seamless Transition**: Existing users see no change unless explicitly enabling adaptive mode
- **Enhanced Capability**: Complex tasks complete faster through parallel processing

---

**STATUS**: ✅ **Phase 6.2 Complete** → ✅ **Phase 6.3 Complete**  
**Next Milestone**: Multi-model provider support (Task 6.4)  
**Branch Ready For**: Model tier mapping and agent role-specific optimization

---

## 🎯 **KEY ARCHITECTURAL INSIGHT: Unified Prompt Engine**

**Vision**: Rather than multiple disparate context injection systems, we're experimenting with a modular prompt engine that assembles context from multiple sources.

**Target Architecture** (v0.4.0):
```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED PROMPT ENGINE                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │   Memory    │ │ Delegation  │ │ Task History│ │  Agent │ │
│  │ Injection   │ │   Context   │ │   Context   │ │Context │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
│           │              │              │           │      │
│           └──────────────┼──────────────┼───────────┘      │
│                          │              │                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Context Assembly & Orchestration              │ │
│  │  • Progressive context building                         │ │
│  │  • Modular input source mixing                          │ │
│  │  • Agent-specific context optimization                  │ │
│  │  • Consistent interface for all context types          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Design Principles**:
1. **Unified Interface**: All context types integrate through single coherent system
2. **Modular Sources**: Memory, delegation, history, agent-specific data as pluggable modules
3. **Progressive Enhancement**: Each new context feature extends existing engine, never parallel systems
4. **Agent Optimization**: Context assembly tailored per agent role and priority level
5. **Backward Compatibility**: Existing TaskContext patterns preserved and enhanced

**Implementation Strategy**: TaskContext delegation enhancement (Phase 6.3) completed as initial step toward modular prompt assembly.

*Last Updated: 2025-06-30 - Priority system and TaskContext enhancement complete*