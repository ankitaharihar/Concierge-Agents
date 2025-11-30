# main.py — entrypoint for ChronoKen agent (clean + reliable .env loading)
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict

# --- Load .env from project root (guaranteed) ---
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
print("MAIN: env_path =", env_path)

# If .env contains a BOM, remove it (idempotent)
if env_path.exists():
    raw = env_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        env_path.write_bytes(raw.lstrip(b"\xef\xbb\xbf"))
    load_dotenv(env_path, override=True)
    print("MAIN: .env loaded, GOOGLE_API_KEY prefix:", (os.getenv("GOOGLE_API_KEY") or "None")[:12] + "...")
else:
    # Still attempt to load from OS environment if present
    load_dotenv(override=True)
    print("MAIN: .env not found; environment variables will be used if set.")
    print("MAIN: GOOGLE_API_KEY prefix:", (os.getenv("GOOGLE_API_KEY") or "None")[:12] + "...")

# Import agent AFTER loading env so agent sees API key at import time
from agent import handle_user_message


def main():
    print("\n=== Smart Study Concierge Agent (ChronoKen) ===")
    print("Type 'exit' or 'quit' to stop.\n")

    history: List[Dict[str, str]] = []

    try:
        while True:
            user_message = input("You: ").strip()
            if not user_message:
                continue
            if user_message.lower() in {"exit", "quit"}:
                print("Agent: Bye! Stay productive ✨")
                break

            assistant_message = handle_user_message(user_message, history)
            print("\nAgent:", assistant_message, "\n")

            history.append({"user": user_message, "assistant": assistant_message})
    except KeyboardInterrupt:
        print("\nAgent: Goodbye (keyboard interrupt).")


if __name__ == "__main__":
    main()
