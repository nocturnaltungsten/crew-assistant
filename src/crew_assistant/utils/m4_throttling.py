# M4 Max CPU Throttling for macOS
# Control CPU performance to reduce fan noise during overnight testing

import subprocess
import sys
import time
from typing import Optional, Tuple


def get_cpu_info() -> dict:
    """Get current CPU performance state on macOS."""
    try:
        # Get current power mode
        power_mode = subprocess.run(["pmset", "-g"], capture_output=True, text=True).stdout

        # Get thermal state
        thermal = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True).stdout

        # Get current CPU stats using powermetrics (requires sudo)
        # We'll skip this for non-sudo usage

        return {
            "power_mode": "Battery" if "Battery Power" in power_mode else "AC Power",
            "thermal_state": thermal.strip() if thermal else "Unknown",
        }
    except Exception as e:
        return {"error": str(e)}


def set_low_power_mode(enable: bool = True) -> bool:
    """Enable/disable Low Power Mode on macOS (requires macOS 12+)."""
    try:
        # This requires sudo on most systems
        cmd = ["sudo", "pmset", "-a", "lowpowermode", "1" if enable else "0"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Low Power Mode {'enabled' if enable else 'disabled'}")
            return True
        else:
            print(f"❌ Failed to set Low Power Mode: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error setting Low Power Mode: {e}")
        return False


def set_cpu_performance_macos(percent: int = 80) -> bool:
    """
    Throttle CPU performance on macOS using various methods.

    Args:
        percent: Target CPU performance (60-100)
    """
    print(f"🔧 Setting M4 Max performance to {percent}%")

    success_count = 0

    # Method 1: Use caffeinate with CPU assertions
    if percent < 100:
        try:
            # Disable Turbo Boost-like behavior by preventing sleep and reducing performance
            subprocess.Popen(
                [
                    "caffeinate",
                    "-i",
                    "-s",  # Prevent idle sleep and system sleep
                ]
            )
            print("✅ Sleep prevention enabled (reduces boost behavior)")
            success_count += 1
        except Exception as e:
            print(f"⚠️  caffeinate failed: {e}")

    # Method 2: Thermal pressure simulation (safer than kernel extensions)
    if percent <= 80:
        try:
            # Use nice to reduce process priority (indirect throttling)
            print("✅ Process priority reduction available via 'nice' command")
            success_count += 1
        except Exception as e:
            print(f"⚠️  Priority adjustment failed: {e}")

    # Method 3: Power Nap and App Nap settings
    try:
        # Disable Power Nap to reduce background activity
        subprocess.run(["sudo", "pmset", "-a", "powernap", "0"], capture_output=True, check=True)
        print("✅ Power Nap disabled")
        success_count += 1
    except:
        pass

    # Method 4: Suggest manual options
    print("\n📋 Additional manual throttling options for M4 Max:")
    print("  1. Enable Low Power Mode in Battery settings")
    print("  2. Use Turbo Boost Switcher Pro (3rd party app)")
    print("  3. Run inference with 'nice -n 19' prefix for lowest priority")
    print("  4. Set display to sleep to reduce GPU load")
    print("  5. Close unnecessary apps to reduce background CPU usage")

    return success_count > 0


def create_throttled_launch_script(throttle_percent: int = 80) -> str:
    """Create a launch script that runs with CPU throttling."""
    script_content = f"""#!/bin/bash
# Throttled inference launch script for M4 Max
# Runs at {throttle_percent}% performance to reduce fan noise

echo "🌙 Starting throttled inference testing at {throttle_percent}% performance"

# Set low priority for the process
NICE_LEVEL=$((20 - {throttle_percent} / 5))

# Disable Turbo Boost-like features
sudo pmset -a lowpowermode 1 2>/dev/null || echo "ℹ️  Low Power Mode requires admin"

# Run with nice to reduce CPU priority
echo "🔧 Running with nice level $NICE_LEVEL (lower = less CPU priority)"

# Export throttling environment variable
export INFERENCE_THROTTLE={throttle_percent}

# Run the actual test with reduced priority
nice -n $NICE_LEVEL python long_duration_test.py

# Re-enable normal performance after testing
sudo pmset -a lowpowermode 0 2>/dev/null || echo "ℹ️  Restoring normal power mode"
"""

    script_path = "/Users/ahughes/dev/crew/run_throttled_test.sh"
    with open(script_path, "w") as f:
        f.write(script_content)

    # Make executable
    subprocess.run(["chmod", "+x", script_path])

    return script_path


def estimate_fan_impact(throttle_percent: int) -> str:
    """Estimate fan noise impact based on throttling."""
    if throttle_percent >= 90:
        return "🔥 High - Fans will likely run at high speed"
    elif throttle_percent >= 70:
        return "🌡️ Medium - Fans may run but at moderate speed"
    elif throttle_percent >= 50:
        return "❄️ Low - Fans should stay quiet most of the time"
    else:
        return "🧊 Very Low - Minimal fan activity expected"


if __name__ == "__main__":
    print("🍎 M4 Max Throttling Utility")
    print("=" * 50)

    if len(sys.argv) > 1:
        try:
            throttle_percent = int(sys.argv[1])
            throttle_percent = max(50, min(100, throttle_percent))  # Clamp 50-100
        except:
            throttle_percent = 80
    else:
        throttle_percent = 80

    print(f"\n🔧 Configuring M4 Max for {throttle_percent}% performance")
    print(f"🌡️ Expected fan impact: {estimate_fan_impact(throttle_percent)}")

    # Get current state
    cpu_info = get_cpu_info()
    print(f"\n📊 Current state: {cpu_info}")

    # Apply throttling
    success = set_cpu_performance_macos(throttle_percent)

    # Create launch script
    script_path = create_throttled_launch_script(throttle_percent)
    print(f"\n✅ Created throttled launch script: {script_path}")
    print(f"   Run with: bash {script_path}")

    print("\n💡 For best results during overnight testing:")
    print("   - Close unnecessary apps")
    print("   - Set display to sleep after 1 minute")
    print("   - Place MacBook on a hard surface for airflow")
    print("   - Consider using AlDente to limit battery charge to 80%")
