#!/usr/bin/env python3
"""
audit_chapters.py

Accurate content quality audit for the Bible vault.
Replaces the buggy CONTENT_GAP_REPORT.md with correct data.

WHAT IT CHECKS:
  1. KEYWORD INDEX format (backtick vs label vs empty)
  2. Actual hashtag count from the **Tags:** line in CHAPTER METADATA
  3. Placeholder/empty sections (COMMONLY MISQUOTED, SYMBOLIC THREADS, etc.)
  4. Word-dump backtick phrases (9+ words — legitimately too long)
  5. Missing sections entirely

USAGE:
  python3 scripts/audit_chapters.py                    # Regenerate CONTENT_GAP_REPORT.md
  python3 scripts/audit_chapters.py --print-only       # Print to stdout, don't write
  python3 scripts/audit_chapters.py --section MISQUOTED  # Focus on one section type
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = VAULT_ROOT / "CONTENT_GAP_REPORT.md"

# The 9 required sections in every chapter file
REQUIRED_SECTIONS = [
    "CHAPTER METADATA",
    "CHAPTER SUMMARY",
    "CROSS-REFERENCES",
    "KEYWORD INDEX",
    "KEY TERMS",
    "THE ACTUAL VERSES",
    "PROPHETIC",
    "COMMONLY MISQUOTED",
    "SYMBOLIC THREADS",
]

# Phrases that indicate a section is placeholder-only.
# These are checked as whole-word / start-of-line patterns to avoid false positives
# on legitimate content (e.g. "human/agricultural" containing "n/a").
PLACEHOLDER_PHRASES_EXACT = [
    "review and add",
    "to be added",
    "coming soon",
    "*(add",
    "*(review",
    "*(to be",
]

# These require word-boundary matching so they don't hit embedded substrings
PLACEHOLDER_PHRASES_WORD = [
    "placeholder",
    "none identified",
]

# These only flag when they appear at the start of a line (standalone use, not in sentences)
PLACEHOLDER_PHRASES_LINE_START = [
    "no specific",
    "not applicable",
    "n/a",
]


def find_all_chapter_files() -> list[Path]:
    return sorted(VAULT_ROOT.glob("**/*_REBUILT.md"))


def count_hashtags(content: str) -> int:
    """Count proper #hashtag entries in the **Tags:** line."""
    match = re.search(r"\*\*Tags:\*\*\s*(.+)", content)
    if not match:
        return 0
    tags_line = match.group(1)
    return len(re.findall(r"#[\w-]+", tags_line))


def get_section_content(content: str, section_name: str) -> str:
    """Extract the content of a specific section by full section name."""
    lines = content.split("\n")
    start = None
    end = None
    # Match using the full section name (not just first word) to avoid
    # false matches between similarly-named sections (e.g. KEY TERMS vs KEYWORD INDEX,
    # CHAPTER METADATA vs CHAPTER SUMMARY).
    for i, line in enumerate(lines):
        if re.match(rf"^##\s+.*{re.escape(section_name.upper())}",
                    line, re.IGNORECASE):
            if start is None:
                start = i + 1
        elif start is not None and re.match(r"^##\s+", line):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start: end or len(lines)])


def is_placeholder(section_text: str) -> bool:
    """Check if a section contains only placeholder content."""
    text_lower = section_text.lower().strip()
    if not text_lower:
        return True
    # Exact substring matches (safe — these don't appear in legitimate content)
    for phrase in PLACEHOLDER_PHRASES_EXACT:
        if phrase in text_lower:
            return True
    # Word-boundary matches
    for phrase in PLACEHOLDER_PHRASES_WORD:
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            return True
    # Line-start matches only — avoids catching these phrases mid-sentence
    for phrase in PLACEHOLDER_PHRASES_LINE_START:
        if re.search(rf"^{re.escape(phrase)}\b", text_lower, re.MULTILINE):
            return True
    # Very short section (< 30 chars of actual content) is suspicious
    actual_content = re.sub(r"[#\-*\s]", "", text_lower)
    if len(actual_content) < 30:
        return True
    return False


def detect_keyword_format(content: str) -> str:
    """Returns 'backtick', 'label', 'empty', or 'missing'."""
    kw_section = get_section_content(content, "KEYWORD INDEX")
    if not kw_section.strip():
        # Check if section exists at all
        if "## KEYWORD INDEX" in content.upper():
            return "empty"
        return "missing"
    backtick_count = len(re.findall(r"`[^`]+`", kw_section))
    label_count = len(re.findall(r"\*\*[^*]+?:\*\*", kw_section))
    if backtick_count >= 3:
        return "backtick"
    elif label_count >= 1:
        return "label"
    return "empty"


def count_backtick_keywords(content: str) -> int:
    """Count backtick-wrapped keywords in the KEYWORD INDEX section."""
    kw_section = get_section_content(content, "KEYWORD INDEX")
    return len(re.findall(r"`[^`]+`", kw_section))


