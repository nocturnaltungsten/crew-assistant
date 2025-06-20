import subprocess
import pyperclip
from datetime import datetime

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stderr:
        print(f"[stderr] {result.stderr.strip()}")
    return result.stdout.strip()

def get_git_diff_report():
    # Fetch latest remote changes (optional if you always pull manually)
    subprocess.run("git fetch origin", shell=True)

    # Get diff summary
    status_output = run_cmd("git status --short")
    diff_output = run_cmd("git diff --stat origin/main")

    # Timestamp for context
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Compose report
    report_lines = [
        f"🕒 Git Diff Report — {now}",
        "========================================",
        "",
        "🔍 Changed Files (vs origin/main):",
        status_output or "(No local changes)",
        "",
        "📊 Diff Summary:",
        diff_output or "(No diffs)",
        ""
    ]
    report = "\n".join(report_lines)

    return report

if __name__ == "__main__":
    report = get_git_diff_report()
    print(report)
    try:
        pyperclip.copy(report)
        print("\n✅ Copied diff report to clipboard.")
    except Exception as e:
        print(f"\n⚠️ Failed to copy to clipboard: {e}")
