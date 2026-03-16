#!/usr/bin/env python3
"""
fix_keyword_index.py

Fixes the KEYWORD INDEX format inconsistency across the Bible vault.

PROBLEM:
  ~679 chapters use "Format 2" for the KEYWORD INDEX:
    **Label:** word1 word2, word3 word4
  The semantic search system expects "Format 1":
    `keyword` `keyword` `keyword`
    **Relevance to Current Events:**

WHAT THIS SCRIPT DOES:
  1. Identifies Format 2 chapters (no backtick keywords in KEYWORD INDEX)
  2. Extracts meaningful keywords from the **Label:** entries
  3. ADDS a backtick keyword line + Relevance placeholder AFTER the existing content
     (non-destructive — does NOT remove any existing content)
  4. Also finds and reports Format 1 chapters with overly long backtick phrases (9+ words)

USAGE:
  # Dry run — see what would be changed (no files written)
  python3 scripts/fix_keyword_index.py --dry-run

  # Fix all Format 2 chapters
  python3 scripts/fix_keyword_index.py

  # Fix a specific book only
  python3 scripts/fix_keyword_index.py --book ROMANS

  # Also report word-dump issues in Format 1 chapters
  python3 scripts/fix_keyword_index.py --report-word-dumps

  # After fixing, regenerate CONTENT_GAP_REPORT
  python3 scripts/fix_keyword_index.py && python3 scripts/audit_chapters.py
"""

import argparse
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent

# Stopwords to filter out when extracting keywords from Format 2 label sections
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "into",
    "it", "its", "this", "that", "these", "those", "he", "she", "we",
    "they", "his", "her", "our", "their", "all", "which", "who", "whom",
    "not", "no", "so", "then", "than", "when", "where", "why", "how",
    "if", "what", "also", "about", "through", "after", "before", "him",
    "them", "me", "my", "your", "up", "out", "over", "under", "more",
    "own", "other", "such", "only", "same", "very", "just", "even",
    "shall", "upon", "unto", "thy", "thou", "thee", "thine", "ye",
}

# Short words (2 chars) to skip
MIN_KEYWORD_LENGTH = 3

def find_all_chapter_files() -> list[Path]:
    """Find all REBUILT.md chapter files in the vault."""
    return sorted(VAULT_ROOT.glob("**/*_REBUILT.md"))


def get_keyword_index_section(content: str) -> tuple[int, int, str]:
    """
    Locate the KEYWORD INDEX section in a chapter file.
    Returns (start_line_idx, end_line_idx, section_text)
    where end is the line index of the section terminator (--- or next ##).
    """
    lines = content.split("\n")
    start = None
    end = None

    for i, line in enumerate(lines):
        if re.match(r"^##\s+KEYWORD INDEX", line, re.IGNORECASE):
            start = i
        elif start is not None and i > start:
            # Section ends at the next ## heading or end of file
            if re.match(r"^##\s+", line):
                end = i
                break

    if start is None:
        return -1, -1, ""

    if end is None:
        end = len(lines)

    section_text = "\n".join(lines[start:end])
    return start, end, section_text


def detect_format(section_text: str) -> str:
    """
    Detect whether a KEYWORD INDEX section is Format 1 (backtick) or Format 2 (label).
    Returns "backtick", "label", or "empty".
    """
    if not section_text.strip():
        return "empty"

    # Count backtick-wrapped keywords: `word` or `multi word`
    backtick_count = len(re.findall(r"`[^`]+`", section_text))

    # Count **Label:** entries
    label_count = len(re.findall(r"\*\*[^*]+?:\*\*", section_text))

    if backtick_count >= 3:
        return "backtick"
    elif label_count >= 1:
        return "label"
    else:
        return "empty"


