# Compute Throttling Utilities
# Optional GPU throttling for testing to avoid overheating

import subprocess
import sys
from typing import Optional


def set_gpu_power_limit(limit_percent: int = 80) -> bool:
    """
    Set GPU power limit for testing (NVIDIA only, optional).

    Args:
        limit_percent: GPU power limit as percentage (default 80%)

    Returns:
        bool: True if successful, False if failed or not available
    """
    try:
        # Check if nvidia-smi is available
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print("ℹ️  NVIDIA GPU not detected or nvidia-smi not available")
            return False

        gpu_names = result.stdout.strip().split("\n")
        print(f"🔍 Found {len(gpu_names)} NVIDIA GPU(s): {', '.join(gpu_names)}")

        # Get current power limit
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=power.max_limit", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            current_limits = [float(x.strip()) for x in result.stdout.strip().split("\n")]

            # Set power limit for each GPU
            success_count = 0
            for i, (gpu_name, max_power) in enumerate(zip(gpu_names, current_limits)):
                target_power = max_power * (limit_percent / 100.0)

                try:
                    subprocess.run(
                        ["nvidia-smi", "-i", str(i), "-pl", str(int(target_power))],
                        capture_output=True,
                        check=True,
                        timeout=5,
                    )
                    print(
                        f"✅ GPU {i} ({gpu_name}): Set power limit to {int(target_power)}W ({limit_percent}% of {max_power}W)"
                    )
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to set power limit for GPU {i}: {e}")
                except Exception as e:
                    print(f"⚠️  Error setting power limit for GPU {i}: {e}")

            return success_count > 0

        return False

    except subprocess.TimeoutExpired:
        print("⚠️  nvidia-smi timeout - GPU throttling not available")
        return False
    except FileNotFoundError:
        print("ℹ️  nvidia-smi not found - GPU throttling not available")
        return False
    except Exception as e:
        print(f"⚠️  GPU throttling error: {e}")
        return False


def reset_gpu_power_limit() -> bool:
    """
    Reset GPU power limit to maximum.

    Returns:
        bool: True if successful, False if failed or not available
    """
    try:
        # Check if nvidia-smi is available
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,power.default_limit", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return False

        lines = result.stdout.strip().split("\n")
        success_count = 0

        for i, line in enumerate(lines):
            parts = line.split(", ")
            if len(parts) >= 2:
                gpu_name = parts[0]
                default_power = parts[1]

                try:
                    subprocess.run(
                        ["nvidia-smi", "-i", str(i), "-pl", default_power],
                        capture_output=True,
                        check=True,
                        timeout=5,
                    )
                    print(f"🔄 GPU {i} ({gpu_name}): Reset power limit to {default_power}W")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to reset power limit for GPU {i}: {e}")

        return success_count > 0

    except Exception as e:
        print(f"⚠️  GPU reset error: {e}")
        return False


def get_gpu_info() -> Optional[dict]:
    """
    Get current GPU information and power usage.

    Returns:
        dict: GPU information or None if not available
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        gpus = []
        for i, line in enumerate(result.stdout.strip().split("\n")):
            parts = [p.strip() for p in line.split(", ")]
            if len(parts) >= 7:
                gpus.append(
                    {
                        "id": i,
                        "name": parts[0],
                        "temperature": f"{parts[1]}°C",
                        "power_draw": f"{parts[2]}W",
                        "power_limit": f"{parts[3]}W",
                        "gpu_utilization": f"{parts[4]}%",
                        "memory_used": f"{parts[5]}MB",
                        "memory_total": f"{parts[6]}MB",
                    }
                )

        return {"gpus": gpus, "count": len(gpus)}

    except Exception:
        return None


def print_gpu_status():
    """Print current GPU status for monitoring."""
    gpu_info = get_gpu_info()

    if not gpu_info:
        print("ℹ️  No NVIDIA GPU information available")
        return

    print(f"\n📊 GPU Status ({gpu_info['count']} GPU{'s' if gpu_info['count'] > 1 else ''}):")
    print("─" * 80)

    for gpu in gpu_info["gpus"]:
        print(f"GPU {gpu['id']}: {gpu['name']}")
        print(f"  🌡️  Temperature: {gpu['temperature']}")
        print(f"  ⚡ Power: {gpu['power_draw']} / {gpu['power_limit']}")
        print(f"  🔥 Utilization: {gpu['gpu_utilization']}")
        print(f"  💾 Memory: {gpu['memory_used']} / {gpu['memory_total']}")
        print()


if __name__ == "__main__":
    """Command line interface for GPU throttling."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "throttle":
            limit = 80
            if len(sys.argv) > 2:
                try:
                    limit = int(sys.argv[2])
                except ValueError:
                    print("Invalid limit percentage")
                    sys.exit(1)

            print(f"🔧 Setting GPU power limit to {limit}%...")
            success = set_gpu_power_limit(limit)
            sys.exit(0 if success else 1)

        elif command == "reset":
            print("🔄 Resetting GPU power limits...")
            success = reset_gpu_power_limit()
            sys.exit(0 if success else 1)

        elif command == "status":
            print_gpu_status()
            sys.exit(0)

        else:
            print("Usage: python compute_throttling.py [throttle|reset|status] [limit_percent]")
            sys.exit(1)
    else:
        print_gpu_status()
