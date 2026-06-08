"""
embed.py — Stage 3: Embedding + Vector Store
TXST Professor Reviews RAG Pipeline

Loads all chunks from data/chunks/all_chunks.json (produced by chunk.py),
embeds them using all-MiniLM-L6-v2 via sentence-transformers,
and stores them in a local ChromaDB collection named 'txst_professors'.

Usage:
  python embed.py

Output:
  data/chroma/   — ChromaDB database files (created automatically)

Requirements:
  pip install sentence-transformers chromadb
"""

import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# ── Paths ─────────────────────────────────────────────────────────────────────

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "data", "chunks", "all_chunks.json")
CHROMA_DIR  = os.path.join(os.path.dirname(__file__), "data", "chroma")
COLLECTION  = "txst_professors"

# ── Main ──────────────────────────────────────────────────────────────────────

def embed_all():
    # 1. Load chunks
    print("Loading chunks...")
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  {len(chunks)} chunks loaded from {CHUNKS_FILE}")

    if not chunks:
        print("No chunks found. Run chunk.py first.")
        return

    # 2. Load embedding model
    print("\nLoading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Model loaded.")

    # 3. Connect to ChromaDB
    print(f"\nConnecting to ChromaDB at {CHROMA_DIR}...")
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if it exists so we start fresh
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing:
        print(f"  Deleting existing '{COLLECTION}' collection...")
        client.delete_collection(COLLECTION)

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}   # cosine similarity as per planning.md
    )
    print(f"  Created collection '{COLLECTION}'.")

    # 4. Embed and upsert in batches
    print(f"\nEmbedding and upserting {len(chunks)} chunks...")

    BATCH_SIZE = 32
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        ids        = [c["chunk_id"]    for c in batch]
        texts      = [c["text"]        for c in batch]
        metadatas  = [
            {
                "source":      c.get("source", ""),
                "url":         c.get("url", ""),
                "chunk_type":  c.get("chunk_type", ""),
                "professor":   c.get("professor", ""),
                "token_count": str(c.get("token_count", 0)),  # ChromaDB requires strings
            }
            for c in batch
        ]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        end = min(i + BATCH_SIZE, len(chunks))
        print(f"  Upserted chunks {i+1}–{end}")

    # 5. Verify
    total = collection.count()
    print(f"\nDone. {total} documents stored in ChromaDB collection '{COLLECTION}'.")

    if total != len(chunks):
        print(f"  WARNING: expected {len(chunks)}, got {total}. Check for duplicate chunk_ids.")
    else:
        print("  Chunk count matches. Embedding stage complete.")

    # 6. Quick sanity check — run one test query
    print("\nRunning sanity check query: 'Does Ted Lehr give a lot of homework?'")
    test_embedding = model.encode(["Does Ted Lehr give a lot of homework?"]).tolist()
    results = collection.query(
        query_embeddings=test_embedding,
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    print("\nTop 3 results:")
    for j, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        print(f"\n  Result {j+1} (distance: {dist:.4f})")
        print(f"  Source    : {meta['source']}")
        print(f"  Professor : {meta['professor'] or 'not detected'}")
        print(f"  Preview   : {doc[:200]}...")


if __name__ == "__main__":
    embed_all()