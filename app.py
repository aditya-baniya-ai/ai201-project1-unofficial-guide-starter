"""
app.py — Gradio Web Interface
TXST Professor Reviews — Unofficial Guide

Run with:
  python app.py

Then open: http://localhost:7860

Requirements:
  pip install gradio
"""

import gradio as gr
from generate import ask

# ── Handler ───────────────────────────────────────────────────────────────────

def handle_query(question: str):
    """Called by Gradio on every button click or Enter press."""
    question = question.strip()
    if not question:
        return "Please enter a question.", ""

    result  = ask(question)
    answer  = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])

    if not sources:
        sources = "No sources found."

    return answer, sources


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="TXST Professor Guide") as demo:

    gr.Markdown("""
    # 🤘 TXST Unofficial Professor Guide
    Ask anything about Texas State University professors — grading, attendance,
    exams, workload, and more. Answers are grounded in real student reviews.

    **Example questions:**
    - Does Dr. Lehr give a lot of assignments?
    - Is Dr. Lehr strict about attendance?
    - Is Dr. Francis Mendez's grading easy to pass?
    - Does Dr. Basanta give practice exam questions?
    """)

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. Is Dr. Lehr strict about phone use in class?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("### Tips\n- Be specific about the professor's name\n- Ask one question at a time\n- If no answer, try rephrasing")

    answer_box = gr.Textbox(
        label="Answer",
        lines=8,
        interactive=False,
    )

    sources_box = gr.Textbox(
        label="Retrieved from",
        lines=4,
        interactive=False,
    )

    gr.Markdown("""
    ---
    *Answers are based only on collected student reviews and Reddit posts from r/txstate.
    This is an unofficial tool — always verify with official TXST sources.*
    """)

    # Wire up interactions
    ask_btn.click(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()