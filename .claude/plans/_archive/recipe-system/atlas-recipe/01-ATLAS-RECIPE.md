# Atlas Recipe — Full Specification

## Concept

The Atlas Recipe is a four-pass pipeline that transforms an imported manuscript into a complete reference atlas — character profiles, location maps, timelines, theme analysis, plot structure, relationship networks — all assembled as `.codex.yaml` files inside the project's git repo.

Unlike the Analysis Recipe (which produces per-chapter data), the Atlas Recipe **synthesizes** — it reads the entire manuscript, extracts entities, analyzes every chapter in parallel, then cross-references everything into cohesive atlas sections.

The Atlas is also a **Codex project** — meaning it's browsable on ChapterWise.app, renderable through `codex_shell.html`, downloadable as ZIP, and compatible with the Reader Recipe for custom styled output.

## How It's Triggered

### After Import

The agent offers automatically:

> "Your novel is imported — 28 chapters, 87,000 words. Want me to build an Atlas too? Characters, locations, timeline, themes — the full map."

### Independently

- `/atlas` — Build an atlas for the current project
- `/atlas --update` — Update an existing atlas with manuscript changes
- `/import my-novel.pdf --atlas` — Import AND build atlas in one go

### From Existing Project

> "Build an atlas for this project"

The agent scans the project structure, finds the chapters, and starts the pipeline.

## The Four Passes

```
/atlas
    |
    v
[Pass 0: Scan]         — Read manuscript, propose atlas folder structure (FREE, 10 sec)
    |
    v
[Pass 1: Extract]      — Entity extraction: characters, locations, objects (FREE, 30 sec)
    |
    v
[Pass 2: Analyze]      — Per-chapter deep analysis using 32 modules (PAID, parallel)
    |
    v
[Pass 3: Synthesize]   — Cross-reference, build arcs, assemble atlas files (PAID, 5-10 min)
    |
    v
ATLAS COMMITTED TO PROJECT GIT REPO
```

---

## Pass 0: Scan and Structure Proposal

**What the agent does:**
1. Reads the imported manuscript's `index.codex.yaml` to understand chapters, parts, word count
2. Samples a few chapters to detect genre, POV, complexity
3. Proposes an atlas folder structure tailored to the content

**Why it matters:** A 10-chapter novella with 3 characters doesn't need the same atlas structure as a 40-chapter epic fantasy with 15 POV characters, a magic system, and 5 factions. Pass 0 adapts.

**Structure proposal examples:**

Simple literary fiction:
```yaml
atlas/
  index.codex.yaml
  characters.codex.yaml      # All characters in one file
  timeline.codex.yaml        # Chapter-by-chapter timeline
  themes.codex.yaml          # Thematic analysis
  plot-structure.codex.yaml  # Three-act / hero's journey
```

Complex epic fantasy:
```yaml
atlas/
  index.codex.yaml
  characters/
    protagonists.codex.yaml
    antagonists.codex.yaml
    supporting-cast.codex.yaml
    relationship-map.codex.yaml
  world/
    locations.codex.yaml
    factions.codex.yaml
    magic-system.codex.yaml
    artifacts.codex.yaml
  plot/
    three-act-structure.codex.yaml
    timeline.codex.yaml
    story-beats.codex.yaml
    subplots.codex.yaml
  themes/
    thematic-depth.codex.yaml
    symbolism.codex.yaml
    motifs.codex.yaml
```

**The agent asks ONE question:**

> "Here's the atlas structure I'd recommend for your three-act novel with 12 characters:"
> ```
> atlas/
>   characters.codex.yaml
>   timeline.codex.yaml
>   themes.codex.yaml
>   plot-structure.codex.yaml
> ```
> "Looks right, or adjust?"

Options:
- **Looks good** (Recommended) — Use proposed structure
- **More detail** — Expand sections into folders with sub-files
- **Simpler** — Fewer files, more consolidated

**Progress messaging:**
> "Scanning manuscript... literary fiction, 28 chapters, 87,000 words."
> "Proposing atlas structure..."

