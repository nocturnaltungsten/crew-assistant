#!/bin/bash
# Throttled inference launch script for M4 Max
# Runs at 80% performance to reduce fan noise

echo "🌙 Starting throttled inference testing at 80% performance"

# Set low priority for the process
NICE_LEVEL=$((20 - 80 / 5))

# Disable Turbo Boost-like features
sudo pmset -a lowpowermode 1 2>/dev/null || echo "ℹ️  Low Power Mode requires admin"

# Run with nice to reduce CPU priority
echo "🔧 Running with nice level $NICE_LEVEL (lower = less CPU priority)"

# Export throttling environment variable
export INFERENCE_THROTTLE=80

# Run the actual test with reduced priority
nice -n $NICE_LEVEL python long_duration_test.py

# Re-enable normal performance after testing
sudo pmset -a lowpowermode 0 2>/dev/null || echo "ℹ️  Restoring normal power mode"
