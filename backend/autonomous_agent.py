import os, json, asyncio, logging
from file_processor import extract_text
from memory import add_to_memory, retrieve_from_memory, add_relationship, add_node
from agent import agent_response
from notifier import notify
from config import UPLOAD_FOLDER, RESULTS_FOLDER, TASK_FILE

if os.environ.get("STOP_AGENT") == "1":
    print("Agent start blocked")
    exit(0)

logging.basicConfig(filename='agentic_lab.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

PROCESSED_FILES = set()

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

def get_pending_tasks():
    with open(TASK_FILE, "r") as f:
        tasks = json.load(f)
    return [t for t in tasks if t["status"]=="pending"]

async def process_single_task(task):
    task_id = task["id"]
    logging.info(f"Processing task {task_id}: {task['description']}")
    context = "\n".join(retrieve_from_memory(task["description"], k=5))
    response = await agent_response(task["description"], context)
    add_to_memory(response, {"task_id": task_id})
    add_node(f"task_{task_id}", node_type="task", label=task["description"])
    add_node(f"insight_{task_id}", node_type="insight", label=f"Insight {task_id}")
    add_relationship(f"task_{task_id}", f"insight_{task_id}", relation_type="produces")
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    with open(os.path.join(RESULTS_FOLDER, f"task_{task_id}_result.txt"), "w") as f:
        f.write(response)
    task["status"] = "completed"
    logging.info(f"Completed task {task_id}")
    notify(f"Task {task_id} Completed", f"Result saved for task: {task['description']}", method="console")

async def process_all_tasks():
    tasks = get_pending_tasks()
    if not tasks:
        return
    tasks.sort(key=lambda x: x.get('priority',0), reverse=True)
    await asyncio.gather(*(process_single_task(t) for t in tasks))
    with open(TASK_FILE, "r+") as f:
        all_tasks = json.load(f)
        for t in tasks:
            for at in all_tasks:
                if at["id"]==t["id"]:
                    at["status"]=t["status"]
        f.seek(0)
        json.dump(all_tasks, f, indent=2)
        f.truncate()