---

## Pass 1: Entity Extraction

**What the agent does:**
1. Reads the manuscript text chapter-by-chapter (see Context Window Strategy below)
2. Extracts: characters, locations, objects, factions, key events
3. Maps entity presence per chapter (where each character/location appears)
4. Deduplicates entities across chapters (merge pass)
5. Creates one deep protagonist profile (free tier preview)
6. Estimates word counts and reading time

**Technology:** Claude Haiku — fast, cheap, optimized for extraction tasks.

### Context Window Strategy (Pass 1)

Large manuscripts exceed Haiku's context window. The agent handles this with a **chapter-by-chapter extraction + merge** approach:

1. **Per-chapter extraction:** Process each chapter individually. Extract entities mentioned in that chapter with descriptions, roles, and traits.
2. **Overlapping context:** Include the last 500 tokens of the previous chapter as overlap to catch cross-boundary references (e.g., a character introduced at the end of chapter 4 and named in chapter 5).
3. **Entity merge pass:** After all chapters are processed, deduplicate entities by name similarity (fuzzy match for nicknames, full names, and aliases). Merge chapter presence lists.
4. **Conflict resolution:** If two chapters describe the same entity differently (e.g., "Elena — marine biologist" vs "Elena — activist"), keep the most detailed description and note the evolution.

This is **much cheaper** than stuffing the entire manuscript into one context window, and works with manuscripts of any size.

**Output:**
```yaml
entities:
  characters:
    - name: "Elena Vasquez"
      description: "Former marine biologist turned environmental activist"
      chapters_present: [1, 3, 4, 5, 7, 9, 12, 15, 18, 21, 24, 27, 28]
      key_traits: [determined, haunted, brilliant]
      story_role: protagonist
    - name: "Marcus Chen"
      description: "Corporate lawyer with a hidden conscience"
      chapters_present: [2, 5, 8, 11, 14, 17, 20, 23, 26, 28]
      key_traits: [conflicted, strategic, empathetic]
      story_role: deuteragonist
    # ... all characters

  locations:
    - name: "Coral Bay Research Station"
      description: "Isolated marine research facility on the Pacific coast"
      chapters_present: [1, 3, 7, 15, 27]
    # ...

  objects:
    - name: "The Blackwood Report"
      description: "Suppressed environmental impact study"
      chapters_present: [5, 11, 17, 24]
    # ...

  factions:
    - name: "Pacific Conservation Alliance"
      members: ["Elena Vasquez", "Dr. Yuki Tanaka", "Sam Reyes"]
    # ...

  key_events:
    - event: "Report leaked to press"
      chapter: 17
      characters_involved: ["Elena Vasquez", "Marcus Chen"]
    # ...

stats:
  total_chapters: 28
  unique_characters: 14
  unique_locations: 8
  manuscript_length: 87234
  estimated_reading_hours: 6
```

**Progress messaging:**
> "Extracting entities... 14 characters, 8 locations found across 28 chapters."

**This pass is FREE.** It uses Haiku (cheap) and gives the writer a preview of what the full atlas will contain. The conversion hook: "Here's what I found — want me to build the full atlas?"

---

## Pass 2: Per-Chapter Deep Analysis

**What the agent does:**
1. Selects relevant analysis modules based on atlas type (genre-aware)
2. Dispatches modules on every chapter in parallel using Task subagents
3. Collects results into `.analysis.json` files per chapter

**Module selection per atlas type:**

| Atlas Type | Modules Selected | Modules Skipped |
|------------|-----------------|-----------------|
| **Literary Fiction** | characters, character_relationships, three_act_structure, story_beats, story_pacing, writing_style, thematic_depth, reader_emotions, immersion, jungian_analysis, summary, tags | gag_analysis, win_loss_wave, four_weapons |
| **Thriller** | characters, story_pacing, plot_twists, misdirection_surprise, win_loss_wave, story_beats, heros_journey, reader_emotions, summary, tags | jungian_analysis, dream_symbolism, rhythmic_cadence |
| **Fantasy/Sci-Fi** | characters, character_relationships, psychogeography, story_beats, thematic_depth, tags, summary, writing_style | gag_analysis |
| **Non-Fiction** | summary, tags, clarity_accessibility, writing_style, language_style, thematic_depth | All narrative modules |
| **Poetry** | writing_style, language_style, rhythmic_cadence, literary_devices, emotional_dynamics, tags | All plot/structure modules |

