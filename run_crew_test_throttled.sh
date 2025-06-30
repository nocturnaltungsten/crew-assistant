#!/bin/bash
# Throttled Crew Workflow Test Runner
# Optimized for quiet M4 Max operation

set -e

# Get duration parameter (default 4 hours)
DURATION=${1:-4}

echo "🧠 Starting Throttled Crew Workflow Test"
echo "⏱️  Duration: ${DURATION} hours"
echo "🔧 Setting up M4 Max throttling for quiet operation..."

# Set up M4 Max throttling at 80% for quiet fans
python utils/m4_throttling.py 80

# Enable low power mode for thermal management
sudo pmset -a lowpowermode 1

# Prevent system sleep during test
caffeinate -d -i -m -s &
CAFFEINATE_PID=$!

echo "💤 System sleep disabled, low power mode enabled"
echo "🚀 Starting crew workflow test..."

# Run the test with low priority
nice -n 10 python long_duration_crew_test.py ${DURATION}

# Cleanup
echo "🧹 Cleaning up..."
kill $CAFFEINATE_PID 2>/dev/null || true
sudo pmset -a lowpowermode 0

echo "✅ Crew workflow test completed!"
echo "📁 Check test_logs/crew_workflow_*/ for results"