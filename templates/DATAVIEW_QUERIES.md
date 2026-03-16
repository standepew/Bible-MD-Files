# Dataview Query Library
*Pre-Built Obsidian Dataview Queries for the Bible Vault*

---

> **Requirements**
> - Obsidian with the [Dataview plugin](https://github.com/blacksmithgu/obsidian-dataview) installed and enabled
> - Plugin Settings → Dataview → Enable JavaScript Queries: ON
> - Plugin Settings → Dataview → Enable Inline Queries: ON
>
> **How to Use**
> Copy any query block below into any Obsidian note. It will render as a live, dynamic table or list. Queries auto-update when linked files change.
>
> **YAML Fields Used in This Vault**
> The following frontmatter fields are used across chapter files:
> - `chronology.chapter_type` — genealogy / narrative / prophecy / epistle
> - `chronology.calendar` — Anno Mundi year
> - `chronology.anchor_events[]` — list of dateable events
> - `prophecy_ids` — list of prophecy IDs from PROPHECY_FULFILLMENT_INDEX
> - `covenant` — which covenant the chapter primarily develops (C1–C7)
> - `typology` — type or antitype references

---

## Section 1: Navigation & Overview Queries

### Q01 — All Chapter Files (Full Vault Map)
*Shows every chapter in the vault sorted by filename*
```dataview
TABLE file.folder AS "Book", file.name AS "Chapter"
FROM ""
WHERE contains(file.name, "REBUILT")
SORT file.name ASC
```

### Q02 — Hub Chapter Navigator
*Shows all Tier 1 and Tier 2 hub chapters (most connected in the vault)*
```dataview
TABLE file.name AS "Chapter", file.inlinks.length AS "Inbound Links"
FROM ""
WHERE contains(file.name, "REBUILT")
SORT file.inlinks.length DESC
LIMIT 25
```

### Q03 — Recently Modified Chapters
*Shows the 20 most recently edited chapter files — useful for tracking your study progress*
```dataview
TABLE file.name AS "Chapter", file.mtime AS "Last Modified"
FROM ""
WHERE contains(file.name, "REBUILT")
SORT file.mtime DESC
LIMIT 20
```

### Q04 — Orphaned Notes (No Incoming Links)
*Finds notes with no inbound wikilinks — these may need to be better connected*
```dataview
LIST
FROM ""
WHERE file.inlinks.length = 0
AND file.name != "_VAULT_HOME"
AND !contains(file.name, "REBUILT")
SORT file.name ASC
```

---

## Section 2: Chronology Queries

### Q05 — Genealogy Chapters (Chapters with Anno Mundi Data)
*Lists all chapters with chronological/genealogical frontmatter*
```dataview
TABLE chronology.chapter_type AS "Type", chronology.calendar AS "Calendar"
FROM ""
WHERE chronology.chapter_type = "genealogy"
SORT file.name ASC
```

### Q06 — Timeline Events (All Dateable Events)
*Extracts all anchor events with their Anno Mundi dates from frontmatter*
```dataview
TABLE chronology.anchor_events AS "Events"
FROM ""
WHERE chronology.anchor_events
SORT file.name ASC
```

### Q07 — Chapters by Chapter Type
*Groups chapters by their content type (genealogy, narrative, prophecy, epistle)*
```dataview
TABLE file.name AS "Chapter"
FROM ""
WHERE chronology.chapter_type = "prophecy"
SORT file.name ASC
```

---

## Section 3: Cross-Reference & Connectivity Queries

### Q08 — Most Linked-To Files (Custom Cross-Reference Heat Map)
*Shows which vault files are most referenced — confirms hub chapter findings*
```dataview
TABLE file.inlinks.length AS "Times Referenced", file.outlinks.length AS "References Made"
FROM ""
WHERE file.inlinks.length > 50
SORT file.inlinks.length DESC
```

### Q09 — Everything Linking to a Specific Chapter
*Change `ROMANS_08_REBUILT` to any chapter to see all chapters that cross-reference it*
```dataview
LIST
FROM [[ROMANS_08_REBUILT]]
```

### Q10 — Everything a Chapter Links To
*Change the file name to see all outbound cross-references from any chapter*
```dataview
LIST
FROM outgoing([[DANIEL_09_REBUILT]])
```

### Q11 — Mutual References (Chapters That Cross-Reference Each Other)
*Finds chapters that mutually reference each other — strong topical pairs*
```dataviewjs
const files = dv.pages('""').where(p => p.file.name.includes("REBUILT"));
const pairs = [];
for (const f of files) {
    const outLinks = f.file.outlinks.map(l => l.path);
    for (const target of outLinks) {
        const targetFile = dv.page(target);
        if (targetFile) {
            const targetOut = targetFile.file.outlinks.map(l => l.path);
            if (targetOut.includes(f.file.path)) {
                const pair = [f.file.name, targetFile.file.name].sort().join(" ↔ ");
                if (!pairs.includes(pair)) pairs.push(pair);
            }
        }
    }
}
dv.list(pairs.slice(0, 50));
```

---

## Section 4: Prophecy Tracking Queries

### Q12 — Open Prophecies (Awaiting Fulfillment)
*Lists all prophecy entries from PROPHECY_FULFILLMENT_INDEX that are ⏳ AWAITING*
```dataview
TABLE prophecy_category AS "Category", ot_source AS "OT Source", nt_fulfillment AS "Status"
FROM [[PROPHECY_FULFILLMENT_INDEX]]
WHERE prophecy_status = "awaiting"
SORT prophecy_category ASC
```

### Q13 — Chapters with Prophecy IDs Tagged
*Shows all chapter files that have been linked to specific prophecy IDs*
```dataview
TABLE prophecy_ids AS "Prophecy IDs", file.name AS "Chapter"
FROM ""
WHERE prophecy_ids
SORT file.name ASC
```

### Q14 — Chapters by Covenant
*Lists all chapters tagged with a specific covenant — change C6 to any covenant*
```dataview
TABLE file.name AS "Chapter", covenant AS "Covenant"
FROM ""
WHERE covenant = "C6"
SORT file.name ASC
```

### Q15 — Chapters with Typology Tags
*Shows chapters that have been tagged with typological type/antitype references*
```dataview
TABLE typology AS "Type Reference", file.name AS "Chapter"
FROM ""
WHERE typology
SORT file.name ASC
```

---

## Section 5: Current Events / News Queries

### Q16 — Latest News-to-Prophecy Mappings
*Shows the most recent entries from NEWS_PROPHECY_MAP — auto-updated by the mapper script*
```dataview
TABLE news_date AS "Date", prophecy_match AS "Matched Prophecy", news_category AS "Category"
FROM [[NEWS_PROPHECY_MAP]]
WHERE news_date
SORT news_date DESC
LIMIT 20
```

### Q17 — High-Alert Prophecy Categories
*Shows news entries matching highest-priority prophecy watch categories*
```dataview
TABLE news_headline AS "Headline", prophecy_match AS "Prophecy", confidence AS "Match Score"
FROM [[NEWS_PROPHECY_MAP]]
WHERE news_alert_level = "red"
SORT news_date DESC
```

### Q18 — News by Prophetic Category
*Filter news entries by category — change "gog_magog" to any watch category*
```dataview
TABLE news_headline AS "Headline", news_date AS "Date"
FROM [[NEWS_PROPHECY_MAP]]
WHERE news_category = "gog_magog"
SORT news_date DESC
LIMIT 15
```

---

## Section 6: Study Planning Queries

### Q19 — Chapters You Haven't Visited
*Finds chapter files not opened recently — identify unstudied areas*
```dataview
TABLE file.name AS "Chapter", file.mtime AS "Last Modified"
FROM ""
WHERE contains(file.name, "REBUILT")
SORT file.mtime ASC
LIMIT 20
```

### Q20 — Complete Book Study (All Chapters of a Book)
*Change `DANIEL` to any book prefix to see all chapters of that book*
```dataview
TABLE file.name AS "Chapter"
FROM ""
WHERE startswith(file.name, "DANIEL")
SORT file.name ASC
```

### Q21 — Chapters with Content Gaps
*References CONTENT_GAP_REPORT — shows chapters needing completion*
```dataview
TABLE file.name AS "Chapter"
FROM [[CONTENT_GAP_REPORT]]
WHERE gap_type = "missing_section"
SORT file.name ASC
```

---

## Section 7: Thematic Study Queries

### Q22 — All Messianic Prophecy Chapters
*Finds chapters tagged with messianic or christological content*
```dataview
TABLE file.name AS "Chapter", file.inlinks.length AS "References"
FROM ""
WHERE contains(tags, "messianic") OR contains(tags, "christological")
SORT file.inlinks.length DESC
```

### Q23 — Eschatology Cluster
*All chapters heavily tagged with end-times themes*
```dataview
TABLE file.name AS "Chapter"
FROM ""
WHERE contains(tags, "eschatology") OR contains(tags, "end times") OR contains(tags, "tribulation")
SORT file.inlinks.length DESC
LIMIT 30
```

### Q24 — Holy Spirit Chapters
*Chapters with significant pneumatological content*
```dataview
TABLE file.name AS "Chapter"
FROM ""
WHERE contains(tags, "holy spirit") OR contains(tags, "spirit of god") OR contains(tags, "pneumatology")
SORT file.inlinks.length DESC
```

### Q25 — Resurrection and New Life Chapters
*Chapters treating resurrection, new creation, new life themes*
```dataview
TABLE file.name AS "Chapter"
FROM ""
WHERE contains(tags, "resurrection") OR contains(tags, "new creation") OR contains(tags, "eternal life")
SORT file.name ASC
```

---

## Section 8: Inline Query Examples

*These go directly in note text and render inline:*

Count of all chapter files: `= length(filter(dv.pages(""), p => p.file.name.includes("REBUILT")))`

Most referenced chapter: `= sort(filter(dv.pages(""), p => p.file.inlinks.length > 100), p => -p.file.inlinks.length)[0].file.name`

Today's date: `= date(today)`

---

## Section 9: Canvas-Friendly Data Extraction

### Q26 — Export Chapter Data for Canvas Mapping
*Useful for building Obsidian Canvas maps — outputs clean chapter list with metadata*
```dataviewjs
const chapters = dv.pages('""')
    .where(p => p.file.name.includes("REBUILT"))
    .sort(p => p.file.inlinks.length, "desc")
    .limit(30);

const rows = chapters.map(p => [
    p.file.link,
    p.file.inlinks.length,
    p.covenant || "—",
    p.typology || "—"
]);

dv.table(["Chapter", "Link Count", "Covenant", "Typology"], rows);
```

---

## Tips for Optimal Obsidian Performance

1. **Enable Dataview caching** — Settings → Dataview → Refresh Interval: 30s minimum
2. **Index only needed folders** — If queries are slow, limit scope with folder paths in FROM clause
3. **Use `FROM ""` sparingly** — searching the entire vault is slow; use book-specific folders when possible
4. **Combine Dataview with Graph View** — Run a Dataview query to identify a cluster, then use Graph View filters to visualize the connections
5. **Tag Consistency** — The queries in sections 4–5 work best when YAML frontmatter is consistently filled in across chapter files. Use `CONTENT_GAP_REPORT` to track progress.

---

## YAML Frontmatter Schema (for new chapter files)

```yaml
---
book: "Romans"
chapter: 8
testament: "New Testament"
covenant: "C7"
prophecy_ids: []
typology: ""
tags:
  - "#holy-spirit"
  - "#justification"
  - "#no-condemnation"
chronology:
  chapter_type: "epistle"
  calendar: ""
  anchor_events: []
---
```

---

## See Also
- [[OBSIDIAN_VAULT_SETUP]] — Complete setup guide for all Obsidian plugins
- [[_VAULT_HOME]] — The vault dashboard
- [[PROPHECY_FULFILLMENT_INDEX]] — Prophecy data source for queries Q12–Q18
- [[NEWS_PROPHECY_MAP]] — Live news data source for queries Q16–Q18
