import json, os
from config import TASK_FILE

def _atomic_write_json(path: str, data: list):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def generate_new_tasks():
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    new_id = max([t["id"] for t in tasks], default=0) + 1
    tasks.append({"id": new_id, "description": f"Auto task {new_id}",
                  "status": "pending", "priority": 1})
    _atomic_write_json(TASK_FILE, tasks)
