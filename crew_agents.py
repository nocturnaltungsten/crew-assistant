"""CLI entrypoint for running the default crew."""
from crew_assistant import run_crew

if __name__ == "__main__":
    result = run_crew()
    print("\n✅ Mission Complete:\n")
    print(result)
