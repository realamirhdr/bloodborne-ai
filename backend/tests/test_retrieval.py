from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.retrieval.retriever import SearchResult, retrieve


@patch("src.retrieval.retriever.get_collection")
@patch("src.retrieval.retriever._client")
def test_retrieve_builds_search_results_from_query(mock_client, mock_get_collection):
    mock_client.return_value.embed.return_value = MagicMock(
        embeddings=[[0.1, 0.2, 0.3]]
    )
    mock_get_collection.return_value.query.return_value = {
        "documents": [["Gehrman is the first hunter."]],
        "metadatas": [[{"name": "Gehrman", "type": "character"}]],
        "distances": [[0.12]],
    }

    results = retrieve("Who is Gehrman?", top_k=1)

    assert results == [
        SearchResult(
            text="Gehrman is the first hunter.",
            metadata={"name": "Gehrman", "type": "character"},
            score=0.12,
        )
    ]
    mock_client.return_value.embed.assert_called_once_with(
        ["Who is Gehrman?"], model="voyage-4-lite", input_type="query"
    )
    mock_get_collection.return_value.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2, 0.3]],
        n_results=1,
        include=["documents", "metadatas", "distances"],
    )


@patch("src.retrieval.retriever.get_collection")
@patch("src.retrieval.retriever._client")
def test_retrieve_returns_empty_list_when_no_matches(mock_client, mock_get_collection):
    mock_client.return_value.embed.return_value = MagicMock(
        embeddings=[[0.1, 0.2, 0.3]]
    )
    mock_get_collection.return_value.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    assert retrieve("Nonexistent thing") == []
