# Visual Exegesis Templates

Excalidraw templates for interactive, visual Bible study.
Pre-linked to the Nine-Part Roadmap structure and master cross-reference system.

## How to Use

### In Obsidian (recommended)
1. Install the **Excalidraw** plugin by Zsolt Viczián
2. Open any `.excalidraw` file in this folder — Obsidian will render it as a visual canvas
3. Drag and drop chapter files from your vault onto the template nodes
4. Excalidraw will auto-create links between nodes as you connect them

### In VS Code
1. Install the **Excalidraw** VS Code extension
2. Open any `.excalidraw` file — it renders inline in the editor

### Standalone
1. Go to [excalidraw.com](https://excalidraw.com)
2. Click "Open" → load any `.excalidraw` file from this folder
3. Work locally in the browser (no account required)

---

## Templates Included

### `NINE_PART_ROADMAP.excalidraw`
A nine-panel workspace matching the standardized chapter structure:

```
[1. Metadata]    [2. Summary]     [3. Cross-Refs]
[4. Keywords]    [5. Key Terms]   [6. KJV Text]
[7. Typology]    [8. Symbols]     [9. First Mentions]
                    (Hub Chapter)
                                   [Chronology Sidebar]
```

**Use case:** Load a single chapter and see all its layers simultaneously.
Drag the hub chapter ellipse to the center to visually anchor cross-reference flow.

---

### `CROSS_REFERENCE_WEB.excalidraw`
A radial hub-and-spoke layout for mapping Scripture cross-references:

```
        [OT Prophecy]   [OT Symbol]   [OT Law]
[Psalms]         ← ANCHOR CHAPTER →          [NT Fulfillment]
[Wisdom]     (Hub chapter in center)          [NT Epistle]
        [Gospel Parallel]  [Major Prophecy]  [NT Apocalyptic]
```

**Use case:** Pick any Tier 1–2 hub chapter (from `HUB_CHAPTERS_INDEX.md`) and place it
in the center. Fill the surrounding nodes with the chapters that reference it.
The resulting web reveals the Bible's topography at a glance.

---

## Workflow: "Drag and Drop Exegesis"

1. Open `NINE_PART_ROADMAP.excalidraw` in Obsidian
2. Open your chapter file (e.g., `Romans_08_REBUILT.md`) in a separate pane
3. Drag the file link into the **Cross-References** panel on the template
4. Repeat for connected chapters — Excalidraw draws the connection lines automatically
5. Export as PNG/SVG for teaching or printing

---

## Connecting to the Hub Chapters Index

The templates are designed to work alongside:
- `HUB_CHAPTERS_INDEX.md` — tells you which chapters to put at center
- `MASTER_CROSS_REFERENCE_INDEX.md` — gives you the spoke chapters to add around it
- `scripts/semantic_search.py` — finds conceptually related chapters you might miss