**Parallel execution:**

The agent dispatches chapter analysis in batches using Task subagents:

```
Task 1: Analyze chapters 1-7  (all selected modules)
Task 2: Analyze chapters 8-14 (all selected modules)
Task 3: Analyze chapters 15-21 (all selected modules)
Task 4: Analyze chapters 22-28 (all selected modules)
```

Each task is independent — no shared state. Results collected after all tasks finish.

**Progress messaging:**
> "Analyzing 28 chapters with 12 modules... running in parallel."
> "Chapters 1-14 done. 15-28 still running..."
> "All 28 chapters analyzed. 336 module results collected."

**This pass is PAID.** Credit cost = chapters x modules selected.

### Reusing Existing Analysis Data

If the user already ran `/analysis` on this project, the atlas should **not** re-run those modules. The agent checks for existing `.analysis.json` files before dispatching:

1. **Scan for existing results:** Check each chapter for `.analysis.json` files
2. **Verify freshness:** Compare the `sourceHash` in each analysis result against the current chapter content hash (uses `staleness_checker.py` from `scripts/`)
3. **Reuse fresh results:** If the analysis hash matches, skip that chapter/module combo entirely
4. **Re-run stale results:** If the chapter content changed since the analysis was run, re-analyze

```
28 chapters, 10 modules each = 280 potential analyses
- 200 already exist and are fresh → reuse (free)
- 60 are stale (chapters changed) → re-run (paid)
- 20 are missing (new modules) → run (paid)
Total cost: 80 analyses instead of 280 (71% savings)
```

**Progress messaging:**
> "Found existing analysis for 20 of 28 chapters. Re-analyzing 8 changed chapters..."
> "80 module runs needed (200 reused from previous analysis)."

**This is automatic.** The agent doesn't ask — it always checks for existing data first. The writer only pays for new work.

---

## Pass 3: Synthesis and Assembly

**What the agent does:**
1. Reads Pass 1 entity map + Pass 2 per-chapter analysis results
2. Synthesizes cross-chapter insights into atlas sections
3. Writes `.codex.yaml` files following the Pass 0 structure
4. Generates atlas `index.codex.yaml` with full hierarchy
5. Commits atlas to project git repo

**Synthesis is the magic.** This is where isolated per-chapter data becomes a cohesive atlas. The agent cross-references:

- **Character arcs**: How does Elena change from chapter 1 to chapter 28? What's the emotional journey?
- **Relationship evolution**: Elena and Marcus start as adversaries. When do they ally? What triggers the shift?
- **Timeline reconstruction**: Events in chronological order, even if the narrative is non-linear
- **Theme threads**: Which themes appear in which chapters? How do they build and resolve?
- **Location significance**: Coral Bay isn't just a setting — it's where the climax happens. Why does the story keep returning there?

**Synthesizer types:**

| Synthesizer | Input | Output |
|-------------|-------|--------|
| CharacterSynthesizer | Per-chapter character data, entity map | Full profiles with arcs, traits, relationships |
| TimelineSynthesizer | Story beats, summaries, key events | Chronological event map with chapter references |
| ThemeSynthesizer | Thematic depth, tags, emotional data | Theme analysis with evolution across narrative |
| StructureSynthesizer | Three-act, hero's journey, story beats | Structural overview with turning points |
| LocationSynthesizer | Psychogeography, setting descriptions | Location profiles with narrative significance |
| RelationshipSynthesizer | Character relationships, emotional data | Relationship matrix with evolution timeline |
| WorldSynthesizer | Factions, magic/tech systems, artifacts | World reference (fantasy/sci-fi only) |
| TopicMapSynthesizer | Summaries, tags, key arguments | Topic hierarchy with cross-references (non-fiction only) |
| ImageryDevicesSynthesizer | Literary devices, emotional dynamics, rhythmic data | Imagery catalog and formal analysis (poetry only) |

