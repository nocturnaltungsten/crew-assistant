# Simple Chat Mode - Direct LM Studio API without CrewAI
# Bypasses CrewAI to work with models that only support user/assistant roles

import os
import json
import requests
from datetime import datetime
from typing import Optional

def simple_chat_session(raw_mode: bool = False) -> None:
    """
    Simple chat session that talks directly to LM Studio API.
    Only uses user/assistant roles - no system messages.
    """
    api_base = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
    api_key = os.getenv("OPENAI_API_KEY", "not-needed")
    model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
    
    print("🤖 Simple Chat Mode (Direct API)")
    print("💡 This mode works with any model that supports user/assistant roles")
    print("💡 Type 'exit' to quit\n")
    
    conversation = []
    
    while True:
        try:
            user_input = input("👤 > ").strip()
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                print("👋 Chat session ended")
                break
                
            if not user_input:
                continue
            
            # Add user message to conversation
            conversation.append({"role": "user", "content": user_input})
            
            # Keep conversation manageable (last 10 exchanges)
            if len(conversation) > 20:
                conversation = conversation[-20:]
            
            # Make API call
            response = call_lm_studio_api(
                api_base=api_base,
                api_key=api_key,
                model=model,
                messages=conversation
            )
            
            if response:
                # Add assistant response to conversation
                conversation.append({"role": "assistant", "content": response})
                
                # Display response
                if raw_mode:
                    print(response)
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    border = "─" * 60
                    print(f"\n🤖 Assistant │ {timestamp}\n{border}")
                    print(response)
                    print(f"{border}\n")
            else:
                print("❌ No response received")
                
        except KeyboardInterrupt:
            print("\n👋 Chat session ended")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def call_lm_studio_api(
    api_base: str, 
    api_key: str, 
    model: str, 
    messages: list,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Optional[str]:
    """Make a direct API call to LM Studio."""
    
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_api_connection() -> bool:
    """Test if we can connect to LM Studio API."""
    api_base = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
    
    try:
        response = requests.get(f"{api_base}/models", timeout=5)
        if response.status_code == 200:
            models = response.json().get("data", [])
            if models:
                print(f"✅ Connected to LM Studio - {len(models)} model(s) available")
                return True
            else:
                print("⚠️ Connected to LM Studio but no models loaded")
                return False
        else:
            print(f"❌ LM Studio API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to LM Studio: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple chat with LM Studio")
    parser.add_argument("--raw", action="store_true", help="Raw output mode")
    args = parser.parse_args()
    
    if test_api_connection():
        simple_chat_session(raw_mode=args.raw)
    else:
        print("💡 Make sure LM Studio is running with a model loaded")