"""
generate.py — Stage 5: Generation
TXST Professor Reviews RAG Pipeline

Retrieves top-k chunks, sends them to Groq with a strict grounding prompt,
and returns both the answer AND a programmatic source list.

Usage (as a module):
  from generate import ask
  result = ask("Does Ted Lehr give a lot of homework?")
  print(result["answer"])
  print(result["sources"])

Usage (standalone test):
  python generate.py

Requirements:
  pip install groq python-dotenv
  .env file with: GROQ_API_KEY=your_key_here
"""

import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve

# ── Load API key ──────────────────────────────────────────────────────────────

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)
MODEL  = "llama-3.3-70b-versatile"

# ── Grounding prompt ──────────────────────────────────────────────────────────
# "enforce" not "suggest" — the model is told it has NO other source of truth

SYSTEM_PROMPT = """You are an unofficial guide for Texas State University (TXST) students.
You answer questions about professors EXCLUSIVELY from the student review excerpts provided.

STRICT RULES:
- You may ONLY use information explicitly stated in the provided review excerpts.
- If the excerpts do not contain enough information to answer the question, you MUST respond with:
  "I don't have enough information in my sources to answer that."
- Do NOT use your general training knowledge about professors, universities, or teaching styles.
- Do NOT invent, assume, or infer details that are not in the excerpts.
- Do NOT say things like "typically" or "generally" — only say what the reviews actually state.
- Keep answers concise and student-friendly.
- If reviews conflict, present both perspectives.
- Do not add a source list — sources will be added separately."""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        professor = chunk["professor"] or "unknown"
        source    = chunk["source"]
        context_parts.append(
            f"[Excerpt {i} | source: {source} | professor: {professor}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)
    return f"""Use ONLY the following student review excerpts to answer the question.
If the excerpts don't contain the answer, say so explicitly.

{context}

---

Question: {query}
Answer:"""


def format_sources(chunks: list[dict]) -> list[str]:
    """
    Build a deduplicated, human-readable source list from retrieved chunks.
    This is done programmatically — not left to the LLM.
    """
    seen   = set()
    sources = []
    for chunk in chunks:
        source    = chunk.get("source", "unknown")
        professor = chunk.get("professor", "")
        url       = chunk.get("url", "")
        label = f"{source}"
        if professor:
            label += f" (professor: {professor})"
        if url:
            label += f" — {url}"
        if label not in seen:
            seen.add(label)
            sources.append(label)
    return sources


# ── Main function ─────────────────────────────────────────────────────────────

def ask(query: str, top_k: int = 3) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → generate → return with sources.

    Args:
        query:  the student's question
        top_k:  chunks to retrieve (default 3)

    Returns:
        dict with keys:
            "answer"  — grounded answer string from the LLM
            "sources" — list of source strings (programmatically built)
            "chunks"  — raw retrieved chunks (for debugging)
    """
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer":  "I don't have enough information in my sources to answer that.",
            "sources": [],
            "chunks":  [],
        }

    prompt  = build_prompt(query, chunks)
    sources = format_sources(chunks)   # built from metadata, not from LLM

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,
    }


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_questions = [
        # Evaluation plan questions
        "Does Professor Ted give a lot of assignments?",
        "Is Dr. Lehr very strict about his attendance policies?",
        "Is Dr. Lehr angry if someone uses a phone in his class?",
        "Is Dr. Francis Mendez's grading criteria easy to pass?",
        "Does Dr. Ram Kumar Basanta give exam questions prior to exams?",
        # Grounding test — should say "I don't have enough information"
        "What is Dr. Lehr's office hours schedule?",
        "Does TXST have a good computer science department overall?",
    ]

    for question in test_questions:
        print("=" * 60)
        print(f"Q: {question}")
        print("=" * 60)
        result = ask(question)
        print(f"A: {result['answer']}")
        print()
        print("Sources:")
        for s in result["sources"]:
            print(f"  • {s}")
        print()