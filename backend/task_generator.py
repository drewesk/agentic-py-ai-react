import json
from config import TASK_FILE

def generate_new_tasks():
    with open(TASK_FILE, "r+") as f:
        tasks = json.load(f)
        new_id = max([t["id"] for t in tasks], default=0) + 1
        tasks.append({"id": new_id, "description": f"Auto task {new_id}", "status": "pending", "priority": 1})
        f.seek(0)
        json.dump(tasks, f, indent=2)
        f.truncate()
