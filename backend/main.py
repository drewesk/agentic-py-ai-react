import os, json, asyncio, logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from autonomous_agent import monitor_new_files, process_all_tasks, get_pending_tasks
from task_generator import generate_new_tasks
from memory import vector_db, get_knowledge_graph

INTERVAL = int(os.getenv("LAB_LOOP_INTERVAL", "30"))

app = FastAPI(title="AgenticPY")

logging.basicConfig(filename='agentic_lab.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Basic CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

shutdown_event = asyncio.Event()

# ---------- singleton guard to avoid multiple background loops ----------
# Only start lab loop in a single process (useful when uvicorn reload/workers > 1)
_singleton_lock_file = None

def _acquire_singleton() -> bool:
    import fcntl
    global _singleton_lock_file
    lock_path = "./lab_loop.lock"
    _singleton_lock_file = open(lock_path, "w")
    try:
        fcntl.flock(_singleton_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _singleton_lock_file.write(str(os.getpid()))
        _singleton_lock_file.flush()
        os.fsync(_singleton_lock_file.fileno())
        return True
    except BlockingIOError:
        return False


# ---------- background loop ----------
async def lab_loop():
    logging.info("Lab loop started.")
    while not shutdown_event.is_set():
        try:
            monitor_new_files()
            await process_all_tasks()
            # Optional auto-task: throttle so we don't flood the queue
            generate_new_tasks()
            await asyncio.sleep(INTERVAL)
        except Exception as e:
            logging.exception("Lab loop error")
            await asyncio.sleep(INTERVAL)
    logging.info("Lab loop stopped.")


# ---------- routes ----------
@app.get("/tasks_stream")
async def tasks_stream():
    async def event_generator():
        while not shutdown_event.is_set():
            pending = await get_pending_tasks()
            yield f"data: {json.dumps(pending)}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/memory_metrics")
async def memory_metrics():
    return {"memory_count": len(vector_db["documents"])}


@app.get("/knowledge_graph")
async def knowledge_graph():
    return get_knowledge_graph()


@app.on_event("startup")
async def startup_event():
    if _acquire_singleton():
        asyncio.create_task(lab_loop())
        logging.info("Startup acquired singleton lock; background loop active.")
    else:
        logging.warning("Another process holds the lab_loop lock; skipping background loop.")


@app.on_event("shutdown")
async def shutdown():
    shutdown_event.set()