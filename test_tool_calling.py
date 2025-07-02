#!/usr/bin/env python3
"""
Simple test script for the new tool calling system.
Tests the robust parser and file operations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crew_assistant.agents.tools import ToolCall, default_registry
from crew_assistant.agents.tool_parser import ToolCallParser
from crew_assistant.agents.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool

def test_tool_registration():
    """Test that tools are properly registered."""
    print("=== Testing Tool Registration ===")
    
    tools = default_registry.list_tools()
    print(f"Registered tools: {tools}")
    
    expected_tools = ['read_file', 'write_file', 'list_directory']
    for tool_name in expected_tools:
        if tool_name in tools:
            print(f"✅ {tool_name} is registered")
        else:
            print(f"❌ {tool_name} is NOT registered")
    
    print()

def test_file_operations():
    """Test basic file operations."""
    print("=== Testing File Operations ===")
    
    # Test write file
    write_tool = WriteFileTool()
    write_result = write_tool.safe_execute({
        'file_path': '/tmp/test_tool_file.txt',
        'content': 'Hello from the tool calling system!\nThis is a test file.',
        'create_dirs': True
    })
    
    print(f"Write result: {write_result.status}")
    if write_result.success:
        print(f"✅ Write successful: {write_result.content}")
    else:
        print(f"❌ Write failed: {write_result.error_message}")
    
    # Test read file
    read_tool = ReadFileTool()
    read_result = read_tool.safe_execute({
        'file_path': '/tmp/test_tool_file.txt'
    })
    
    print(f"Read result: {read_result.status}")
    if read_result.success:
        print(f"✅ Read successful: {len(read_result.content)} characters")
        print(f"Content preview: {read_result.content[:50]}...")
    else:
        print(f"❌ Read failed: {read_result.error_message}")
    
    # Test list directory
    list_tool = ListDirectoryTool()
    list_result = list_tool.safe_execute({
        'dir_path': '/tmp',
        'show_details': False
    })
    
    print(f"List result: {list_result.status}")
    if list_result.success:
        print(f"✅ List successful")
        print(f"Directory listing preview: {list_result.content[:200]}...")
    else:
        print(f"❌ List failed: {list_result.error_message}")
    
    print()

def test_robust_parser():
    """Test the robust tool call parser with various malformed inputs."""
    print("=== Testing Robust Parser ===")
    
    parser = ToolCallParser(default_registry)
    
    # Test cases with various levels of malformed JSON
    test_cases = [
        # Perfect JSON
        '''```json
{
  "tool_name": "read_file",
  "parameters": {
    "file_path": "/tmp/test_tool_file.txt"
  }
}
```''',
        
        # Missing quotes around keys
        '''{
  tool_name: "write_file",
  parameters: {
    file_path: "/tmp/test2.txt",
    content: "Test content"
  }
}''',
        
        # Single quotes instead of double
        """{'tool_name': 'read_file', 'parameters': {'file_path': '/tmp/test_tool_file.txt'}}""",
        
        # Function call format
        """read_file(file_path="/tmp/test_tool_file.txt")""",
        
        # XML-like format
        """<read_file>
<file_path>/tmp/test_tool_file.txt</file_path>
</read_file>""",
        
        # Natural language
        """I need to read the file /tmp/test_tool_file.txt to see what's in it.""",
        
        # Badly formatted JSON with trailing commas
        """{
  "tool_name": "list_directory",
  "parameters": {
    "dir_path": "/tmp",
    "show_details": true,
  },
}""",
        
        # Misspelled tool name (should use fuzzy matching)
        """{"tool_name": "read_fil", "parameters": {"file_path": "/tmp/test_tool_file.txt"}}""",
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_input[:60]}...")
        
        result = parser.parse(test_input)
        
        print(f"Tool calls found: {len(result.tool_calls)}")
        print(f"Parse confidence: {result.confidence:.2f}")
        
        if result.parse_errors:
            print(f"Parse errors: {result.parse_errors}")
        
        for j, tool_call in enumerate(result.tool_calls):
            print(f"  Call {j+1}: {tool_call.tool_name} with params {tool_call.parameters}")
            print(f"  Confidence: {tool_call.confidence:.2f}")
            
            # Try executing the tool call
            execution_result = default_registry.execute_tool(tool_call)
            if execution_result.success:
                print(f"  ✅ Execution successful")
            else:
                print(f"  ❌ Execution failed: {execution_result.error_message}")
    
    print()

def test_agent_integration():
    """Test tool calling integration with a mock agent."""
    print("=== Testing Agent Integration ===")
    
    # This would normally test with a real agent, but for now we'll just
    # test the system prompt generation
    from crew_assistant.agents.base import BaseAgent, AgentConfig
    
    # Create a mock agent class for testing
    class MockAgent(BaseAgent):
        def get_system_prompt(self) -> str:
            return "You are a helpful assistant."
    
    # Create mock provider (we won't actually call it)
    class MockProvider:
        @property
        def name(self):
            return "mock"
    
    config = AgentConfig(
        role="Test Agent",
        goal="Test tool calling",
        backstory="A test agent",
        tools_enabled=True,
        allowed_tools=["read_file", "write_file"]  # Restrict to file tools
    )
    
    agent = MockAgent(MockProvider(), "mock-model", config)
    
    # Test tool definitions prompt
    tool_prompt = agent.get_tool_definitions_prompt()
    print("Tool definitions prompt generated:")
    print(tool_prompt[:300] + "..." if len(tool_prompt) > 300 else tool_prompt)
    
    # Test tool permission checking
    print(f"\nTool permission tests:")
    print(f"read_file allowed: {agent.is_tool_allowed('read_file')}")
    print(f"write_file allowed: {agent.is_tool_allowed('write_file')}")
    print(f"list_directory allowed: {agent.is_tool_allowed('list_directory')}")
    
    print()

def main():
    """Run all tests."""
    print("🧪 Tool Calling System Test Suite")
    print("=" * 50)
    
    try:
        test_tool_registration()
        test_file_operations()
        test_robust_parser()
        test_agent_integration()
        
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())