# Enterprise-Grade Long Duration Model Testing

🏭 **Production-grade research database profiling for local LLM capabilities**

This comprehensive testing suite evaluates consumer hardware models for enterprise use cases, focusing on tool calling, structured output, and continuous operation capabilities.

## 🚀 Quick Start

### Option 1: Quiet Operation (Recommended for Overnight)
```bash
# Set up M4 Max throttling at 80% for quiet fans
python utils/m4_throttling.py 80
bash /Users/ahughes/dev/crew/run_throttled_test.sh 4

# For even quieter operation (60% performance)
python utils/m4_throttling.py 60
bash /Users/ahughes/dev/crew/run_throttled_test.sh 6
```

### Option 2: Full Performance
```bash
# Run at full performance for maximum throughput data
python long_duration_test.py 4    # 4 hours
python long_duration_test.py 2.5  # 2.5 hours custom
```

### Option 3: Short Development Test
```bash
# Quick 30-minute test for development
python long_duration_test.py 0.5
```

## 📊 What This Tests

### 🤖 **Multi-Model Enterprise Profiling**
- **Automatic Model Discovery**: Tests ALL models under 15GB
- **Size Optimization**: Prioritizes 7B-14B models for consumer hardware
- **Model Rotation**: Cycles through models every 5-10 tests
- **Comprehensive Profiling**: Builds detailed capability database

### 🎯 **Test Scenarios**

| Scenario | Weight | Purpose |
|----------|--------|---------|
| **Prompt Variety** | 3.0 | Tests 100+ enterprise prompts across categories |
| **Simple Inference** | 3.0 | Varying token sizes (100-10k tokens) |
| **Tool Calling** | 2.0 | Explicit & implicit tool use detection |
| **Streaming** | 2.0 | Real-time response capabilities |
| **Concurrent Load** | 1.5 | Multi-request handling |
| **Large Context** | 0.5 | 10k-40k token contexts |
| **Provider Failover** | 0.5 | Resilience & recovery testing |

### 🛠️ **Tool Calling Analysis**
- **Explicit Prompts**: "Use the calculate_metrics function..."
- **Implicit Prompts**: "What is the current CPU usage?"
- **Parser Detection**: Tracks successful tool call recognition
- **Success Rate Tracking**: Builds tool calling capability database

### 📝 **100+ Enterprise Prompt Bank**
- **Technical Analysis**: Architecture, security, performance
- **Code Generation**: Python, React, SQL, system design
- **Problem Solving**: Debugging, optimization, scaling
- **DevOps**: CI/CD, infrastructure, monitoring
- **Business Logic**: Workflows, pricing, recommendations

## 📁 Generated Logs & Reports

### Log Directory Structure
```
test_logs/long_duration_YYYYMMDD_HHMMSS/
├── main_test.log              # Overall progress & summary
├── performance_metrics.log    # Detailed response metrics
├── model_profiling.log        # Model capability database
├── tool_calling.log          # Tool use detection analysis
├── integration_events.log    # System interactions
├── errors.log                # Failure analysis
├── test_summary.json         # Live updating summary (every 5min)
└── final_report.md           # Comprehensive markdown report
```

### Real-Time Monitoring
```bash
# Watch overall progress
tail -f test_logs/long_duration_*/main_test.log

# Monitor model profiling data
tail -f test_logs/long_duration_*/model_profiling.log

# Check tool calling success rates
tail -f test_logs/long_duration_*/tool_calling.log

# View current summary
cat test_logs/long_duration_*/test_summary.json | jq .
```

## 🔧 Pre-Flight Checklist

### 1. **Verify LM Studio Setup**
```bash
# Check LM Studio is running
curl http://localhost:1234/v1/models

# Verify you have suitable models (7B-14B preferred)
curl http://localhost:1234/v1/models | jq '.data[].id'
```

### 2. **Optimize for Quiet Operation**
```bash
# Close unnecessary applications
# Set display sleep to 1 minute: System Preferences > Lock Screen
# Place MacBook on hard surface for airflow
# Optional: Use AlDente to limit battery charge to 80%
```