def find_word_dumps(content: str, max_words: int = 8) -> list[str]:
    """Find backtick phrases over max_words words in the KEYWORD INDEX."""
    kw_section = get_section_content(content, "KEYWORD INDEX")
    return [
        m.group(1)
        for m in re.finditer(r"`([^`]+)`", kw_section)
        if len(m.group(1).split()) > max_words
    ]


def get_book_chapter(file_path: Path) -> tuple[str, int]:
    """Extract human-readable book and chapter number from filename."""
    stem = file_path.stem  # e.g. ROMANS_08_REBUILT
    parts = stem.replace("_REBUILT", "").split("_")
    if not parts:
        return stem, 0
    # Last part is the chapter number
    try:
        chapter = int(parts[-1])
        book = " ".join(p.title() for p in parts[:-1])
        # Fix common abbreviations
        abbr_map = {
            "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus",
            "Num": "Numbers", "Deu": "Deuteronomy", "Jos": "Joshua",
            "1Sa": "1 Samuel", "2Sa": "2 Samuel", "1Ki": "1 Kings",
            "2Ki": "2 Kings", "1Chr": "1 Chronicles", "2Chr": "2 Chronicles",
            "Jdg": "Judges",
        }
        for abbr, full in abbr_map.items():
            book = book.replace(abbr, full)
        return book, chapter
    except (ValueError, IndexError):
        return stem, 0


