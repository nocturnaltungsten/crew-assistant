# 🧪 Crew Assistant Test Suite

This directory contains comprehensive tests for the crew-assistant project, organized by test type and purpose.

## Test Structure

```
tests/
├── unit/                  # Component isolation tests
├── integration/           # Multi-component interaction tests
├── system/               # End-to-end workflow tests
├── long_duration/        # Performance and stress tests
├── fixtures/             # Test data and utilities
└── conftest.py           # Pytest configuration
```

## Test Categories

### Unit Tests (`unit/`)
Fast, isolated tests for individual components:
- `test_config.py` - Configuration and settings validation
- `test_context_router.py` - Context routing logic
- `test_enhanced_providers.py` - Provider base functionality

### Integration Tests (`integration/`)
Tests for component interactions:
- `test_real_providers.py` - LM Studio/Ollama provider integration
- `test_crew_workflow.py` - Multi-agent workflow execution
- `test_battle_providers.py` - High-load provider testing (10k-30k tokens)
- `test_task_validation.py` - Task validation system

### System Tests (`system/`)
End-to-end application tests:
- `test_end_to_end.py` - Full application workflow testing

### Long-Duration Tests (`long_duration/`)
Extended performance and reliability tests:
- `long_duration_crew_test.py` - 139 tasks across 9 complexity levels
- `long_duration_test.py` - Extended workflow scenarios

## Running Tests

### Basic Test Execution
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test category
uv run python -m pytest tests/unit/ -v
uv run python -m pytest tests/integration/ -v
uv run python -m pytest tests/system/ -v

# Run with coverage
uv run python -m pytest tests/ -v --cov=crew_assistant --cov-report=term-missing
```

### Test Markers
```bash
# Run only unit tests
uv run python -m pytest -m unit

# Run only integration tests  
uv run python -m pytest -m integration

# Run only system tests
uv run python -m pytest -m system

# Skip slow tests
uv run python -m pytest -m "not slow"
```

### Long-Duration Testing
```bash
# 30-minute validation test
python tests/long_duration/long_duration_crew_test.py 0.5

# 4-hour comprehensive test
python tests/long_duration/long_duration_crew_test.py 4

# Quiet operation (M4 Max optimized)
bash run_crew_test_throttled.sh 6
```

## Test Features

### Task Complexity Distribution
The long-duration test suite includes 139 tasks distributed across complexity levels:
- **Trivial** (20 tasks): Basic questions and lookups
- **Simple** (20 tasks): Single-function implementations
- **Moderate** (20 tasks): Multi-component features
- **Complex** (20 tasks): System design tasks
- **Vague** (20 tasks): Underspecified requests
- **Advanced** (19 tasks): Architecture and optimization
- **Research** (10 tasks): Investigation and analysis
- **Creative** (5 tasks): Open-ended creative tasks
- **Vague Override** (5 tasks): Tests "JUST BUILD IT" pattern

### Quality Metrics Collection
Tests collect comprehensive quality metrics:
- Numeric ratings (1-10) across 5 criteria
- Agent execution times
- Token usage statistics
- Success/failure patterns
- Workflow completion rates

### Logging and Analytics
- 5-stream structured JSON logging
- Separate logs for each test category
- Real-time performance metrics
- Session-based analytics storage

## Test Configuration

### Environment Variables
```bash
# Provider configuration for tests
export AI_PROVIDER=lmstudio
export OPENAI_API_BASE=http://localhost:1234/v1
export OPENAI_API_MODEL=qwen2.5-coder-7b-instruct

# Test-specific settings
export TEST_TIMEOUT=300
export TEST_VERBOSE=true
```

### Pytest Configuration
See `pyproject.toml` for pytest settings:
- Test discovery patterns
- Coverage configuration
- Plugin settings
- Marker definitions

## Writing Tests

### Test Guidelines
1. **Isolation**: Tests should not depend on external state
2. **Clarity**: Test names should describe what they test
3. **Speed**: Unit tests should complete in <1 second
4. **Coverage**: Aim for >90% coverage of critical paths
5. **Fixtures**: Use pytest fixtures for common setup

### Example Test Structure
```python
import pytest
from crew_assistant.module import MyClass

class TestMyClass:
    @pytest.fixture
    def instance(self):
        return MyClass()
    
    def test_basic_functionality(self, instance):
        # Arrange
        input_data = "test"
        
        # Act
        result = instance.process(input_data)
        
        # Assert
        assert result.success
        assert result.output == "expected"
```

### Mock Guidelines
- Mock external dependencies (LLM providers, file I/O)
- Use `pytest-mock` for clean mocking
- Avoid over-mocking that reduces test value
- Integration tests should use real providers when possible

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Fast unit tests run on every commit
- Integration tests run on pull requests
- Long-duration tests run nightly
- Coverage reports generated automatically

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure you're in the project root
- Check that `src/` is in the Python path
- Verify all dependencies are installed with `uv sync`

**Provider Connection Failures**
- Verify LM Studio/Ollama is running
- Check provider URLs and ports
- Review provider logs for errors

**Timeout Issues**
- Increase timeout with `--timeout=600`
- Check for hanging provider calls
- Review system resource usage

**Coverage Gaps**
- Focus on testing critical paths first
- Use `--cov-report=html` for detailed reports
- Add tests for error conditions

## Future Enhancements

- [ ] Add performance regression tests
- [ ] Implement property-based testing
- [ ] Add mutation testing
- [ ] Create visual test reports
- [ ] Add load testing scenarios
- [ ] Implement contract testing for providers

---

*Last Updated: 2025-07-02 | Test Count: 71 tests | Coverage Target: 90%*