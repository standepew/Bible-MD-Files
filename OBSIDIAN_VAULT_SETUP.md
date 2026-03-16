# Obsidian Vault Setup Guide
*Complete Configuration for the Bible-MD-Files Knowledge System*

---

> **Goal:** Configure Obsidian so that the 1,200+ files in this vault become a living, interconnected knowledge graph — with dynamic queries, visual prophecy maps, live news integration, and conversational AI search.

---

## Step 1: Open the Vault

1. Download [Obsidian](https://obsidian.md) (free)
2. Open Obsidian → **Open folder as vault**
3. Navigate to and select the `Bible-MD-Files` directory
4. Wait for Obsidian to index all 1,200+ files (takes 30–90 seconds first time)

---

## Step 2: Required Plugin Setup

Open **Settings → Community Plugins → Browse** and install:

### Core Required Plugins

| Plugin | Why It's Needed | Settings to Enable |
|--------|----------------|-------------------|
| **Dataview** | Powers all dynamic queries in [[templates/DATAVIEW_QUERIES]] | Enable JavaScript Queries + Inline Queries |
| **Templater** | For creating new notes with the 9-part structure | Template folder = `templates/` |
| **Excalidraw** | For the visual exegesis canvases in `templates/` | Enable embed support |
| **Calendar** | For tracking daily Bible reading and news log | Link to daily notes folder |

### Strongly Recommended Plugins

| Plugin | Purpose |
|--------|---------|
| **Breadcrumbs** | Visual hierarchy showing book → chapter relationships |
| **Graph Analysis** | Advanced graph metrics (finds clusters, bridges, hubs) |
| **Strange New Worlds** | Shows all references to a passage inline while reading |
| **Tag Wrangler** | Manages the 15,856 tags in the vault |
| **Kanban** | Tracks study progress and content gap completion |
| **Commander** | Adds toolbar buttons for common vault operations |

### For Live News Integration

| Plugin | Purpose |
|--------|---------|
| **Tasks** | Tracks prophecy watch items and study tasks |
| **Periodic Notes** | Creates daily/weekly prophetic news journals |
| **RSS Reader** (optional) | Pulls news feeds directly into Obsidian |

---

## Step 3: Graph View Configuration

The Graph View is where this vault truly shines. Configure it to reveal biblical connections:

### Global Graph Settings (Settings → Graph View)
- **Node size:** Linked (larger nodes = more connections)
- **Link thickness:** On
- **Text fade threshold:** 50
- **Show orphans:** Off (reduces clutter)

### Recommended Color Groups
Open the Graph View → Click the settings gear → Add color groups:

```
Group 1: Prophecy files
  Filter: file contains "PROPHECY" OR file contains "REVELATION"
  Color: #FF4444 (red — prophetic fire)

Group 2: Covenant files
  Filter: file contains "COVENANT" OR tag:#covenant
  Color: #4444FF (blue — divine covenant)

Group 3: Hub Chapters (Tier 1)
  Filter: file:ROMANS_08 OR file:JAMES_01 OR file:JOHN_10 OR file:ACTS_02
  Color: #FFD700 (gold — highest connectivity)

Group 4: Old Testament
  Filter: path includes "/01. Genesis/" OR path includes "/02. Exodus/"
  Color: #8B4513 (brown — the root)

Group 5: New Testament
  Filter: path includes "/40. Matthew/" OR path includes "/45. Romans/"
  Color: #228B22 (green — the fruit)

Group 6: News/Current Events
  Filter: file:NEWS_PROPHECY_MAP
  Color: #FF8C00 (orange — current events)
```

### Recommended Graph Filters
- **Depth:** 2–3 (shows connections of connections — reveals clusters)
- **Hide:**
  - `tags/` — prevents tag explosion
  - Files with < 3 links (reduces noise, shows only connected chapters)

---

## Step 4: The Canvas Maps

Three Obsidian Canvas files are available for visual study:

### Using NINE_PART_ROADMAP.excalidraw
1. Open `templates/NINE_PART_ROADMAP.excalidraw`
2. Drag any chapter file from the file explorer into the central node
3. The 9-part structure automatically maps to the 9 panels
4. Use it for visual sermon/teaching preparation

### Using CROSS_REFERENCE_WEB.excalidraw
1. Open `templates/CROSS_REFERENCE_WEB.excalidraw`
2. Place a hub chapter (from [[HUB_CHAPTERS_INDEX]]) in the center
3. Drag related chapters into the spoke positions
4. Creates a visual Scripture-Interprets-Scripture map

### Creating a Prophecy Timeline Canvas (Manual)
1. In Obsidian: **New Canvas** → save as `PROPHECY_TIMELINE.canvas`
2. Add nodes for each major prophecy category from [[PROPHECY_FULFILLMENT_INDEX]]
3. Use arrows to show fulfillment relationships
4. Color-code by status: green (fulfilled), yellow (partial), red (awaiting)

---

## Step 5: Quick Switcher & Search

### Optimize Search
- Settings → Core Plugins → Search → Enable "Search in all files"
- Settings → Quick Switcher → Show existing only: OFF (allows creating new notes)

### Useful Search Queries
```
# Find all chapters with a specific tag
tag:#resurrection

# Find all chapters in a book
path:"40. Matthew"

# Find prophecy matches for a topic
"gog" OR "magog" OR "russia" file:("BUILT")

# Find chapters with specific YAML field
[covenant: C6]

# Full text search for a verse reference
"Zech 12:10"
```

---

## Step 6: Linking the News Mapper

The `scripts/news_prophecy_mapper.py` script generates `NEWS_PROPHECY_MAP.md` automatically. To integrate it with Obsidian:

### One-Time Setup
```bash
# Install dependencies
pip3 install -r scripts/requirements.txt

# Run the mapper once to create the file
python3 scripts/news_prophecy_mapper.py
```

### Automated Daily Updates (Linux/Mac)
Add to crontab to run every morning:
```bash
crontab -e
# Add this line (runs at 7:00 AM daily):
0 7 * * * cd /path/to/Bible-MD-Files && python3 scripts/news_prophecy_mapper.py >> logs/news_mapper.log 2>&1
```

### Viewing in Obsidian
- Open `NEWS_PROPHECY_MAP.md` — it auto-refreshes in Obsidian when the file changes
- Pin it to a sidebar or create a shortcut on your `_VAULT_HOME.md` dashboard
- The Dataview queries in [[templates/DATAVIEW_QUERIES]] (Q16–Q18) pull from this file

---

## Step 7: Bible QA Setup (Conversational Search)

The `scripts/bible_qa.py` script enables conversational Q&A over the entire vault using a local LLM.

### Prerequisites
1. **Install Ollama:** [ollama.ai](https://ollama.ai)
2. **Pull a model:**
   ```bash
   ollama pull llama3        # Recommended: 8B, ~5GB RAM
   ollama pull mistral       # Alternative: fast, less RAM
   ollama pull phi3          # Lightweight option
   ```
3. **Generate embeddings** (one-time, ~5 minutes on GPU):
   ```bash
   python3 scripts/generate_embeddings.py
   ```

### Using Bible QA
```bash
# Ask a question
python3 scripts/bible_qa.py "What does Scripture say about the mark of the beast?"

# Get top chapter matches with explanations
python3 scripts/bible_qa.py "Why did Jesus have to die?" --verbose

# Use a specific model
python3 scripts/bible_qa.py "Explain Daniel's 70 weeks" --model mistral
```

The script:
1. Embeds your question with the same model as the chapters
2. Finds the top-K most semantically similar chapters
3. Feeds them as context to your local LLM
4. Returns a Scripture-grounded answer with citations

---

## Step 8: Workspace Layout

For optimal study workflow, configure these Obsidian workspaces:

### Workspace: "Deep Study"
- Left panel: File Explorer (sorted by folder)
- Center: Active chapter file
- Right panel: Backlinks (all chapters linking to current)
- Bottom panel: Outgoing links
- Floating panel: Graph View (filtered to current file, depth 2)

### Workspace: "Prophecy Watch"
- Left panel: PROPHECY_FULFILLMENT_INDEX
- Center: NEWS_PROPHECY_MAP (auto-refreshing)
- Right panel: A Dataview query (Q16 — latest news mappings)
- Bottom: Calendar + daily note

### Workspace: "Structural Study"
- Left: COVENANT_INDEX or CHIASM_INDEX
- Center: Chapter file being studied
- Right: TYPOLOGY_REGISTER (filtered to relevant entries)
- Graph View: Open with depth 3

Save each workspace via Settings → Workspaces.

---

## Step 9: Custom CSS (Optional)

Add to **Settings → Appearance → CSS Snippets** → Create `bible-vault.css`:

```css
/* Highlight prophecy wikilinks in red */
.internal-link[data-href*="PROPHECY"] {
    color: #FF4444;
    font-weight: bold;
}

/* Highlight covenant wikilinks in blue */
.internal-link[data-href*="COVENANT"] {
    color: #4444FF;
    font-weight: bold;
}

/* Style the 9-part headings */
.markdown-rendered h2 {
    border-left: 4px solid #DAA520;
    padding-left: 8px;
}

/* Callout styling for prophecy status */
.callout[data-callout="fulfilled"] {
    background: rgba(0, 200, 0, 0.1);
    border-color: #00C800;
}

.callout[data-callout="awaiting"] {
    background: rgba(255, 140, 0, 0.1);
    border-color: #FF8C00;
}
```

---

## Vault Performance Tips

| Issue | Solution |
|-------|----------|
| Indexing slow | Exclude `embeddings/` folder: Settings → Files & Links → Excluded files |
| Graph View laggy | Reduce depth to 1; filter to specific tags |
| Dataview queries slow | Add folder filters to FROM clause; increase refresh interval |
| Too many tags | Use Tag Wrangler to merge similar tags |
| Search misses | Enable "Search in all files" in settings |

---

## See Also
- [[_VAULT_HOME]] — Start here for daily use
- [[templates/DATAVIEW_QUERIES]] — All dynamic queries
- [[PROPHECY_FULFILLMENT_INDEX]] — The prophecy tracker
- [[NEWS_PROPHECY_MAP]] — Live current events mapping
- `scripts/news_prophecy_mapper.py` — Auto-generates news map
- `scripts/bible_qa.py` — Conversational Bible search
