# Enhanced Provider Setup
# Updated for new modular architecture

import os

from ..providers import get_provider


def interactive_provider_setup() -> tuple[str, str, str] | None:
    """Interactive setup for provider and model selection."""
    print("🚀 Enhanced Crew Assistant - Provider & Model Setup")
    print("=" * 60)

    # Step 1: Select inference mode
    inference_mode = select_inference_mode()
    if not inference_mode:
        print("👋 Setup cancelled.")
        return None

    # Step 2: Handle different inference modes
    if inference_mode == "single":
        return setup_single_model_mode()
    elif inference_mode == "assigned":
        return setup_assigned_tier_mode()
    elif inference_mode == "dynamic":
        return setup_dynamic_mode()
    else:
        print("❌ Invalid inference mode selected.")
        return None


def select_inference_mode() -> str | None:
    """Select inference mode for multi-agent operations."""
    print("\n🧠 Select Inference Mode:")
    print("─" * 50)
    print("1. 🎯 Single Model      - Use one model for all agents (simple)")
    print("2. 📊 Assigned Tiers    - Different models per performance tier (smart)")
    print("3. 🌟 Dynamic Selection - Adaptive model routing (coming soon!)")
    print()

    while True:
        choice = input("Select mode (1-3) or 'q' to quit: ").strip()

        if choice.lower() == "q":
            return None

        if choice == "1":
            print("✅ Selected: Single Model Mode")
            return "single"
        elif choice == "2":
            print("✅ Selected: Assigned Tier Mode")
            return "assigned"
        elif choice == "3":
            print("🎭 Selected: Dynamic Mode")
            return "dynamic"
        else:
            print("❌ Please enter 1, 2, 3, or 'q' to quit")


def setup_single_model_mode() -> tuple[str, str, str] | None:
    """Setup single model for all agents."""
    print("\n🎯 Single Model Mode Setup")
    print("─" * 40)
    print("This mode uses one model for all agent roles.")
    print()

    # Step 1: Select provider
    provider_name = select_provider()
    if not provider_name:
        return None

    # Step 2: Select model from provider
    result = select_model_from_provider(provider_name)
    if not result:
        return None

    model_id, provider_name = result

    # Step 3: Get provider config
    provider_config = _get_provider_config(provider_name)
    api_base = provider_config.get("base_url", "Unknown")

    print("\n🎉 Single Model Setup Complete!")
    print(f"Provider: {provider_name.title()}")
    print(f"Model: {model_id}")
    print(f"API Base: {api_base}")
    print("📋 All agents (UX, Planner, Developer, Reviewer, Commander) will use this model.")

    return model_id, provider_name, api_base


def setup_assigned_tier_mode() -> tuple[str, str, str] | None:
    """Setup tier-specific model assignments."""
    print("\n📊 Assigned Tier Mode Setup")
    print("─" * 45)
    print("This mode assigns different models to performance tiers:")
    print("• Fast Tier    → UX agents (quick responses)")
    print("• Balanced Tier → Planner, Commander agents")
    print("• Capable Tier → Developer, Reviewer agents (complex tasks)")
    print()

    # Get last used model as default
    last_model = os.getenv("OPENAI_API_MODEL", "")
    last_provider = os.getenv("AI_PROVIDER", "")

    if last_model and last_provider:
        print(f"💡 Default: All tiers will use '{last_model}' from {last_provider}")
        use_default = input("Use this for all tiers? (y/n): ").strip().lower()
        if use_default == "y":
            provider_config = _get_provider_config(last_provider)
            api_base = provider_config.get("base_url", "Unknown")

            print("\n🎉 Assigned Tier Setup Complete!")
            print(f"Provider: {last_provider.title()}")
            print(f"Model: {last_model} (all tiers)")
            print(f"API Base: {api_base}")
            return last_model, last_provider, api_base

    # Manual configuration
    print("🔧 Configure tier assignments manually...")

    # For now, fall back to single model selection
    # TODO: Implement per-tier model selection
    print("⚠️ Manual tier configuration coming soon. Using single model for now.")
    return setup_single_model_mode()


