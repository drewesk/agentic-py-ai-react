import os, requests
from dotenv import load_dotenv

load_dotenv()  # load SERPER_API_KEY, WEB_TOPK, WEB_MAX_SNIPPET from .env

SERPER_KEY = os.getenv("SERPER_API_KEY")
TOPK = int(os.getenv("WEB_TOPK", "3"))
SNIP = int(os.getenv("WEB_MAX_SNIPPET", "400"))

def web_brief(query: str) -> str:
    """Return a compact markdown WebBrief. Empty string if no key/query."""
    if not SERPER_KEY or not query:
        return ""
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": TOPK},
        timeout=12,
    )
    r.raise_for_status()
    rows = (r.json().get("organic") or [])[:TOPK]
    return "\n".join(
        f"- **{(x.get('title') or x.get('link'))}** • {x.get('link')}\n  {(x.get('snippet') or '')[:SNIP]}"
        for x in rows
    )
