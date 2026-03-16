#!/usr/bin/env python3
"""
news_prophecy_mapper.py

Fetches current world news from RSS feeds and maps headlines to biblical
prophecy chapters using:
  1. Semantic similarity (if embeddings are generated)
  2. Keyword matching against PROPHECY_FULFILLMENT_INDEX categories
  3. A curated prophecy keyword dictionary

Output: Appends dated entries to NEWS_PROPHECY_MAP.md
        formatted for Obsidian with wikilinks and YAML frontmatter.

Usage:
    python3 scripts/news_prophecy_mapper.py [OPTIONS]

Options:
    --feeds N         Max news items to process (default: 30)
    --top K           Top K chapter matches per headline (default: 3)
    --output FILE     Output file (default: NEWS_PROPHECY_MAP.md)
    --dry-run         Print results without writing to file
    --categories CAT  Only process specific categories (comma-separated)
    --since HOURS     Only process news from last N hours (default: 24)
    --verbose         Show detailed matching information

Requirements:
    pip3 install -r scripts/requirements.txt

For semantic search, run first:
    python3 scripts/generate_embeddings.py
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── Optional dependency imports ─────────────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

# ─── Configuration ────────────────────────────────────────────────────────────

VAULT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = VAULT_ROOT / "embeddings"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.npy"
INDEX_FILE = EMBEDDINGS_DIR / "index.json"

DEFAULT_OUTPUT = VAULT_ROOT / "NEWS_PROPHECY_MAP.md"

# News RSS feeds — ordered by prophetic relevance for the Middle East / end times
RSS_FEEDS = [
    ("Times of Israel",   "https://www.timesofisrael.com/feed/"),
    ("Jerusalem Post",    "https://www.jpost.com/rss/rssfeedsfrontpage.aspx"),
    ("BBC World News",    "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Reuters World",     "https://feeds.reuters.com/reuters/worldnews"),
    ("Al Jazeera",        "https://www.aljazeera.com/xml/rss/all.xml"),
    ("AP Top News",       "https://rsshub.app/ap/topics/apf-topnews"),
    ("The Guardian World","https://www.theguardian.com/world/rss"),
    ("Arutz Sheva",       "https://www.israelnationalnews.com/rss.aspx"),
]

# ─── Prophecy Keyword Dictionary ─────────────────────────────────────────────
# Maps keyword groups → prophetic category → relevant prophecy IDs and chapters

PROPHECY_KEYWORDS: dict[str, dict] = {
    "gog_magog": {
        "label": "Gog-Magog War (Ezek 38–39)",
        "prophecy_ids": ["P051"],
        "chapters": ["EZEKIEL_38_REBUILT", "EZEKIEL_39_REBUILT"],
        "alert_level": "red",
        "keywords": [
            "russia", "russian", "iran", "iranian", "turkey", "turkish",
            "hezbollah", "hamas", "coalition", "invasion", "invade",
            "israel attack", "attack israel", "strike israel",
            "gog", "magog", "rosh", "persia", "put", "cush", "togarmah",
            "military alliance", "multi-front", "northern alliance",
        ],
    },
    "israel_middle_east": {
        "label": "Israel / Middle East Tensions",
        "prophecy_ids": ["P038", "P040", "P041", "P042", "P051", "P052"],
        "chapters": ["EZEKIEL_36_REBUILT", "ZECHARIAH_12_REBUILT", "ZECHARIAH_14_REBUILT"],
        "alert_level": "red",
        "keywords": [
            "israel", "israeli", "jerusalem", "tel aviv", "west bank",
            "gaza", "hamas", "hezbollah", "idf", "netanyahu",
            "dome of the rock", "temple mount", "al-aqsa",
            "two-state", "abraham accords", "normalization",
            "middle east war", "regional war",
        ],
    },
    "third_temple": {
        "label": "Third Temple Preparations",
        "prophecy_ids": ["P048"],
        "chapters": ["DANIEL_09_REBUILT", "MATTHEW_24_REBUILT", "REVELATION_11_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "third temple", "temple mount", "temple institute",
            "red heifer", "sanhedrin", "temple vessels", "cornerstone",
            "rebuild temple", "jewish temple", "holy of holies",
            "ark of the covenant", "temple plans",
        ],
    },
    "global_governance": {
        "label": "Global Governance / One-World System",
        "prophecy_ids": ["P044"],
        "chapters": ["DANIEL_07_REBUILT", "REVELATION_13_REBUILT", "REVELATION_17_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "world government", "global governance", "new world order",
            "united nations reform", "world court", "international court",
            "global authority", "world parliament", "global treaty",
            "sovereignty transfer", "supranational",
        ],
    },
    "digital_currency_mark": {
        "label": "Digital Currency / Mark of the Beast Infrastructure",
        "prophecy_ids": ["P045"],
        "chapters": ["REVELATION_13_REBUILT", "REVELATION_14_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "cbdc", "central bank digital currency", "digital currency",
            "digital dollar", "e-yuan", "digital euro", "crypto ban",
            "cashless", "cash ban", "no cash", "digital id",
            "biometric", "microchip", "implant chip", "rfid implant",
            "social credit", "financial surveillance", "payment ban",
            "buy or sell", "mark", "666",
        ],
    },
    "ai_surveillance": {
        "label": "AI / Surveillance Infrastructure",
        "prophecy_ids": ["P045"],
        "chapters": ["REVELATION_13_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "facial recognition", "mass surveillance", "ai surveillance",
            "surveillance state", "total surveillance", "monitor citizens",
            "track population", "social scoring", "ai control",
            "digital tracking", "location tracking", "ai police",
        ],
    },
    "apostasy_false_religion": {
        "label": "Apostasy / False Religion / One-World Religion",
        "prophecy_ids": ["P044"],
        "chapters": ["REVELATION_17_REBUILT", "REVELATION_18_REBUILT", "2_THESSALONIANS_02_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "pope", "ecumenical", "one world religion", "interfaith",
            "chrislam", "united religions", "false prophet",
            "prosperity gospel", "apostate church", "deception church",
            "new age", "mysticism mainline", "syncretism",
        ],
    },
    "earthquakes_natural": {
        "label": "Earthquakes / Natural Disasters / Birth Pangs",
        "prophecy_ids": ["P050"],
        "chapters": ["MATTHEW_24_REBUILT", "LUKE_21_REBUILT", "REVELATION_06_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "earthquake", "magnitude", "richter", "tsunami",
            "volcano", "volcanic eruption", "hurricane", "typhoon",
            "wildfire", "flood", "biblical flood", "famine",
            "pestilence", "plague", "pandemic", "birth pangs",
        ],
    },
    "russia_ukraine_nato": {
        "label": "Russia / NATO / European Conflict",
        "prophecy_ids": ["P051"],
        "chapters": ["EZEKIEL_38_REBUILT", "DANIEL_11_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "russia", "ukraine", "nato", "nuclear", "nuclear threat",
            "world war", "world war 3", "ww3", "global war",
            "russia israel", "putin", "nuclear weapon",
            "escalate", "escalation", "military buildup",
        ],
    },
    "iran_nuclear": {
        "label": "Iran Nuclear Program",
        "prophecy_ids": ["P051"],
        "chapters": ["EZEKIEL_38_REBUILT", "DANIEL_11_REBUILT"],
        "alert_level": "red",
        "keywords": [
            "iran nuclear", "nuclear iran", "uranium enrichment",
            "nuclear deal", "jcpoa", "iranian bomb", "iran sanctions",
            "attack iran", "iran attack", "strike iran",
        ],
    },
    "armageddon_tribulation": {
        "label": "Armageddon / Tribulation Signs",
        "prophecy_ids": ["P049", "P052", "P053"],
        "chapters": ["REVELATION_16_REBUILT", "REVELATION_19_REBUILT", "ZECHARIAH_14_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "armageddon", "tribulation", "great tribulation", "7 years",
            "antichrist", "beast", "false prophet", "abomination",
            "second coming", "rapture", "day of the lord",
            "end of the world", "apocalypse", "revelation",
        ],
    },
    "israel_national_restoration": {
        "label": "Israel National / Spiritual Restoration",
        "prophecy_ids": ["P038", "P039", "P040", "P042"],
        "chapters": ["EZEKIEL_37_REBUILT", "ZECHARIAH_12_REBUILT", "ROMANS_11_REBUILT"],
        "alert_level": "yellow",
        "keywords": [
            "jewish revival", "israel revival", "messianic jews",
            "aliyah", "jewish immigration", "return to israel",
            "jewish population", "demographic", "orthodox revival",
            "israel nation", "jewish homeland",
        ],
    },
}

# ─── Helper Functions ─────────────────────────────────────────────────────────

def fetch_rss(url: str, timeout: int = 10) -> list[dict]:
    """Fetch and parse an RSS feed. Returns list of {title, link, description, pubdate}."""
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BibleProphecyMapper/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()

        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Handle standard RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pubdate = item.findtext("pubDate", "").strip()

            # Strip HTML from description
            desc = re.sub(r"<[^>]+>", " ", desc)
            desc = re.sub(r"\s+", " ", desc).strip()[:300]

            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "pubdate": pubdate,
                })

        # Handle Atom feeds
        if not items:
            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                link_el = entry.find("atom:link[@rel='alternate']", ns)
                if link_el is None:
                    link_el = entry.find("atom:link", ns)
                title = title_el.text.strip() if title_el is not None else ""
                link = link_el.get("href", "") if link_el is not None else ""
                if title:
                    items.append({"title": title, "link": link, "description": "", "pubdate": ""})

    except Exception as e:
        pass  # Silent fail — don't let one bad feed stop the whole run

    return items


def match_keyword_categories(text: str) -> list[dict]:
    """
    Match text against the prophecy keyword dictionary.
    Returns list of matching categories sorted by number of keyword hits.
    """
    text_lower = text.lower()
    matches = []

    for cat_id, cat_data in PROPHECY_KEYWORDS.items():
        hits = [kw for kw in cat_data["keywords"] if kw in text_lower]
        if hits:
            matches.append({
                "category_id": cat_id,
                "label": cat_data["label"],
                "prophecy_ids": cat_data["prophecy_ids"],
                "chapters": cat_data["chapters"],
                "alert_level": cat_data["alert_level"],
                "keyword_hits": hits,
                "score": len(hits),
            })

    return sorted(matches, key=lambda x: x["score"], reverse=True)


def load_embeddings() -> tuple:
    """Load pre-generated embeddings and chapter index. Returns (embeddings, index, model)."""
    if not HAS_NUMPY or not HAS_EMBEDDINGS:
        return None, None, None
    if not EMBEDDINGS_FILE.exists() or not INDEX_FILE.exists():
        return None, None, None

    try:
        embeddings = np.load(str(EMBEDDINGS_FILE))
        with open(INDEX_FILE) as f:
            index = json.load(f)

        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        return embeddings, index, model
    except Exception:
        return None, None, None


def semantic_search(query: str, embeddings, index: list, model, top_k: int = 3) -> list[dict]:
    """Find top-K most semantically similar chapters to the query."""
    query_embedding = model.encode([query], normalize_embeddings=True)
    scores = (embeddings @ query_embedding.T).flatten()
    top_indices = scores.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "chapter": Path(index[idx]).stem,
            "file_path": index[idx],
            "score": float(scores[idx]),
        })
    return results


def format_chapter_link(chapter_stem: str) -> str:
    """Convert a file stem like ROMANS_08_REBUILT to an Obsidian wikilink."""
    # Create a human-readable display name
    display = chapter_stem.replace("_REBUILT", "").replace("_", " ").title()
    # Fix common abbreviations
    replacements = {
        "Gen ": "Genesis ", "Exo ": "Exodus ", "Lev ": "Leviticus ",
        "Num ": "Numbers ", "Deu ": "Deuteronomy ", "Jos ": "Joshua ",
        "1Sa ": "1 Samuel ", "2Sa ": "2 Samuel ", "1Ki ": "1 Kings ",
        "2Ki ": "2 Kings ", "1Chr ": "1 Chronicles ", "2Chr ": "2 Chronicles ",
        "Neh ": "Nehemiah ", "Est ": "Esther ", "Psa ": "Psalm ",
        "Pro ": "Proverbs ", "Ecc ": "Ecclesiastes ",
    }
    for abbr, full in replacements.items():
        display = display.replace(abbr, full)
    return f"[[{chapter_stem}|{display}]]"


def generate_news_entry(item: dict, keyword_matches: list, semantic_matches: list, verbose: bool) -> str:
    """Format a single news item as an Obsidian-formatted entry."""
    lines = []
    title = item["title"]
    link = item["link"]
    pubdate = item.get("pubdate", "")

    # Determine highest alert level
    alert_level = "green"
    if keyword_matches:
        levels = [m["alert_level"] for m in keyword_matches]
        if "red" in levels:
            alert_level = "red"
        elif "yellow" in levels:
            alert_level = "yellow"

    alert_icon = {"red": "🔴", "yellow": "🟡", "green": "⚪"}.get(alert_level, "⚪")

    lines.append(f"\n### {alert_icon} {title}")
    if link:
        lines.append(f"> **Source:** [{link[:60]}...]({link})")
    if pubdate:
        lines.append(f"> **Published:** {pubdate}")

    # Keyword category matches
    if keyword_matches:
        lines.append(f"\n**Prophetic Categories Matched:**")
        for m in keyword_matches[:3]:  # Max 3 categories
            prophecy_links = " · ".join(
                f"[[PROPHECY_FULFILLMENT_INDEX#{pid}|{pid}]]" for pid in m["prophecy_ids"]
            )
            chapter_links = " · ".join(format_chapter_link(ch) for ch in m["chapters"][:2])
            lines.append(f"- **{m['label']}** | Prophecies: {prophecy_links}")
            lines.append(f"  - Key chapters: {chapter_links}")
            if verbose:
                lines.append(f"  - Keyword hits: `{', '.join(m['keyword_hits'][:5])}`")

    # Semantic matches
    if semantic_matches:
        lines.append(f"\n**Semantically Similar Chapters** (embedding search):")
        for sm in semantic_matches:
            ch_link = format_chapter_link(sm["chapter"])
            score_pct = f"{sm['score']*100:.0f}%"
            lines.append(f"- {ch_link} — similarity: {score_pct}")

    # Description excerpt
    desc = item.get("description", "")
    if desc and len(desc) > 20:
        lines.append(f"\n> *{desc[:200]}...*" if len(desc) > 200 else f"\n> *{desc}*")

    lines.append("\n---")
    return "\n".join(lines)


def build_output_header(date_str: str, total_items: int, matched_items: int) -> str:
    """Build the dated section header for the news map."""
    return f"""
