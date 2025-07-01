# 🧠 Crew Workflow Long Duration Testing

**Enterprise-grade multi-agent workflow testing and performance analysis**

This comprehensive testing suite evaluates the entire crew workflow system with varying task complexity and specificity levels, focusing on validation behavior, agent performance, and workflow completion rates.

## 🚀 Quick Start

### Option 1: Standard 4-Hour Test (Recommended)
```bash
# Run comprehensive crew workflow test
python long_duration_crew_test.py 4

# Logs saved to: test_logs/crew_workflow_YYYYMMDD_HHMMSS/
```

### Option 2: Development Test (30 minutes)
```bash
# Quick development test
python long_duration_crew_test.py 0.5
```

### Option 3: Overnight Test (8 hours)
```bash
# Extended overnight testing
python long_duration_crew_test.py 8
```

### Option 4: Quiet Operation (M4 Max Throttled)
```bash
# Set up throttling for quiet fans
python utils/m4_throttling.py 80
nice -n 10 python long_duration_crew_test.py 6
```

## 🎯 What This Tests

### 🏗️ **Complete Crew Workflow System**
- **4-Agent Pipeline**: UX → Planner → Developer → Reviewer
- **Task Validation**: Pre-workflow validation with "JUST BUILD IT" override testing
- **Workflow Iterations**: Multi-iteration refinement loops
- **Quality Gates**: Reviewer acceptance/rejection patterns
- **Agent Performance**: Individual agent execution times and success rates

### 📊 **Task Complexity Levels**

| Level | Weight | Description | Examples |
|-------|--------|-------------|----------|
| **Trivial** | 3.0 | Single-step, clear requests | "What is Python?", "List 5 programming languages" |
| **Simple** | 3.0 | Clear implementation requests | "Write a factorial function", "Create HTML form" |
| **Moderate** | 2.5 | Multi-step projects | "Build REST API with auth", "Create web scraper" |
| **Complex** | 2.0 | Multi-component systems | "Build microservices architecture", "ML pipeline" |
| **Vague** | 1.5 | Ambiguous requests | "Make something cool", "Build an app" |
| **Vague Override** | 2.0 | Vague + "JUST BUILD IT" | "Make something cool - JUST BUILD IT" |

### 🔬 **Validation Behavior Analysis**
- **Pre-workflow Validation**: Tests task specification approval/rejection
- **"JUST BUILD IT" Directive**: Measures override effectiveness
- **Complexity vs Approval Rate**: Correlates task clarity with validation success
- **Reviewer Strictness**: Analyzes post-development quality gates

### 🤖 **Agent Performance Metrics**
- **Individual Agent Times**: UX, Planner, Developer, Reviewer execution durations
- **Success Rates by Agent**: Which agents fail most frequently
- **Token Usage**: LLM token consumption per agent
- **Workflow Iterations**: How many refinement cycles are needed

## 📁 Generated Logs & Reports

### Log Directory Structure
```
test_logs/crew_workflow_YYYYMMDD_HHMMSS/
├── main_test.log              # Overall progress & test execution
├── workflow_performance.log   # Detailed workflow metrics (JSON)
├── agent_performance.log      # Individual agent performance (JSON)
├── task_complexity.log        # Task complexity analysis (JSON)
├── errors.log                 # Failure analysis & stack traces
├── test_summary.json          # Live updating summary (every 5min)
└── final_report.md           # Comprehensive markdown report
```

### Real-Time Monitoring
```bash
# Watch overall progress
tail -f test_logs/crew_workflow_*/main_test.log

# Monitor workflow performance
tail -f test_logs/crew_workflow_*/workflow_performance.log | jq .

# Check agent performance
tail -f test_logs/crew_workflow_*/agent_performance.log | jq .

# View current summary
cat test_logs/crew_workflow_*/test_summary.json | jq .

# Watch for errors
tail -f test_logs/crew_workflow_*/errors.log
```

## 📊 Key Metrics Tracked

### 🎯 **Workflow Metrics**
- **Task Success Rate**: Overall workflow completion percentage
- **Validation Approval Rate**: How often tasks pass initial validation
- **Workflow Completion Rate**: How often approved tasks complete successfully
- **Average Execution Time**: End-to-end workflow duration
- **Iteration Count**: Average refinement cycles needed

### 🤖 **Agent Metrics**
- **Agent Success Rates**: Individual agent failure rates
- **Agent Execution Times**: Performance by role
- **Token Consumption**: LLM usage efficiency
- **Error Patterns**: Common failure modes by agent

### 🧠 **Validation Intelligence**
- **Complexity vs Approval**: How task complexity affects validation
- **Override Effectiveness**: "JUST BUILD IT" success rate improvement
- **Reviewer Strictness**: Post-development acceptance patterns
- **Validation Time**: How long validation takes

### 📈 **Performance Patterns**
- **Model Performance**: How different models handle workflows
- **Time Distribution**: Where time is spent in the pipeline
- **Failure Points**: Where workflows most commonly fail
- **Scalability**: Performance with increasing load

## 🔧 Pre-Flight Checklist

### 1. **Verify LM Studio Setup**
```bash
# Check LM Studio is running
curl http://localhost:1234/v1/models

# Verify you have suitable models
curl http://localhost:1234/v1/models | jq '.data[].id'
```

### 2. **Expected Performance Baselines**
- **Simple Tasks**: 30-60 seconds end-to-end
- **Complex Tasks**: 2-5 minutes end-to-end
- **Validation**: <30 seconds for approval/rejection
- **Success Rate**: >70% for well-specified tasks
- **Override Improvement**: 20-40% better approval rate with "JUST BUILD IT"

