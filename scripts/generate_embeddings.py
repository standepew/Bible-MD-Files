#!/usr/bin/env python3
"""
generate_embeddings.py
Generates semantic vector embeddings for every chapter in the repository
using a local sentence-transformer model. No data leaves your machine.

Usage:
    python3 scripts/generate_embeddings.py
    python3 scripts/generate_embeddings.py --model BAAI/bge-large-en-v1.5
    python3 scripts/generate_embeddings.py --batch-size 64
    python3 scripts/generate_embeddings.py --rebuild     # force regenerate all

Requirements:
    pip install -r scripts/requirements.txt
"""

import json
import time
import argparse
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = REPO_ROOT / "embeddings"
INDEX_FILE = EMBEDDINGS_DIR / "index.json"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.npy"

# Default model — change to bge-large for best quality on your RTX 5070
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

# Sections to extract from each chapter for embedding (ordered by priority)
EMBED_SECTIONS = [
    "CHAPTER METADATA",
    "CHAPTER SUMMARY",
    "CROSS-REFERENCES",
    "KEYWORD INDEX",
    "KEY TERMS",
]


def find_all_chapter_files(root: Path) -> list[Path]:
    """Find all *_REBUILT.md chapter files in the repository."""
    files = sorted(root.glob("**/*_REBUILT.md"))
    # Exclude any files in special directories
    files = [f for f in files if "STANLEY_DEPEW_SERIES" not in str(f)]
    return files


def extract_text_for_embedding(filepath: Path) -> str:
    """
    Extract the most semantically rich sections from a chapter file.
    Returns a single string suitable for embedding.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # Strip YAML frontmatter
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            text = text[end + 4:]
            lines = text.split("\n")

    # Collect lines from target sections
    collected: list[str] = []
    in_target_section = False
    chars_collected = 0
    max_chars = 3000  # Keep embedding input under ~800 tokens for bge-small

    for line in lines:
        # Detect section headers
        if line.startswith("## "):
            section_name = line.lstrip("#").strip().upper()
            in_target_section = any(s in section_name for s in EMBED_SECTIONS)

        if in_target_section or line.startswith("**Key Themes:**") or line.startswith("**Tags:**"):
            stripped = line.strip()
            if stripped and not stripped.startswith("---"):
                collected.append(stripped)
                chars_collected += len(stripped)

        if chars_collected >= max_chars:
            break

    return " ".join(collected) if collected else filepath.stem


def generate_embeddings(model_name: str, batch_size: int, rebuild: bool):
    """Main embedding generation routine."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("Run: pip install -r scripts/requirements.txt")
        return

    # Find chapters
    chapters = find_all_chapter_files(REPO_ROOT)
    print(f"Found {len(chapters)} chapter files.\n")

    # Check if we can skip already-embedded chapters
    existing_index: list[str] = []
    if INDEX_FILE.exists() and EMBEDDINGS_FILE.exists() and not rebuild:
        existing_index = json.loads(INDEX_FILE.read_text())
        print(f"Existing index has {len(existing_index)} entries. Embedding new chapters only.")
        print("Use --rebuild to regenerate everything.\n")

    existing_set = set(existing_index)
    new_chapters = [c for c in chapters if str(c.relative_to(REPO_ROOT)) not in existing_set]

    if not new_chapters and not rebuild:
        print("All chapters already embedded. Nothing to do.")
        print("Use --rebuild to regenerate.\n")
        return

    to_embed = chapters if rebuild else new_chapters
    print(f"Embedding {len(to_embed)} chapters...\n")

    # Load model
    print(f"Loading model: {model_name}")
    print("(First run will download ~130 MB — subsequent runs use local cache)\n")
    model = SentenceTransformer(model_name)

    # Extract text
    texts = []
    paths = []
    for ch in to_embed:
        text = extract_text_for_embedding(ch)
        texts.append(text)
        paths.append(str(ch.relative_to(REPO_ROOT)))

    # Generate embeddings in batches
    print(f"Generating embeddings (batch_size={batch_size})...")
    start = time.time()
    new_embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # Enables cosine similarity via dot product
        device=None,  # Auto-detect GPU/CPU
    )
    elapsed = time.time() - start
    print(f"\nEmbedding complete: {len(texts)} chapters in {elapsed:.1f}s")

    # Merge with existing embeddings
    EMBEDDINGS_DIR.mkdir(exist_ok=True)
    if rebuild or not existing_index:
        final_index = paths
        final_embeddings = new_embeddings
    else:
        existing_embeddings = np.load(EMBEDDINGS_FILE)
        final_index = existing_index + paths
        final_embeddings = np.vstack([existing_embeddings, new_embeddings])

    # Save
    np.save(EMBEDDINGS_FILE, final_embeddings.astype(np.float32))
    INDEX_FILE.write_text(json.dumps(final_index, indent=2))

    print(f"\nSaved {len(final_index)} embeddings to:")
    print(f"  {EMBEDDINGS_FILE}")
    print(f"  {INDEX_FILE}")
    print(f"\nEmbedding dimensions: {final_embeddings.shape}")
    print("Ready for semantic search. Run: python3 scripts/semantic_search.py \"your query\"")


def main():
    parser = argparse.ArgumentParser(description="Generate semantic embeddings for all Bible chapters")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Sentence-transformer model (default: {DEFAULT_MODEL})")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for encoding (default: 32)")
    parser.add_argument("--rebuild", action="store_true", help="Force regenerate all embeddings")
    args = parser.parse_args()

    generate_embeddings(args.model, args.batch_size, args.rebuild)


if __name__ == "__main__":
    main()
