# Bible-MD-Files — Vault Home
*The Operational Hub for Bible-MD-Files*

> *"Your word is a lamp to my feet and a light to my path."* — Psalm 119:105

---

## Quick Launch

| Resource | Purpose | Status |
|----------|---------|--------|
| [[PROPHECY_FULFILLMENT_INDEX]] | 60 prophecies tracked with live event monitoring | 🔴 Active watch |
| [[NEWS_PROPHECY_MAP]] | Today's headlines mapped to Scripture | 🔄 Auto-updates |
| [[COVENANT_INDEX]] | The 7 covenants — the theological spine | ✅ Complete |
| [[TYPOLOGY_REGISTER]] | 40 type→antitype pairs | ✅ Complete |
| [[PEOPLE_INDEX]] | Major biblical figures and their typological roles | ✅ Complete |
| [[CHIASM_INDEX]] | Literary architecture — where the Bible shows its emphasis | ✅ Complete |
| [[SYMBOL_DICTIONARY]] | 45 biblical symbols with all occurrences | ✅ Complete |
| [[HUB_CHAPTERS_INDEX]] | Most-connected chapters (Scripture's own emphasis) | ✅ Complete |
| [[MASTER_CROSS_REFERENCE_INDEX]] | 1,183 chapters cross-referenced | ✅ Complete |

---

## The Bible in One View

```
CREATION ──────────────────────────────────────────────── NEW CREATION
Gen 1-2              ↓                                    Rev 21-22
                  THE FALL
                  Gen 3
                     │
    ┌────────────────┼────────────────┐
    │                │                │
  C3: Noahic      C4: Abrahamic     C2: Grace
  (Gen 9)         (Gen 12,15,17)    (Gen 3:15)
    │                │                │
    └────────────────┼────────────────┘
                  C5: Mosaic
                  (Exo 19-24)
                     │
                  C6: Davidic
                  (2 Sam 7)
                     │
              ┌──────┴──────┐
           THE CROSS    THE RESURRECTION
           (Luke 23)    (Luke 24)
              └──────┬──────┘
                  C7: New Covenant
                  (Jer 31; Heb 8-10)
                     │
              ┌──────┴──────┐
           CHURCH AGE    ← WE ARE HERE →
           (Acts-Jude)
              └──────┬──────┘
                  TRIBULATION
                  (Rev 6-19)
                     │
                MILLENNIUM
                (Rev 20)
                     │
              NEW CREATION
              (Rev 21-22)
```

---

## Prophecy Watch Dashboard

> Run `python3 scripts/news_prophecy_mapper.py` to refresh [[NEWS_PROPHECY_MAP]]

| Category | Prophecy | Watch Level |
|----------|----------|------------|
| Gog-Magog Coalition (Russia-Iran-Turkey) | [[PROPHECY_FULFILLMENT_INDEX#P051\|P051]] | 🔴 Active |
| Jerusalem Sanctuary / Altar Activity (miqdash) | [[PROPHECY_FULFILLMENT_INDEX#P048\|P048]] | 🟡 Stage-Setting |
| Global Digital Currency / Mark Infrastructure | [[PROPHECY_FULFILLMENT_INDEX#P045\|P045]] | 🟡 Infrastructure |
| Middle East Peace Framework | [[PROPHECY_FULFILLMENT_INDEX#P043\|P043]] | 🟡 Precursor |
| Israel's Spiritual Awakening | [[PROPHECY_FULFILLMENT_INDEX#P042\|P042]] | ⏳ Future |

---

## Study Pathways

### Pathway 1: Understand the Gospel Story
1. [[COVENANT_INDEX]] — Read the 7 covenants in order
2. [[TYPOLOGY_REGISTER#T15---the-passover--the-crucifixion|T15 — The Passover]] + [[EXO_12_REBUILT|Exo 12]] + [[JOHN_19_REBUILT|John 19]]
3. [[TYPOLOGY_REGISTER#T20---day-of-atonement--christs-final-sacrifice|T20 — Day of Atonement]] + [[LEV_16_REBUILT|Lev 16]] + [[HEBREWS_09_REBUILT|Heb 9]]
4. [[PEOPLE_INDEX#joseph|Joseph]] → [[PEOPLE_INDEX#moses|Moses]] → [[PEOPLE_INDEX#david|David]] → Christ

### Pathway 2: Understand the End Times
1. [[DANIEL_09_REBUILT|Daniel 9]] — The 70 Weeks: the master prophetic calendar
2. [[MATTHEW_24_REBUILT|Matthew 24]] — Christ's own overview (Olivet Discourse)
3. [[PROPHECY_FULFILLMENT_INDEX#category-3-tribulation-period-prophecies-p043p052|Tribulation Prophecies]] — P043–P052
4. [[REVELATION_12_REBUILT|Revelation 12]] — The cosmic backstory (chiastic center)
5. [[PROPHETIC_SERIES_MAP]] — Extended prophetic commentary

### Pathway 3: Scripture Interprets Scripture
1. [[HUB_CHAPTERS_INDEX]] — Start with Tier 1 hub chapters
2. Run Dataview Q09: "Everything linking to ROMANS_08_REBUILT"
3. Use Graph View at depth 2 on any Tier 1 hub chapter
4. See [[templates/DATAVIEW_QUERIES]] for all query options

### Pathway 4: Map Current Events to Scripture
1. Run `python3 scripts/news_prophecy_mapper.py`
2. Open [[NEWS_PROPHECY_MAP]]
3. Cross-reference with [[PROPHECY_FULFILLMENT_INDEX]] for context
4. Check [[RESEARCH_BIBLE_CONNECTION_MAP]] for theological framework

---

## Vault Statistics

| Metric | Count |
|--------|-------|
| Total chapter files | 1,188 |
| Total index/reference files | ~20 |
| Unique tags | 15,856 |
| Tier 1 Hub Chapters | 8 |
| Most-referenced chapter | Romans 8 (135x) |
| Prophecies tracked | 60 |
| Fulfilled prophecies | 38 (63%) |
| Prophecies awaiting fulfillment | 18 (30%) |
| Major type→antitype pairs | 40 |
| Biblical covenants indexed | 7 |
| Major figures profiled | 30+ |

---

## System Commands

```bash
# Generate semantic embeddings (one-time setup, ~5 min)
python3 scripts/generate_embeddings.py

# Semantic search: find chapters by concept
python3 scripts/semantic_search.py "sacrificial love that costs the giver"

# Update news-to-prophecy map (run daily)
python3 scripts/news_prophecy_mapper.py

# Ask the vault a question (requires Ollama + embeddings)
python3 scripts/bible_qa.py "What does Scripture say about the spirit of antichrist?"

# Regenerate hub chapters index
python3 scripts/generate_hub_chapters.py

# Validate chronology YAML
python3 scripts/generate_yaml_chronology.py --timeline
```

---

## The Nine-Part Chapter Structure

Every one of the 1,188 chapter files is structured identically:

```
1. CHAPTER METADATA         — Book, chapter, tags, key themes
2. CHAPTER SUMMARY          — 2–4 paragraph narrative overview
3. CROSS-REFERENCES         — Scripture interpreting Scripture
4. KEYWORD INDEX            — AI-searchable tags with current-event relevance
5. KEY TERMS                — Hebrew/Greek word studies
6. THE ACTUAL VERSES (KJV)  — Full chapter text
7. PROPHETIC/TYPOLOGICAL    — Types, shadows, fulfillments
8. MISQUOTED PASSAGES       — Context and correction
9. SYMBOLIC THREADS         — Patterns and first-mention principles
```

---

## Index of All Index Files

| File | Description |
|------|-------------|
| [[_VAULT_HOME]] | This file — the starting point |
| [[COVENANT_INDEX]] | The 7 biblical covenants |
| [[TYPOLOGY_REGISTER]] | 40 type→antitype pairs |
| [[PROPHECY_FULFILLMENT_INDEX]] | 60 prophecies with status tracking |
| [[PEOPLE_INDEX]] | 30+ major biblical figures |
| [[CHIASM_INDEX]] | 13 chiastic structures |
| [[SYMBOL_DICTIONARY]] | 45 biblical symbols |
| [[HUB_CHAPTERS_INDEX]] | Most-connected chapters by tier |
| [[MASTER_CROSS_REFERENCE_INDEX]] | Complete chapter cross-reference network |
| [[TAG_THEME_ANALYSIS]] | 15,856 tag frequency analysis |
| [[KEYWORD_LOOKUP_TABLE]] | Topic → chapter lookup for current events |
| [[CONTENT_GAP_REPORT]] | Quality control — chapters needing work |
| [[NEWS_PROPHECY_MAP]] | Auto-generated current events → Scripture |
| [[OBSIDIAN_VAULT_SETUP]] | Complete Obsidian configuration guide |
| [[templates/DATAVIEW_QUERIES]] | 26 dynamic Dataview queries |

