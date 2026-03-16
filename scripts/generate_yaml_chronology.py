#!/usr/bin/env python3
"""
generate_yaml_chronology.py
Reads genealogy chapter files and validates / reports on YAML chronology frontmatter.
Can also generate a Gantt-ready CSV of anchor events across all chapters.

Usage:
    python3 scripts/generate_yaml_chronology.py               # Validate all YAML frontmatter
    python3 scripts/generate_yaml_chronology.py --gantt       # Export Gantt-ready CSV
    python3 scripts/generate_yaml_chronology.py --timeline    # Print ASCII timeline
"""

import re
import yaml
import csv
import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent

# Known genealogy chapters (expand this list as more YAML frontmatter is added)
GENEALOGY_CHAPTERS = [
    "01. Genesis/GEN_05_REBUILT.md",
    "01. Genesis/GEN_10_REBUILT.md",
    "01. Genesis/GEN_11_REBUILT.md",
    # Add more as frontmatter is added:
    # "13. 1 Chronicles/1CH_01_REBUILT.md",
    # "40. Matthew/MATTHEW_01_REBUILT.md",
    # "42. Luke/LUKE_03_REBUILT.md",
]


def extract_yaml_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter block from a Markdown file."""
    text = filepath.read_text(encoding="utf-8")
    # YAML frontmatter is between the first two '---' markers
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        print(f"  YAML parse error in {filepath.name}: {e}")
        return None


def collect_all_anchor_events(chapters: list[Path]) -> list[dict]:
    """Collect all anchor_events from chapters with chronology frontmatter."""
    events = []
    for filepath in chapters:
        data = extract_yaml_frontmatter(filepath)
        if not data or "chronology" not in data:
            continue
        chron = data["chronology"]
        chapter_name = filepath.stem.replace("_REBUILT", "")
        for evt in chron.get("anchor_events", []):
            am = evt.get("anno_mundi")
            if isinstance(am, str):
                # Handle approximate values like "~1757"
                am = int(re.sub(r"[^0-9]", "", am)) if re.search(r"\d", am) else None
            if am is not None:
                events.append({
                    "source_chapter": chapter_name,
                    "event": evt.get("event", ""),
                    "anno_mundi": am,
                    "source_verse": evt.get("source_verse", ""),
                    "note": evt.get("note", ""),
                })
    events.sort(key=lambda x: x["anno_mundi"])
    return events


def validate_frontmatter(filepath: Path) -> list[str]:
    """Check a chapter file's YAML frontmatter for completeness. Returns list of issues."""
    issues = []
    data = extract_yaml_frontmatter(filepath)
    if data is None:
        issues.append("No YAML frontmatter found")
        return issues

    chron = data.get("chronology")
    if not chron:
        issues.append("No 'chronology' key in frontmatter")
        return issues

    required_keys = ["chapter_type", "calendar", "anchor_events"]
    for key in required_keys:
        if key not in chron:
            issues.append(f"Missing key: chronology.{key}")

    for i, evt in enumerate(chron.get("anchor_events", [])):
        if "event" not in evt:
            issues.append(f"anchor_events[{i}] missing 'event'")
        if "anno_mundi" not in evt:
            issues.append(f"anchor_events[{i}] missing 'anno_mundi'")
        if "source_verse" not in evt:
            issues.append(f"anchor_events[{i}] missing 'source_verse'")

    return issues


def export_gantt_csv(events: list[dict], output_path: Path):
    """Export events as a Gantt-ready CSV for timeline tools."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["event", "anno_mundi", "source_verse", "source_chapter", "note"])
        writer.writeheader()
        writer.writerows(events)
    print(f"Gantt CSV written to: {output_path}")


def print_ascii_timeline(events: list[dict]):
    """Print a simple ASCII timeline of all anchor events."""
    if not events:
        print("No events found.")
        return

    min_am = events[0]["anno_mundi"]
    max_am = events[-1]["anno_mundi"]
    width = 80

    print(f"\n{'='*width}")
    print(f"BIBLICAL TIMELINE — Anno Mundi (AM)")
    print(f"AM {min_am} → AM {max_am}")
    print(f"{'='*width}\n")

    for evt in events:
        am = evt["anno_mundi"]
        # Scale position to width
        if max_am > min_am:
            pos = int((am - min_am) / (max_am - min_am) * (width - 20))
        else:
            pos = 0
        bar = "─" * pos + "●"
        print(f"AM {am:>5}  {bar}")
        print(f"         {'':>{pos}}  {evt['event']}")
        if evt["source_verse"]:
            print(f"         {'':>{pos}}  [{evt['source_verse']}]")
        print()


def main():
    parser = argparse.ArgumentParser(description="Validate and export biblical chronology YAML frontmatter")
    parser.add_argument("--gantt", action="store_true", help="Export Gantt-ready CSV")
    parser.add_argument("--timeline", action="store_true", help="Print ASCII timeline")
    parser.add_argument("--validate", action="store_true", help="Validate all chapter frontmatter (default)")
    args = parser.parse_args()

    chapters = []
    for rel_path in GENEALOGY_CHAPTERS:
        p = REPO_ROOT / rel_path
        if p.exists():
            chapters.append(p)
        else:
            print(f"WARNING: Chapter file not found: {rel_path}")

    print(f"Found {len(chapters)} genealogy chapters with potential YAML frontmatter.\n")

    # Always validate unless a specific action is chosen
    if args.validate or not (args.gantt or args.timeline):
        print("=== FRONTMATTER VALIDATION ===\n")
        all_clean = True
        for filepath in chapters:
            issues = validate_frontmatter(filepath)
            if issues:
                all_clean = False
                print(f"  ✗ {filepath.name}:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"  ✓ {filepath.name}: OK")
        if all_clean:
            print("\nAll chapters passed validation.")
        print()

    events = collect_all_anchor_events(chapters)
    print(f"Collected {len(events)} anchor events across all chapters.\n")

    if args.gantt:
        out_path = REPO_ROOT / "embeddings" / "chronology_gantt.csv"
        out_path.parent.mkdir(exist_ok=True)
        export_gantt_csv(events, out_path)

    if args.timeline:
        print_ascii_timeline(events)


if __name__ == "__main__":
    main()
