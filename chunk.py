"""
chunk.py — Stage 2: Chunking
TXST Professor Reviews RAG Pipeline

Implements the chunking strategy from planning.md:
  - Chunk size:  300 tokens
  - Overlap:     30 tokens
  - RMP rule:    one review = one chunk (never split a single review)
  - Reddit rule: one top-level post + its top reply = one chunk

Reads all .txt files from data/raw/ (produced by ingest.py).
Saves chunks as JSON to data/chunks/, one file per source.
Also writes data/chunks/all_chunks.json — the full combined corpus.

Usage:
  python chunk.py

Output:
  data/chunks/<slug>_chunks.json   — chunks for one source
  data/chunks/all_chunks.json      — all chunks combined
  data/chunks/chunk_report.txt     — summary stats + 5 sample chunks
"""

import os
import re
import json
from typing import List, Dict

# ── Tokenisation ─────────────────────────────────────────────────────────────
# We approximate tokens as whitespace-split words.
# This avoids a heavyweight tokeniser dependency while staying close enough
# to the 300-token target for sentence-transformers (which uses WordPiece,
# averaging ~1.2 words per token — so 300 "word-tokens" ≈ 250 real tokens,
# safely under the 256-token hard limit of all-MiniLM-L6-v2).

def word_tokenize(text: str) -> List[str]:
    return text.split()

def token_count(text: str) -> int:
    return len(word_tokenize(text))

# ── Config ────────────────────────────────────────────────────────────────────

CHUNK_SIZE   = 300   # max tokens per chunk
OVERLAP      = 30    # overlap tokens between consecutive chunks
MIN_CHUNK    = 20    # discard chunks shorter than this (noise fragments)

RAW_DIR      = os.path.join(os.path.dirname(__file__), "data", "raw")
CHUNKS_DIR   = os.path.join(os.path.dirname(__file__), "data", "chunks")
os.makedirs(CHUNKS_DIR, exist_ok=True)

# ── Professor name detection ──────────────────────────────────────────────────
# Used to tag each chunk with a detected professor name for metadata.
# Expand this list as you add more professors to your corpus.

KNOWN_PROFESSORS = [
    "Ted Lehr", "Lehr",
    "Francis Mendez", "Mendez",
    "Ram Kumar Basanta", "Basanta",
    "Stefanie Ramirez", "Ramirez",
]

def detect_professor(text: str) -> str:
    """Return the first known professor name found in the text, or empty string."""
    for name in KNOWN_PROFESSORS:
        if name.lower() in text.lower():
            return name
    return ""


# ── Source-type detection ─────────────────────────────────────────────────────

def is_reddit_source(slug: str) -> bool:
    return "reddit" in slug.lower()

def is_rmp_professor_source(slug: str) -> bool:
    return "rmp_professor" in slug.lower()


# ── RMP chunking ──────────────────────────────────────────────────────────────
# Strategy: split on "REVIEW:" markers written by ingest.py.
# Each review becomes its own chunk (never split a single review).
# If a review exceeds CHUNK_SIZE, it falls through to the generic chunker.

def chunk_rmp_professor(text: str, slug: str, url: str) -> List[Dict]:
    """
    One review = one chunk.
    Reviews are delimited by the 'REVIEW:' prefix written by ingest.py.
    The professor name/department header is prepended to every chunk
    so each chunk is self-contained.
    """
    chunks = []

    # Extract professor header (lines before first REVIEW:)
    header_match = re.split(r"\bREVIEW:", text, maxsplit=1)
    header = header_match[0].strip() if len(header_match) > 1 else ""

    # Split into individual reviews
    review_blocks = re.split(r"\bREVIEW:\s*", text)
    review_blocks = [b.strip() for b in review_blocks if b.strip()]

    # First block might be the header — skip if it has no review-like content
    if review_blocks and not any(
        kw in review_blocks[0].lower()
        for kw in ["professor", "class", "exam", "grade", "homework", "attend"]
    ):
        header = review_blocks.pop(0) if not header else header

    for i, review in enumerate(review_blocks):
        # Prepend header for context
        full_text = f"{header}\n\nREVIEW: {review}".strip() if header else f"REVIEW: {review}".strip()

        if token_count(full_text) < MIN_CHUNK:
            continue  # discard noise fragments

        # If a single review is too long, fall back to generic chunking
        if token_count(full_text) > CHUNK_SIZE:
            sub_chunks = chunk_generic(full_text, slug, url)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "chunk_id":   f"{slug}_review_{i}",
                "source":     slug,
                "url":        url,
                "chunk_type": "rmp_review",
                "professor":  detect_professor(full_text),
                "text":       full_text,
                "token_count": token_count(full_text),
            })

    # If no REVIEW: markers found, fall back to generic
    if not chunks:
        chunks = chunk_generic(text, slug, url)

    return chunks


