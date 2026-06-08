"""
ingest.py — Stage 1: Document Ingestion
TXST Professor Reviews RAG Pipeline

Fetches raw text from all 10 source URLs defined in planning.md.
Saves one cleaned-but-not-chunked text file per source to data/raw/.

Usage:
  python ingest.py

Output:
  data/raw/<source_name>.txt  — one file per source, UTF-8 plain text
  data/raw/manifest.json      — records source URL, file path, fetch timestamp
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

SOURCES = [
    ("rmp_txst_school",          "https://www.ratemyprofessors.com/school/938",                                       "rmp_school"),
    ("rmp_txst_all_professors",  "https://www.ratemyprofessors.com/search/professors/938?q=*",                        "rmp_search"),
    ("rmp_professor_ramirez",    "https://www.ratemyprofessors.com/professor/1957208",                                 "rmp_professor"),
    ("coursicle_txst_professors","https://www.coursicle.com/txstate/professors/",                                     "generic"),
    ("reddit_txstate_subreddit", "https://old.reddit.com/r/txstate/",                                                 "reddit_listing"),
    ("reddit_txstate_search_professor", "https://old.reddit.com/r/txstate/search/?q=professor&restrict_sr=1&sort=top","reddit_listing"),
    ("reddit_txstate_search_rmp","https://old.reddit.com/r/txstate/search/?q=rate+my+professor&restrict_sr=1&sort=top","reddit_listing"),
    ("uloop_txst_professors",    "https://txstate.uloop.com/professors",                                              "generic"),
    ("professors_directory_txst","https://www.professors.directory/school/tx-texas_state_university/",                "generic"),
    ("rmp_io_txst",              "https://ratemyprofessors.io/texas-state-university",                                "generic"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def strip_boilerplate(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove nav/footer/script/ad tags from soup IN PLACE. Returns soup."""
    for tag in soup.find_all(["nav", "header", "footer", "aside",
                               "script", "style", "noscript", "iframe", "form"]):
        tag.decompose()

    boilerplate_patterns = [
        "cookie", "banner", "ad-", "advertisement", "sidebar",
        "share", "social", "comment-count", "read-more",
        "related", "newsletter", "popup", "modal", "overlay",
        "breadcrumb", "pagination", "site-header", "site-footer",
        "menu", "nav-", "toolbar",
    ]
    for tag in soup.find_all(True):
        # Guard: tag may already have been decomposed by a parent
        if tag.parent is None:
            continue
        tag_id    = (tag.get("id") or "").lower()
        tag_class = " ".join(tag.get("class") or []).lower()
        combined  = tag_id + " " + tag_class
        if any(p in combined for p in boilerplate_patterns):
            tag.decompose()

    return soup


def clean_text(raw: str) -> str:
    """Decode entities, collapse whitespace, drop boilerplate lines."""
    raw = re.sub(r"<[^>]+>", " ", raw)
    for entity, char in [("&amp;","&"),("&nbsp;"," "),("&lt;","<"),
                          ("&gt;",">"),("&quot;",'"'),("&#39;","'"),("&apos;","'")]:
        raw = raw.replace(entity, char)

    raw = re.sub(r"[ \t]+", " ", raw)

    nav_fragments = [
        "sign in", "log in", "sign up", "create account",
        "privacy policy", "terms of service", "cookie policy",
        "all rights reserved", "copyright ©", "skip to content",
        "rate my professors", "© 20", "helpful?", "thumbs up",
        "load more", "show more", "read more", "share this",
        "tweet", "facebook",
    ]

    lines = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if len(ln) < 20:
            continue
        if any(frag in ln.lower() for frag in nav_fragments):
            continue
        lines.append(ln)

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