### 3. **System Requirements**
- **Memory**: 8GB+ available for model inference
- **Storage**: 500MB+ for logs during 4-hour test
- **Models**: At least one 7B-14B model in LM Studio
- **Network**: Stable localhost connection to LM Studio

## 📋 Sample Task Distribution

### Task Examples by Complexity:

#### **Trivial (Weight 3.0)**
- "What is Python?"
- "List 5 programming languages"
- "Explain what a variable is"
- "Define REST API"

#### **Simple (Weight 3.0)**
- "Write a Python function to calculate factorial"
- "Create a simple HTML contact form"
- "Write a bash script to backup files"
- "Create a basic calculator in Python"

#### **Moderate (Weight 2.5)**
- "Build a REST API for a todo app with authentication"
- "Create a web scraper that saves data to CSV"
- "Build a chat application using WebSockets"
- "Design a database schema for an e-commerce site"

#### **Complex (Weight 2.0)**
- "Build a microservices architecture for user management with Docker"
- "Create a real-time analytics dashboard with React and Python backend"
- "Design and implement a distributed caching system"
- "Build a machine learning pipeline for text classification"

#### **Vague (Weight 1.5)**
- "Make something cool"
- "Build an app"
- "Create a system for managing stuff"
- "I need something automated"

#### **Vague Override (Weight 2.0)**
- "Make something cool - JUST BUILD IT"
- "Build an app. Do your best with what I've given you"
- "Create a system for managing stuff. Just build it the best you can"
- "I need something automated - work with what I've told you"

## 🔍 Analysis Features

### **Validation Pattern Analysis**
- Tracks approval rates by complexity level
- Measures "JUST BUILD IT" override effectiveness
- Identifies validation bottlenecks
- Analyzes correlation between task clarity and success

### **Agent Performance Profiling**
- Individual agent success rates and timing
- Token usage efficiency by agent
- Common failure patterns by role
- Performance degradation over time

### **Workflow Efficiency Analysis**
- End-to-end completion rates
- Iteration requirements by complexity
- Time distribution across agents
- Bottleneck identification

### **Model Capability Assessment**
- Model-specific performance patterns
- Workflow handling capabilities
- Token efficiency analysis
- Reliability under extended use

## 📊 Expected Results (4-Hour Test)

### **Test Volume**
- **Total Tests**: 200-400 tasks
- **Tasks per Hour**: 50-100 (depending on complexity mix)
- **Complexity Distribution**: Weighted by task level weights
- **Model Cycles**: 1-3 models tested (if multiple available)

### **Success Rate Expectations**
- **Trivial/Simple**: 85-95% success rate
- **Moderate**: 70-85% success rate
- **Complex**: 50-70% success rate
- **Vague**: 20-40% success rate
- **Vague Override**: 40-70% success rate (testing override effectiveness)

### **Performance Baselines**
- **Average Task Time**: 45-90 seconds
- **Validation Time**: 5-15 seconds
- **Agent Distribution**: UX(15%) + Planner(25%) + Developer(45%) + Reviewer(15%)
- **Iteration Rate**: 1.2-1.8 iterations per successful task

## 🛠️ Customization

### **Adding New Task Categories**
```python
# Edit TaskComplexity class in long_duration_crew_test.py
NEW_CATEGORY = {
    "level": "custom_level",
    "description": "Custom task type",
    "weight": 2.0,
    "examples": [
        "Your custom task examples here",
        # ...
    ]
}
```

### **Adjusting Test Weights**
```python
# Modify weights in TaskComplexity definitions
SIMPLE["weight"] = 4.0  # Increase simple task frequency
COMPLEX["weight"] = 1.0  # Decrease complex task frequency
```

### **Custom Test Duration**
```bash
# Any decimal hours supported
python long_duration_crew_test.py 1.5   # 90 minutes
python long_duration_crew_test.py 12    # 12 hours
python long_duration_crew_test.py 0.25  # 15 minutes
```

## 🔧 Troubleshooting

### **Common Issues**

#### **No Models Available**
```bash
# Check LM Studio is running and has models loaded
curl http://localhost:1234/v1/models
# If empty, load a model in LM Studio GUI
```

#### **High Memory Usage**
```bash
# Use throttling for M4 Max systems
python utils/m4_throttling.py 70
nice -n 10 python long_duration_crew_test.py 4
```

#### **Test Failures**
- Check `errors.log` for detailed failure analysis
- Verify crew engine setup in main test log
- Monitor agent performance logs for bottlenecks

#### **Performance Issues**
- Use smaller models (7B-8B instead of 13B+)
- Reduce test duration for development
- Monitor system resources during test

### **Debug Mode**
```bash
# Run with increased logging
export PYTHONPATH=/Users/ahughes/dev/crew
python -v long_duration_crew_test.py 0.5
```

## 🎯 Development Workflow

### **Quick Development Test**
```bash
# 15-minute test for development
python long_duration_crew_test.py 0.25
```

### **Targeted Testing**
```bash
# Edit task examples in TaskComplexity to focus on specific scenarios
# Run short tests to validate changes
python long_duration_crew_test.py 0.5
```

### **Performance Tuning**
```bash
# Use performance logs to identify bottlenecks
tail -f test_logs/crew_workflow_*/workflow_performance.log | jq '.execution_time'
```

---

## 📈 Report Analysis

The final report provides:
- **Validation effectiveness analysis**
- **Agent performance rankings**
- **Task complexity success patterns**
- **Workflow efficiency metrics**
- **Model capability assessment**
- **Actionable recommendations for system improvements**

**Start your test**: `python long_duration_crew_test.py 4`

*Happy testing! 🚀*