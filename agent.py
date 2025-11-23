import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv
from google import genai  # ✅ new SDK

from tools import create_task, list_tasks, update_task_status, generate_plan, get_today_view


# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

# ✅ Create a GenAI client (new SDK)
client = genai.Client(api_key=API_KEY)


SYSTEM_PROMPT = """
You are a Smart Study & Productivity Concierge Agent for students.

You have access to the following ACTIONS (these are not function calls, just logical actions):

1. create_task
   Use when the user wants to add a new task, assignment, exam, or study item.
   Parameters:
     - title (string)
     - deadline (string, 'YYYY-MM-DD')
     - estimated_hours (number)
     - priority (string: 'low' | 'medium' | 'high')

2. list_tasks
   Use when the user wants to see existing tasks.
   Parameters:
     - status (optional string: 'pending' | 'in_progress' | 'done')

3. update_task_status
   Use when the user marks a task as started/completed/etc.
   Parameters:
     - task_id (integer)
     - new_status (string: 'pending' | 'in_progress' | 'done')

4. generate_plan
   Use when the user wants a study plan or schedule.
   Parameters:
     - daily_hours (number, default 3)
     - num_days (integer, default 7)

5. chat_only
   Use when the user is just chatting, asking for motivation, or questions
   that do not require modifying tasks or generating a plan.

IMPORTANT:
- ALWAYS respond in VALID JSON ONLY.
- NO extra text, no commentary outside JSON.
- JSON format:

{
  "action": "create_task | list_tasks | update_task_status | generate_plan | chat_only",
  "params": { ... appropriate parameters ... },
  "assistant_message": "Natural language reply to the user."
}
"""


def _call_llm(user_message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Send the conversation to the LLM and parse the JSON response.
    history: list of {"user": "...", "assistant": "..."} for previous turns
    """
    conversation = ""
    for turn in history:
        conversation += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"

    prompt = SYSTEM_PROMPT + "\n\n" + conversation + f"User: {user_message}\nAssistant:"

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",   # light & fast model
            contents=prompt,
        )
        raw = getattr(response, "text", None) or str(response)
        raw = raw.strip()
    except Exception as e:
        # 🔴 If LLM fails (429/quota, network, etc.), fall back gracefully
        return {
            "action": "chat_only",
            "params": {},
            "assistant_message": f"""LLM request failed: {e}

You can still use me with explicit commands like:
- add task: title=DBMS assignment, deadline=2025-11-25, hours=3, priority=high
- list tasks
- plan: daily_hours=2 num_days=3
""",
        }

    # In case the model wraps JSON in ```json ... ``` fences
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    # Try to extract JSON object
    start = raw.find("{")
    end = raw.rfind("}")
    json_str = raw[start:end + 1] if start != -1 and end != -1 else ""

    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        data = {
            "action": "chat_only",
            "params": {},
            "assistant_message": raw,
        }

    data.setdefault("action", "chat_only")
    data.setdefault("params", {})
    data.setdefault("assistant_message", "")
    return data


def handle_user_message(user_message: str, history: List[Dict[str, str]]) -> str:
    """
    Main entry point for the app.
    - Calls LLM
    - Executes tools based on 'action'
    - Returns assistant_message (augmented with tool results if needed)
    """
    llm_output = _call_llm(user_message, history)
    action = llm_output.get("action", "chat_only")
    params = llm_output.get("params", {}) or {}
    assistant_message = llm_output.get("assistant_message", "")

    # Tool execution
    if action == "create_task":
        task = create_task(
            title=params.get("title", "Untitled task"),
            deadline=params.get("deadline", "2099-12-31"),
            estimated_hours=params.get("estimated_hours", 1),
            priority=params.get("priority", "medium"),
        )
        assistant_message += f"\n\n[Task created with ID {task['id']}]"

    elif action == "list_tasks":
        tasks = list_tasks(status=params.get("status"))
        if not tasks:
            assistant_message += "\n\nYou currently have no tasks matching that filter."
        else:
            assistant_message += "\n\nHere are your tasks:\n"
            for t in tasks:
                assistant_message += (
                    f"- ID {t['id']}: {t['title']} "
                    f"(deadline: {t['deadline']}, "
                    f"hours: {t['estimated_hours']}, "
                    f"priority: {t['priority']}, "
                    f"status: {t['status']})\n"
                )

    elif action == "update_task_status":
        ok = update_task_status(
            task_id=params.get("task_id"),
            new_status=params.get("new_status", "pending"),
        )
        if ok:
            assistant_message += "\n\n[Task status updated successfully.]"
        else:
            assistant_message += "\n\n[I couldn’t find that task ID. Please check and try again.]"

    elif action == "generate_plan":
        daily_hours = params.get("daily_hours", 3)
        num_days = params.get("num_days", 7)
        plan = generate_plan(daily_hours=daily_hours, num_days=num_days)

        assistant_message += "\n\nHere’s your study plan:\n"
        for date, slots in plan.items():
            assistant_message += f"\n📅 {date}\n"
            if not slots:
                assistant_message += "  - No tasks scheduled.\n"
                continue
            for s in slots:
                assistant_message += f"  - {s['title']} ({s['hours']} hours) [Task ID {s['task_id']}]\n"

    return assistant_message