**Technology:** Claude Sonnet or Opus — synthesis requires the strongest reasoning.

### Context Window Strategy (Pass 3)

Synthesis needs to cross-reference ALL entity data + ALL analysis results. For large manuscripts, this exceeds even Opus's context window. The agent uses a **two-stage synthesis** approach:

**Stage 1: Condense per-chapter data into entity-centric summaries**

Instead of feeding raw analysis JSON into synthesis, the agent first creates compressed entity profiles:

```
For each character:
  - Merge all per-chapter character analysis data into one summary
  - Include: chapters present, key actions per chapter, trait evolution, relationships per chapter
  - Target: ~200-500 tokens per character (vs. ~2000+ raw)

For each theme:
  - Merge thematic_depth results across chapters into one thread
  - Include: chapters present, intensity per chapter, key quotes
  - Target: ~100-300 tokens per theme
```

**Stage 2: Synthesize from condensed data**

Each synthesizer receives the condensed entity profiles, not raw per-chapter dumps. This means:
- CharacterSynthesizer gets ~500 tokens x 14 characters = ~7,000 tokens (fits easily)
- TimelineSynthesizer gets entity map events + story beats summaries = ~5,000 tokens
- ThemeSynthesizer gets condensed theme threads = ~3,000 tokens

Each synthesizer runs independently — they don't share a context window. The agent dispatches them in parallel.

**For extremely large manuscripts (50+ chapters, 30+ characters):**

Add a third stage: the agent runs a "meta-synthesizer" that reads all synthesizer outputs and checks for cross-section consistency (e.g., timeline events match character arc turning points).

### Selective Section Building

The user can choose which atlas sections to build. After Pass 0 proposes the structure:

> "Here's the atlas I'd recommend:"
> ```
> atlas/
>   characters.codex.yaml      ✓ selected
>   timeline.codex.yaml        ✓ selected
>   themes.codex.yaml          ✓ selected
>   plot-structure.codex.yaml  ✓ selected
>   locations.codex.yaml       ✓ selected
>   relationships.codex.yaml   ✓ selected
> ```
> "Build all sections, or pick specific ones?"

Options:
- **Build all** (Recommended) — Full atlas
- **Select sections** — Checkboxes for each section
- **Characters only** — Quick shortcut for the most popular section

**Why this matters:** A full atlas for 28 chapters might cost ~380 credits. Characters + Timeline alone might cost ~180. Writers on a budget can build incrementally — start with characters, add more sections later.

**Adding sections later:** The agent detects an existing atlas and offers to extend it:
> "Your atlas has characters and timeline. Want to add themes and locations?"

The existing sections are preserved; only new synthesizers run.

**Progress messaging:**
> "Synthesizing character arcs... 14 characters across 28 chapters."
> "Building timeline... 47 key events in chronological order."
> "Assembling atlas files... 6 sections."
> "Committing to project repo..."
> "Done. Atlas complete — 6 files, 14 characters, 47 events mapped."

---

## Multiple Atlases Per Project

A project can have **multiple atlases**, each with a customizable name. This enables different atlas perspectives on the same manuscript.

### Use Cases

- **"Story Atlas"** — Characters, timeline, themes, plot structure (the default)
- **"World Atlas"** — Locations, factions, magic system, artifacts (for fantasy/sci-fi)
- **"Character Deep Dive"** — Just characters with maximum depth (uses Opus for synthesis)
- **"Revision Atlas"** — Generated after a rewrite to compare with the original

### How It Works

**Creating a named atlas:**

> `/atlas` — Creates default atlas (named "atlas" unless one exists)
> `/atlas --name "world"` — Creates atlas named "world"
> `/atlas --name "character-deep-dive"` — Creates atlas with custom name

**The agent asks for the name on first creation:**

