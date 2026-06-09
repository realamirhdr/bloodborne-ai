from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

try:
    from .chunker import Chunk, chunk_all
    from .loader import load_all
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.ingestion.chunker import Chunk, chunk_all
    from src.ingestion.loader import load_all

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "bloodborne"
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"
DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"


def embed_and_store(
    chunks: list[Chunk],
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = COLLECTION_NAME,
) -> int:
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64).tolist()
    ids = [f"chunk-{i}" for i in range(len(chunks))]
    metadatas = [_sanitize(c.metadata) for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return collection.count()


def _sanitize(meta: dict) -> dict:
    # Chroma metadata values must be str, int, float, or bool
    return {
        k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
        for k, v in meta.items()
    }


if __name__ == "__main__":
    import sys

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    db_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DB_PATH

    print("Loading and chunking records...")
    records = load_all(data_dir)
    chunks = chunk_all(records)
    print(f"  {len(records)} records  ->  {len(chunks)} chunks")

    print(f"Embedding with {MODEL_NAME} and storing in Chroma...")
    stored = embed_and_store(chunks, db_path=db_path)
    print(f"Done. {stored} chunks stored at {db_path}")
