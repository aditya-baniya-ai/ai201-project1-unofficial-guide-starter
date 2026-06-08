# The Unofficial Guide — Project 1

---

## Domain

This guide covers student experiences with professors at Texas State University (TXST), drawn from public review platforms, course planning tools, and student communities. It captures the kind of candid, practical information — grading style, attendance policies, workload, teaching clarity — that doesn't appear in official course catalogs or department websites. Because this knowledge is scattered across multiple platforms and buried in individual reviews, it's hard to find in one place and easy to miss before registration deadlines.

---

## Document Sources

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

**Chunk size:** 300 tokens (approximated as whitespace-split words)

**Overlap:** 30 tokens

**Why these choices fit your documents:**
RMP reviews are naturally short — typically 100–150 tokens each — so a 300-token chunk gives enough room to fit one full review plus its structured tags without splitting it mid-sentence. Reddit posts are longer and more conversational, so the 300-token ceiling also accommodates a top-level post paired with its most useful reply as a single chunk, keeping question and response together. The 30-token overlap (roughly 1–2 sentences) protects against a sentence straddling a chunk boundary in longer Reddit posts, without wasting space on the short RMP reviews that have natural break points.

Two source-specific rules were applied before the sliding window ran:
- **RMP rule:** one review = one chunk, never split. The professor name and department were prepended to every chunk so each one is self-contained.
- **Reddit rule:** one top-level post + its body = one chunk. Small posts were accumulated until hitting the 300-token ceiling.
Before chunking, all documents were cleaned to remove HTML tags, navigation menus, cookie banners, share buttons, footer text, and lines shorter than 20 characters.

**Final chunk count:** 67 chunks across 10 source documents

---

## Sample Chunks
 
Five representative chunks drawn from the corpus:
 
**Chunk 1**
- **ID:** `reddit_txstate_search_rmp_post_1`
- **Source:** `reddit_txstate_search_rmp`
- **Professor detected:** none
- **Tokens:** 235
- **Text:**
  > POST TITLE: Some advice — use HB 2504, not just RateMyProfessor
  > POST BODY: So I'm sure most of us rely on RateMyProfessor when registering for classes. However, in many cases there are not enough reviews to be helpful. Go to the Texas State website and type in HB 2504. Not only will it show you the ratings given by students for course evaluations, but it also has the syllabus so you can check out what the class entails. Far more helpful than RMP alone.
**Chunk 2**
- **ID:** `professors_directory_txst_chunk_2`
- **Source:** `professors_directory_txst`
- **Professor detected:** none
- **Tokens:** 300
- **Text:**
  > Biology 0 Rate Jessica Warren Health Physical Education 0 Rate Julia Sainz Spanish 5 Rate J Whalin Music 4 Rate T.J. Halatin Management 0 Rate M. Clay Green Biology 5 Rate April Buck Family & Consumer Science 0 Rate Judith Easton Psychology 28 Rate Beth Sanders Criminal Justice 0 Rate Erik Nielsen Art 0 Rate A C Ryder Art & Design 0 Rate Rocky Hobson Fine Arts 0 Rate John Payne Political Science 0
**Chunk 3**
- **ID:** `rmp_io_txst_chunk_14`
- **Source:** `rmp_io_txst`
- **Professor detected:** none
- **Tokens:** 300
- **Text:**
  > Professor: Leslie Shroyer School: Texas State University City: San Marcos State: Texas Department: Mathematics Helpful Score: 3.5 Easy Score: 3.7 Clarity Score: 3.5 Professor: Leslie Shroyer School: Texas State University City: San Marcos Department: Mathematics Helpful Score: 2.5 Easy Score: 3.4 Clarity Score: 2.5 ...
**Chunk 4**
- **ID:** `rmp_professor_lehr_review_1` *(added manually — this chunk type is the primary signal source)*
- **Source:** `rmp_professor_lehr`
- **Professor detected:** Ted Lehr
- **Tokens:** ~78
- **Text:**
  > PROFESSOR: Ted Lehr
  > DEPARTMENT: Computer Science — Texas State University
  >
  > REVIEW: Lehr is strict about attendance and phones. He will literally stop his lecture and stare at you if you are on your phone. Homework every week, sometimes more. Grading is fair but he does not give extra credit. If you stay on top of the assignments you will be fine.
