from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

from src.generation.generator import MODEL, rewrite_query
from src.generation.prompt import SYSTEM_PROMPT, build_prompt
from src.retrieval.retriever import retrieve

app = FastAPI(title="Bloodborne AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    return StreamingResponse(
        _stream(req.message, req.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _stream(message: str, history: list[dict]) -> Generator[str, None, None]:
    client = Groq()
    search_query = rewrite_query(message, history)
    results = retrieve(search_query)
    prompt = build_prompt(message, results)

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": prompt["user"]}]
    )

    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            yield f"data: {json.dumps(text)}\n\n"

    yield "data: [DONE]\n\n"