# ── Reddit chunking ───────────────────────────────────────────────────────────
# Strategy: pair each POST TITLE + POST BODY as one chunk.
# If the pair is within CHUNK_SIZE, keep it whole.
# Multiple small posts may be merged if together they fit in one chunk.

def chunk_reddit(text: str, slug: str, url: str) -> List[Dict]:
    """
    One top-level post + its body = one chunk.
    Posts are delimited by 'POST TITLE:' markers written by ingest.py.
    """
    chunks = []

    # Split into (title, body) pairs
    parts = re.split(r"\bPOST TITLE:\s*", text)
    parts = [p.strip() for p in parts if p.strip()]

    buffer_tokens = 0
    buffer_texts  = []
    chunk_idx     = 0

    for part in parts:
        # Separate body from next post
        body_split = re.split(r"\bPOST BODY:\s*", part, maxsplit=1)
        title = body_split[0].strip()
        body  = body_split[1].strip() if len(body_split) > 1 else ""

        entry = f"POST TITLE: {title}"
        if body:
            entry += f"\nPOST BODY: {body}"

        entry_tokens = token_count(entry)

        if entry_tokens < MIN_CHUNK:
            continue  # skip near-empty posts

        # If single post exceeds CHUNK_SIZE, chunk it generically
        if entry_tokens > CHUNK_SIZE:
            sub = chunk_generic(entry, slug, url)
            for s in sub:
                s["chunk_type"] = "reddit_post"
                s["chunk_id"] = f"{slug}_post_{chunk_idx}"
                chunk_idx += 1
            chunks.extend(sub)
            continue

        # Accumulate posts into one chunk until full
        if buffer_tokens + entry_tokens > CHUNK_SIZE and buffer_texts:
            combined = "\n\n".join(buffer_texts)
            chunks.append({
                "chunk_id":    f"{slug}_post_{chunk_idx}",
                "source":      slug,
                "url":         url,
                "chunk_type":  "reddit_post",
                "professor":   detect_professor(combined),
                "text":        combined,
                "token_count": token_count(combined),
            })
            chunk_idx += 1
            # Start new buffer with overlap: keep last post as context
            buffer_texts  = buffer_texts[-1:] if buffer_texts else []
            buffer_tokens = token_count(buffer_texts[0]) if buffer_texts else 0

        buffer_texts.append(entry)
        buffer_tokens += entry_tokens

    # Flush remaining buffer
    if buffer_texts:
        combined = "\n\n".join(buffer_texts)
        if token_count(combined) >= MIN_CHUNK:
            chunks.append({
                "chunk_id":    f"{slug}_post_{chunk_idx}",
                "source":      slug,
                "url":         url,
                "chunk_type":  "reddit_post",
                "professor":   detect_professor(combined),
                "text":        combined,
                "token_count": token_count(combined),
            })

    if not chunks:
        chunks = chunk_generic(text, slug, url)

    return chunks


# ── Generic sliding-window chunking ──────────────────────────────────────────
# Used for: Coursicle, Uloop, Professors.directory, RMP school/search pages.
# Also used as fallback when RMP or Reddit extractors find no markers.

def chunk_generic(text: str, slug: str, url: str) -> List[Dict]:
    """
    Sliding window: 300 tokens, 30-token overlap.
    Splits on word boundaries only — never mid-word.
    """
    words  = word_tokenize(text)
    chunks = []
    start  = 0
    idx    = 0

    while start < len(words):
        end        = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        chunk_text  = " ".join(chunk_words).strip()

        if token_count(chunk_text) >= MIN_CHUNK:
            chunks.append({
                "chunk_id":    f"{slug}_chunk_{idx}",
                "source":      slug,
                "url":         url,
                "chunk_type":  "generic",
                "professor":   detect_professor(chunk_text),
                "text":        chunk_text,
                "token_count": token_count(chunk_text),
            })
            idx += 1

        # Slide forward by (CHUNK_SIZE - OVERLAP)
        step = CHUNK_SIZE - OVERLAP
        start += step

        if end == len(words):
            break   # reached the end

    return chunks


