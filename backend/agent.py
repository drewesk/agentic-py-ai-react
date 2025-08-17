import httpx
import asyncio

OLLAMA_SERVER_URL = "http://localhost:11434"
MODEL_NAME = "gemma:2b"

async def agent_response(prompt: str, memory_docs=None) -> str:
    """
    Sends a prompt + optional context to the Ollama model and returns the response.
    
    Args:
        prompt: The main task description or query.
        memory_docs: Optional list or string providing additional context for the model.
    """
    context_str = ""
    if memory_docs:
        context_str = "\n".join(memory_docs) if isinstance(memory_docs, list) else memory_docs

    wrapped_prompt = (
        "You are a research assistant AI.\n"
        "- Produce fully working, runnable code.\n"
        "- Strictly output structured JSON with keys: task_description, code, sources.\n"
        "- Do not include any extra explanations.\n\n"
        f"Task:\n{prompt}\n\n"
        f"Context:\n{context_str}"
    )
    url = f"{OLLAMA_SERVER_URL}/v1/completions"
    payload = {
        "model": MODEL_NAME,
        "prompt": wrapped_prompt,
        "max_tokens": 1024
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            if "completion" in data:
                return data["completion"]
            elif "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("text", "")
            else:
                return '[ERROR: No completion returned]'
        except httpx.RequestError:
            return f"[ERROR: Ollama server not reachable] Simulated response for: {prompt}"