**Chunk 5**
- **ID:** `rmp_professor_mendez_basanta_review_0`
- **Source:** `rmp_professor_mendez_basanta`
- **Professor detected:** Francis Mendez
- **Tokens:** ~72
- **Text:**
  > PROFESSOR: Francis Mendez
  > DEPARTMENT: Biology — Texas State University
  >
  > REVIEW: Dr. Mendez is a tough grader. His exams are harder than the material you think you know. He does post study guides and practice questions on Canvas — use them. Does not curve individual exams but adjusts final grades slightly at the end.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, running locally

This model was chosen for its latency advantage — it runs entirely on-device with no API calls, no rate limits, and no cost. It is also well-suited to short texts like student reviews, where its 256-token context window is rarely a limitation.

**Production tradeoff reflection:**
If deploying this for real TXST students where cost was not a constraint, two tradeoffs would be worth reconsidering. First, context length: `all-MiniLM-L6-v2` has a hard 256-token input limit, meaning longer Reddit posts may be silently truncated during embedding, which could cause the most informative part of a post to be lost. A model like OpenAI's `text-embedding-3-small` supports much longer inputs and would handle Reddit-style posts more reliably, at the cost of API latency and per-call pricing. Second, accuracy on domain-specific text: student slang such as "prof is lowkey goated" or "this class is an L" may not embed meaningfully with a general-purpose model, causing semantically relevant reviews to rank poorly against formal query language. A model fine-tuned on student review text would close that gap, but no such 
model is publicly available for this domain.

---

## Retrieval Test Results
 
Three evaluation queries run against ChromaDB (top-k=3):
 
**Query 1: "Is Dr. Lehr strict about phones in class?"**
 
| Result | Distance | Source | Professor |
|--------|----------|--------|-----------|
| 1 | 0.3033 | rmp_professor_lehr | Ted Lehr |
| 2 | 0.3437 | rmp_professor_lehr | Ted Lehr |
| 3 | 0.5528 | rmp_professor_lehr | Ted Lehr |
 
Top chunk preview:
> "Lehr is strict about attendance and phones. He will literally stop his lecture and stare at you if you are on your phone."
 
**Why these chunks are relevant:** All three results come from the correct source file and the correct professor. Results 1 and 2 both explicitly mention phone policy, with distances of 0.30 and 0.34 — well below the 0.5 threshold. The embedding model correctly matched "phones in class" to reviews that used the exact phrase "no phones allowed" and described the professor's reaction to phone use. Result 3 is slightly less relevant (distance 0.55) but still from the right professor and source.
 
---
 
**Query 2: "Is Dr. Francis Mendez grading easy to pass?"**
 
| Result | Distance | Source | Professor |
|--------|----------|--------|-----------|
| 1 | 0.2103 | rmp_professor_mendez_basanta | Francis Mendez |
| 2 | 0.2351 | rmp_professor_mendez_basanta | Francis Mendez |
| 3 | 0.2579 | rmp_professor_mendez_basanta | Francis Mendez |
 
Top chunk preview:
> "Dr. Mendez is a tough grader. His exams are harder than the material you think you know."
 
**Why these chunks are relevant:** All three results are from the correct professor with exceptionally low distances (0.21–0.26), indicating very strong semantic matches. Each chunk directly addresses grading difficulty — the exact topic of the query. The embedding successfully linked "easy to pass" in the query to phrases like "tough grader", "not easy to pass without effort", and "grading criteria are clearly laid out" in the reviews.
 
---
 
**Query 3: "Does Basanta give practice exam questions?"**
 
| Result | Distance | Source | Professor |
|--------|----------|--------|-----------|
| 1 | 0.4003 | rmp_professor_mendez_basanta | Francis Mendez (metadata error) |
| 2 | 0.4409 | rmp_professor_mendez_basanta | Francis Mendez (metadata error) |
| 3 | 0.4504 | rmp_professor_mendez_basanta | Francis Mendez (metadata error) |
 
Top chunk preview:
> "Took Basanta for Calc II. He posts practice exam questions about a week before the real test and they are very similar to what shows up."
 
The content is correct and relevant — distances are below 0.5 and all three chunks describe Basanta's practice exam behavior accurately. However, the professor metadata field incorrectly reads "Francis Mendez" because both professors were stored in the same source file. This is a known metadata bug described in the Failure Case section.
 
---

## Grounded Generation

**System prompt grounding instruction:**
The system prompt uses hard, enforceable language rather than suggestions. The full instruction given to the model is:
 
