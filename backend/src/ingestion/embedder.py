from __future__ import annotations

from pathlib import Path

import chromadb
import voyageai

try:
    from .chunker import Chunk, chunk_all
    from .loader import load_all
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.ingestion.chunker import Chunk, chunk_all
    from src.ingestion.loader import load_all

VOYAGE_MODEL = "voyage-4-lite"
COLLECTION_NAME = "bloodborne"
BATCH_SIZE = 128  # Voyage AI max texts per request
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"
DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"


def embed_and_store(
    chunks: list[Chunk],
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = COLLECTION_NAME,
) -> int:
    vo = voyageai.Client()  # reads VOYAGE_API_KEY from env
    client = chromadb.PersistentClient(path=str(db_path))

    # Drop and recreate so dimension changes don't cause conflicts
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c.text for c in chunks]
    ids = [f"chunk-{i}" for i in range(len(chunks))]
    metadatas = [_sanitize(c.metadata) for c in chunks]

    embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = vo.embed(batch, model=VOYAGE_MODEL, input_type="document")
        embeddings.extend(result.embeddings)
        print(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return collection.count()


def _sanitize(meta: dict) -> dict:
    return {
        k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
        for k, v in meta.items()
    }


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    db_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DB_PATH

    print("Loading and chunking records...")
    records = load_all(data_dir)
    chunks = chunk_all(records)
    print(f"  {len(records)} records  ->  {len(chunks)} chunks")

    print(f"Embedding with {VOYAGE_MODEL} via Voyage AI...")
    stored = embed_and_store(chunks, db_path=db_path)
    print(f"Done. {stored} chunks stored at {db_path}")
