# Unit Tests for TaskContext Delegation Enhancement
# Tests Task 6.3.1: Add optional delegation_data field to existing TaskContext

import pytest
from agents.base import TaskContext, TaskDelegationData


class TestTaskDelegationData:
    """Test TaskDelegationData functionality."""
    
    def test_delegation_data_creation(self):
        """Test basic TaskDelegationData creation."""
        delegation_data = TaskDelegationData(
            complexity_assessment=7,
            delegation_instructions="Create a REST API with authentication",
            expected_subtasks=["Design API endpoints", "Implement auth", "Write tests"],
            expected_cycles=3,
            priority_level="capable"
        )
        
        assert delegation_data.complexity_assessment == 7
        assert delegation_data.delegation_instructions == "Create a REST API with authentication"
        assert len(delegation_data.expected_subtasks) == 3
        assert delegation_data.expected_cycles == 3
        assert delegation_data.priority_level == "capable"
        
    def test_delegation_data_defaults(self):
        """Test TaskDelegationData default values."""
        delegation_data = TaskDelegationData(
            complexity_assessment=5,
            delegation_instructions="Simple task"
        )
        
        assert delegation_data.expected_subtasks == []
        assert delegation_data.context_target_range == (1000, 4000)
        assert delegation_data.expected_cycles == 1
        assert delegation_data.priority_level == "standard"


class TestTaskContextBackwardCompatibility:
    """Test 100% backward compatibility - CRITICAL for production safety."""
    
    def test_original_task_context_creation(self):
        """Test that existing TaskContext creation works identically."""
        # Original usage pattern
        context = TaskContext(
            task_description="Create a calculator",
            expected_output="Python function with basic operations"
        )
        
        assert context.task_description == "Create a calculator"
        assert context.expected_output == "Python function with basic operations"
        assert context.previous_results == []
        assert context.memory_context == ""
        assert context.user_input == ""
        assert context.delegation_data is None  # NEW: Should be None by default
        
    def test_original_task_context_with_all_fields(self):
        """Test existing TaskContext with all original fields."""
        context = TaskContext(
            task_description="Build web app",
            expected_output="Complete application",
            previous_results=["Step 1 done", "Step 2 done"],
            memory_context="Previous project context",
            user_input="User wants modern design"
        )
        
        assert context.task_description == "Build web app"
        assert context.expected_output == "Complete application"
        assert len(context.previous_results) == 2
        assert context.memory_context == "Previous project context"
        assert context.user_input == "User wants modern design"
        assert context.delegation_data is None  # NEW: Should be None
        
    def test_original_to_prompt_behavior(self):
        """Test that to_prompt() works identically for existing usage."""
        context = TaskContext(
            task_description="Write documentation",
            expected_output="Complete README file",
            previous_results=["Research completed"],
            memory_context="Company style guide",
            user_input="Include examples"
        )
        
        prompt = context.to_prompt()
        
        # Should contain all original elements
        assert "User Request: Include examples" in prompt
        assert "Task: Write documentation" in prompt
        assert "Expected Output: Complete README file" in prompt
        assert "Previous Results:" in prompt
        assert "1. Research completed" in prompt
        assert "Memory Context: Company style guide" in prompt
        
        # Should NOT contain delegation context when delegation_data is None
        assert "Delegation Context:" not in prompt
        assert "Complexity Level:" not in prompt