def extract_keywords_from_label_format(section_text: str) -> list[str]:
    """
    Extract meaningful individual keywords from Format 2 label entries.

    Input format:
      **No Condemnation:** condemnation Christ, Jesus walk, flesh Spirit
      **Life in the Spirit:** flesh mind, Spirit mind, things Spirit

    Output: ["condemnation", "christ", "flesh", "spirit", "mind", ...]
    """
    keywords = set()

    # Extract content after **Label:** patterns
    label_pattern = re.compile(r"\*\*[^*]+?:\*\*\s*(.+?)(?=\n|$)", re.MULTILINE)
    for match in label_pattern.finditer(section_text):
        content = match.group(1)
        # Split on commas and spaces
        raw_words = re.split(r"[,\s]+", content)
        for word in raw_words:
            word = word.strip().lower()
            # Clean punctuation
            word = re.sub(r"[^\w\s-]", "", word)
            if (len(word) >= MIN_KEYWORD_LENGTH
                    and word not in STOPWORDS
                    and not word.isdigit()):
                keywords.add(word)

    # Also extract the label names themselves as keywords
    label_name_pattern = re.compile(r"\*\*([^*]+?):\*\*")
    for match in label_name_pattern.finditer(section_text):
        label = match.group(1).strip()
        # Split multi-word labels
        for word in re.split(r"\s+", label):
            word = word.lower().strip()
            word = re.sub(r"[^\w-]", "", word)
            if (len(word) >= MIN_KEYWORD_LENGTH
                    and word not in STOPWORDS):
                keywords.add(word)

    # Sort alphabetically for consistency
    return sorted(keywords)


def build_backtick_line(keywords: list[str]) -> str:
    """Format a list of keywords as a backtick keyword line."""
    return " ".join(f"`{kw}`" for kw in keywords)


def find_word_dump_phrases(section_text: str, max_words: int = 8) -> list[str]:
    """Find backtick phrases that are longer than max_words words."""
    dumps = []
    for match in re.finditer(r"`([^`]+)`", section_text):
        phrase = match.group(1)
        word_count = len(phrase.split())
        if word_count > max_words:
            dumps.append(phrase)
    return dumps


