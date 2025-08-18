# Agentic AI

## Overview

![runtime_image_here](runtime.png)

- If a file is `.gitignored`, just touch it as an empty file in the corresponding location to tree-map.

```
./
├─ backend/
│   ├─ main.py
│   ├─ autonomous_agent.py
│   ├─ task_generator.py
│   ├─ agent.py
│   ├─ memory.py
│   ├─ file_processor.py
│   ├─ notifier.py
│   ├─ config.py
│   ├─ tasks.json
│   ├─ uploads/ # Create me Empty
│   ├─ results/ # Create me Empty
│   └─ agentic_lab.log 
├─ frontend/
│   └─ ai-lab-dashboard/
│       ├─ package.json
│       ├─ vite.config.ts
│       └─ src/
│           ├─ Dashboard.tsx
│           ├─ TaskMonitor.tsx
│           ├─ MemoryMetrics.tsx
│           └─ KnowledgeGraph.tsx
└─ README.md
```

This package provides a **fully autonomous AI research lab**:

- Multi-agent parallel task execution  
- Self-generating tasks with priorities  
- File ingestion & persistent memory  
- Cross-referencing and insight generation  
- Email / Slack / Console notifications  
- Logging & metrics  
- Live React dashboard with:  
  - Task monitor  
  - Memory metrics  
  - Interactive knowledge graph  

---

> ⚠️ **Kill Switch Notice**  
> If the backend server goes rogue and keeps spawning no matter how many `kill -9 <PIDs>` you do, we've added a kill switch to the autonomous loop.  
> Run in the shell (inside `backend/` where the server is running):  
> ```bash
> export STOP_AGENT=1
> ```  
> Then run:  
> ```bash
> pkill -f python
> ```  
> to prevent the server from overtaking society. You're a true hero now!  

---

## Setup

First run `ollama serve`, edit the model name in `agent.py`, or run `ollama run gemma:2b` in a separate shell.

### Frontend
#### Node.js, React/Vite

> Runs on `localhost:5173`

```bash
cd frontend
npm i
npm run dev
```

### Backend
#### Python

> Runs on `localhost:5173`

```bash
cd backend   # in new terminal
pip install -r requirements.txt

mkdir uploads results
echo "[]" > tasks.json

uvicorn main:app --reload
```

Or if rerunning the server after install:

```bash
cd backend

# uploads/ and results/ already exist
# wipe tasks.json and initialize with empty list
python -c 'import json; json.dump([], open("tasks.json", "w"))'

uvicorn main:app --reload
```
