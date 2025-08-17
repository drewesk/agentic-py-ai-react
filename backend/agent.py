import httpx
import asyncio
from config import PERPLEXITY_API_KEY  # optional

# Ollama server config
OLLAMA_SERVER_URL = "http://localhost:11434"  # default Ollama server endpoint
MODEL_NAME = "gemma:2b"  # replace with your model name

async def agent_response(prompt: str, context: str = "") -> str:
    """
    Send a task + context to the local Ollama server asynchronously
    and return the model response.
    """
    url = f"{OLLAMA_SERVER_URL}/v1/completions"
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{prompt}\n\nContext:\n{context}",
        "max_tokens": 512  # adjust as needed
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data.get("completion", "")
        except httpx.RequestError as e:
            return f"[ERROR: Ollama server not reachable] Simulated response for: {prompt}\nContext: {context}"
