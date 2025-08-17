# Agentic AI

## Overview

This package provides a **fully autonomous AI research lab**:

- Multi-agent parallel task execution
- Self-generating tasks with priorities
- File ingestion & persistent memory
- Cross-referencing and insight generation
- Email/Slack/Console notifications 
- Logging & metrics
- Live React dashboard with:
  - Task monitor
  - Memory metrics
  - Interactive knowledge graph
*********
  > If backend server goes rogue and keeps spawning no matter how many kill -9 <PIDs> that you do. We've added a kill switch to the autonomous loop, type in the shell `export STOP_AGENT=1` in the backend/ local to where the server is running. Then pkill -f python to prevent the server from overtaking society. You're a true hero now!
******

## Setup

### Front end
#### Node.js, React/Vite

> on localhost:5173

```
cd frontend
npm i
npm run dev
```

### Backend
#### Python

> on localhost:5173

```zsh
cd backend # in new terminal
pip install -r requirements.txt
mkdir uploads results
echo "[]" > tasks.json
uvicorn main:app --reload
```

