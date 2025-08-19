import os
import requests
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv() # your secure system prompt and API KEYS

# ---------- Config ----------

# Ollama (local)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "cas/nous-hermes-2-mistral-7b-dpo:latest")

# ---------- System brief (concise, actionable) ----------
DEFAULT_SYSTEM_BRIEF = """
You are a blah blah default instructions

Insert context on what the agent works on and guildlines here or in your env file
"""

# use env SYSTEM_BRIEF first otherwise default to above var
SYSTEM_BRIEF = os.getenv("SYSTEM_BRIEF")
if SYSTEM_BRIEF:
    SYSTEM_BRIEF = SYSTEM_BRIEF.replace("\\n", "\n")  # convert literal \n into real newlines
else:
    SYSTEM_BRIEF = DEFAULT_SYSTEM_BRIEF


def _pack_messages(prompt: str, memory_docs: str = "") -> List[Dict[str, str]]:
    context_block = f"Context (past tasks/results):\n{memory_docs.strip()}" if memory_docs.strip() else ""
    task_block = f"{prompt.strip()}\n\n{context_block}"
    return [
        {"role": "system", "content": SYSTEM_BRIEF},
        {"role": "task", "content": task_block},
    ]

# ---------- Providers ----------
def _ask_ollama(messages: List[Dict[str, str]]) -> str:
    """
    Non-streaming Ollama chat call: one complete JSON reply.
    """
    resp = requests.post(
        OLLAMA_URL,
        json={ 
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 1050, "num_ctx": 2048},
            "keep_alive": "3m",
        },
        timeout=222 #Change tokens and timeout when using stronger servers in production
    )
    resp.raise_for_status()
    data = resp.json()
    # Ollama returns: {"message": {"role": "...", "content": "..."}, ...}
    # or choices-like in some versions; prefer "message"
    if "message" in data and isinstance(data["message"], dict):
        return data["message"].get("content", "")
    # fallback: try last message in 'messages' array if present
    if "messages" in data and isinstance(data["messages"], list) and data["messages"]:
        return data["messages"][-1].get("content", "")
    return ""

# ---------- Public API ----------
def agent_response(prompt: str, memory_docs: str = "", allow_web: bool = True) -> str:
    """
    Called by autonomous_agent.py. Keep it simple:
      - We always pack past memory into the context window.
    """
    messages = _pack_messages(prompt, memory_docs)
    return _ask_ollama(messages)

# Optional convenience wrapper for router use
def agent_router(task_description: str, memory_context: str = "") -> str:
    return agent_response(task_description, memory_docs=memory_context, allow_web=True)

if __name__ == "__main__":
    # Quick smoke test (set env first)
    print(agent_response("List 3 minimal changes to harden the kill-switch logic.", memory_docs="(no results)"))
