import os
import importlib
import sys
import pathlib

# Ensure the repo root is on sys.path (when running this script from the scripts/ folder)
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Ensure agent won't raise at import due to missing API key
os.environ.setdefault("GOOGLE_API_KEY", "DUMMY_KEY_FOR_LOCAL_TEST")

try:
    agent = importlib.import_module("agent")
except Exception as e:
    print("ERROR: failed to import agent.py:\n", e)
    sys.exit(1)


def _stub_call_llm(user_message, history):
    # Simulate the LLM returning a generate_plan action
    return {
        "action": "generate_plan",
        "params": {"daily_hours": 2, "num_days": 3},
        "assistant_message": "Here's a generated study plan:",
    }


# Monkeypatch the LLM caller to avoid external network calls
agent._call_llm = _stub_call_llm


def main():
    prompt = "Please create a 3-day study plan with 2 hours/day"
    print("Prompt:", prompt)
    try:
        reply = agent.handle_user_message(prompt, history=[])
    except Exception as e:
        print("ERROR: agent raised during handle_user_message:\n", e)
        sys.exit(1)

    print("\nAgent Response:\n")
    print(reply)


if __name__ == "__main__":
    main()
