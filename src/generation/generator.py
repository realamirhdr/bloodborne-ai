from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

try:
    from .prompt import build_prompt
    from ..retrieval.retriever import retrieve
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.generation.prompt import build_prompt
    from src.retrieval.retriever import retrieve

MODEL = "llama-3.3-70b-versatile"


def rewrite_query(query: str, history: list[dict], model: str = MODEL) -> str:
    """Rewrite a follow-up question into a standalone query for vector search."""
    if not history:
        return query

    formatted = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:]
    )
    client = Groq()
    response = client.chat.completions.create(
        model=model,
        max_tokens=64,
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite the follow-up question as a single standalone question "
                    "that includes all necessary context from the conversation. "
                    "Output only the rewritten question, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f"Conversation:\n{formatted}\n\nFollow-up: {query}",
            },
        ],
    )
    return response.choices[0].message.content.strip()


def generate(prompt: dict[str, str], model: str = MODEL) -> str:
    client = Groq()  # reads GROQ_API_KEY from env
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user",   "content": prompt["user"]},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    query = " ".join(sys.argv[1:]) or "Who is Gehrman?"
    print(f"Query: {query}\n{'=' * 60}")

    results = retrieve(query)
    prompt = build_prompt(query, results)

    client = Groq()
    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user",   "content": prompt["user"]},
        ],
        stream=True,
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        print(text, end="", flush=True)
    print()
