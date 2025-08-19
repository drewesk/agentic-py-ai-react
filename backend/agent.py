import os
import json
import requests
from typing import List, Dict

from serper import web_brief

from dotenv import load_dotenv
load_dotenv() # your secure system prompt and API KEYS

# ------- Config ----------

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

# _________ WebSearch ___________  
_DECIDER = (
    'Return STRICT JSON only: {"do_search": true|false, "query": "<short query or empty>"} '
    'Bias: default to do_search=true unless the CONTEXT fully answers. '
    'Query rules: (a) 3–7 words, (b) MUST include at least one salient term from TASK or CONTEXT, '
    '(c) add a disambiguator (year/product/library/site) when useful, (d) no quotes, no punctuation.'
)

def _decide_search(prompt: str, context: str) -> tuple[bool, str]:
    """Ask the LLM if web is needed. Uses your same roles: system + task."""
    messages = [
        {"role": "system", "content": _DECIDER},
        {"role": "task", "content": f"{prompt.strip()}\n\nContext (past tasks/results):\n{(context or '').strip()}"},
    ]
    raw = _ask_ollama(messages).strip()
    print("[WEBSEARCH] Raw decider output:", raw)

    try:
        obj = json.loads(raw)
        return bool(obj.get("do_search")), (obj.get("query") or "").strip()
    except Exception:
        return False, ""



# ---------- Public API ----------
def agent_response(prompt: str, memory_docs: str = "", allow_web: bool = True) -> str:
    """
    Called by autonomous_agent.py. Keep it simple:
      - We always pack past memory into the context window.
      - If allowed and needed, we may fetch a small WebBrief first.
    """
    do_search, query = (False, "")
    if allow_web and os.getenv("SERPER_API_KEY"):
        do_search, query = _decide_search(prompt, memory_docs)
        print(f"[WEBSEARCH] Search decision: {do_search}, query='{query}+?'")

    if do_search and query:
        print(f"[WEBSEARCH] Sending request to Serper with query: {query}")
        brief = web_brief(query)  # sync HTTP; your caller can thread this
        if brief:
            print(f"[WEBSEARCH] Got Serper response length: {len(brief)} chars")
            addon = "WebBrief:\n" + brief
            memory_docs = (memory_docs + "\n\n" + addon) if memory_docs.strip() else addon
        else:
            print("[WEBSEARCH] No response from Serper")

    messages = _pack_messages(prompt, memory_docs)
    print(f"[WEBSEARCH] Messages packed, roles={[m['role'] for m in messages]}")
    return _ask_ollama(messages)


if __name__ == "__main__":
    # Quick smoke test (set env first)
    print(agent_response("List 3 minimal changes to harden the kill-switch logic.", memory_docs="(no results)"))