def fix_chapter_file(
    file_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Detect and fix the KEYWORD INDEX format in a single chapter file.

    Returns a dict with:
      - 'file': file path
      - 'format_before': 'backtick'|'label'|'empty'
      - 'format_after': same
      - 'keywords_added': int
      - 'word_dumps': list of long phrases found
      - 'changed': bool
    """
    result = {
        "file": file_path,
        "format_before": "unknown",
        "format_after": "unknown",
        "keywords_added": 0,
        "word_dumps": [],
        "changed": False,
    }

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        result["error"] = str(e)
        return result

    start, end, section_text = get_keyword_index_section(content)
    if start == -1:
        result["format_before"] = "missing"
        result["format_after"] = "missing"
        return result

    fmt = detect_format(section_text)
    result["format_before"] = fmt
    result["word_dumps"] = find_word_dump_phrases(section_text)

    if fmt == "backtick":
        # Format 1 — already good; just report word dumps
        result["format_after"] = "backtick"
        return result

    if fmt in ("label", "empty"):
        # Extract keywords from label format
        keywords = extract_keywords_from_label_format(section_text)

        if not keywords:
            result["format_after"] = fmt
            return result

        # Build the addition: a backtick keyword line + Relevance placeholder
        backtick_line = build_backtick_line(keywords)
        addition = (
            f"\n*AI Keywords for current event matching:*\n"
            f"{backtick_line}\n"
        )

        # Find where to insert — just before the section-ending separator
        # We want to insert before the first '---' separator within the section
        # (which sits at the end of the KEYWORD INDEX, before KEY TERMS)
        lines = content.split("\n")
        # Find the last '---' line before end of section
        insert_idx = end  # default: insert at end of section
        for i in range(end - 1, start, -1):
            if lines[i].strip() == "---":
                insert_idx = i
                break

        # Insert the addition
        new_lines = lines[:insert_idx] + addition.split("\n") + lines[insert_idx:]
        new_content = "\n".join(new_lines)

        result["keywords_added"] = len(keywords)
        result["format_after"] = "backtick"
        result["changed"] = True

        if verbose:
            print(f"  Keywords extracted ({len(keywords)}): {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}")

        if not dry_run:
            file_path.write_text(new_content, encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Fix KEYWORD INDEX format inconsistency across Bible vault chapters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing files")
    parser.add_argument("--book", type=str,
                        help="Only process files matching this book prefix (e.g. ROMANS, PSALM)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show keywords extracted for each file")
    parser.add_argument("--report-word-dumps", action="store_true",
                        help="List all word-dump phrases (9+ words in backtick tags)")
    parser.add_argument("--stats-only", action="store_true",
                        help="Only show statistics without making changes")
    args = parser.parse_args()

    if args.dry_run or args.stats_only:
        print("[DRY RUN — no files will be modified]" if args.dry_run else "[STATS ONLY]")

    files = find_all_chapter_files()
    if args.book:
        book_upper = args.book.upper()
        files = [f for f in files if book_upper in f.name.upper()]
        print(f"Filtered to {len(files)} files matching '{args.book}'")

    print(f"Scanning {len(files)} chapter files...\n")

    stats = {
        "total": len(files),
        "format1_backtick": 0,
        "format2_label": 0,
        "format_empty": 0,
        "format_missing": 0,
        "fixed": 0,
        "word_dump_files": 0,
        "word_dump_phrases": [],
    }

    fixed_files = []
    label_format_files = []

    for file_path in files:
        result = fix_chapter_file(
            file_path,
            dry_run=(args.dry_run or args.stats_only),
            verbose=args.verbose,
        )

        fmt = result["format_before"]
        if fmt == "backtick":
            stats["format1_backtick"] += 1
        elif fmt == "label":
            stats["format2_label"] += 1
            label_format_files.append(result)
        elif fmt == "empty":
            stats["format_empty"] += 1
        elif fmt == "missing":
            stats["format_missing"] += 1

        if result.get("word_dumps"):
            stats["word_dump_files"] += 1
            for phrase in result["word_dumps"]:
                stats["word_dump_phrases"].append((file_path.name, phrase))

        if result.get("changed"):
            stats["fixed"] += 1
            fixed_files.append(result)
            if args.verbose or args.dry_run:
                marker = "[DRY RUN]" if args.dry_run else "[FIXED]"
                print(f"{marker} {file_path.name} — {result['keywords_added']} keywords added")

    # Summary
    print("\n" + "=" * 60)
    print("KEYWORD INDEX FORMAT AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total chapter files scanned:     {stats['total']}")
    print(f"Format 1 (backtick — correct):   {stats['format1_backtick']}")
    print(f"Format 2 (label — needs fix):    {stats['format2_label']}")
    print(f"Empty / missing section:         {stats['format_empty'] + stats['format_missing']}")
    print(f"Files fixed/to fix:              {stats['fixed'] if not args.dry_run else len(label_format_files)}")
    print()
    print(f"Files with word-dump phrases:    {stats['word_dump_files']}")
    print(f"Total word-dump phrases found:   {len(stats['word_dump_phrases'])}")

    if args.report_word_dumps and stats["word_dump_phrases"]:
        print("\nWORD-DUMP PHRASES (9+ word backtick tags):")
        for fname, phrase in stats["word_dump_phrases"][:50]:
            print(f"  [{fname}] `{phrase}`")
        if len(stats["word_dump_phrases"]) > 50:
            print(f"  ...and {len(stats['word_dump_phrases']) - 50} more")

    if args.dry_run and label_format_files:
        print(f"\nFirst 10 files that would be fixed:")
        for r in label_format_files[:10]:
            print(f"  {r['file'].name}")

    if not args.dry_run and not args.stats_only:
        print(f"\n[✓] Fixed {stats['fixed']} files.")
        print(f"[✓] Run 'python3 scripts/audit_chapters.py' to regenerate the gap report.")


if __name__ == "__main__":
    main()