## {date_str} — Daily Prophetic News Scan

> **Items processed:** {total_items} | **Prophetically significant:** {matched_items}
> *Generated by `scripts/news_prophecy_mapper.py` | Cross-reference: [[PROPHECY_FULFILLMENT_INDEX]]*

"""


def ensure_news_map_exists(output_path: Path) -> None:
    """Create NEWS_PROPHECY_MAP.md with a header if it doesn't exist."""
    if not output_path.exists():
        header = """# News → Prophecy Map
*Auto-generated current events mapped to biblical prophecy*

> **How this file is generated:**
> Run `python3 scripts/news_prophecy_mapper.py` to fetch today's news and map it to Scripture.
> Refresh automatically via cron: `0 7 * * * python3 /path/to/scripts/news_prophecy_mapper.py`
>
> **Important hermeneutical note:** The presence of current events that match prophetic patterns
> does NOT mean these prophecies are being fulfilled *right now*. Infrastructure and precursor
> conditions may exist for years or decades before actual fulfillment. This tool is for
> theological awareness and preparation, NOT date-setting.
>
> Cross-reference: [[PROPHECY_FULFILLMENT_INDEX]] · [[COVENANT_INDEX]] · [[_VAULT_HOME]]

---

"""
        output_path.write_text(header, encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Map current news to biblical prophecy")
    parser.add_argument("--feeds", type=int, default=30, help="Max news items to process")
    parser.add_argument("--top", type=int, default=3, help="Top K chapters per headline")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--dry-run", action="store_true", help="Print only, don't write")
    parser.add_argument("--categories", type=str, help="Filter to specific categories (comma-separated)")
    parser.add_argument("--since", type=int, default=24, help="Hours of news to process")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    output_path = Path(args.output)
    category_filter = [c.strip() for c in args.categories.split(",")] if args.categories else None

    print(f"[Bible Prophecy Mapper] Starting — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Load embeddings (optional)
    embeddings, index, model = None, None, None
    if HAS_NUMPY and HAS_EMBEDDINGS:
        print("[+] Loading semantic embeddings...")
        embeddings, index, model = load_embeddings()
        if embeddings is not None:
            print(f"[+] Embeddings loaded — {len(index)} chapters indexed")
        else:
            print("[!] Embeddings not found. Run generate_embeddings.py for semantic search.")
            print("[!] Falling back to keyword-only matching.")
    else:
        print("[!] sentence-transformers not installed. Using keyword matching only.")

    # Fetch news from all RSS feeds
    print(f"[+] Fetching news from {len(RSS_FEEDS)} RSS feeds...")
    all_items = []
    for feed_name, feed_url in RSS_FEEDS:
        items = fetch_rss(feed_url)
        if items:
            print(f"  [{feed_name}] {len(items)} items")
            for item in items:
                item["source"] = feed_name
            all_items.extend(items)
        else:
            print(f"  [{feed_name}] Failed or empty")
        time.sleep(0.3)  # Be polite to servers

    # Deduplicate by title
    seen_titles = set()
    unique_items = []
    for item in all_items:
        norm_title = re.sub(r"\W+", " ", item["title"].lower()).strip()
        if norm_title not in seen_titles and len(norm_title) > 10:
            seen_titles.add(norm_title)
            unique_items.append(item)

    # Limit to requested count
    unique_items = unique_items[:args.feeds]
    print(f"[+] Processing {len(unique_items)} unique headlines...")

    # Process each item
    significant_entries = []
    for item in unique_items:
        search_text = f"{item['title']} {item.get('description', '')}"

        # Keyword matching
        keyword_matches = match_keyword_categories(search_text)
        if category_filter:
            keyword_matches = [m for m in keyword_matches if m["category_id"] in category_filter]

        # Semantic matching
        semantic_matches = []
        if embeddings is not None and model is not None:
            semantic_matches = semantic_search(search_text, embeddings, index, model, top_k=args.top)
            # Filter to meaningful matches (>45% similarity)
            semantic_matches = [m for m in semantic_matches if m["score"] > 0.45]

        # Only include items with at least one match
        if keyword_matches or semantic_matches:
            entry_text = generate_news_entry(item, keyword_matches, semantic_matches, args.verbose)
            significant_entries.append({
                "item": item,
                "keyword_matches": keyword_matches,
                "semantic_matches": semantic_matches,
                "entry_text": entry_text,
                "alert_level": keyword_matches[0]["alert_level"] if keyword_matches else "green",
            })

    # Sort by alert level: red first, then yellow, then green
    level_order = {"red": 0, "yellow": 1, "green": 2}
    significant_entries.sort(key=lambda x: level_order.get(x["alert_level"], 2))

    print(f"[+] Found {len(significant_entries)} prophetically significant headlines")

    # Build output
    date_str = datetime.now().strftime("%B %d, %Y")
    date_tag = datetime.now().strftime("%Y-%m-%d")

    section_header = build_output_header(date_str, len(unique_items), len(significant_entries))
    entry_texts = [e["entry_text"] for e in significant_entries]

    full_section = section_header + "\n".join(entry_texts)

    if args.dry_run:
        print("\n" + "─" * 60)
        print(full_section)
        print("─" * 60)
        print("[DRY RUN] No file written.")
        return

    # Write to output file
    ensure_news_map_exists(output_path)
    existing_content = output_path.read_text(encoding="utf-8")

    # Check if today already has an entry — update it rather than duplicating
    date_pattern = f"## {date_str}"
    if date_pattern in existing_content:
        # Find and replace today's section
        lines = existing_content.split("\n")
        start_idx = None
        end_idx = len(lines)
        for i, line in enumerate(lines):
            if line.startswith(f"## {date_str}"):
                start_idx = i
            elif start_idx is not None and line.startswith("## ") and i > start_idx:
                end_idx = i
                break

        if start_idx is not None:
            new_lines = lines[:start_idx] + full_section.split("\n") + lines[end_idx:]
            output_path.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"[+] Updated today's entry in {output_path.name}")
    else:
        # Append new section after the header (before first ## date entry)
        # Find where first daily entry starts
        header_end = existing_content.find("\n## ")
        if header_end == -1:
            output_path.write_text(existing_content + full_section, encoding="utf-8")
        else:
            output_path.write_text(
                existing_content[:header_end] + "\n" + full_section + existing_content[header_end:],
                encoding="utf-8"
            )
        print(f"[+] Added new entry to {output_path.name}")

    print(f"\n[✓] Done — {len(significant_entries)} entries written")
    print(f"[✓] Open {output_path.name} in Obsidian to see results")
    print(f"\nTop matches today:")
    for e in significant_entries[:5]:
        icon = "🔴" if e["alert_level"] == "red" else "🟡"
        print(f"  {icon} {e['item']['title'][:70]}")


if __name__ == "__main__":
    main()