> "What should I call this atlas? Default is 'atlas'."
> [atlas]  [story-atlas]  [Custom name]

**Folder structure with multiple atlases:**

```
my-novel/
├── index.codex.yaml           # Root index with atlases array
├── chapters/
│   └── ...
├── atlas/                     # Default atlas
│   ├── index.codex.yaml       # type: atlas
│   └── ...
└── world-atlas/               # Second atlas
    ├── index.codex.yaml       # type: atlas
    └── ...
```

### Atlas Registration in index.codex.yaml

Atlases are registered in the project's root `index.codex.yaml` via an `atlases` array. This is how ChapterWise.app, the VS Code extension, and the Reader Recipe discover and render atlases.

```yaml
# my-novel/index.codex.yaml (project root)
type: project
name: "The Long Way Home"
description: "A literary fiction novel"

atlases:
  - name: "Story Atlas"
    path: atlas/
    atlas_type: story
    generated: "2026-02-27T15:25:00Z"
    generator: atlas-recipe
    sections: [characters, timeline, themes, plot-structure, locations, relationships]
  - name: "World Atlas"
    path: world-atlas/
    atlas_type: story
    generated: "2026-03-05T10:00:00Z"
    generator: atlas-recipe
    sections: [locations, world-rules, factions, artifacts]

children:
  - type: part
    name: "Part I: Departure"
    src: part-1-departure/
  # ... manuscript content
```

**The `atlases` array is separate from `children`.** Atlases are not mixed into the manuscript's content tree — they're registered at the top level as a distinct concept.

### How Atlases Appear in the Project

**On ChapterWise.app:** Atlases appear in a dedicated section above or below the manuscript tree, with a distinct icon (e.g., compass, map). Each atlas expands to show its sections.

**In VS Code:** The ChapterWise extension reads the `atlases` array and renders them in a separate tree section with atlas-specific icons.

**In the file tree:** Atlas folders are normal directories with `index.codex.yaml` files. They're browsable like any Codex content. The `type: atlas` on their index distinguishes them from manuscript content.

### Recipe Folder Per Atlas

Each atlas gets its own recipe folder:

```
.chapterwise/
├── import-recipe/              # Import recipe (one per project)
├── atlas-recipe/               # Default atlas recipe
│   └── recipe.yaml
└── atlas-recipe-world/         # "World Atlas" recipe
    └── recipe.yaml
```

The recipe folder name matches the atlas: `atlas-recipe-{name}/`. The default atlas uses `atlas-recipe/`.

---

## Git Behavior

### When to Commit

The agent **asks before committing** atlas files to the project's git repo:

> "Atlas complete — 6 files ready. Commit to the project repo?"
> [Commit]  [Save without committing]  [Review first]

If the user chose "Commit", the agent creates a descriptive commit:

```
Add atlas: Story Atlas (6 sections, 14 characters, 47 events)

Sections: characters, timeline, themes, plot-structure, locations, relationships
Generated by atlas-recipe with claude-sonnet-4-6
```

### Git Requirements

- **Existing repo:** The project must be a git repo. If not, the agent offers to `git init`.
- **Same branch:** Atlas commits go on the current branch (the agent never switches branches).
- **Clean working tree not required:** Atlas files are new additions — they don't conflict with uncommitted manuscript changes.
- **No auto-push:** The agent never pushes to remote. The writer pushes when ready.

### .gitignore

Recipe artifacts (`.chapterwise/`) are typically gitignored. Atlas output folders (`atlas/`, `world-atlas/`) are **not** gitignored — they're the deliverable.

```gitignore
# .gitignore
.chapterwise/
```

---

## Atlas Management Commands

| Command | What It Does |
|---------|-------------|
| `/atlas` | Build a new atlas (or extend existing) |
| `/atlas --update` | Incremental update after manuscript changes |
| `/atlas --name "world"` | Build a named atlas |
| `/atlas --rebuild` | Delete and rebuild atlas from scratch |
| `/atlas --delete` | Delete an atlas (removes folder + recipe + index entry) |
| `/atlas --list` | Show all atlases in this project |
| `/atlas --add-sections` | Add sections to an existing atlas |

