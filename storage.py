from pathlib import Path
import json

TASKS_FILE = Path("tasks.json")


def load_tasks():
    """Load tasks from tasks.json; return a list of task dicts."""
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, start fresh (you can log this)
        return []


def save_tasks(tasks):
    """Save the list of tasks back to tasks.json."""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def get_next_task_id(tasks):
    """Get the next integer ID for a new task."""
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1