class TestTaskContextDelegationEnhancement:
    """Test new delegation functionality."""
    
    def test_task_context_with_delegation_data(self):
        """Test TaskContext with delegation_data field."""
        delegation_data = TaskDelegationData(
            complexity_assessment=8,
            delegation_instructions="Build microservice architecture",
            expected_subtasks=["API Gateway", "User Service", "Auth Service"],
            expected_cycles=5,
            priority_level="capable"
        )
        
        context = TaskContext(
            task_description="Create microservices system",
            expected_output="Production-ready architecture",
            delegation_data=delegation_data
        )
        
        assert context.delegation_data is not None
        assert context.delegation_data.complexity_assessment == 8
        assert context.delegation_data.delegation_instructions == "Build microservice architecture"
        assert len(context.delegation_data.expected_subtasks) == 3
        
    def test_enhanced_to_prompt_with_delegation(self):
        """Test to_prompt() includes delegation context when present."""
        delegation_data = TaskDelegationData(
            complexity_assessment=6,
            delegation_instructions="Create API with database integration",
            expected_subtasks=["Database schema", "API endpoints", "Integration tests"],
            expected_cycles=3,
            priority_level="standard"
        )
        
        context = TaskContext(
            task_description="Build REST API",
            expected_output="Working API with documentation",
            user_input="Use PostgreSQL",
            delegation_data=delegation_data
        )
        
        prompt = context.to_prompt()
        
        # Should contain original elements
        assert "User Request: Use PostgreSQL" in prompt
        assert "Task: Build REST API" in prompt
        assert "Expected Output: Working API with documentation" in prompt
        
        # Should contain NEW delegation context
        assert "Delegation Context:" in prompt
        assert "Complexity Level: 6/10" in prompt
        assert "Instructions: Create API with database integration" in prompt
        assert "Expected Cycles: 3" in prompt
        assert "Context Target: 1000-4000 tokens" in prompt
        assert "Performance Tier: standard" in prompt
        assert "Expected Subtasks:" in prompt
        assert "1. Database schema" in prompt
        assert "2. API endpoints" in prompt
        assert "3. Integration tests" in prompt
        
    def test_delegation_context_formatting(self):
        """Test _format_delegation_context() method."""
        delegation_data = TaskDelegationData(
            complexity_assessment=9,
            delegation_instructions="Complex system design",
            expected_subtasks=["Architecture", "Implementation"],
            context_target_range=(2000, 8000),
            expected_cycles=4,
            priority_level="capable"
        )
        
        context = TaskContext(
            task_description="System design",
            expected_output="Complete system",
            delegation_data=delegation_data
        )
        
        delegation_context = context._format_delegation_context()
        
        assert "Delegation Context:" in delegation_context
        assert "Complexity Level: 9/10" in delegation_context
        assert "Instructions: Complex system design" in delegation_context
        assert "Expected Cycles: 4" in delegation_context
        assert "Context Target: 2000-8000 tokens" in delegation_context
        assert "Performance Tier: capable" in delegation_context
        assert "Expected Subtasks:" in delegation_context
        assert "1. Architecture" in delegation_context
        assert "2. Implementation" in delegation_context
        
    def test_delegation_context_no_subtasks(self):
        """Test delegation context formatting without subtasks."""
        delegation_data = TaskDelegationData(
            complexity_assessment=3,
            delegation_instructions="Simple utility function",
            expected_subtasks=[],  # No subtasks
            priority_level="fast"
        )
        
        context = TaskContext(
            task_description="Create utility",
            expected_output="Working function",
            delegation_data=delegation_data
        )
        
        delegation_context = context._format_delegation_context()
        
        assert "Delegation Context:" in delegation_context
        assert "Complexity Level: 3/10" in delegation_context
        assert "Performance Tier: fast" in delegation_context
        # Should not include subtasks section when empty
        assert "Expected Subtasks:" not in delegation_context
        
    def test_format_delegation_context_returns_empty_when_none(self):
        """Test _format_delegation_context() returns empty string when delegation_data is None."""
        context = TaskContext(
            task_description="Simple task",
            expected_output="Simple output",
            delegation_data=None
        )
        
        delegation_context = context._format_delegation_context()
        assert delegation_context == ""