> "You may ONLY use information explicitly stated in the provided review excerpts. If the excerpts do not contain enough information to answer the question, you MUST respond with: 'I don't have enough information in my sources to answer that.' Do NOT use your general training knowledge about professors, universities, or teaching styles. Do NOT invent, assume, or infer details that are not in the excerpts. Do NOT say things like 'typically' or 'generally' — only say what the reviews actually state."
 
The user prompt labels each retrieved chunk with its source file and detected professor name, e.g. `[Excerpt 1 | source: rmp_professor_lehr | professor: Ted Lehr]`, making it explicit to the model which documents it is working from.
 
Temperature is set to 0.2 to reduce creative generation and keep responses factual.

**How source attribution is surfaced in the response:**

Source attribution is built **programmatically** from chunk metadata — it is not left to the LLM to add. After generation, the `format_sources()` function in `generate.py` deduplicates the retrieved chunks by source slug and professor name, and returns a list of human-readable labels. The Gradio interface displays these in a separate "Retrieved from" box beneath the answer, so they are always present regardless of what the LLM chose to say.

---

## Example Responses
 
**Example 1 — grounded answer with source attribution:**
 
> **Query:** Is Dr. Lehr angry if someone uses a phone in his class?
>
> **Answer:** According to the excerpts, Dr. Lehr will "literally stop his lecture and stare at you" if you are on your phone, which suggests he is strict about phone use, but it doesn't explicitly state that he gets angry.
>
> **Retrieved from:**
> • rmp_professor_lehr (professor: Ted Lehr)
 
---
 
**Example 2 — grounded answer with source attribution:**
 
> **Query:** Is Dr. Francis Mendez's grading criteria easy to pass?
>
> **Answer:** No, according to the reviews, Dr. Francis Mendez's grading criteria is not easy to pass. One review states "Would not say his class is easy to pass without effort" and another describes him as a "tough grader." However, students mention that using his posted resources such as practice questions can make his class doable.
>
> **Retrieved from:**
> • rmp_professor_mendez_basanta (professor: Francis Mendez)
 
---
 
**Example 3 — out-of-scope query showing refusal response:**
 
> **Query:** What is Dr. Lehr's office hours schedule?
>
> **Answer:** I don't have enough information in my sources to answer that.
>
> **Retrieved from:**
> • rmp_professor_lehr (professor: Ted Lehr)
 
The system correctly declined to answer even though it retrieved relevant Lehr chunks — because none of those chunks mentioned office hours, the grounding instruction prevented the model from inventing a schedule.
 
---
 
## Query Interface
 
The system uses a Gradio web UI launched via `python app.py` and accessible at `http://localhost:7860`.
 
**Input fields:**
- **Your question** — a free-text box where the student types any question about a TXST professor
**Output fields:**
- **Answer** — the LLM's grounded response, drawn only from retrieved review chunks
- **Retrieved from** — a programmatically generated list of source documents the answer was drawn from
**Sample interaction transcript:**
 
```
User types: Does Dr. Lehr give a lot of assignments?
 
Answer:
Yes, according to the excerpts, Professor Ted Lehr gives a lot of programming
assignments, with one review stating "He gives a lot of programming assignments
throughout the semester, usually one every week or two" and another review
mentioning "Homework every week, sometimes more."
 
Retrieved from:
• rmp_professor_lehr (professor: Ted Lehr)
```
 
---

## Evaluation Report


| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Does Professor Ted give a lot of assignments? | Reviews indicate frequent homework — weekly programming assignments | Correctly stated Lehr gives programming assignments weekly or every two weeks, citing two reviews | Relevant | Accurate |
| 2 | Is Dr. Lehr very strict about his attendance policies? | Reviews confirm strict daily attendance that counts toward grade | Correctly confirmed strict attendance, daily tracking, grade impact, and removal for talking | Relevant | Accurate |
| 3 | Is Dr. Lehr angry if someone uses a phone in his class? | Reviews mention he stops lecture and stares at phone users | Correctly quoted "literally stop his lecture and stare at you" and noted it implies strictness without claiming anger explicitly | Relevant | Accurate |
| 4 | Is Dr. Francis Mendez's grading criteria easy to pass? | Reviews say grading is strict and requires real effort | Correctly identified him as a "tough grader" and cited "would not say his class is easy to pass without effort" | Relevant | Accurate |
| 5 | Does Dr. Ram Kumar Basanta give exam questions prior to exams? | Reviews confirm he posts practice problems ~1 week before exams | Correctly confirmed practice questions posted a week before exams, very similar to actual test | Relevant | Partially accurate — source metadata incorrectly labels Basanta chunks as Francis Mendez due to both professors being stored in the same source file |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**
"Does Dr. Ram Kumar Basanta give exam questions prior to exams?"

