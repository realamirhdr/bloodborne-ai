from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    from .loader import Record
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.ingestion.loader import Record


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_all(
    records: list[Record],
    max_chars: int = 800,
    overlap_chars: int = 100,
) -> list[Chunk]:
    chunks = []
    for record in records:
        chunks.extend(_chunk_record(record, max_chars, overlap_chars))
    return chunks


def _chunk_record(record: Record, max_chars: int, overlap_chars: int) -> list[Chunk]:
    header = f"Type: {record.type}\nName: {record.name}\n\n"
    sentences = _split_sentences(record.text)
    if not sentences:
        return []

    groups = _group_sentences(sentences, max_chars - len(header), overlap_chars)
    total = len(groups)
    return [
        Chunk(
            text=header + group,
            metadata={**record.metadata, "chunk_index": i, "chunk_count": total},
        )
        for i, group in enumerate(groups)
    ]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _group_sentences(sentences: list[str], max_chars: int, overlap_chars: int) -> list[str]:
    groups: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence) + 1  # +1 for the joining space
        if current and current_len + s_len > max_chars:
            groups.append(" ".join(current))
            # seed next chunk with overlap from the tail of the current one
            overlap: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) + 1 > overlap_chars:
                    break
                overlap.insert(0, s)
                overlap_len += len(s) + 1
            current = overlap
            current_len = overlap_len
        current.append(sentence)
        current_len += s_len

    if current:
        groups.append(" ".join(current))

    return groups


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.ingestion.loader import load_all

    data_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).parent.parent.parent / "data" / "raw"
    )
    records = load_all(data_dir)
    chunks = chunk_all(records)

    print(f"Records: {len(records)}  ->  Chunks: {len(chunks)}\n{'=' * 60}")
    for c in chunks[:3]:
        print(c.text[:500])
        print(f"Metadata: {c.metadata}")
        print("-" * 60)
