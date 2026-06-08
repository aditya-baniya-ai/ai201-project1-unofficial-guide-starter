"""
retrieve.py — Stage 4: Retrieval
TXST Professor Reviews RAG Pipeline

Loads the ChromaDB collection built by embed.py,
embeds a query using the same all-MiniLM-L6-v2 model,
and returns the top-k most similar chunks.

Usage (as a module):
  from retrieve import retrieve
  chunks = retrieve("Does Ted Lehr give a lot of homework?")

Usage (standalone test):
  python retrieve.py
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

CHROMA_DIR  = os.path.join(os.path.dirname(__file__), "data", "chroma")
COLLECTION  = "txst_professors"
TOP_K       = 3

# ── Load model + collection once at import time ───────────────────────────────
# This means the model is only downloaded/loaded once per session,
# not on every call to retrieve().

print("Loading embedding model...")
_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Connecting to ChromaDB...")
_client     = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_collection(COLLECTION)
print(f"Connected. {_collection.count()} chunks in collection.\n")


# ── Retrieval function ────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks from ChromaDB.

    Args:
        query:  the user's question as a plain string
        top_k:  number of chunks to return (default 3 per planning.md)

    Returns:
        list of dicts, each with keys:
            text       — the chunk text
            source     — slug of the source file
            url        — original URL
            professor  — detected professor name (may be empty)
            chunk_type — rmp_review, reddit_post, or generic
            distance   — cosine distance (lower = more similar)
    """
    query_embedding = _model.encode([query]).tolist()

    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":       text,
            "source":     meta.get("source", ""),
            "url":        meta.get("url", ""),
            "professor":  meta.get("professor", ""),
            "chunk_type": meta.get("chunk_type", ""),
            "distance":   round(dist, 4),
        })

    return chunks


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run all 5 evaluation questions from planning.md
    test_questions = [
        "Does Professor Ted give a lot of assignments?",
        "Is Dr. Lehr very strict about his attendance policies?",
        "Is Dr. Lehr angry if someone uses a phone in his class?",
        "Is Dr. Francis Mendez's grading criteria easy to pass?",
        "Does Dr. Ram Kumar Basanta give exam questions prior to exams?",
    ]

    for question in test_questions:
        print("=" * 60)
        print(f"QUERY: {question}")
        print("=" * 60)
        chunks = retrieve(question)
        for i, chunk in enumerate(chunks, 1):
            print(f"\n  Result {i} (distance: {chunk['distance']})")
            print(f"  Professor : {chunk['professor'] or 'not detected'}")
            print(f"  Source    : {chunk['source']}")
            print(f"  Preview   : {chunk['text'][:200]}...")
        print()