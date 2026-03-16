#!/usr/bin/env python3
"""
semantic_search.py
Search the Bible by concept, not just keyword.
Uses locally-generated embeddings — no internet required after setup.

Usage:
    python3 scripts/semantic_search.py "sacrificial love that costs the giver everything"
    python3 scripts/semantic_search.py "God dwelling physically among His people" --top 10
    python3 scripts/semantic_search.py "the remnant who hold fast when everyone falls away" --verbose
    python3 scripts/semantic_search.py --interactive     # continuous search session

Requirements:
    1. Run generate_embeddings.py first
    2. pip install -r scripts/requirements.txt
"""

import json
import argparse
import re
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = REPO_ROOT / "embeddings"
INDEX_FILE = EMBEDDINGS_DIR / "index.json"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.npy"

DEFAULT_TOP_K = 7
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


def load_index_and_embeddings() -> tuple[list[str], np.ndarray] | None:
    if not INDEX_FILE.exists() or not EMBEDDINGS_FILE.exists():
        print("ERROR: Embeddings not found.")
        print("Run: python3 scripts/generate_embeddings.py")
        return None
    index = json.loads(INDEX_FILE.read_text())
    embeddings = np.load(EMBEDDINGS_FILE)
    return index, embeddings


def search(query: str, index: list[str], embeddings: np.ndarray,
           model, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """Embed the query and find the top-k most similar chapters."""
    query_vec = model.encode([query], normalize_embeddings=True)
    # Cosine similarity (embeddings are pre-normalized)
    scores = (embeddings @ query_vec.T).squeeze()
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        path = index[idx]
        score = float(scores[idx])
        # Parse a human-readable chapter name from the path
        stem = Path(path).stem.replace("_REBUILT", "").replace("_", " ")
        book_dir = Path(path).parent.name
        results.append({
            "path": path,
            "chapter": stem,
            "book_dir": book_dir,
            "score": score,
        })
    return results


def get_excerpt(filepath: Path, max_lines: int = 6) -> str:
    """Pull the CHAPTER SUMMARY section from a chapter file."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"## CHAPTER SUMMARY\s*\n(.*?)(?=\n---|\n## )", text, re.DOTALL)
    if match:
        lines = [l.strip() for l in match.group(1).strip().split("\n") if l.strip()]
        excerpt = " ".join(lines[:max_lines])
        return excerpt[:400] + ("..." if len(excerpt) > 400 else "")
    return ""


def display_results(results: list[dict], verbose: bool = False):
    print(f"\n{'━'*60}")
    for i, r in enumerate(results, 1):
        score_bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
        print(f"\n  {i}. {r['chapter']}")
        print(f"     Similarity: [{score_bar}] {r['score']:.3f}")
        print(f"     Path: {r['path']}")
        if verbose:
            full_path = REPO_ROOT / r["path"]
            if full_path.exists():
                excerpt = get_excerpt(full_path)
                if excerpt:
                    print(f"     Summary: {excerpt}")
    print(f"\n{'━'*60}")


def run_search(query: str, index, embeddings, model, top_k: int, verbose: bool):
    print(f"\nQuery: \"{query}\"")
    results = search(query, index, embeddings, model, top_k)
    display_results(results, verbose)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Semantic search across 1,188 Bible chapters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/semantic_search.py "sacrificial love that costs the giver everything"
  python3 scripts/semantic_search.py "God's wrath poured out on a substitute" --top 10
  python3 scripts/semantic_search.py "the remnant preserved through judgment" --verbose
  python3 scripts/semantic_search.py --interactive
        """
    )
    parser.add_argument("query", nargs="?", help="Your semantic search query")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_K, help=f"Number of results (default: {DEFAULT_TOP_K})")
    parser.add_argument("--verbose", action="store_true", help="Show chapter summaries in results")
    parser.add_argument("--interactive", action="store_true", help="Run an interactive search session")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (must match what was used to generate embeddings)")
    args = parser.parse_args()

    if not args.query and not args.interactive:
        parser.print_help()
        return

    # Load data
    result = load_index_and_embeddings()
    if result is None:
        return
    index, embeddings = result
    print(f"Loaded {len(index)} chapter embeddings.")

    # Load model
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("Run: pip install -r scripts/requirements.txt")
        return

    print(f"Loading model: {args.model} ...")
    model = SentenceTransformer(args.model)

    if args.interactive:
        print("\n=== SEMANTIC BIBLE SEARCH ===")
        print("Type your query and press Enter. Type 'quit' to exit.\n")
        while True:
            try:
                query = input("Search: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            if query:
                run_search(query, index, embeddings, model, args.top, args.verbose)
    else:
        run_search(args.query, index, embeddings, model, args.top, args.verbose)


if __name__ == "__main__":
    main()
