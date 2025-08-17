import httpx
import asyncio
from config import PERPLEXITY_API_KEY  # optional

# Ollama server config
OLLAMA_SERVER_URL = "http://localhost:11434"
MODEL_NAME = "gemma:2b"

# Template for code+research instructions
INSTRUCTION_TEMPLATE = """
You are a research assistant AI whose job is to:
- Produce fully working web app code from scratch
- Use any online coding knowledge, documentation, or Perplexity-style searches to find the best solutions
- Strictly produce structured JSON output:
  {{
      "task_description": "{task_description}",
      "code": "<complete runnable code>",
      "sources": ["<list of references or sources you used>"]
  }}
- Do not add explanations outside the JSON
- Ensure code is complete and ready to run

Task:
{task_description}

Context:
{context}
"""

async def agent_response(prompt: str, context: str = "") -> str:
    """
    Send a task + context to the local Ollama server asynchronously
    and return the model response.
    """
    wrapped_prompt = INSTRUCTION_TEMPLATE.format(task_description=prompt, context=context)

    url = f"{OLLAMA_SERVER_URL}/v1/completions"
    payload = {
        "model": MODEL_NAME,
        "prompt": wrapped_prompt,
        "max_tokens": 2048  # allow larger code outputs
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()

            # Ollama response parsing
            if "completion" in data:
                return data["completion"]
            elif "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("text", "")
            else:
                return '[ERROR: No completion returned]'

        except httpx.RequestError as e
