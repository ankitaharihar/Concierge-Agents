from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from storage import load_tasks, save_tasks, get_next_task_id


def create_task(
    title: str,
    deadline: str,
    estimated_hours: float,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Create a new task and store it.

    deadline: 'YYYY-MM-DD'
    priority: 'low' | 'medium' | 'high'
    """
    tasks = load_tasks()

    new_task = {
        "id": get_next_task_id(tasks),
        "title": title,
        "deadline": deadline,          # store as string
        "estimated_hours": float(estimated_hours),
        "priority": priority.lower(),  # normalize
        "status": "pending"            # pending | in_progress | done
    }

    tasks.append(new_task)
    save_tasks(tasks)
    return new_task


def list_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all tasks, optionally filtered by status.
    status: 'pending' | 'in_progress' | 'done' or None
    """
    tasks = load_tasks()
    if status:
        status = status.lower()
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


def update_task_status(task_id: int, new_status: str) -> bool:
    """
    Update the status of a task. Returns True if successful.
    new_status: 'pending' | 'in_progress' | 'done'
    """
    tasks = load_tasks()
    found = False

    for t in tasks:
        if t["id"] == int(task_id):
            t["status"] = new_status.lower()
            found = True
            break

    if found:
        save_tasks(tasks)
    return found


def generate_plan(daily_hours: float = 3.0, num_days: int = 7) -> Dict[str, Any]:
    """
    Simple greedy study plan:
    - Only considers tasks not 'done'
    - Sorts by deadline then priority
    - Fills each day up to daily_hours
    - Does NOT permanently modify task estimated_hours in storage
    """
    tasks = load_tasks()
    # Work on a copy so we don't change actual stored hours
    task_copies = [t.copy() for t in tasks if t["status"] != "done"]

    priority_order = {"high": 0, "medium": 1, "low": 2}

    # Parse deadline as date for sorting; invalid dates go far in future
    def parse_deadline(d: str):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return datetime.max.date()

    task_copies.sort(
        key=lambda t: (parse_deadline(t["deadline"]), priority_order.get(t["priority"], 1))
    )

    plan: Dict[str, Any] = {}
    today = datetime.today().date()

    for day_offset in range(num_days):
        date = str(today + timedelta(days=day_offset))
        remaining = float(daily_hours)
        plan[date] = []

        for task in task_copies:
            if task["estimated_hours"] <= 0 or remaining <= 0:
                continue

            slot_hours = min(task["estimated_hours"], remaining)
            plan[date].append(
                {
                    "task_id": task["id"],
                    "title": task["title"],
                    "hours": round(slot_hours, 2),
                }
            )
            task["estimated_hours"] -= slot_hours
            remaining -= slot_hours

    return plan
