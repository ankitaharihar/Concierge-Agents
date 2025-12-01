# agent.py - ChronoKen agent core (clean, robust, safe for missing SDK)
import os
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional

# Load .env explicitly from project root so environment is available at import time
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent
_env_path = _project_root / ".env"
if _env_path.exists():
    raw = _env_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        _env_path.write_bytes(raw.lstrip(b"\xef\xbb\xbf"))
    load_dotenv(_env_path, override=True)
else:
    # still try loading from environment
    load_dotenv(override=True)

print("AGENT.PY loaded GOOGLE_API_KEY prefix:", (os.getenv("GOOGLE_API_KEY") or "None")[:12] + "...")
print("AGENT: env_path =", _env_path)

# Import correct GenAI SDK (google-generativeai). Make import safe if not installed.
GENAI_AVAILABLE = False
genai = None
try:
    import google.generativeai as genai  # correct SDK
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

# Tools (local)
from tools import create_task, list_tasks, update_task_status, generate_plan, get_today_view

# Read config from env
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME") or "models/gemini-2.5-pro"

# Configure SDK if possible
model = None
if GENAI_AVAILABLE and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
        print("AGENT: GenAI initialized with model:", MODEL_NAME)
    except Exception as e:
        print("AGENT: GenAI configure/instantiate failed:", type(e).__name__, e)
        model = None
else:
    if not GENAI_AVAILABLE:
        print("AGENT: google.generativeai SDK not installed.")
    if not API_KEY:
        print("AGENT: GOOGLE_API_KEY not set; GenAI disabled.")


# Small caches used to reduce repeated LLM calls
class LRUCache:
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        v = self.data.get(key)
        if v is not None:
            self.data.move_to_end(key)
        return v

    def set(self, key, value):
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)


class TTLCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.store = {}
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            v = self.store.get(key)
            if not v:
                return None
            value, exp = v
            if time.time() > exp:
                del self.store[key]
                return None
            return value

    def set(self, key, value, ttl: Optional[int] = None):
        with self.lock:
            exp = time.time() + (ttl if ttl is not None else self.ttl)
            self.store[key] = (value, exp)


RESPONSE_CACHE = TTLCache(ttl=300)
_CACHE = LRUCache(capacity=256)


def _history_to_key(user_message: str, history: List[Dict[str, str]]) -> str:
    import hashlib
    last = history[-6:] if history else []
    s = user_message + "||" + "::".join(f"{t.get('user','')}->{t.get('assistant','')}" for t in last)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _truncate_history_by_chars(history: List[Dict[str, str]], max_chars: int = 4000) -> List[Dict[str, str]]:
    if not history:
        return history
    total = sum(len(t.get("user", "")) + len(t.get("assistant", "")) for t in history)
    if total <= max_chars:
        return history
    out = history.copy()
    while out and total > max_chars:
        oldest = out.pop(0)
        total -= (len(oldest.get("user", "")) + len(oldest.get("assistant", "")))
    return out


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
    # prepare prompt
    history_trunc = _truncate_history_by_chars(history, max_chars=4000)
    conv = ""
    for turn in history_trunc:
        conv += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
    prompt = SYSTEM_PROMPT + "\n\n" + conv + f"User: {user_message}\nAssistant:"

    # If GenAI not available, return helpful fallback
    if model is None:
        reasons = []
        if not GENAI_AVAILABLE:
            reasons.append("GenAI SDK not installed (python package 'google.generativeai')")
        if not API_KEY:
            reasons.append("GOOGLE_API_KEY not set in .env or environment")
        reason_text = "; ".join(reasons) if reasons else "GenAI client not available"
        return {
            "action": "chat_only",
            "params": {},
            "assistant_message": (
                f"LLM unavailable: {reason_text}\n\n"
                "You can still use me with explicit commands like:\n"
                "- add task: title=DBMS assignment, deadline=2025-11-25, hours=3, priority=high\n"
                "- list tasks\n"
                "- plan: daily_hours=2 num_days=3\n"
            ),
        }

    try:
        # Use the high-level model object (works with google-generativeai)
        resp = model.generate_content(prompt)
        raw = getattr(resp, "text", None) or str(resp)
        raw = raw.strip()
    except Exception as e:
        return {
            "action": "chat_only",
            "params": {},
            "assistant_message": f"LLM request failed: {e}\n\nYou can still use explicit commands (add/list/plan).",
        }

    # If model returns fenced JSON, remove fences
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    # Try to extract JSON blob
    start = raw.find("{")
    end = raw.rfind("}")
    json_str = raw[start:end + 1] if start != -1 and end != -1 else ""

    try:
        data = json.loads(json_str) if json_str else {"action": "chat_only", "params": {}, "assistant_message": raw}
    except (json.JSONDecodeError, ValueError):
        data = {"action": "chat_only", "params": {}, "assistant_message": raw}

    data.setdefault("action", "chat_only")
    data.setdefault("params", {})
    data.setdefault("assistant_message", "")
    return data