# ── Dispatcher ────────────────────────────────────────────────────────────────

def chunk_document(text: str, slug: str, url: str) -> List[Dict]:
    """
    Route to the correct chunker based on source slug.
    """
    if is_rmp_professor_source(slug):
        return chunk_rmp_professor(text, slug, url)
    elif is_reddit_source(slug):
        return chunk_reddit(text, slug, url)
    else:
        return chunk_generic(text, slug, url)


# ── Main ──────────────────────────────────────────────────────────────────────

def chunk_all() -> List[Dict]:
    """
    Load every .txt file from data/raw/, chunk it, save per-source JSON,
    then save the combined all_chunks.json.
    Returns the full list of chunks.
    """
    # Load manifest to get URL metadata
    manifest_path = os.path.join(RAW_DIR, "manifest.json")
    url_map: Dict[str, str] = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        url_map = {entry["slug"]: entry["url"] for entry in manifest}

    all_chunks: List[Dict] = []

    raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".txt")]
    if not raw_files:
        print("No .txt files found in data/raw/. Run ingest.py first.")
        return []

    for fname in sorted(raw_files):
        slug = fname.replace(".txt", "")
        fpath = os.path.join(RAW_DIR, fname)
        url  = url_map.get(slug, "")

        with open(fpath, encoding="utf-8") as f:
            text = f.read().strip()

        if not text or text.startswith("[No content"):
            print(f"Skipping {slug} — empty or failed fetch")
            continue

        chunks = chunk_document(text, slug, url)

        # Save per-source chunk file
        out_path = os.path.join(CHUNKS_DIR, f"{slug}_chunks.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        all_chunks.extend(chunks)
        print(f"  {slug}: {len(chunks)} chunks")

    # Save combined corpus
    combined_path = os.path.join(CHUNKS_DIR, "all_chunks.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Combined corpus → {combined_path}")

    write_report(all_chunks)
    return all_chunks


def write_report(chunks: List[Dict]):
    """
    Print and save a summary report:
      - Total chunk count
      - Token distribution (min, max, mean)
      - Breakdown by chunk_type
      - 5 representative sample chunks (for manual inspection)
    """
    if not chunks:
        print("No chunks to report.")
        return

    import random
    token_counts = [c["token_count"] for c in chunks]
    mean_tokens  = sum(token_counts) / len(token_counts)

    by_type: Dict[str, int] = {}
    for c in chunks:
        by_type[c["chunk_type"]] = by_type.get(c["chunk_type"], 0) + 1

    lines = []
    lines.append("=" * 60)
    lines.append("CHUNK REPORT")
    lines.append("=" * 60)
    lines.append(f"Total chunks    : {len(chunks)}")
    lines.append(f"Token min       : {min(token_counts)}")
    lines.append(f"Token max       : {max(token_counts)}")
    lines.append(f"Token mean      : {mean_tokens:.1f}")
    lines.append("")
    lines.append("Chunks by type:")
    for ctype, count in sorted(by_type.items()):
        lines.append(f"  {ctype:<20} {count}")
    lines.append("")
    lines.append("Chunks by professor detected:")
    by_prof: Dict[str, int] = {}
    for c in chunks:
        prof = c.get("professor") or "unknown"
        by_prof[prof] = by_prof.get(prof, 0) + 1
    for prof, count in sorted(by_prof.items(), key=lambda x: -x[1]):
        lines.append(f"  {prof:<30} {count}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("5 SAMPLE CHUNKS (for manual inspection)")
    lines.append("=" * 60)

    samples = random.sample(chunks, min(5, len(chunks)))
    for i, s in enumerate(samples, 1):
        lines.append(f"\n--- Sample {i} ---")
        lines.append(f"ID         : {s['chunk_id']}")
        lines.append(f"Type       : {s['chunk_type']}")
        lines.append(f"Professor  : {s.get('professor') or 'not detected'}")
        lines.append(f"Token count: {s['token_count']}")
        lines.append(f"Source     : {s['source']}")
        lines.append(f"Text preview:")
        lines.append(s["text"][:500])
        if len(s["text"]) > 500:
            lines.append("  [...truncated]")

    report_text = "\n".join(lines)
    print(report_text)

    report_path = os.path.join(CHUNKS_DIR, "chunk_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\nReport saved → {report_path}")


if __name__ == "__main__":
    chunk_all()