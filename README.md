# Bloodborne AI — Lore Expert

A conversational AI that answers questions about *Bloodborne* lore using Retrieval-Augmented Generation (RAG). Ask about bosses, NPCs, weapons, attire, Caryll runes, and more — answers are grounded in the game's own data.

## How It Works

```
User question
    → Query rewriting  (Groq LLM, using conversation history)
    → Vector retrieval (all-MiniLM-L6-v2 + ChromaDB)
    → Context prompt   (top-10 chunks, metadata-labelled)
    → Response stream  (llama-3.3-70b-versatile via Groq)
```

The system refuses to invent lore — if the retrieved context doesn't contain an answer, it says so.

## Project Structure

```
bloodborne-ai/
├── cli.py                  # Interactive chat entrypoint
├── data/
│   ├── raw/                # Source Bloodborne XML files
│   └── chroma/             # Persistent vector database
├── src/
│   ├── ingestion/          # XML parsing, chunking, embedding
│   ├── retrieval/          # Vector search
│   └── generation/         # Prompt building & LLM calls
├── config/
│   └── settings.py
└── tests/
```

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# or: source .venv/bin/activate  (Linux/macOS)

pip install groq chromadb sentence-transformers python-dotenv
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 3. Ingest the data

Run the ingestion pipeline to parse the XML files, chunk them, embed them, and store them in ChromaDB:

```python
from src.ingestion.loader import load_all
from src.ingestion.chunker import chunk_records
from src.ingestion.embedder import embed_and_store

records = load_all("data/raw")
chunks = chunk_records(records)
embed_and_store(chunks)
```

This only needs to be run once. The vector database is persisted in `data/chroma/`.

### 4. Start the chat

```bash
python cli.py
```

**Available commands during chat:**
- `quit` / `exit` — end the session
- `reset` — clear conversation history

## Data Sources

The `data/raw/` directory contains Bloodborne game data in XML format:

| File | Contents |
|------|----------|
| `bossInfo.xml` | Boss descriptions, locations, notes, dialogue |
| `npcInfo.xml` | NPC information and dialogue |
| `weapons.xml` | Melee weapon data |
| `firearmWeapons.xml` | Firearm weapon data |
| `attireInfoUpdate.xml` | Armor and clothing sets |
| `mainXML.xml` | Caryll runes and effects |

## Configuration

| Setting | Location | Default |
|---------|----------|---------|
| Groq API key | `.env` | — |
| Embedding model | `src/ingestion/embedder.py` | `all-MiniLM-L6-v2` |
| LLM model | `src/generation/generator.py` | `llama-3.3-70b-versatile` |
| Chunk size | `src/ingestion/chunker.py` | 800 chars, 100 overlap |
| Retrieval results | `src/retrieval/retriever.py` | Top 10 |
| Max response tokens | `src/generation/generator.py` | 1024 |

## Tech Stack

- **[Groq](https://groq.com)** — fast LLM inference (llama-3.3-70b-versatile)
- **[ChromaDB](https://www.trychroma.com)** — local vector database
- **[sentence-transformers](https://www.sbert.net)** — text embeddings (all-MiniLM-L6-v2)
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — environment configuration