### Reset / Rebuild

`/atlas --rebuild` does a **clean rebuild**:

1. Asks for confirmation: "This will delete the existing atlas and rebuild from scratch. User edits (`source: user`) will be lost. Continue?"
2. Deletes the atlas output folder
3. Deletes the atlas recipe folder
4. Removes the atlas entry from the project's `atlases` array
5. Runs the full four-pass pipeline from scratch
6. Re-registers the atlas in the index

### Delete

`/atlas --delete` removes an atlas entirely:

1. Asks for confirmation: "Delete the Story Atlas? This removes 6 files and can't be undone."
2. Deletes the atlas output folder
3. Deletes the atlas recipe folder
4. Removes the atlas entry from `index.codex.yaml`
5. Commits the deletion

If the project has multiple atlases, the agent asks which one:
> "You have 2 atlases: Story Atlas, World Atlas. Which one to delete?"

---

## Self-Validation and Self-Healing

Atlas generation and atlas updates both end with a mandatory validator pass:

1. Run `codex_validator.py` on the atlas output folder with `fix: true`
2. Run `recipe_validator.py` on `.chapterwise/atlas-recipe/` (or named atlas recipe folder)
3. Cross-check atlas index references against actual section files and manuscript chapters

Auto-fix behavior:
- Missing frontmatter fields, UUID issues, and word counts are repaired automatically
- Orphan atlas files are registered in `index.codex.yaml`
- Broken section references are patched or removed with a warning note

Release criteria for an atlas run:
- Validators return `valid: true`
- No unresolved cross-recipe issues remain
- User-facing completion message is shown only after validation succeeds

---

## Atlas Recipe Format

```yaml
# .chapterwise/atlas-recipe/recipe.yaml
type: atlas                     # Recipe type identifier
version: "1.0"
created: "2026-02-27T15:00:00Z"
updated: "2026-02-27T15:30:00Z"

atlas:
  name: "Story Atlas"           # User-chosen name (displayed in project tree)
  slug: "atlas"                 # Folder name (derived from name, or custom)
  output_path: "atlas/"         # Relative path within project

source:
  project_path: "./my-novel/"
  chapter_count: 28
  word_count: 87234
  chapter_hashes:             # Per-chapter content hash for Update Atlas diffing
    chapter-01: "a1b2c3d4"
    chapter-02: "e5f6g7h8"
    # ...

manuscript:
  title: "The Long Way Home"
  type: literary_fiction
  atlas_type: story           # story | script | nonfiction | research | poetry (immersive: deferred to post-v2.0.0)

structure:
  proposed: true              # Pass 0 completed
  user_confirmed: true
  layout: simple              # simple | detailed | custom
  sections_selected:          # Which sections the user chose to build
    - characters
    - timeline
    - themes
    - plot-structure
    - locations
    - relationships
  sections_available:         # Full list proposed by Pass 0 (for adding later)
    - characters
    - timeline
    - themes
    - plot-structure
    - locations
    - relationships
  folders:
    - path: "atlas/"
      files:
        - "index.codex.yaml"
        - "characters.codex.yaml"
        - "timeline.codex.yaml"
        - "themes.codex.yaml"
        - "plot-structure.codex.yaml"
        - "locations.codex.yaml"

passes:
  pass0:
    status: complete
    completed_at: "2026-02-27T15:00:10Z"
  pass1:
    status: complete
    completed_at: "2026-02-27T15:00:45Z"
    entities_found:
      characters: 14
      locations: 8
      objects: 5
      factions: 3
      key_events: 47
  pass2:
    status: complete
    completed_at: "2026-02-27T15:15:00Z"
    modules_used:
      - characters
      - character_relationships
      - three_act_structure
      - story_beats
      - story_pacing
      - writing_style
      - thematic_depth
      - reader_emotions
      - summary
      - tags
    modules_skipped:
      - gag_analysis
      - win_loss_wave
    chapters_analyzed: 28
    total_module_results: 280
    analysis_reuse:                 # Existing analysis data reuse stats
      chapters_reused: 20           # Had fresh .analysis.json files
      chapters_reanalyzed: 8        # Stale or missing, re-run
      credits_saved: 200            # Estimated savings from reuse
  pass3:
    status: complete
    completed_at: "2026-02-27T15:25:00Z"
    model: claude-sonnet-4-6
    sections_synthesized:
      - characters
      - timeline
      - themes
      - plot-structure
      - locations
      - relationships

output:
  path: "atlas/"
  file_count: 6
  git_commit: "abc123def"

preferences:
  atlas_type: story
  structure_layout: simple
  include_relationship_map: true
  include_locations: true
  synthesis_depth: standard     # standard | deep (deep uses Opus)
```

