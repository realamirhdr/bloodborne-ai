from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from groq import Groq
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

from src.generation.generator import MODEL, rewrite_query
from src.generation.prompt import SYSTEM_PROMPT, build_prompt
from src.retrieval.retriever import retrieve

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="Bloodborne AI")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://amirheidari.com",
        "https://www.amirheidari.com",
        "https://bloodborne-ai.amirheidari.com",
    ],
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
@limiter.limit("10/minute")
def chat(request: Request, req: ChatRequest):
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