**What the system returned:**
The answer was factually correct — the system accurately described that Dr. Basanta posts practice exam questions about a week before the real test and that they closely mirror the actual exam. However, the source attribution displayed `rmp_professor_mendez_basanta (professor: Francis Mendez)` for all three retrieved chunks, incorrectly crediting the answer to Mendez rather than Basanta.

**Root cause (tied to a specific pipeline stage):**
The failure originated in Stage 1 (Document Ingestion) and carried through to Stage 2 (Chunking). Both Dr. Mendez and Dr. Basanta were stored in the same source file (`rmp_professor_mendez_basanta.txt`). When `chunk.py` ran professor name detection, it scanned each chunk for the first known professor name it found. Because "Francis Mendez" appeared in the `PROFESSOR:` header at the top of the file and that header was prepended to every chunk, all chunks — including the Basanta reviews — were tagged with `professor: Francis Mendez` in their ChromaDB metadata. The retrieval and generation stages worked correctly; the metadata attached at ingestion time was simply wrong.

**What you would change to fix it:**
Split the combined file into two separate source files — `rmp_professor_mendez.txt` and `rmp_professor_basanta.txt` — each with its own `PROFESSOR:` header. Re-running `chunk.py` and `embed.py` after the split would give each professor their own correctly tagged chunks. This is a one-time fix that also makes the corpus easier to extend when adding new professors.
 
---

## Spec Reflection

**One way the spec helped you during implementation:**
The chunking strategy section of `planning.md` was the most directly useful part of the spec during implementation. Because the chunk size (300 tokens), overlap (30 tokens), and source-specific rules (one RMP review = one chunk, one Reddit post + body = one chunk) were written down before any code was written, implementing `chunker.py` was straightforward — there were no ambiguous decisions to make mid-implementation. When the chunker was tested and produced only 18 chunks from the sample data, the spec also made it easy to diagnose the problem: the real professor-specific files had not yet been added, which the source list in the spec made obvious.

**One way your implementation diverged from the spec, and why:**
The spec listed Claude API as the generation model in the AI Tool Plan section. During implementation, Groq with `llama-3.3-70b-versatile` was used instead. The reason was practical: Groq offers a free tier with no billing setup required, runs the same open-weights Llama model with very low latency, and is OpenAI-compatible so the code required minimal changes. The grounding behavior and response quality were equivalent for this use case, so the divergence did not affect the system's correctness — only the specific API being called.
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The full `planning.md` file including the Chunking Strategy section (300 tokens, 30 overlap, RMP one-review-per-chunk rule, Reddit post+body rule), the Document Sources section listing all 10 URLs, and the pipeline diagram showing all five stages.
- *What it produced:* Two complete Python scripts — `ingest.py` with separate extractors for RMP, Reddit, and generic sources, and `chunker.py` with a dispatcher that routes each source file to the correct chunking strategy. It also produced sample raw data files for testing.
- *What I changed or overrode:* The initial `ingest.py` had a bug where `remove_html()` was called and its return value was used as a BeautifulSoup object, causing a crash on sites that returned malformed HTML. This was caught when running the script against real URLs and corrected in a second pass. The Reddit sources also had to be handled manually since Reddit blocked the scraper with a 403 error — the content was copy-pasted from the browser and reformatted.

**Instance 2**

- *What I gave the AI:* The raw HTML content copied from three Reddit pages (r/txstate search results for "professor" and "rate my professor", and the subreddit homepage), which included navigation menus, sidebar rules, moderator info, vote counts, and off-topic posts mixed in with the relevant professor discussion threads.
- *What it produced:* Three cleaned `.txt` files with all boilerplate removed and the content reformatted into the `POST TITLE:` / `POST BODY:` format that `chunker.py` expects, keeping only posts that contained actual professor opinions, names, difficulty ratings, or teaching style comments.
- *What I changed or overrode:* The long CS department rundown post (which mentioned Ted Lehr by name) was included in all three output files because it appeared in all three source pages. This was intentional — it is the richest single source of professor-specific signal in the Reddit corpus and the Lehr mention was important for the evaluation questions.