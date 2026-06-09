from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sentence_transformers import SentenceTransformer

try:
    from .vector_store import get_collection
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.retrieval.vector_store import get_collection

MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass
class SearchResult:
    text: str
    metadata: dict
    score: float  # cosine distance: 0.0 = identical, 2.0 = opposite


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def retrieve(query: str, top_k: int = 10) -> list[SearchResult]:
    embedding = _model().encode(query).tolist()
    results = get_collection().query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return [
        SearchResult(text=doc, metadata=meta, score=dist)
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    query = " ".join(sys.argv[1:]) or "What is the Blood-Starved Beast weak to?"
    print(f"Query: {query}\n{'=' * 60}")
    for i, r in enumerate(retrieve(query), 1):
        name = r.metadata.get("name", "?")
        type_ = r.metadata.get("type", "?")
        print(f"[{i}] score={r.score:.4f}  {name} ({type_})")
        print(r.text[:300])
        print("-" * 60)