def fetch_generic(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    if not resp.text.strip():
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    strip_boilerplate(soup)   # modifies in place, returns soup (not str)

    parts = []
    for tag in soup.find_all(["p", "li", "h2", "h3", "span", "div"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            parts.append(text)

    return clean_text("\n".join(parts))


def fetch_rmp_professor(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    parts = []

    name_tag = soup.find("div", class_=re.compile(r"NameTitle"))
    if name_tag:
        parts.append("PROFESSOR: " + name_tag.get_text(separator=" ", strip=True))

    dept_tag = soup.find("div", class_=re.compile(r"Department|Title"))
    if dept_tag:
        parts.append("DEPARTMENT: " + dept_tag.get_text(separator=" ", strip=True))

    review_cards = soup.find_all("div", class_=re.compile(r"Rating__RatingBody|rating-body|Review"))
    if review_cards:
        for card in review_cards:
            text = card.get_text(separator=" ", strip=True)
            if len(text) > 30:
                parts.append("REVIEW: " + text)
    else:
        # RMP is JS-rendered — fall back to generic text extraction
        strip_boilerplate(soup)
        for tag in soup.find_all(["p", "li", "div"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) > 40:
                parts.append(text)

    return clean_text("\n\n".join(parts))


def fetch_rmp_search(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    parts = []
    cards = soup.find_all("div", class_=re.compile(r"TeacherCard|professor-card|CardName"))
    if cards:
        for card in cards:
            text = card.get_text(separator=" ", strip=True)
            if len(text) > 20:
                parts.append(text)
    else:
        strip_boilerplate(soup)
        for tag in soup.find_all(["p", "li", "div"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) > 40:
                parts.append(text)

    return clean_text("\n".join(parts))


def fetch_rmp_school(url: str) -> str:
    return fetch_generic(url)


def fetch_reddit_listing(url: str) -> str:
    """
    Reddit blocks most scrapers. We try old.reddit.com first.
    If blocked, return an empty string — the user should
    manually paste Reddit content using the POST TITLE / POST BODY format.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"  Reddit blocked ({e}). Create the file manually — see instructions below.")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    parts = []
    for entry in soup.find_all("div", class_="entry"):
        title_tag = entry.find("a", class_="title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        body_tag = entry.find("div", class_="expando")
        body = body_tag.get_text(separator=" ", strip=True)[:400] if body_tag else ""
        if title and len(title) > 10:
            parts.append(f"POST TITLE: {title}")
            if body and len(body) > 20:
                parts.append(f"POST BODY: {body}")

    return clean_text("\n".join(parts)) if parts else ""


EXTRACTOR_MAP = {
    "rmp_professor":  fetch_rmp_professor,
    "rmp_search":     fetch_rmp_search,
    "rmp_school":     fetch_rmp_school,
    "reddit_listing": fetch_reddit_listing,
    "generic":        fetch_generic,
}


# ---------------------------------------------------------------------------
# Main ingestion loop
# ---------------------------------------------------------------------------

def ingest_all(sources=SOURCES, delay=1.5):
    manifest = []

    for slug, url, source_type in sources:
        out_path = os.path.join(RAW_DIR, f"{slug}.txt")
        print(f"Fetching [{source_type}] {slug} ...")

        try:
            extractor = EXTRACTOR_MAP.get(source_type, fetch_generic)
            text = extractor(url)

            if not text.strip():
                print(f"  WARNING: empty result for {slug} — create {out_path} manually")
                text = f"[No content retrieved from {url} — paste content here manually]"

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

            word_count = len(text.split())
            print(f"  Saved {word_count} words → {out_path}")

            manifest.append({
                "slug": slug, "url": url, "source_type": source_type,
                "file": out_path, "word_count": word_count,
                "fetched_at": datetime.utcnow().isoformat(), "status": "ok",
            })

        except Exception as exc:
            print(f"  ERROR: {exc}")
            # Still write a placeholder so chunk.py can skip gracefully
            placeholder = f"[Failed to fetch {url}: {exc}]"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(placeholder)
            manifest.append({
                "slug": slug, "url": url, "source_type": source_type,
                "file": out_path, "status": f"error: {exc}",
                "fetched_at": datetime.utcnow().isoformat(),
            })

        time.sleep(delay)

    manifest_path = os.path.join(RAW_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. {len(manifest)} sources processed.")
    print(f"Manifest → {manifest_path}")

    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS — manual content for blocked sources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For any file that says [No content retrieved...]:
  1. Open the source URL in your browser
  2. Copy the review/post text
  3. Paste into the .txt file using this format:

  For RMP professor pages:
    PROFESSOR: Ted Lehr
    DEPARTMENT: Computer Science

    REVIEW: <paste review text here>

    REVIEW: <paste next review here>

  For Reddit threads:
    POST TITLE: <paste post title here>
    POST BODY: <paste post body or top reply here>

    POST TITLE: <next post title>
    POST BODY: <next post body>

Then run: python chunk.py
""")

    return manifest


if __name__ == "__main__":
    ingest_all()