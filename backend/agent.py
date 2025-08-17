import httpx

OLLAMA_SERVER_URL = "http://localhost:11434"
MODEL_NAME = "gemma:2b"

async def agent_response(prompt: str, memory_docs=None) -> str:
    context_str = ""
    if isinstance(memory_docs, list):
        context_str = "\n\n".join(memory_docs)
    elif isinstance(memory_docs, str):
        context_str = memory_docs or ""

    full_prompt = (
        "You are a research assistant, you learn python and get better with each task. You are creating fun web apps in file format. Use the CONTEXT if relevant.\n\n"
        f"CONTEXT:\n{context_str}\n\nTASK:\n{prompt}\n"
    )

    url = f"{OLLAMA_SERVER_URL}/api/generate"
    payload = {"model": MODEL_NAME, "prompt": full_prompt, "stream": False}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
            # For Ollama, field is "response"
            return data.get("response") or data.get("completion") or "[ERROR: No completion returned]"
        except httpx.RequestError:
            return f"[ERROR: Ollama server not reachable] Simulated response for: {prompt}"