class TestUnifiedPromptEngineFoundation:
    """Test TaskContext as foundation for unified prompt engine."""
    
    def test_progressive_context_assembly(self):
        """Test that context can progressively build complexity."""
        # Start simple
        context = TaskContext(
            task_description="Build calculator",
            expected_output="Working calculator"
        )
        
        basic_prompt = context.to_prompt()
        assert len(basic_prompt.split('\n')) >= 2  # At least task and expected output
        
        # Add memory context
        context.memory_context = "Previous calculator used classes"
        memory_prompt = context.to_prompt()
        assert len(memory_prompt) > len(basic_prompt)
        assert "Memory Context:" in memory_prompt
        
        # Add delegation data
        context.delegation_data = TaskDelegationData(
            complexity_assessment=5,
            delegation_instructions="Use object-oriented design",
            expected_subtasks=["Define Calculator class", "Implement operations", "Add error handling"]
        )
        
        full_prompt = context.to_prompt()
        assert len(full_prompt) > len(memory_prompt)
        assert "Delegation Context:" in full_prompt
        assert "Complexity Level: 5/10" in full_prompt
        
    def test_modular_context_sources(self):
        """Test that different context sources can be mixed and matched."""
        delegation_data = TaskDelegationData(
            complexity_assessment=7,
            delegation_instructions="Build scalable system",
            expected_subtasks=["Design", "Implement", "Test", "Deploy"]
        )
        
        # Create context with all possible sources
        context = TaskContext(
            task_description="Create web service",
            expected_output="Production-ready service",
            previous_results=["Requirements gathered", "Architecture designed"],
            memory_context="Company uses microservices pattern",
            user_input="Must handle 1000 concurrent users",
            delegation_data=delegation_data
        )
        
        prompt = context.to_prompt()
        
        # Verify all context sources are present and properly formatted
        assert "User Request: Must handle 1000 concurrent users" in prompt
        assert "Task: Create web service" in prompt
        assert "Expected Output: Production-ready service" in prompt
        assert "Previous Results:" in prompt
        assert "1. Requirements gathered" in prompt
        assert "2. Architecture designed" in prompt
        assert "Memory Context: Company uses microservices pattern" in prompt
        assert "Delegation Context:" in prompt
        assert "Complexity Level: 7/10" in prompt
        assert "Expected Subtasks:" in prompt
        assert "4. Deploy" in prompt
        
        # Verify proper section ordering (user request first, then task, etc.)
        lines = prompt.split('\n')
        user_idx = next(i for i, line in enumerate(lines) if "User Request:" in line)
        task_idx = next(i for i, line in enumerate(lines) if "Task:" in line)
        delegation_idx = next(i for i, line in enumerate(lines) if "Delegation Context:" in line)
        
        assert user_idx < task_idx < delegation_idx


class TestPerformanceAndMemory:
    """Test performance characteristics of enhanced TaskContext."""
    
    def test_memory_efficiency_without_delegation(self):
        """Test that TaskContext without delegation_data has minimal overhead."""
        context = TaskContext(
            task_description="Simple task",
            expected_output="Simple output"
        )
        
        # delegation_data should be None, not an empty object
        assert context.delegation_data is None
        
        # to_prompt() should not create delegation objects
        prompt = context.to_prompt()
        assert "Delegation Context:" not in prompt
        
    def test_prompt_generation_performance(self):
        """Test that prompt generation is efficient even with complex delegation."""
        import time
        
        delegation_data = TaskDelegationData(
            complexity_assessment=10,
            delegation_instructions="Very complex task with detailed requirements",
            expected_subtasks=[f"Subtask {i}" for i in range(50)],  # Many subtasks
            expected_cycles=10
        )
        
        context = TaskContext(
            task_description="Complex system",
            expected_output="Complete implementation",
            previous_results=[f"Result {i}" for i in range(10)],  # Many previous results
            memory_context="Large memory context with lots of information",
            delegation_data=delegation_data
        )
        
        start_time = time.time()
        prompt = context.to_prompt()
        generation_time = time.time() - start_time
        
        # Should generate prompt quickly even with complex data
        assert generation_time < 0.01  # Less than 10ms
        assert len(prompt) > 1000  # Should be substantial
        assert "Delegation Context:" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])