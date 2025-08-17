import os
import requests
from typing import List, Dict

# ---------- Config ----------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama" or "perplexity"

# Ollama (local)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")

# Perplexity (hosted)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")  # required if using Perplexity
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

# ---------- System brief (concise, actionable) ----------
SYSTEM_BRIEF = """You are an autonomous research & coding agent. 
You make your own decisions and make your task different from the memory of tasks provided. Code the next best app, be verbose

Output ONE markdown block with these EXACT headings:
### Actions
### Findings
### Files
### Sources

RULES:
2. Findings = concise, specific facts from CONTEXT or WebBrief only.
3. Files = list **filename** + 5-sentence summary, or 'None'.
5. No placeholders, no boilerplate, no "start web search"; use what you have NOW.
"""


def _pack_messages(prompt: str, memory_docs: str = "") -> List[Dict[str, str]]:
    context_block = f"Context (past tasks/results):\n{memory_docs.strip()}" if memory_docs else "Context: (none)"
    user_block = f"{prompt.strip()}\n\n{context_block}"
    return [
        {"role": "system", "content": SYSTEM_BRIEF},
        {"role": "user", "content": user_block},
    ]

# ---------- Providers ----------
def _ask_ollama(messages: List[Dict[str, str]]) -> str:
    """
    Minimal Ollama chat call. Requires ollama serve and model pulled.
    """
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=120,
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

def _ask_perplexity(messages: List[Dict[str, str]], allow_web: bool = True) -> str:
    """
    Minimal Perplexity call. If allow_web=True, let Perplexity decide/search.
    """
    if not PERPLEXITY_API_KEY:
        raise RuntimeError("Missing PERPLEXITY_API_KEY for Perplexity provider.")
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1400,
        "search_mode": "web",                # or "academic"
        "disable_search": not allow_web,     # False enables web search
        "enable_search_classifier": allow_web,  # let it auto-decide when to search
        # "web_search_options": {"search_context_size": "medium"},
    }
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(PERPLEXITY_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

# ---------- Public API ----------
def agent_response(prompt: str, memory_docs: str = "", allow_web: bool = True) -> str:
    """
    Called by autonomous_agent.py. Keep it simple:
      - We always pack past memory into the context window.
      - Provider is selected via LLM_PROVIDER env.
      - Perplexity can auto-search when allow_web=True.
    """
    messages = _pack_messages(prompt, memory_docs)
    if LLM_PROVIDER == "perplexity":
        return _ask_perplexity(messages, allow_web=allow_web)
    return _ask_ollama(messages)

# Optional convenience wrapper for router use
def agent_router(task_description: str, memory_context: str = "") -> str:
    return agent_response(task_description, memory_docs=memory_context, allow_web=True)

if __name__ == "__main__":
    # Quick smoke test (set env first)
    print(agent_response("List 3 minimal changes to harden the kill-switch logic.", memory_docs="(no results)"))