def audit_file(file_path: Path) -> dict:
    """Run all quality checks on a single chapter file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {"file": file_path, "error": str(e)}

    book, chapter = get_book_chapter(file_path)

    result = {
        "file": file_path,
        "book": book,
        "chapter": chapter,
        "hashtag_count": count_hashtags(content),
        "keyword_format": detect_keyword_format(content),
        "backtick_keyword_count": count_backtick_keywords(content),
        "word_dumps": find_word_dumps(content),
        "placeholder_sections": [],
        "missing_sections": [],
    }

    # Check each required section
    for section in REQUIRED_SECTIONS:
        section_content = get_section_content(content, section)
        if not section_content.strip():
            if f"## {section.upper()}" not in content.upper():
                result["missing_sections"].append(section)
        elif is_placeholder(section_content):
            result["placeholder_sections"].append(section)

    return result


def generate_report(results: list[dict]) -> str:
    """Generate the updated CONTENT_GAP_REPORT.md content."""
    total = len(results)
    errors = [r for r in results if "error" in r]

    # Stats
    hashtag_low = [r for r in results if r.get("hashtag_count", 99) < 3]
    format2_label = [r for r in results if r.get("keyword_format") == "label"]
    format1_backtick = [r for r in results if r.get("keyword_format") == "backtick"]
    format_empty = [r for r in results if r.get("keyword_format") in ("empty", "missing")]
    word_dump_files = [r for r in results if r.get("word_dumps")]

    # Placeholder sections
    placeholder_by_section = defaultdict(list)
    missing_by_section = defaultdict(list)
    for r in results:
        for sec in r.get("placeholder_sections", []):
            placeholder_by_section[sec].append(f"{r['book']} {r['chapter']}")
        for sec in r.get("missing_sections", []):
            missing_by_section[sec].append(f"{r['book']} {r['chapter']}")

    total_placeholder = sum(len(v) for v in placeholder_by_section.values())
    files_with_gaps = len(set(
        r["file"] for r in results
        if r.get("placeholder_sections") or r.get("missing_sections")
    ))

    lines = [
        "# CONTENT GAP REPORT",
        "",
        f"**Generated by:** `python3 scripts/audit_chapters.py`",
        f"**Total files scanned:** {total}",
        f"**Files with content gaps:** {files_with_gaps}",
        f"**Total placeholder instances:** {total_placeholder}",
        "",
        "---",
        "",
        "## KEYWORD INDEX FORMAT AUDIT",
        "",
        "The KEYWORD INDEX section uses two different formats across the vault.",
        "Format 1 (backtick keywords) is required for semantic search and current-event matching.",
        "Format 2 (label: text) is human-readable but not machine-parseable.",
        "Run `python3 scripts/fix_keyword_index.py` to convert Format 2 → Format 1.",
        "",
        f"| Format | Count | Note |",
        f"|--------|-------|------|",
        f"| Format 1 — backtick `keywords` (correct) | {len(format1_backtick)} | ✅ Search-ready |",
        f"| Format 2 — **Label:** text (needs fix) | {len(format2_label)} | ⚠️ Run fix script |",
        f"| Empty / missing | {len(format_empty)} | ⚠️ Needs content |",
        "",
        "### Files Using Format 2 (Label Format) — First 30",
        "",
    ]

    for r in format2_label[:30]:
        lines.append(f"- **{r['book']} {r['chapter']}** — {r.get('backtick_keyword_count', 0)} backtick keywords (label format)")
    if len(format2_label) > 30:
        lines.append(f"- *...and {len(format2_label) - 30} more — run script to see all*")

    lines += [
        "",
        "---",
        "",
        "## HASHTAG TAG COUNT (from **Tags:** line)",
        "",
        "*(This counts #hashtag entries in the CHAPTER METADATA Tags line — separate from KEYWORD INDEX)*",
        "",
    ]

    # Hashtag counts
    if hashtag_low:
        lines.append(f"### Chapters with Fewer Than 3 Hashtag Tags ({len(hashtag_low)} chapters)")
        lines.append("")
        for r in hashtag_low[:30]:
            lines.append(f"- **{r['book']} {r['chapter']}** — {r['hashtag_count']} hashtags")
        if len(hashtag_low) > 30:
            lines.append(f"- *...and {len(hashtag_low) - 30} more*")
    else:
        lines.append("✅ All chapters have 3+ hashtag tags in the **Tags:** line.")

    lines += [
        "",
        "---",
        "",
        "## SECTION CONTENT GAPS",
        "",
        "*(PLACEHOLDER = section exists but only has generic text; MISSING = section not present)*",
        "",
    ]

    if total_placeholder == 0 and not missing_by_section:
        lines.append("✅ No placeholder or missing sections found.")
    else:
        lines.append(f"**Total placeholder instances:** {total_placeholder}")
        lines.append("")

        for section, chapters in sorted(placeholder_by_section.items(), key=lambda x: -len(x[1])):
            lines.append(f"### Placeholder: {section} ({len(chapters)} chapters)")
            lines.append("")
            for ch in sorted(chapters)[:20]:
                lines.append(f"  - {ch}")
            if len(chapters) > 20:
                lines.append(f"  - *...and {len(chapters) - 20} more*")
            lines.append("")

        for section, chapters in sorted(missing_by_section.items(), key=lambda x: -len(x[1])):
            lines.append(f"### Missing Section: {section} ({len(chapters)} chapters)")
            lines.append("")
            for ch in sorted(chapters)[:20]:
                lines.append(f"  - {ch}")
            if len(chapters) > 20:
                lines.append(f"  - *...and {len(chapters) - 20} more*")
            lines.append("")

    lines += [
        "---",
        "",
        "## WORD-DUMP BACKTICK PHRASES",
        "",
        "*(Backtick-wrapped keywords with 9+ words — consider splitting into shorter keywords)*",
        "",
        f"Files affected: {len(word_dump_files)}",
        f"Total long phrases: {sum(len(r['word_dumps']) for r in word_dump_files)}",
        "",
    ]

    if word_dump_files:
        lines.append("### Sample Word-Dump Phrases")
        lines.append("")
        count = 0
        for r in word_dump_files:
            for phrase in r["word_dumps"]:
                lines.append(f"- **{r['book']} {r['chapter']}:** `` `{phrase}` ``")
                count += 1
                if count >= 30:
                    break
            if count >= 30:
                break
        if sum(len(r["word_dumps"]) for r in word_dump_files) > 30:
            lines.append(f"- *...and more — run `--report-word-dumps` on fix script for full list*")

    lines += [
        "",
        "---",
        "",
        "## HOW TO FIX",
        "",
        "```bash",
        "# 1. Preview what would change (dry run)",
        "python3 scripts/fix_keyword_index.py --dry-run",
        "",
        "# 2. Fix all Format 2 chapters (adds backtick keywords + Relevance placeholder)",
        "python3 scripts/fix_keyword_index.py",
        "",
        "# 3. Regenerate this report after fixing",
        "python3 scripts/audit_chapters.py",
        "```",
        "",
        "**Sections requiring human review (cannot be auto-fixed):**",
        "- COMMONLY MISQUOTED — needs correct exegetical content per chapter",
        "- SYMBOLIC THREADS — needs theological analysis per chapter",
        "- Relevance to Current Events — needs contemporary connections per chapter",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Accurate content quality audit for the Bible vault"
    )
    parser.add_argument("--print-only", action="store_true",
                        help="Print report to stdout without writing file")
    parser.add_argument("--section", type=str,
                        help="Focus on a specific section (e.g. MISQUOTED)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    files = find_all_chapter_files()
    print(f"Auditing {len(files)} chapter files...", end=" ", flush=True)

    results = []
    for f in files:
        results.append(audit_file(f))

    print("done.")

    report = generate_report(results)

    if args.print_only:
        print(report)
    else:
        OUTPUT_FILE.write_text(report, encoding="utf-8")
        print(f"[✓] Report written to {OUTPUT_FILE.name}")

        # Print summary to console
        fmt2 = sum(1 for r in results if r.get("keyword_format") == "label")
        fmt1 = sum(1 for r in results if r.get("keyword_format") == "backtick")
        placeholders = sum(len(r.get("placeholder_sections", [])) for r in results)
        print(f"\nSummary:")
        print(f"  Format 1 (backtick — search ready): {fmt1}")
        print(f"  Format 2 (label — needs fix):        {fmt2}")
        print(f"  Placeholder sections:                 {placeholders}")
        print(f"\nRun 'python3 scripts/fix_keyword_index.py' to fix Format 2 chapters.")


if __name__ == "__main__":
    main()
