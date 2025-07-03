# Enhanced Crew Assistant - Main Entry Point
# Clean, modular multi-agent system

import argparse
import os
import sys

from .core import CrewEngine, create_crew_engine
from .ui import interactive_provider_setup, run_enhanced_ux_shell
from .workflows.base import WorkflowResult


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Crew Assistant - Modular AI orchestration platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Enhanced UX shell mode (default)
  %(prog)s --setup            # Interactive provider and model setup
  %(prog)s --crew "task"      # Direct crew execution
        """,
    )

    parser.add_argument("--setup", action="store_true", help="Interactive provider and model setup")
    parser.add_argument("--crew", metavar="TASK", help="Execute task directly with crew")
    parser.add_argument("--provider", help="Override provider (ollama/lmstudio)")
    parser.add_argument("--model", help="Override model")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Provider and model setup
    if args.setup:
        setup_result = interactive_provider_setup()
        if setup_result:
            model_id, provider, api_base = setup_result
            # Set environment variables for current session
            os.environ["OPENAI_API_MODEL"] = model_id
            os.environ["OPENAI_API_BASE"] = api_base
            os.environ["AI_PROVIDER"] = provider
            print("\n✅ Environment configured for this session!")
            print("You can now run: python main.py")
        return

    # Direct crew execution
    if args.crew:
        provider = args.provider or os.getenv("AI_PROVIDER") or ""
        model = args.model or os.getenv("OPENAI_API_MODEL") or ""

        if not provider or not model:
            print("❌ Provider and model must be configured.")
            print("Run: python main.py --setup")
            return

        try:
            engine: CrewEngine = create_crew_engine(
                provider=provider, model=model, verbose=args.verbose
            )

            print(f"🚀 Executing task with {provider}/{model}...")
            result: WorkflowResult = engine.execute_task(args.crew)

            if result.success:
                print("\n✅ Task completed successfully!")
                print(result.final_output)
            else:
                print(f"\n❌ Task failed: {result.error_message}")
                sys.exit(1)

        except Exception as e:
            print(f"❌ Execution failed: {e}")
            sys.exit(1)
        return

    # Default to enhanced UX shell - auto-run setup if not configured
    provider = args.provider or os.getenv("AI_PROVIDER") or ""
    model = args.model or os.getenv("OPENAI_API_MODEL") or ""

    if not provider or not model:
        print("🚀 Enhanced Crew Assistant - First Time Setup")
        print("=" * 60)
        print("No AI provider configured. Let's set that up!")
        print()

        setup_result = interactive_provider_setup()
        if setup_result:
            model_id, provider_name, api_base = setup_result
            # Set environment variables for current session
            os.environ["OPENAI_API_MODEL"] = model_id
            os.environ["OPENAI_API_BASE"] = api_base
            os.environ["AI_PROVIDER"] = provider_name
            print("\n✅ Environment configured for this session!")
            provider, model = provider_name, model_id
        else:
            print("❌ Setup cancelled. Cannot proceed without configuration.")
            return

    print("🧠 Starting Enhanced Crew Assistant")
    print(f"🤖 Using: {provider}/{model}")
    print()

    run_enhanced_ux_shell(provider=provider, model=model)


if __name__ == "__main__":
    main()
