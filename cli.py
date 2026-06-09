from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.retrieval.retriever import retrieve
from src.generation.prompt import SYSTEM_PROMPT, build_prompt
from src.generation.generator import MODEL, rewrite_query


def run() -> None:
    client = Groq()
    history: list[dict] = []

    print("=" * 60)
    print("  Bloodborne Lore Expert")
    print("  type 'quit' to exit, 'reset' to clear history")
    print("=" * 60)
    print()

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFarewell, Hunter.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Farewell, Hunter.")
            break
        if query.lower() == "reset":
            history.clear()
            print("(history cleared)\n")
            continue

        search_query = rewrite_query(query, history)
        results = retrieve(search_query)
        prompt = build_prompt(query, results)

        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": prompt["user"]}]
        )

        print("\nHunter: ", end="", flush=True)
        stream = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
            stream=True,
        )

        chunks: list[str] = []
        for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)
            chunks.append(text)
        print("\n")

        answer = "".join(chunks)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
