from __future__ import annotations

from pathlib import Path

import chromadb

DB_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "bloodborne"


def get_collection(
    db_path: str | Path = DB_PATH,
    collection_name: str = COLLECTION_NAME,
) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(db_path))
    return client.get_collection(name=collection_name)
