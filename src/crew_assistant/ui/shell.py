# Enhanced UX Shell
# Modern shell interface for the new crew system

import os

from ..core import create_crew_engine
from .setup import interactive_provider_setup


def run_enhanced_ux_shell(provider: str = None, model: str = None) -> None:
    """Run the enhanced UX shell with the new crew system."""

    # Check if provider is configured, if not, prompt for setup
    if not provider or not model:
        if not os.getenv("AI_PROVIDER") or not os.getenv("OPENAI_API_MODEL"):
            print("🔧 No AI provider configured. Let's set one up!")
            result = interactive_provider_setup()
            if result:
                model, provider, api_base = result
                # Set environment variables for current session
                os.environ["OPENAI_API_MODEL"] = model
                os.environ["OPENAI_API_BASE"] = api_base
                os.environ["AI_PROVIDER"] = provider
                print("✅ Provider configured!")
            else:
                print("❌ Setup cancelled.")
                return
        else:
            provider = os.getenv("AI_PROVIDER", "lmstudio")
            model = os.getenv("OPENAI_API_MODEL", "unknown")

    # Create crew engine
    try:
        engine = create_crew_engine(
            provider=provider, model=model, verbose=True, save_sessions=True, memory_enabled=True
        )
    except Exception as e:
        print(f"❌ Failed to initialize crew engine: {e}")
        return

    print("\n🧠 Enhanced Crew UX online!")
    print("   🤖 4-Agent Crew: Researcher → Planner → Developer → Reviewer")
    print("   🔄 Quality gates with feedback loops")
    print("   📝 Session logging and memory enabled")
    print("\nType 'exit' to disengage, 'help' for commands.\n")

    while True:
        try:
            user_input = input("👤 > ").strip()

            if user_input.lower() in ("exit", "quit", "q"):
                print("🫡 Enhanced Crew Agent signing off.")
                _show_session_stats(engine)
                break

            if user_input.lower() == "help":
                _show_help()
                continue

            if user_input.lower() == "stats":
                _show_stats(engine)
                continue

            if user_input.lower().startswith("switch "):
                _handle_model_switch(engine, user_input)
                continue

            if not user_input:
                continue

            # Execute task with crew
            print("\n🚀 Deploying 4-agent crew...")
            result = engine.execute_task(user_input)

            if result.success:
                print("\n✅ Task completed successfully!")
                print(
                    f"📊 {result.iterations_count} iteration(s), {result.total_execution_time:.1f}s"
                )
                print("\n📋 Final Deliverable:")
                print("─" * 80)
                print(result.final_output)
                print("─" * 80)
            else:
                # Handle different failure types
                if hasattr(result, "status") and result.status.value == "needs_clarification":
                    print("\n📋 Task specification needs clarification:")
                    print("─" * 80)
                    print(result.final_output)
                    print("─" * 80)
                    print("\n💡 Please provide a more detailed or specific request and try again.")
                else:
                    print(f"\n❌ Task failed: {result.error_message}")
                    if result.steps:
                        print(
                            f"📊 Completed {len([s for s in result.steps if s.result and s.result.success])}/{len(result.steps)} steps"
                        )

            print()  # Add spacing

        except KeyboardInterrupt:
            print("\n🫡 Enhanced Crew Agent signing off.")
            _show_session_stats(engine)
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue


def _show_help():
    """Show help commands."""
    print("""
🤖 Enhanced Crew Commands:
─────────────────────────────
  help         Show this help
  stats        Show crew statistics
  switch MODEL Switch to different model
  exit/quit/q  Exit the shell

🧠 How it works:
  1. Researcher analyzes your request
  2. Planner creates implementation roadmap
  3. Developer builds the solution
  4. Reviewer validates & may reject for revision

  The crew will iterate up to 3 times until quality standards are met!
""")


def _show_stats(engine):
    """Show engine statistics."""
    stats = engine.stats
    print(f"""
📊 Crew Statistics:
─────────────────────
  Session ID: {stats["session_id"][:8]}...
  Tasks Executed: {stats["tasks_executed"]}
  Success Rate: {stats["success_rate"]:.1%}

🤖 Agent Stats:
""")
    for role, agent_stats in stats["crew_stats"].items():
        print(f"  {role}: {agent_stats['executions']} executions")


def _show_session_stats(engine):
    """Show session summary."""
    stats = engine.stats
    print(f"""
📝 Session Summary:
──────────────────
  Tasks completed: {stats["tasks_executed"]}
  Success rate: {stats["success_rate"]:.1%}
  Session saved to: crew_runs/
""")


def _handle_model_switch(engine, user_input):
    """Handle model switching."""
    parts = user_input.split(" ", 1)
    if len(parts) < 2:
        print("❌ Usage: switch MODEL_NAME")
        return

    new_model = parts[1].strip()
    try:
        engine.switch_model(new_model)
        print(f"✅ Switched to model: {new_model}")
    except Exception as e:
        print(f"❌ Failed to switch model: {e}")


if __name__ == "__main__":
    run_enhanced_ux_shell()
