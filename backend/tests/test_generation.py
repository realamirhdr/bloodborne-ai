from __future__ import annotations

from src.generation.prompt import SYSTEM_PROMPT, _format_context, build_prompt
from src.retrieval.retriever import SearchResult


def test_format_context_numbers_and_labels_each_result():
    results = [
        SearchResult(
            text="Gehrman trained many hunters.",
            metadata={"name": "Gehrman", "type": "character"},
            score=0.1,
        ),
        SearchResult(
            text="The Hunter's Dream is a safe haven.",
            metadata={"name": "Hunter's Dream", "type": "location"},
            score=0.3,
        ),
    ]
    context = _format_context(results)
    assert "[1] Gehrman (character)" in context
    assert "[2] Hunter's Dream (location)" in context
    assert "Gehrman trained many hunters." in context
    assert "---" in context


def test_format_context_handles_missing_metadata():
    results = [SearchResult(text="Mystery lore.", metadata={}, score=0.5)]
    context = _format_context(results)
    assert "[1] Unknown (?)" in context


def test_format_context_empty_results():
    assert _format_context([]) == ""


def test_build_prompt_includes_system_and_question():
    results = [
        SearchResult(
            text="Lore snippet.", metadata={"name": "Test", "type": "wiki"}, score=0.2
        )
    ]
    prompt = build_prompt("Who is Gehrman?", results)
    assert prompt["system"] == SYSTEM_PROMPT
    assert "Who is Gehrman?" in prompt["user"]
    assert "Lore snippet." in prompt["user"]
