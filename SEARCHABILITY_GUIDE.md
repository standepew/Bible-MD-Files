---
tags: [searchability, search-guide, how-to, Obsidian, vault-reference, MOC, keyword-search, global-search]
aliases: [Search Guide, How to Search, Vault Search]
related: "[[BIBLE_MAP_OF_CONTENT]], [[KEYWORD_LOOKUP_TABLE]], [[_VAULT_HOME]], [[TAG_THEME_ANALYSIS]]"
type: guide
---

# SEARCHABILITY GUIDE

> Because every chapter in this vault is a structured markdown file, you can search across the entire Bible — all 1,188 chapters, all 66 books — instantly.

---

## GLOBAL SEARCH (Find Any Word Across the Entire Bible)

**How:** `Ctrl+Shift+F` in Obsidian (or `Cmd+Shift+F` on Mac)

Type any word and Obsidian instantly returns every chapter file containing that word, with context.

### Example Searches

| Search Term | What You Find |
|---|---|
| `grace` | Every verse and cross-reference mentioning grace across all 66 books |
| `covenant of salt` | All occurrences of the salt-covenant concept |
| `firstborn` | Every firstborn reference — from Genesis to Revelation |
| `seventy weeks` | Daniel's prophecy and every cross-reference to it |
| `remnant` | Every use of the remnant concept — Isaiah, Jeremiah, Romans, Revelation |
| `day of the LORD` | All prophetic occurrences across OT and NT |
| `blood crieth` | From Abel (Genesis 4) through Hebrews 12 |
| `prince of peace` | Isaiah 9, Micah 5, and their NT fulfillments |

---

## MAP OF CONTENT (Clickable Navigation)

See [[BIBLE_MAP_OF_CONTENT]] — a single file with:
- Clickable links to every book (66 books)
- Every chapter accessible by clicking through the book folder
- All major index files linked in one place
- Vault statistics at a glance

---

## KEYWORD INDEX SEARCH

Every chapter file contains a `## KEYWORD INDEX` section with backtick-formatted keywords optimized for search and AI matching.

**How to use:** In Obsidian global search, search for a keyword with backticks, e.g.:
- `` `faith` `` — finds all chapters where "faith" is a keyword entry
- `` `covenant` `` — covenant-tagged chapters
- `` `remnant` `` — remnant-tagged chapters

The [[KEYWORD_LOOKUP_TABLE]] provides a pre-built reverse index: topic → chapters.

---

## TAG SEARCH (#hashtag Navigation)

Every chapter has a `**Tags:**` line in `## CHAPTER METADATA` with `#hashtag` entries.

**In Obsidian:** Click any `#tag` in a file to see all files with that tag. Or use global search for `#tag-name`.

Example tags:
- `#messianic-prophecy` — All Messianic chapters
- `#covenant` — Covenant chapters
- `#faith` — Faith-themed chapters
- `#judgment` — Judgment chapters
- `#resurrection` — Resurrection passages

See [[TAG_THEME_ANALYSIS]] for the complete list of all 15,856 unique tags.

---

## CROSS-REFERENCE SEARCH

The [[MASTER_CROSS_REFERENCE_INDEX]] maps all 1,107 chapters that are cross-referenced within the vault. The most-referenced chapter is **Romans 8** (135 references).

To trace a concept through Scripture:
1. Open [[MASTER_CROSS_REFERENCE_INDEX]] → find your chapter
2. See every other chapter that references it
3. Follow the chain — this is "Scripture interpreting Scripture"

---

## SECTION-SPECIFIC SEARCH

Every chapter has 9 standardized sections. Search within a section type:

| Search for | To find |
|---|---|
| `"COMMONLY MISQUOTED"` | All chapters with misquotation corrections |
| `"SYMBOLIC THREADS"` | All symbolic thread entries |
| `"PROPHETIC/TYPOLOGICAL"` | All typology entries |
| `"KEY TERMS WITH CONTEXTUAL"` | All Hebrew/Greek word studies |
| `"Relevance to Current Events"` | All current-events connection entries |

---

## OBSIDIAN GRAPH VIEW

Every chapter file, index file, and document is linked via `[[wikilinks]]`. The **Graph View** (`Ctrl+G`) shows the full connection network of the vault:

- **Hub chapters** (most connected) appear as large nodes
- **Books** cluster together
- **Index files** connect across multiple books
- The **research documents** ([[FINAL_Distribution_Document]], [[The Complete Biblical Research Collection 2026]]) appear connected to the prophecy and covenant indexes

**Graph Tips:**
- Filter by tag in Graph View to see only tagged chapters
- Increase depth to see second-degree connections
- Use "Existing links only" to see the strongest connections

---

## DATAVIEW QUERIES (Advanced)

If you have the Obsidian Dataview plugin installed, use the queries in [[templates/DATAVIEW_QUERIES]] to:
- List all chapters by tag
- Find all chapters with specific key themes
- Build dynamic reading lists

---

## SEMANTIC SEARCH (AI-Powered)

For concept-based search (not just keyword matching), use the embeddings system:

```bash
# One-time setup (~5 minutes)
python3 scripts/generate_embeddings.py

# Then search by concept
python3 scripts/semantic_search.py "God's faithfulness despite human failure"
python3 scripts/semantic_search.py "suffering that produces growth"
python3 scripts/semantic_search.py "covenant renewal after apostasy"
```

This finds chapters that are *conceptually* related even if they don't share the exact same words.

---

*The vault is designed so that Scripture interprets Scripture — and search is the engine that makes that possible at scale.*