### 3. **Expected Model Performance**
- **7B-8B Models**: 1000-2000 tokens/second
- **13B-14B Models**: 500-1000 tokens/second  
- **First Chunk Latency**: <5 seconds for streaming
- **Success Rate**: >90% for properly sized contexts

## 📊 Enterprise Research Database

### Model Profiling Metrics
Each model tested builds a comprehensive profile:

```json
{
  "model_id": "llama-3.1-8b-instruct",
  "provider": "lmstudio",
  "tests_run": 247,
  "successes": 234,
  "avg_response_time": 1.34,
  "tool_call_success_rate": 87.3,
  "estimated_size_gb": 8,
  "context_length": 128000,
  "scenarios_tested": ["prompt_variety", "tool_calling", "streaming"],
  "prompt_categories": {
    "design": {"count": 23, "success": 22},
    "coding": {"count": 31, "success": 29},
    "tool_explicit": {"count": 15, "success": 13},
    "tool_implicit": {"count": 18, "success": 12}
  }
}
```

### Tool Calling Intelligence
- **Pattern Detection**: Multiple tool call formats (JSON, function syntax, natural language)
- **Success Tracking**: Explicit vs implicit prompt success rates
- **Capability Mapping**: Which models excel at structured output

### Performance Benchmarking
- **Throughput Analysis**: Tokens/second under various loads
- **Context Scaling**: Performance degradation with large contexts
- **Concurrent Handling**: Multi-request processing capabilities
- **Streaming Latency**: Real-time response characteristics

## 🌙 Overnight Testing Strategy

### Night Mode Features
- **Automatic Throttling**: Longer delays between 10pm-6am
- **Fan Noise Reduction**: M4 Max throttling at 60-80%
- **Error Recovery**: Continues testing despite failures
- **Unattended Operation**: No user intervention required

### Expected Results (4-Hour Run)
- **Tests Executed**: 500-1500 depending on model size
- **Models Profiled**: 8-15 models (depending on availability)
- **Tool Call Samples**: 200-400 tool calling attempts
- **Context Variety**: 100+ different prompt categories tested

### Morning Report
The final report provides:
- **Model Rankings**: Performance, reliability, tool calling capability
- **Hardware Utilization**: Thermal performance, fan behavior
- **Capability Matrix**: Which models excel at specific tasks
- **Recommendations**: Best models for production use cases

## 🚨 Troubleshooting

### Common Issues
```bash
# LM Studio not responding
curl http://localhost:1234/v1/models
# If failed: Restart LM Studio, ensure model is loaded

# No suitable models
# Load 7B-14B models in LM Studio
# Avoid: embedding models, 30B+ models

# High fan noise
python utils/m4_throttling.py 60  # Lower to 60%
# Close other apps, ensure good airflow

# Test failures
# Check test_logs/*/errors.log for specific issues
# Common: timeout errors with large models
```

### Performance Optimization
- **Model Selection**: Prefer quantized 7B-8B models for speed
- **Context Management**: Large context tests are intentionally resource-intensive
- **Concurrent Limits**: Automatically limited to prevent overload

## 🏆 Enterprise Use Cases

This testing suite answers critical questions for production deployment:

1. **Which models consistently deliver structured output?**
2. **What's the practical token throughput on consumer hardware?**
3. **How reliable are models for tool calling in extended workflows?**
4. **Which models balance performance vs capability for production use?**
5. **What are the thermal limits for continuous operation?**

The comprehensive dataset generated enables evidence-based model selection for enterprise applications running on consumer hardware.

## 🎯 Next Steps After Testing

1. **Analyze Model Profiles**: Review `model_profiling.log` for capability insights
2. **Compare Tool Calling**: Check which models excel at structured output
3. **Performance Ranking**: Sort by throughput vs accuracy for your use case
4. **Production Selection**: Choose models based on comprehensive profiling data

Sweet dreams! 🌙 The script will build your enterprise-grade model capability database while you sleep.