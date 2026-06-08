"""
generate.py — Stage 5: Generation
TXST Professor Reviews RAG Pipeline

Retrieves the top 3 chunks for a query using retrieve.py,
formats them into a prompt, and sends to Groq (llama-3.3-70b-versatile)
to generate a grounded answer.

Usage (interactive):
  python generate.py

Usage (as a module):
  from generate import generate
  answer = generate("Does Ted Lehr give a lot of homework?")

Requirements:
  pip install groq python-dotenv
  .env file with: GROQ_API_KEY=your_key_here
"""

import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve

# ── Load API key from .env ────────────────────────────────────────────────────

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)
MODEL  = "llama-3.3-70b-versatile"


# ── Prompt template ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful unofficial guide for Texas State University (TXST) students.
Your job is to answer questions about professors based ONLY on the student reviews and posts provided to you.

Rules:
- Only use information from the provided context chunks.
- If the context does not contain enough information to answer, say so clearly.
- Do not invent or assume details not present in the context.
- Keep answers concise and student-friendly.
- If reviews conflict with each other, mention both perspectives.
- Always mention which professor the answer is about."""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        professor = chunk["professor"] or "unknown professor"
        source    = chunk["source"]
        context_parts.append(
            f"[Source {i} — {source} — Professor: {professor}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    return f"""Here are the most relevant student reviews and posts I found:

{context}

---

Based only on the above, please answer this question:
{query}"""


# ── Main generation function ──────────────────────────────────────────────────

def generate(query: str, top_k: int = 3) -> str:
    """
    Retrieve top_k chunks for the query and generate a grounded answer.

    Args:
        query:  the student's question
        top_k:  number of chunks to retrieve (default 3)

    Returns:
        answer string from the LLM
    """
    # Stage 4: retrieve
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return "I could not find any relevant reviews to answer that question."

    # Build prompt
    prompt = build_prompt(query, chunks)

    # Stage 5: generate
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,   # low temperature = more factual, less creative
        max_tokens=512,
    )

    return response.choices[0].message.content


# ── Standalone: run all 5 evaluation questions ────────────────────────────────

if __name__ == "__main__":
    eval_questions = [
        "Does Professor Ted give a lot of assignments?",
        "Is Dr. Lehr very strict about his attendance policies?",
        "Is Dr. Lehr angry if someone uses a phone in his class?",
        "Is Dr. Francis Mendez's grading criteria easy to pass?",
        "Does Dr. Ram Kumar Basanta give exam questions prior to exams?",
    ]

    for question in eval_questions:
        print("=" * 60)
        print(f"Q: {question}")
        print("=" * 60)
        answer = generate(question)
        print(f"A: {answer}")
        print()