def setup_dynamic_mode() -> tuple[str, str, str] | None:
    """Setup dynamic model selection (easter egg)."""
    print("\n🌟 Dynamic Selection Mode")
    print("─" * 35)
    print("🎭 Ah, I see you're feeling adventurous!")
    print("🔮 Dynamic adaptive model routing with:")
    print("   • Real-time performance optimization")
    print("   • Context-aware model switching")
    print("   • Load balancing across providers")
    print("   • Quantum-enhanced decision trees*")
    print()
    print("🚧 This feature is brewing in our secret lab...")
    print("🧪 Expected completion: Q4 2024 (give or take a few decades)")
    print()
    print("*Quantum enhancement may not actually be quantum")
    print()

    continue_choice = (
        input("🎯 Would you like to use Single Model mode instead? (y/n): ").strip().lower()
    )
    if continue_choice == "y":
        return setup_single_model_mode()
    else:
        print("👋 Fair enough! Come back when you're ready for something simpler.")
        return None


def select_provider() -> str | None:
    """Interactive provider selection."""
    print("\n🔧 Select AI Provider:")
    print("─" * 40)

    # Get available providers from registry
    from ..providers.registry import get_registry

    registry = get_registry()
    providers = list(registry._provider_configs.keys())
    available_providers = providers  # For now, assume all are available

    if not available_providers:
        print("❌ No providers are currently online.")
        print("Please start LM Studio or Ollama and try again.")
        return None

    for i, provider_name in enumerate(available_providers):
        config = registry._provider_configs[provider_name]
        status_emoji = "🟢"  # Assume online for now
        print(f"{i + 1}. {status_emoji} {provider_name.title()}")
        print(f"   📍 {config.config.get('base_url', 'N/A')}")
        print()

    while True:
        choice = input(f"Select provider (1-{len(available_providers)}) or 'q' to quit: ").strip()

        if choice.lower() == "q":
            return None

        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue

        try:
            provider_index = int(choice) - 1

            if provider_index < 0 or provider_index >= len(available_providers):
                print(f"❌ Please enter a number between 1 and {len(available_providers)}")
                continue

            selected_provider = available_providers[provider_index]
            print(f"✅ Selected: {selected_provider.title()}")
            return selected_provider

        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(available_providers)}")
            continue


def select_model_from_provider(provider_name: str) -> tuple[str, str] | None:
    """Select a model from the specified provider."""
    print(f"\n🔍 Fetching available models from {provider_name.title()}...")

    # Get provider instance
    provider = get_provider(provider_name)

    try:
        models = provider.list_models()
    except Exception as e:
        print(f"❌ Failed to fetch models: {e}")
        return None

    if not models:
        print(f"⚠️ No models found. Make sure {provider_name.title()} has models loaded.")
        return None

    print(f"\n🧠 Available Models from {provider_name.title()}:")
    print("─" * 80)

    for i, model in enumerate(models):
        status_emoji = {"compatible": "✅", "incompatible": "❌", "unknown": "❓"}[
            model.compatibility
        ]
        print(f"{i + 1:2d}. {status_emoji} {model.compatibility.title()} {model.id}")
        print(f"    📝 {model.description}")
        if model.size:
            print(f"    💾 {model.size}")
        print()

    while True:
        choice = input("Select a model by number (or 'q' to quit): ").strip()

        if choice.lower() == "q":
            return None

        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue

        try:
            model_index = int(choice) - 1
            if model_index < 0 or model_index >= len(models):
                print(f"❌ Please enter a number between 1 and {len(models)}")
                continue

            selected_model = models[model_index]
            model_id = selected_model.id

            print(f"\n🧪 Testing model '{model_id}'...")

            # Test the model
            is_compatible, message = provider.test_model(model_id)

            if is_compatible:
                print(f"✅ {message}")
                print(f"🎯 Model '{model_id}' is now active!")
                return model_id, provider_name
            else:
                print(f"❌ {message}")
                retry = input("Try a different model? (y/n): ").strip().lower()
                if retry != "y":
                    return None
                print()
                continue

        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(models)}")
            continue
        except Exception as e:
            print(f"❌ Error testing model: {e}")
            continue


def _get_provider_config(provider_name: str) -> dict:
    """Get provider configuration."""
    if provider_name == "ollama":
        return {
            "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434").replace("/v1", ""),
            "timeout": 60,
        }
    elif provider_name == "lmstudio":
        return {
            "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
            "api_key": os.getenv("OPENAI_API_KEY", "not-needed-for-local"),
            "timeout": 60,
        }
    else:
        return {}
