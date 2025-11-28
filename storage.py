import sqlite3
from pathlib import Path
import json

DB_PATH = Path("tasks.db")

def _conn():
    # use check_same_thread=False for threads; for heavier usage use a connection pool/ORM
    c = sqlite3.connect(str(DB_PATH), timeout=5, isolation_level=None)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    conn = _conn()
    cur = conn.cursor()
    # enable WAL for better concurrency
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY,
      title TEXT NOT NULL,
      deadline TEXT,
      estimated_hours REAL DEFAULT 0,
      priority TEXT DEFAULT 'medium',
      status TEXT DEFAULT 'pending',
      owner TEXT
    )
    """)
    conn.commit()
    conn.close()

def load_tasks():
    init_db()
    conn = _conn()
    cur = conn.execute("SELECT id, title, deadline, estimated_hours, priority, status, owner FROM tasks ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def save_tasks(tasks):
    """
    Overwrite table contents with provided list (keeps compatibility with existing callers).
    Each task must include an 'id'.
    """
    init_db()
    conn = _conn()
    cur = conn.cursor()
    with conn:
        cur.execute("DELETE FROM tasks")
        for t in tasks:
            cur.execute(
                "INSERT INTO tasks (id, title, deadline, estimated_hours, priority, status, owner) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    t.get("id"),
                    t.get("title"),
                    t.get("deadline"),
                    float(t.get("estimated_hours", 0)),
                    t.get("priority", "medium"),
                    t.get("status", "pending"),
                    t.get("owner"),
                ),
            )
    conn.close()

def get_next_task_id():
    init_db()
    conn = _conn()
    cur = conn.execute("SELECT MAX(id) as m FROM tasks")
    row = cur.fetchone()
    conn.close()
    if not row or row["m"] is None:
        return 1
    return int(row["m"] + 1)

def export_tasks_json(out_path=None):
    """Utility: export current DB tasks to a JSON file for backup/testing."""
    if out_path is None:
        out_path = Path("tasks.json")
    tasks = load_tasks()
    out_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
