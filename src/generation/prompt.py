from __future__ import annotations

from pathlib import Path

try:
    from ..retrieval.retriever import SearchResult
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.retrieval.retriever import SearchResult

SYSTEM_PROMPT = """You are a Bloodborne lore expert. Answer the user's question using only the context provided below.
If the context does not contain enough information to answer confidently, say so — do not invent lore.
Be concise and precise."""


def build_prompt(query: str, results: list[SearchResult]) -> dict[str, str]:
    context = _format_context(results)
    return {
        "system": SYSTEM_PROMPT,
        "user": f"Context:\n\n{context}\n\nQuestion: {query}",
    }


def _format_context(results: list[SearchResult]) -> str:
    blocks = []
    for i, r in enumerate(results, 1):
        name = r.metadata.get("name", "Unknown")
        type_ = r.metadata.get("type", "?")
        blocks.append(f"[{i}] {name} ({type_})\n{r.text.strip()}")
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    from src.retrieval.retriever import retrieve

    query = " ".join(sys.argv[1:]) or "Who is Gehrman?"
    results = retrieve(query)
    prompt = build_prompt(query, results)

    print("=== SYSTEM ===")
    print(prompt["system"])
    print("\n=== USER ===")
    print(prompt["user"])