---

## Atlas Types

The atlas type is derived from the manuscript type and determines which modules run and which sections get synthesized.

| Manuscript Type | Atlas Type | Key Sections |
|----------------|------------|--------------|
| Novel / Literary Fiction | `story` | Characters, Timeline, Themes, Plot Structure, Locations |
| Thriller / Mystery | `story` | Characters, Timeline, Plot Structure, Clues & Red Herrings |
| Fantasy / Sci-Fi | `story` | Characters, World (locations, factions, magic/tech), Timeline, Themes |
| Screenplay | `script` | Characters, Scene Breakdown, Dialogue Stats, Structure |
| Non-Fiction | `nonfiction` | Topic Map, Key Arguments, Source References, Chapter Summaries |
| Academic | `research` | Literature Map, Methodology, Key Findings, Citation Network |
| Poetry Collection | `poetry` | Themes, Imagery, Devices, Emotional Arc |
| Interactive Fiction / Game Writing | `immersive` (deferred) | Branching Paths, Characters, World State, Choice Maps |

The agent picks the atlas type automatically based on the manuscript type from the import recipe. If unsure, it asks:

> "This looks like it could be literary fiction or creative non-fiction. Which fits better?"

---

## Atlas as Codex Project

The atlas output is a proper Codex project — meaning it's fully compatible with the ChapterWise ecosystem:

### index.codex.yaml (Atlas Root)

```yaml
type: atlas
name: "Atlas: The Long Way Home"
description: "Character profiles, timeline, themes, and plot structure for The Long Way Home"
atlas_type: story
source_project: "the-long-way-home"
generated: "2026-02-27T15:25:00Z"
generator: "chapterwise/atlas-recipe"

children:
  - type: section
    name: Characters
    src: characters.codex.yaml
  - type: section
    name: Timeline
    src: timeline.codex.yaml
  - type: section
    name: Themes
    src: themes.codex.yaml
  - type: section
    name: Plot Structure
    src: plot-structure.codex.yaml
  - type: section
    name: Locations
    src: locations.codex.yaml
```

### Style Conventions

Atlas files use a standard set of CSS custom properties that map to ChapterWise's theme system (`--codex-*` variables). This means:

1. **ChapterWise.app renders them natively** via `codex_shell.html` and `_theme_injection.html`
2. **Reader Recipe can style them** with custom fonts, colors, layouts
3. **VS Code extension displays them** with the codex renderer
4. **Download as ZIP** and they're self-contained

The atlas `index.codex.yaml` can include a `style` section for atlas-specific presentation:

```yaml
style:
  preset: atlas-dark          # Built-in atlas theme preset
  variables:
    --codex-accent: "#4a9eff"
    --codex-bg-primary: "#1a1a2e"
    --codex-text-primary: "#e0e0e0"
  fonts:
    heading: "Playfair Display"
    body: "Inter"
```

These map directly to the `--codex-*` CSS custom properties used by `codex-theme.css` and `codex-components.css`. The theme injection system (`_theme_injection.html`) picks them up automatically.

---

## Integration with Reader Recipe

The Atlas is a Codex project. The Reader Recipe can build a custom reader for it — just like any other Codex project.

### The Pipeline

