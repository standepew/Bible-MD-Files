#!/usr/bin/env python3
"""
bible_qa.py

Conversational Bible Q&A using:
  1. Semantic retrieval from the 1,188-chapter embedding index
  2. A local LLM via Ollama for Scripture-grounded answers

Usage:
    python3 scripts/bible_qa.py "Your question here" [OPTIONS]

Options:
    --model MODEL     Ollama model to use (default: llama3)
    --top K           Chapters to retrieve as context (default: 5)
    --verbose         Show retrieved chapters before answering
    --no-llm          Show only retrieved chapters (no LLM needed)
    --temperature T   LLM temperature 0.0–1.0 (default: 0.3)
    --max-tokens N    Max response length (default: 1500)

Prerequisites:
    1. pip3 install -r scripts/requirements.txt
    2. python3 scripts/generate_embeddings.py   (one-time setup)
    3. Install Ollama: https://ollama.ai
    4. Pull a model: ollama pull llama3

Examples:
    python3 scripts/bible_qa.py "What does the Bible say about the mark of the beast?"
    python3 scripts/bible_qa.py "Explain Daniel's 70 weeks prophecy" --model mistral --verbose
    python3 scripts/bible_qa.py "How are covenants related?" --no-llm --top 10
    python3 scripts/bible_qa.py "Who is Gog and Magog?" --model phi3
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("ERROR: numpy not installed. Run: pip3 install numpy", file=sys.stderr)
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False
    print("ERROR: sentence-transformers not installed. Run: pip3 install sentence-transformers", file=sys.stderr)
    sys.exit(1)

# ─── Paths ────────────────────────────────────────────────────────────────────

VAULT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_FILE = VAULT_ROOT / "embeddings" / "embeddings.npy"
INDEX_FILE = VAULT_ROOT / "embeddings" / "index.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a biblical scholar and theologian with deep knowledge of:
- All 66 books of the Bible (KJV)
- Biblical typology and how the Old Testament prefigures the New
- The 7 major biblical covenants and their theological significance
- Eschatology and prophetic interpretation
- Hebrew and Greek word studies
- The principle of Scripture interpreting Scripture

When answering questions:
1. Ground every answer in the specific Bible passages provided as context
2. Quote the KJV text directly when relevant
3. Explain connections between Old Testament types and New Testament fulfillments
4. Note when multiple interpretive positions exist and explain each fairly
5. Connect answers to the overall narrative arc of Scripture (creation → fall → redemption → consummation)
6. Be specific about chapter and verse references
7. Distinguish between what Scripture clearly states and what is inference or interpretation

The chapters provided as context are from a comprehensive Bible study vault with 1,188 chapter files,
each following a 9-part structure including cross-references, typological connections, and keyword analysis.

Format your response with clear sections and Scripture citations. Be thorough but focused."""


# ─── Retrieval ────────────────────────────────────────────────────────────────

def load_embeddings() -> tuple:
    """Load embeddings and index. Returns (embeddings, index, model) or exits with error."""
    if not EMBEDDINGS_FILE.exists():
        print("ERROR: Embeddings not found.", file=sys.stderr)
        print("Run first: python3 scripts/generate_embeddings.py", file=sys.stderr)
        sys.exit(1)

    print("[+] Loading embeddings...", end=" ", flush=True)
    embeddings = np.load(str(EMBEDDINGS_FILE))
    with open(INDEX_FILE) as f:
        index = json.load(f)
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print(f"OK ({len(index)} chapters)")
    return embeddings, index, model


def retrieve_chapters(query: str, embeddings, index: list, model, top_k: int) -> list[dict]:
    """Find top-K chapters most semantically similar to the query."""
    query_emb = model.encode([query], normalize_embeddings=True)
    scores = (embeddings @ query_emb.T).flatten()
    top_indices = scores.argsort()[::-1][:top_k]

    results = []
    for rank, idx in enumerate(top_indices):
        file_path = Path(index[idx])
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            # Try relative path from vault root
            rel_path = VAULT_ROOT / index[idx]
            try:
                content = rel_path.read_text(encoding="utf-8", errors="ignore")
            except FileNotFoundError:
                content = f"[File not found: {index[idx]}]"

        results.append({
            "rank": rank + 1,
            "file": file_path.stem,
            "path": index[idx],
            "score": float(scores[idx]),
            "content": content,
        })

    return results


def extract_key_content(chapter_content: str, max_chars: int = 2000) -> str:
    """
    Extract the most relevant sections from a chapter file for LLM context.
    Prioritizes: Summary, Cross-References, Prophetic/Typological, Key Terms.
    """
    lines = chapter_content.split("\n")
    sections = {
        "summary": [],
        "cross_references": [],
        "prophetic": [],
        "key_terms": [],
        "symbolic": [],
    }

    current_section = None
    section_markers = {
        "## CHAPTER SUMMARY": "summary",
        "## CROSS-REFERENCES": "cross_references",
        "## PROPHETIC": "prophetic",
        "## KEY TERMS": "key_terms",
        "## SYMBOLIC": "symbolic",
        "## COMMONLY MISQUOTED": None,
        "## KEYWORD INDEX": None,
        "## THE ACTUAL VERSES": None,
        "## CHAPTER METADATA": None,
    }

    for line in lines:
        line_upper = line.upper()
        # Check for section start
        for marker, section_name in section_markers.items():
            if marker in line_upper:
                current_section = section_name
                break

        if current_section and sections.get(current_section) is not None:
            sections[current_section].append(line)

    # Build condensed context
    context_parts = []
    priority_sections = ["summary", "cross_references", "prophetic", "key_terms", "symbolic"]

    for sec in priority_sections:
        content = "\n".join(sections[sec]).strip()
        if content:
            context_parts.append(content)

    full_context = "\n\n".join(context_parts)

    # Truncate if too long
    if len(full_context) > max_chars:
        full_context = full_context[:max_chars] + "\n...[truncated]"

    return full_context or chapter_content[:max_chars]


