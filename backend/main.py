import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio, logging
from autonomous_agent import monitor_new_files, process_all_tasks, get_pending_tasks
from task_generator import generate_new_tasks
from memory import vector_db, get_knowledge_graph

INTERVAL = 30

app = FastAPI(title="Agentic Research Lab API")

logging.basicConfig(filename='agentic_lab.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

from fastapi.responses import StreamingResponse

@app.get("/tasks_stream")
async def tasks_stream():
    async def event_generator():
        while True:
            tasks = get_pending_tasks()
            yield f"data: {json.dumps(tasks)}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/memory_metrics")
async def memory_metrics():
    return {"memory_count": len(vector_db["documents"])}

@app.get("/knowledge_graph")
async def knowledge_graph_api():
    return get_knowledge_graph()

async def lab_loop():
    while not os.environ.get("STOP_AGENT") == "1":
        try:
            monitor_new_files()
            await process_all_tasks()
            generate_new_tasks()
            await asyncio.sleep(INTERVAL)
        except Exception as e:
            logging.error(f"Lab loop error: {e}")
            await asyncio.sleep(INTERVAL)
    logging.info("Lab loop stopped by STOP_AGENT flag.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(lab_loop())
