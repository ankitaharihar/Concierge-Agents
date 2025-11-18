from typing import List, Dict
from agent import handle_user_message


def main():
    print("=== Smart Study Concierge Agent ===")
    print("Type 'exit' to quit.\n")

    history: List[Dict[str, str]] = []

    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            print("Agent: Bye! Stay productive ✨")
            break

        assistant_message = handle_user_message(user_message, history)
        print("\nAgent:", assistant_message, "\n")

        history.append({"user": user_message, "assistant": assistant_message})


if __name__ == "__main__":
    main()
