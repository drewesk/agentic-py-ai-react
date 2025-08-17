import os, json, asyncio, logging
from datetime import datetime
from file_processor import extract_text
from memory import add_to_memory, retrieve_from_memory, add_relationship, add_node
from agent import agent_response
from notifier import notify
from config import UPLOAD_FOLDER, RESULTS_FOLDER, TASK_FILE

logging.basicConfig(filename='agentic_lab.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

PROCESSED_FILES = set()
_TASKS_LOCK = asyncio.Lock()  # single-process lock is enough here

# ---------- atomic helpers ----------
def _atomic_write_json(path: str, data: list):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

async def _load_tasks() -> list:
    # no need to lock for pure read in this single-process flow, but do it for safety
    async with _TASKS_LOCK:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

async def _save_tasks(tasks: list):
    async with _TASKS_LOCK:
        _atomic_write_json(TASK_FILE, tasks)

# ---------- file ingestion ----------
def monitor_new_files():
    global PROCESSED_FILES
    files = os.listdir(UPLOAD_FOLDER)
    new_files = [f for f in files if f not in PROCESSED_FILES]
    for file in new_files:
        file_path = os.path.join(UPLOAD_FOLDER, file)
        file_type = file.split(".")[-1]
        text = extract_text(file_path, file_type)
        add_to_memory(text, {"filename": file})
        add_node(f"doc_{file}", node_type="document", label=file)
        PROCESSED_FILES.add(file)
        logging.info(f"Ingested new file: {file}")

# ---------- task helpers ----------
async def get_pending_tasks():
    tasks = await _load_tasks()
    return [t for t in tasks if t.get("status") == "pending"]

async def _set_status(task_ids, new_status):
    tasks = await _load_tasks()
    ids = set(task_ids)
    changed = False
    for t in tasks:
        if t["id"] in ids:
            if t.get("status") != new_status:
                t["status"] = new_status
                if new_status == "running":
                    t["started_at"] = datetime.utcnow().isoformat() + "Z"
                elif new_status == "completed":
                    t["completed_at"] = datetime.utcnow().isoformat() + "Z"
                changed = True
    if changed:
        await _save_tasks(tasks)

# ---------- single task ----------
async def process_single_task(task):
    task_id = task["id"]
    logging.info(f"Processing task {task_id}: {task['description']}")
    # cleaner context join
    ctx = "\n\n".join(retrieve_from_memory(task["description"], k=5))
    response = await agent_response(prompt=task["description"], memory_docs=ctx)
    add_to_memory(response, {"task_id": task_id})
    add_node(f"task_{task_id}", node_type="task", label=task["description"])
    add_node(f"insight_{task_id}", node_type="insight", label=f"Insight {task_id}")
    add_relationship(f"task_{task_id}", f"insight_{task_id}", relation_type="produces")

    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    # ordered + unique filename, atomic write
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    fname = f"task_{task_id:06d}_{stamp}.txt"
    dst = os.path.join(RESULTS_FOLDER, fname)
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(response)
    os.replace(tmp, dst)

    logging.info(f"Completed task {task_id} -> {fname}")
    notify(f"Task {task_id} Completed", f"Result saved for task: {task['description']}", method="console")

# ---------- batch ----------
async def process_all_tasks():
    pending = await get_pending_tasks()
    if not pending:
        return
    # mark RUNNING first so a crash doesn’t re-run and overwrite
    await _set_status([t["id"] for t in pending], "running")

    # parallel execution is fine; file names now sort naturally by ID
    await asyncio.gather(*(process_single_task(t) for t in pending))

    # mark COMPLETED
    await _set_status([t["id"] for t in pending], "completed")
