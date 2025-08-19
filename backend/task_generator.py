import json, os
from config import TASK_FILE
import fcntl

def _atomic_write_json(path: str, data: list):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def generate_new_tasks():
    """Safely add ONE new auto task if and only if there are no pending tasks.
    Uses a file lock to avoid duplicate IDs across processes.
    """
    with open(TASK_FILE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            tasks = json.load(f)
            if not isinstance(tasks, list):
                tasks = []
        except Exception:
            tasks = []

        # only add if queue is empty (pending)
        if any(t.get("status") == "pending" for t in tasks):
            fcntl.flock(f, fcntl.LOCK_UN)
            return

        new_id = max([t.get("id", 0) for t in tasks], default=0) + 1
        tasks.append({
            "id": new_id,
            "description": f"Auto task {new_id}",
            "status": "pending",
            "priority": 1
        })

        f.seek(0); f.truncate()
        json.dump(tasks, f, indent=2)
        f.flush(); os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)
