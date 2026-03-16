#!/usr/bin/env python3
"""
generate_hub_chapters.py
Parses MASTER_CROSS_REFERENCE_INDEX.md to produce a ranked hub-chapters report.

Usage:
    python3 scripts/generate_hub_chapters.py
    python3 scripts/generate_hub_chapters.py --top 50
    python3 scripts/generate_hub_chapters.py --output HUB_CHAPTERS_INDEX.md
"""

import re
import argparse
from pathlib import Path
from collections import defaultdict


REPO_ROOT = Path(__file__).parent.parent
CROSS_REF_FILE = REPO_ROOT / "MASTER_CROSS_REFERENCE_INDEX.md"

TIERS = [
    (80, "TIER 1 — STRUCTURAL PILLARS"),
    (50, "TIER 2 — MAJOR CROSSROADS"),
    (20, "TIER 3 — THEMATIC ANCHORS"),
    (1,  "TIER 4 — BOOK-LEVEL PILLARS"),
]


def parse_cross_reference_index(filepath: Path) -> dict[str, int]:
    """
    Extract chapter → reference-count from the FULL INDEX section.
    Handles both explicit counts like `(135x)` and implicit format `**Chapter** (Nx)`.
    """
    counts: dict[str, int] = {}
    text = filepath.read_text(encoding="utf-8")

    # Match lines like: **Romans 8** (135x) — ...
    pattern = re.compile(
        r"\*\*(?P<chapter>[A-Za-z0-9 ]+?)\*\*\s+\((?P<count>\d+)x\)"
    )
    for match in pattern.finditer(text):
        chapter = match.group("chapter").strip()
        count = int(match.group("count"))
        counts[chapter] = count

    return counts


def tier_label(count: int) -> str:
    for threshold, label in TIERS:
        if count >= threshold:
            return label
    return "TIER 4"


def generate_report(counts: dict[str, int], top_n: int | None = None) -> str:
    if not counts:
        return "ERROR: No data parsed from MASTER_CROSS_REFERENCE_INDEX.md"

    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    if top_n:
        ranked = ranked[:top_n]

    by_tier: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for chapter, count in ranked:
        by_tier[tier_label(count)].append((chapter, count))

    lines = [
        "# HUB CHAPTERS — CONNECTIVITY HEATMAP",
        "",
        f"**Total chapters tracked:** {len(counts)}",
        f"**Chapters in report:** {len(ranked)}",
        "",
        "---",
        "",
    ]

    for _, label in TIERS:
        tier_chapters = by_tier.get(label, [])
        if not tier_chapters:
            continue
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| Rank | Chapter | Inbound References |")
        lines.append("|------|---------|-------------------|")
        rank = sum(len(by_tier[t]) for _, t in TIERS if t < label) + 1
        for chapter, count in tier_chapters:
            lines.append(f"| {rank} | **{chapter}** | {count}x |")
            rank += 1
        lines.append("")

    # Book-level summary
    book_counts: dict[str, int] = defaultdict(int)
    for chapter, count in counts.items():
        book = re.match(r"^([A-Za-z ]+?)\s+\d+$", chapter)
        if book:
            book_counts[book.group(1).strip()] += count

    top_books = sorted(book_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    lines += [
        "---",
        "",
        "## TOP 15 BOOKS BY TOTAL CONNECTIVITY",
        "",
        "| Book | Aggregate Inbound Refs |",
        "|------|----------------------|",
    ]
    for book, total in top_books:
        lines.append(f"| **{book}** | {total} |")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate hub chapters heatmap from cross-reference index")
    parser.add_argument("--top", type=int, default=None, help="Limit to top N chapters")
    parser.add_argument("--output", type=str, default=None, help="Write output to file (default: stdout)")
    args = parser.parse_args()

    if not CROSS_REF_FILE.exists():
        print(f"ERROR: {CROSS_REF_FILE} not found")
        return

    counts = parse_cross_reference_index(CROSS_REF_FILE)
    print(f"Parsed {len(counts)} chapters from cross-reference index.")

    report = generate_report(counts, top_n=args.top)

    if args.output:
        out_path = REPO_ROOT / args.output
        out_path.write_text(report, encoding="utf-8")
        print(f"Written to: {out_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
