# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
This guide covers student experiences with professors at Texas State University (TXST), drawn from public review platforms, course planning tools, and student communities. It captures the kind of candid, practical information — grading style, attendance policies, workload, teaching clarity — that doesn't appear in official course catalogs or department websites. Because this knowledge is scattered across multiple platforms and buried in individual reviews, it's hard to find in one place and easy to miss before registration deadlines.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 |RateMyProfessors — TXST professor search (all) | Full list of rated TXST professors; browse by department | https://www.ratemyprofessors.com/search/professors/938?q=*|
| 2 |RateMyProfessors — TXST school page | Overall school ratings + individual professor links | https://www.ratemyprofessors.com/school/938 | 
| 3 |RateMyProfessors — Individual professor (example: Stefanie Ramirez) | Multi-review page; great example of short review chunks with tags like "Lots of homework", "Skip class? You won't pass" |https://www.ratemyprofessors.com/professor/1957208 |
| 4 |Coursicle TXST — Professor list with course info | Connects professors to specific courses/sections; useful for matching reviews to class numbers | https://www.coursicle.com/txstate/professors/ |
| 5 |r/txstate on Reddit |Student threads asking "who's the best prof for X?", class-specific advice — search within this sub for specific courses |https://www.reddit.com/r/txstate/ |
| 6 |Reddit: r/txstate — search "professor" |Filters all TXST subreddit posts mentioning professors; highly varied, conversational chunks |https://www.reddit.com/r/txstate/search/?q=professor&restrict_sr=1 |
| 7 |Reddit: r/txstate — search "rate my professor" |Posts where students discuss or link RMP pages for specific courses |https://www.reddit.com/r/txstate/search/?q=rate+my+professor&restrict_sr=1 |
| 8 |Uloop TXST professor ratings |Secondary review aggregator with TXST-specific professor ratings; different reviewer base than RMP | https://txstate.uloop.com/professors|
| 9 |Professors.directory — TXST |Another aggregator with ~265 professors indexed; useful for cross-referencing names |https://www.professors.directory/school/tx-texas_state_university/ |
| 10 |RateMyProfessors.io — TXST (unofficial scrape/mirror) |Aggregates scores by department (Literature, Math, History); good for department-level chunking |https://ratemyprofessors.io/texas-state-university |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 300 tokens

**Overlap:** 30 tokens

**Reasoning:**
RMP reviews are naturally short (100–150 tokens each), so a 300-token chunk gives enough breathing room to fit one full review plus its structured tags (e.g. "Lots of homework", "Skip class? You won't pass") without splitting them. Reddit posts are longer and more conversational, so the 300-token ceiling also accommodates a top-level post paired with its top reply as a single chunk — keeping the question and the most useful response together. The 30-token overlap (roughly 1–2 sentences) is intentionally modest: since RMP reviews have such natural break points, a large overlap would waste space. The overlap mainly protects against a sentence straddling a chunk boundary in longer Reddit posts.

Reddit-specific rule: one top-level post + its top reply = one chunk. RMP-specific rule: one review = one chunk.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 3

**Production tradeoff reflection:**
For this project, `all-MiniLM-L6-v2` was chosen primarily for its latency advantage — it runs locally with no API calls, making retrieval fast and free. However, there is a notable context length limitation: the model handles a maximum of 256 tokens per input, which means longer Reddit posts may be silently truncated during embedding, potentially losing the most useful part of a review. In a production setting with real TXST students, two tradeoffs would be worth reconsidering. First, accuracy on domain-specific text: student slang such as "prof is lowkey goated" or "this class is an L" may not embed meaningfully with a general-purpose model, causing relevant reviews to rank poorly. A model fine-tuned on student review text would handle this better. Second, context length: a model like OpenAI's `text-embedding-3-small` supports much longer inputs, reducing the risk of truncation on Reddit-style posts, at the cost of API latency and per-call pricing.
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Does Professor Ted give a lot of assignments? | Reviews should indicate whether Dr. Ted Lehr assigns frequent homework, projects, or readings — high or low workload. |
| 2 | Is Dr. Lehr very strict about his attendance policies? | Reviews should confirm or deny whether missing class significantly impacts the grade in Dr. Lehr's courses. |
| 3 | Is Dr. Lehr angry if someone uses a phone in his class? | Reviews should surface any student comments about Dr. Lehr's reaction to phone use or classroom behavior expectations. |
| 4 | Is Dr. Francis Mendez's grading criteria easy to pass? | Reviews should describe whether Dr. Mendez's grading is lenient, curved, or difficult, and whether most students pass. |
| 5 | Does Dr. Ram Kumar Basanta give exam questions prior to exams? | Reviews should indicate whether Dr. Basanta shares practice questions, study guides, or hints about exam content beforehand. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Sparse coverage:** Some professors — especially newer faculty or those teaching niche upper-division courses — may have very few reviews across all sources. When only one or two reviews exist for a professor, the top-k=3 retrieval will return weak or loosely related chunks, causing the system to hallucinate or hedge excessively. This is especially risky for Dr. Ram Kumar Basanta and Dr. Francis Mendez, who may have limited RMP presence compared to higher-enrollment professors.

