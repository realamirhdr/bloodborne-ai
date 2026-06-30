from __future__ import annotations

import json
from pathlib import Path

from src.ingestion.chunker import Chunk, _group_sentences, _split_sentences, chunk_all
from src.ingestion.loader import Record, load_all


def test_split_sentences_splits_on_terminal_punctuation():
    text = "Gehrman is the first hunter. He sits in the Hunter's Dream! Does he ever leave?"
    assert _split_sentences(text) == [
        "Gehrman is the first hunter.",
        "He sits in the Hunter's Dream!",
        "Does he ever leave?",
    ]


def test_split_sentences_ignores_blank_input():
    assert _split_sentences("   ") == []


def test_group_sentences_respects_max_chars_with_no_overlap():
    sentences = ["AAAA.", "BBBB.", "CCCC."]  # each 5 chars, 6 with joining space
    groups = _group_sentences(sentences, max_chars=10, overlap_chars=0)
    assert groups == ["AAAA.", "BBBB.", "CCCC."]


def test_group_sentences_carries_overlap_into_next_group():
    sentences = ["AAAA.", "BBBB.", "CCCC."]
    groups = _group_sentences(sentences, max_chars=10, overlap_chars=6)
    assert groups == ["AAAA.", "AAAA. BBBB.", "BBBB. CCCC."]


def test_chunk_all_includes_header_and_metadata():
    record = Record(
        name="Gehrman",
        type="character",
        text="Gehrman is the first hunter. He trained many others.",
        metadata={"source_file": "test.json"},
    )
    chunks = chunk_all([record], max_chars=800, overlap_chars=50)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
    assert chunk.text.startswith("Type: character\nName: Gehrman\n\n")
    assert chunk.metadata["source_file"] == "test.json"
    assert chunk.metadata["chunk_index"] == 0
    assert chunk.metadata["chunk_count"] == 1


def test_chunk_all_skips_records_with_empty_text():
    record = Record(name="Empty", type="character", text="   ", metadata={})
    assert chunk_all([record]) == []


def test_load_all_reads_json_records(tmp_path: Path):
    data = [
        {
            "title": "Gehrman",
            "text": "The first hunter.",
            "url": "https://example.com/gehrman",
        },
        {"title": "", "text": "Should be skipped — no title."},
        {"title": "Skipped", "text": ""},
    ]
    (tmp_path / "wiki.json").write_text(json.dumps(data), encoding="utf-8")

    records = load_all(tmp_path)

    assert len(records) == 1
    assert records[0].name == "Gehrman"
    assert records[0].type == "wiki"
    assert records[0].metadata["url"] == "https://example.com/gehrman"


def test_load_all_returns_empty_for_empty_dir(tmp_path: Path):
    assert load_all(tmp_path) == []
