import os, json, asyncio, logging, uuid
from datetime import datetime, timedelta
from typing import Optional
from file_processor import extract_text
from memory import add_to_memory, retrieve_from_memory, add_relationship, add_node
from agent import agent_response
from notifier import notify
from config import UPLOAD_FOLDER, RESULTS_FOLDER, TASK_FILE

# POSIX file locking (macOS/Linux)
import fcntl

logging.basicConfig(filename='agentic_lab.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

PROCESSED_FILES = set()

# intra-process locks
_TASKS_LOCK = asyncio.Lock()
_PROCESS_LOCK = asyncio.Lock()

# worker identity & lease timeout
WORKER_ID = f"{os.getpid()}-{uuid.uuid4().hex[:6]}"
LEASE_TTL_SEC = 15 * 60  # 15 minutes


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---------- atomic helpers ----------
def _atomic_write_json(path: str, data: list):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ---------- file ingestion ----------
def monitor_new_files():
    global PROCESSED_FILES
    files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
    new_files = [f for f in files if f not in PROCESSED_FILES]

    for file in new_files:
        file_path = os.path.join(UPLOAD_FOLDER, file)
        file_type = file.rsplit(".", 1)[-1].lower() if "." in file else ""
        text = extract_text(file_path, file_type) or ""
        if not text.strip():
            logging.info(f"Skipped (no extractable text): {file}")
            PROCESSED_FILES.add(file)
            continue

        CHUNK = 4000
        for i in range(0, len(text), CHUNK):
            add_to_memory(text[i:i+CHUNK], {"filename": file, "offset": i})

        add_node(f"doc_{file}", node_type="document", label=file)
        PROCESSED_FILES.add(file)
        logging.info(f"Ingested new file: {file}")


# ---------- task helpers (file-locked) ----------
def _read_tasks_with_lock(f) -> list:
    try:
        f.seek(0)
        data = json.load(f)
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    return data


async def _claim_next_task() -> Optional[dict]:
    """Claim exactly one pending task with an exclusive file lock.
    Also recovers stale 'running' tasks whose lease expired.
    """
    async with _TASKS_LOCK:
        with open(TASK_FILE, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            tasks = _read_tasks_with_lock(f)

            # recover stale running tasks
            now = datetime.utcnow()
            for t in tasks:
                if t.get("status") == "running":
                    lease_at = t.get("lease_at")
                    if lease_at:
                        try:
                            lease_dt = datetime.fromisoformat(lease_at.replace('Z',''))
                        except Exception:
                            lease_dt = now - timedelta(seconds=LEASE_TTL_SEC + 1)
                    else:
                        lease_dt = now - timedelta(seconds=LEASE_TTL_SEC + 1)

                    if (now - lease_dt).total_seconds() > LEASE_TTL_SEC:
                        t["status"] = "pending"
                        t.pop("owner", None)
                        t.pop("lease_at", None)

            pending = sorted([t for t in tasks if t.get("status") == "pending"], key=lambda x: x["id"])
            if not pending:
                # persist any recovery changes
                f.seek(0); f.truncate()
                json.dump(tasks, f, indent=2); f.flush(); os.fsync(f.fileno())
                fcntl.flock(f, fcntl.LOCK_UN)
                return None

            task = pending[0]
            task["status"] = "running"
            task.setdefault("started_at", _now_iso())
            task["owner"] = WORKER_ID
            task["lease_at"] = _now_iso()

            f.seek(0); f.truncate()
            json.dump(tasks, f, indent=2); f.flush(); os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
            return task


async def _complete_task(task_id: int):
    async with _TASKS_LOCK:
        with open(TASK_FILE, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            tasks = _read_tasks_with_lock(f)
            for t in tasks:
                if t.get("id") == task_id and t.get("owner") == WORKER_ID:
                    t["status"] = "completed"
                    t["completed_at"] = _now_iso()
                    t.pop("owner", None)
                    t.pop("lease_at", None)
                    break
            f.seek(0); f.truncate()
            json.dump(tasks, f, indent=2); f.flush(); os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)


async def _fail_task(task_id: int, error: str):
    async with _TASKS_LOCK:
        with open(TASK_FILE, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            tasks = _read_tasks_with_lock(f)
            for t in tasks:
                if t.get("id") == task_id and t.get("owner") == WORKER_ID:
                    t["status"] = "failed"
                    t["error"] = (error or "").splitlines()[-1][:500]
                    t["failed_at"] = _now_iso()
                    # keep owner/lease; recovery loop will requeue after TTL
                    break
            f.seek(0); f.truncate()
            json.dump(tasks, f, indent=2); f.flush(); os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)


async def get_pending_tasks():
    async with _TASKS_LOCK:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            tasks = _read_tasks_with_lock(f)
            fcntl.flock(f, fcntl.LOCK_UN)
    return sorted([t for t in tasks if t.get("status") == "pending"], key=lambda x: x["id"])


# ---------- single task ----------
async def process_single_task(task):
    task_id = task["id"]
    logging.info(f"Processing task {task_id}: {task['description']}")
    ctx = "\n\n".join(retrieve_from_memory(task["description"], k=5))
    response = await asyncio.to_thread(agent_response, prompt=task["description"], memory_docs=ctx)
    add_to_memory(response, {"task_id": task_id})
    add_node(f"task_{task_id}", node_type="task", label=task["description"])
    add_node(f"insight_{task_id}", node_type="insight", label=f"Insight {task_id}")
    add_relationship(f"task_{task_id}", f"insight_{task_id}", relation_type="produces")

    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    fname = f"task_{task_id:06d}_{stamp}.txt"
    dst = os.path.join(RESULTS_FOLDER, fname)
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(response)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, dst)

    logging.info(f"Completed task {task_id} -> {fname}")
    notify(f"Task {task_id} Completed", f"Result saved for task: {task['description']}", method="console")


# ---------- batch ----------
async def process_all_tasks():
    async with _PROCESS_LOCK:
        task = await _claim_next_task()
        if not task:
            return
        try:
            await process_single_task(task)
        except Exception as e:
            logging.exception("Task failed")
            await _fail_task(task["id"], str(e))
            return
        await _complete_task(task["id"])