2. **Vague review language:** Students frequently write reviews using informal or emotionally vague language — phrases like "he's chill," "not bad," or "lowkey the best" are difficult for a general-purpose embedding model to map accurately to specific queries about grading criteria or exam policies. A query like "Is Dr. Mendez's grading easy to pass?" may not retrieve a review that says "super chill grader, never fails anyone" because the semantic distance between formal query language and casual review language is high for `all-MiniLM-L6-v2`.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
Document Ingestion          Chunking              Embedding + Vector Store       Retrieval         Generation
──────────────────          ────────              ────────────────────────       ─────────         ──────────
10 source URLs         →    300 tokens,      →    all-MiniLM-L6-v2          →   top-k = 3    →   Claude API
(RMP, Reddit,               30 token overlap       (sentence-transformers)        cosine            produces
 Coursicle, Uloop)          1 review = 1 chunk     stored in ChromaDB             similarity        final answer
                            Reddit: post +                                         retrieval         to student
                            top reply = 1 chunk
```
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

### Milestone 1 — Document Ingestion (`ingest.py`)
- **Tool:** Claude
- **Input:** The 10 source URLs from `planning.md`, plus a description of what each source contains (RMP reviews, Reddit threads, Coursicle pages)
- **Expected output:** A Python script that fetches or scrapes each source and saves raw text to a local `/data/raw/` folder, with one file per source
- **Verification:** Manually open 2–3 of the output files and confirm the raw review text is present and readable, not HTML tags or boilerplate

### Milestone 2 — Chunking (`chunk.py`)
- **Tool:** Claude
- **Input:** The Chunking Strategy section of this `planning.md` verbatim, plus the raw text files from Stage 1
- **Expected output:** A `chunk_text()` function that splits text into 300-token chunks with 30-token overlap, applies the Reddit rule (post + top reply = one chunk), and saves chunks to `/data/chunks/` as JSON with metadata (source URL, professor name if detectable)
- **Verification:** Print chunk lengths for 10 random chunks and confirm they fall between 100–320 tokens; spot-check that no chunk splits mid-review

### Milestone 3 — Embedding + Vector Store (`embed.py`)
- **Tool:** Claude
- **Input:** The Retrieval Approach section of this `planning.md`, plus the chunk JSON files from Stage 2
- **Expected output:** A script that loads `all-MiniLM-L6-v2` via `sentence-transformers`, embeds all chunks, and upserts them into a local ChromaDB collection named `txst_professors`
- **Verification:** Query ChromaDB for the total document count and confirm it matches the number of chunks produced in Stage 2

### Milestone 4 — Retrieval (`retrieve.py`)
- **Tool:** Claude
- **Input:** The Retrieval Approach section (model name, top-k=3), plus the ChromaDB collection from Stage 3
- **Expected output:** A `retrieve(query: str) -> list[dict]` function that embeds the query with the same model, queries ChromaDB, and returns the top 3 chunks with their text and source metadata
- **Verification:** Run each of the 5 evaluation questions through `retrieve()` and manually check that the returned chunks are topically relevant to the professor named in the query

### Milestone 5 — Generation (`generate.py`)
- **Tool:** Claude
- **Input:** The 5 evaluation questions from this `planning.md`, the `retrieve()` function from Stage 4, and a prompt template specifying that the model should ground its answer in the retrieved chunks only
- **Expected output:** A `generate(query: str) -> str` function that calls `retrieve()`, formats a prompt with the chunks, calls the Claude API, and returns the answer string
- **Verification:** Run all 5 evaluation questions and compare responses against the expected answers in the Evaluation Plan table; flag any response that invents information not present in the retrieved chunks