```
Manuscript → Import Recipe → Codex Project
                                    ↓
                            Atlas Recipe → Atlas (Codex)
                                    ↓
                            Reader Recipe → Styled Atlas Reader (HTML/CSS/JS)
```

A writer can:
1. Import their manuscript (Import Recipe)
2. Generate an atlas (Atlas Recipe)
3. Build a custom reader for the atlas (Reader Recipe)
4. Publish the styled atlas on ChapterWise.app or host it themselves

### Atlas-Specific Reader Features

When the Reader Recipe detects `type: atlas` in the index, it adds atlas-specific components:

- **Character cards** with portrait placeholders, trait tags, arc summaries
- **Timeline view** — horizontal scrollable timeline with chapter markers
- **Relationship web** — interactive connection diagram (SVG or Canvas)
- **Theme heatmap** — which themes appear in which chapters (color-coded grid)
- **Navigation** — jump from character → chapters where they appear → back

These components use the same `--codex-*` variable system, so custom themes apply uniformly.

---

## Credit / Cost Estimation

The recipe includes cost estimates before execution:

> "Your atlas plan: 28 chapters, 10 modules per chapter, synthesis pass."
> "Estimated cost: ~380 credits."
> "Want to build the full atlas, or just start with the free entity extraction?"

| Pass | Cost | Notes |
|------|------|-------|
| Pass 0: Scan | Free | Haiku, 10 seconds |
| Pass 1: Extract | Free | Haiku, 30 seconds, rate-limited (5/hour) |
| Pass 2: Analyze | 1 credit/chapter/module | 28 chapters x 10 modules = 280 credits |
| Pass 3: Synthesize | 100 credits (Sonnet) or 200 credits (Opus) | Cross-chapter synthesis |
| **Total (typical)** | **~380-480 credits** | Depends on chapter count and module selection |

For **BYOK** (bring your own key) users running locally in Claude Code — no credits. The agent uses the writer's API key directly.

---

## Error Handling

| Error | Agent Response |
|-------|---------------|
| Manuscript too short | "Your manuscript is 3 chapters — an atlas needs more material. Try running individual analysis modules instead." |
| Pass 2 partial failure | "25 of 28 chapters analyzed. 3 had issues — building atlas from what I have, flagging gaps." |
| Synthesis timeout | "Synthesis is taking longer than expected — your manuscript is complex. Continuing in background..." |
| Atlas already exists | "Found an existing atlas. Want me to update it with your latest changes, or rebuild from scratch?" |
| Unknown manuscript type | "I can't determine the genre automatically. What type of work is this?" |

---

## Example: Full Atlas Session

What the user sees:

```
> /atlas

Scanning manuscript... literary fiction, 28 chapters, 87,000 words.
Proposing atlas structure...

Here's the atlas I'd recommend:
  atlas/
    characters.codex.yaml
    timeline.codex.yaml
    themes.codex.yaml
    plot-structure.codex.yaml
    locations.codex.yaml

Looks right, or adjust?
  [Looks good]  [More detail]  [Simpler]

Extracting entities... 14 characters, 8 locations, 47 key events found.

Ready to build the full atlas? Estimated cost: ~380 credits.
  [Build full atlas]  [Just the free overview]

Analyzing 28 chapters with 10 modules... running in parallel.
Chapters 1-14 done. 15-28 still running...
All 28 chapters analyzed. 280 module results collected.

Synthesizing character arcs... 14 characters.
Building timeline... 47 events mapped.
Weaving theme threads... 6 major themes.
Assembling atlas files...
Committing to project repo...

Done. Atlas complete.

  atlas/
  ├── index.codex.yaml
  ├── characters.codex.yaml    (14 profiles with arcs)
  ├── timeline.codex.yaml      (47 events, chronological)
  ├── themes.codex.yaml        (6 themes with chapter mapping)
  ├── plot-structure.codex.yaml (three-act breakdown)
  └── locations.codex.yaml     (8 locations with significance)

Next steps:
  View on ChapterWise.app or open in VS Code
  Run /atlas --update after revisions
  Run /reader on atlas/ for a custom styled version
```