def handle_user_message(user_message: str, history: List[Dict[str, str]]) -> str:
    # Delegate to structured processor and return assistant_message for backward compatibility
    res = process_user_message(user_message, history)
    return res.get('assistant_message', '')


def process_user_message(user_message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Process a user message and return a structured result:
    { action, params, assistant_message, plan? }
    This executes actions (create_task, update_task_status, generate_plan) like
    `handle_user_message` used to, but returns structured data useful for APIs.
    """
    key = _history_to_key(user_message, history)
    cached = RESPONSE_CACHE.get(key)
    if cached is not None:
        return {"action": "chat_only", "params": {}, "assistant_message": cached}

    llm_output = _call_llm(user_message, history)
    action = llm_output.get("action", "chat_only")
    params = llm_output.get("params", {}) or {}
    assistant_message = llm_output.get("assistant_message", "")

    structured = {"action": action, "params": params, "assistant_message": assistant_message}

    if action == "create_task":
        task = create_task(
            title=params.get("title", "Untitled task"),
            deadline=params.get("deadline", "2099-12-31"),
            estimated_hours=params.get("estimated_hours", 1),
            priority=params.get("priority", "medium"),
        )
        structured["task"] = task
        structured["assistant_message"] += f"\n\n[Task created with ID {task['id']}]"

    elif action == "list_tasks":
        tasks = list_tasks(status=params.get("status"))
        structured["tasks"] = tasks
        if not tasks:
            structured["assistant_message"] += "\n\nYou currently have no tasks matching that filter."
        else:
            structured["assistant_message"] += "\n\nHere are your tasks:\n"
            for t in tasks:
                structured["assistant_message"] += (
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
        structured["updated"] = ok
        if ok:
            structured["assistant_message"] += "\n\n[Task status updated successfully.]"
        else:
            structured["assistant_message"] += "\n\n[I couldn’t find that task ID. Please check and try again.]"

    elif action == "generate_plan":
        daily_hours = params.get("daily_hours", 3)
        num_days = params.get("num_days", 7)
        plan = generate_plan(daily_hours=daily_hours, num_days=num_days)
        structured["plan"] = plan

        structured["assistant_message"] += "\n\nHere’s your study plan:\n"
        for date, slots in plan.items():
            structured["assistant_message"] += f"\n📅 {date}\n"
            if not slots:
                structured["assistant_message"] += "  - No tasks scheduled.\n"
                continue
            for s in slots:
                structured["assistant_message"] += f"  - {s['title']} ({s['hours']} hours) [Task ID {s['task_id']}]\n"

    # cache reply text for performance
    try:
        RESPONSE_CACHE.set(key, structured.get('assistant_message', ''))
    except Exception:
        pass

    return structured


# Async & streaming helpers
async def handle_user_message_async(user_message: str, history: List[Dict[str, str]]) -> str:
    import asyncio
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, handle_user_message, user_message, history)
    return result


def stream_handle_user_message(user_message: str, history: List[Dict[str, str]], chunk_size: int = 80) -> Generator[str, None, None]:
    full = handle_user_message(user_message, history)
    try:
        key = _history_to_key(user_message, history)
        _CACHE.set(key, full)
    except Exception:
        pass
    for i in range(0, len(full), chunk_size):
        yield full[i:i + chunk_size]
