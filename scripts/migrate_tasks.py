from pathlib import Path
import json
import sys

# Ensure repo root is on sys.path so 'storage' module can be imported when
# running this script from the scripts/ folder.
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from storage import init_db, save_tasks

TASKS_FILE = ROOT / "tasks.json"

if TASKS_FILE.exists():
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
else:
    tasks = []

init_db()
# ensure tasks have integer ids
for i, t in enumerate(tasks, start=1):
    if 'id' not in t:
        t['id'] = i

save_tasks(tasks)
print(f"Imported {len(tasks)} tasks into tasks.db")