def format_context_for_llm(chapters: list[dict], max_chars_per_chapter: int = 2000) -> str:
    """Format retrieved chapters as context for the LLM."""
    context_parts = []

    for ch in chapters:
        ch_name = ch["file"].replace("_REBUILT", "").replace("_", " ")
        key_content = extract_key_content(ch["content"], max_chars=max_chars_per_chapter)
        context_parts.append(
            f"=== {ch_name} (similarity: {ch['score']*100:.0f}%) ===\n{key_content}"
        )

    return "\n\n".join(context_parts)


# ─── Ollama Integration ────────────────────────────────────────────────────────

def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def list_available_models() -> list[str]:
    """List models available in Ollama."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def ask_ollama(
    question: str,
    context: str,
    model: str = "llama3",
    temperature: float = 0.3,
    max_tokens: int = 1500,
    stream: bool = True,
) -> str:
    """Send question + context to Ollama and stream the response."""
    prompt = f"""Based on the following Bible chapter excerpts from my Bible study vault, please answer this question:

QUESTION: {question}

CONTEXT FROM RELEVANT BIBLE CHAPTERS:
{context}

Please provide a thorough, Scripture-grounded answer with specific verse references."""

    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        full_response = ""
        with urllib.request.urlopen(req, timeout=180) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    token = chunk.get("response", "")
                    if token:
                        print(token, end="", flush=True)
                        full_response += token
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

        print()  # Final newline
        return full_response

    except urllib.error.URLError:
        print("\nERROR: Cannot connect to Ollama.", file=sys.stderr)
        print("Make sure Ollama is running: ollama serve", file=sys.stderr)
        print("Or use --no-llm to see only retrieved chapters.", file=sys.stderr)
        return ""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Conversational Bible Q&A using local embeddings and LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("question", nargs="+", help="Your question (wrap in quotes)")
    parser.add_argument("--model", default="llama3", help="Ollama model (default: llama3)")
    parser.add_argument("--top", type=int, default=5, help="Chapters to retrieve (default: 5)")
    parser.add_argument("--verbose", action="store_true", help="Show retrieved chapters")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM; show retrieved chapters only")
    parser.add_argument("--temperature", type=float, default=0.3, help="LLM temperature (default: 0.3)")
    parser.add_argument("--max-tokens", type=int, default=1500, help="Max response length")
    args = parser.parse_args()

    question = " ".join(args.question)

    print("\n" + "─" * 60)
    print(f"Question: {question}")
    print("─" * 60 + "\n")

    # Load embeddings
    embeddings, index, model = load_embeddings()

    # Retrieve relevant chapters
    print(f"[+] Searching {len(index)} chapters...", end=" ", flush=True)
    chapters = retrieve_chapters(question, embeddings, index, model, top_k=args.top)
    print(f"Found top {len(chapters)} matches")

    # Show retrieved chapters
    print(f"\n{'─'*60}")
    print("RETRIEVED CHAPTERS (by semantic similarity):")
    print("─" * 60)
    for ch in chapters:
        ch_name = ch["file"].replace("_REBUILT", "").replace("_", " ")
        print(f"  {ch['rank']}. {ch_name} — {ch['score']*100:.0f}% match")

    if args.verbose:
        print(f"\n{'─'*60}")
        print("CHAPTER CONTENT EXCERPTS:")
        print("─" * 60)
        for ch in chapters:
            ch_name = ch["file"].replace("_REBUILT", "").replace("_", " ")
            key_content = extract_key_content(ch["content"], max_chars=500)
            print(f"\n[{ch['rank']}] {ch_name}:")
            print(key_content[:500])
            print("---")

    if args.no_llm:
        print("\n[--no-llm mode] Skipping LLM response.")
        print("Chapters above are the most relevant for your question.")
        return

    # Check Ollama
    print(f"\n{'─'*60}")
    if not check_ollama():
        print("ERROR: Ollama is not running.", file=sys.stderr)
        print("Start Ollama: ollama serve", file=sys.stderr)
        print("Or use --no-llm to see only retrieved chapters.", file=sys.stderr)
        sys.exit(1)

    available_models = list_available_models()
    if available_models:
        if args.model not in available_models and not any(args.model in m for m in available_models):
            print(f"WARNING: Model '{args.model}' not found in Ollama.")
            print(f"Available models: {', '.join(available_models)}")
            if available_models:
                args.model = available_models[0]
                print(f"Using: {args.model}")

    # Build context and ask LLM
    context = format_context_for_llm(chapters, max_chars_per_chapter=1800)

    print(f"ANSWER (using {args.model}):")
    print("─" * 60)

    ask_ollama(
        question=question,
        context=context,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    print("\n" + "─" * 60)
    print("Scripture references retrieved from:")
    for ch in chapters:
        ch_name = ch["file"].replace("_REBUILT", "").replace("_", " ")
        print(f"  • {ch_name}")
    print("─" * 60)


if __name__ == "__main__":
    main()
