# Atlas Recipe — Atlas Sections and Output Format

## What Goes in an Atlas

An atlas is a Codex project — a folder of `.codex.yaml` files with an `index.codex.yaml` root. Each file represents a section of the atlas. The agent selects which sections to generate based on the manuscript type and content.

## Section Types

### Characters Section

**Generated for:** All fiction atlas types (story, script)

**Contains:**
- Full character profiles with description, role, key traits
- Character arc summary (beginning → middle → end)
- Chapter presence map (which chapters they appear in)
- Key relationships (links to other characters)
- Key quotes (pulled from the manuscript)

**Codex format:**
```yaml
type: section
name: Characters
description: "14 characters across 28 chapters"

children:
  - type: character
    name: Elena Vasquez
    source: generated
    attributes:
      role: protagonist
      first_appearance: chapter-01
      last_appearance: chapter-28
      chapters_present: 13
      key_traits:
        - determined
        - haunted
        - brilliant
    content: |
      ## Elena Vasquez

      Former marine biologist turned environmental activist. Drives the central
      conflict by pursuing the suppressed Blackwood Report against corporate
      opposition.

      ### Arc

      **Beginning (Ch 1-9):** Isolated researcher, disillusioned with academia,
      discovers evidence of corporate environmental cover-up.

      **Middle (Ch 10-19):** Reluctant activist, builds unlikely alliance with
      Marcus Chen, faces personal and professional consequences.

      **End (Ch 20-28):** Transformed leader, sacrifices career security for
      public disclosure, finds purpose beyond the institution.

      ### Key Relationships

      - **Marcus Chen** — Adversary → reluctant ally → trusted partner
      - **Dr. Yuki Tanaka** — Mentor, provides scientific credibility
      - **Director Webb** — Antagonist, represents institutional suppression

      ### Key Moments

      - Ch 1: Discovers anomalous coral data
      - Ch 5: First confrontation with Marcus
      - Ch 17: Leaks the Blackwood Report
      - Ch 28: Public hearing testimony

  - type: character
    name: Marcus Chen
    source: generated
    # ...
```

### Timeline Section

**Generated for:** All fiction atlas types

**Contains:**
- Chronological event list (even if narrative is non-linear)
- Chapter references for each event
- Characters involved in each event
- Act/part markers

**Codex format:**
```yaml
type: section
name: Timeline
description: "47 key events across 28 chapters"

children:
  - type: event
    name: "Discovery of anomalous coral data"
    source: generated
    attributes:
      chapter: chapter-01
      characters: [Elena Vasquez]
      act: 1
      significance: inciting_incident
    content: |
      Elena discovers unexplained coral die-off patterns in her research data,
      contradicting the official environmental reports from Pacific Dynamics Corp.

  - type: event
    name: "Marcus assigned to the case"
    source: generated
    attributes:
      chapter: chapter-02
      characters: [Marcus Chen]
      act: 1
      significance: setup
    content: |
      Pacific Dynamics assigns Marcus to handle potential whistleblower threats
      from the Coral Bay Research Station.

  # ... 45 more events
```

### Themes Section

**Generated for:** All atlas types

**Contains:**
- Major themes with descriptions
- Theme presence per chapter (heatmap data)
- Theme evolution across the narrative
- Supporting quotes and evidence

**Codex format:**
```yaml
type: section
name: Themes
description: "6 major themes across 28 chapters"

children:
  - type: theme
    name: "Institutional Corruption"
    source: generated
    attributes:
      prominence: primary
      chapters_present: [1, 3, 5, 8, 11, 14, 17, 20, 24, 27, 28]
      first_appearance: chapter-01
      peak_intensity: chapter-17
    content: |
      ## Institutional Corruption

      The central theme — how institutions prioritize self-preservation over
      truth. Manifests through Pacific Dynamics' environmental cover-up, the
      university's reluctance to support Elena, and the regulatory agency's
      complicity.

      ### Evolution

      **Introduction (Ch 1-5):** Subtle hints — redacted reports, dismissive
      administrators, corporate PR language masking environmental damage.

      **Development (Ch 6-17):** Explicit confrontation — Elena uncovers the
      suppression chain, Marcus sees it from inside the corporate machine.

      **Resolution (Ch 18-28):** Systemic exposure — the Blackwood Report
      reveals the full scope, forcing institutional reckoning.

  - type: theme
    name: "Personal Integrity vs. Career Security"
    source: generated
    # ...
```

### Plot Structure Section

**Generated for:** Fiction atlas types (story, script)

**Contains:**
- Three-act structure breakdown with turning points
- Hero's journey mapping (if applicable)
- Story beats per chapter
- Pacing analysis (tension curve)
- Subplot tracking

**Codex format:**
```yaml
type: section
name: Plot Structure
description: "Three-act structure with 5 turning points"

children:
  - type: structure
    name: "Three-Act Breakdown"
    source: generated
    content: |
      ## Act I: Setup (Chapters 1-9)

      **Inciting Incident (Ch 1):** Elena discovers anomalous coral data.
      **Lock-In (Ch 5):** First confrontation with Marcus — no turning back.
      **Act I Climax (Ch 9):** Elena decides to investigate despite university
      pressure.

      ## Act II: Confrontation (Chapters 10-21)

      **Midpoint (Ch 14):** Marcus discovers the Blackwood Report exists.
      **Low Point (Ch 18):** Elena is fired, Marcus is reassigned.
      **Act II Climax (Ch 21):** Alliance formed — Elena and Marcus decide
      to go public together.

      ## Act III: Resolution (Chapters 22-28)

      **Climax (Ch 26):** Public hearing — testimony and evidence presented.
      **Resolution (Ch 28):** Aftermath — institutional reform begins, personal
      cost acknowledged.

  - type: structure
    name: "Pacing Analysis"
    source: generated
    attributes:
      tension_peaks: [5, 9, 14, 18, 21, 26]
      quiet_chapters: [3, 7, 13, 22]
    content: |
      ## Pacing

      The novel follows a classic escalation pattern with breather chapters
      between tension peaks. Average chapter length: 3,100 words (consistent
      pacing). Chapters 17-21 are the densest section — 5 consecutive high-
      tension chapters averaging 3,800 words each.
```

### Locations Section

**Generated for:** Fiction atlas types with significant settings

**Contains:**
- Location profiles with narrative significance
- Chapter presence
- Characters associated with each location
- Mood/atmosphere notes

**Codex format:**
```yaml
type: section
name: Locations
description: "8 locations across 28 chapters"

children:
  - type: location
    name: "Coral Bay Research Station"
    source: generated
    attributes:
      chapters_present: [1, 3, 7, 15, 27]
      characters_associated: [Elena Vasquez, Dr. Yuki Tanaka, Sam Reyes]
      significance: primary_setting
    content: |
      ## Coral Bay Research Station

      Isolated marine research facility on the Pacific coast. Elena's workplace
      and the site of the original data discovery. The station's isolation
      mirrors Elena's professional isolation — surrounded by ocean, cut off
      from institutional support.

      **Narrative function:** Safe harbor that becomes contested ground.
      The station is where Elena feels most competent (her scientific domain)
      but also where she's most vulnerable (remote, under surveillance).

      **Key scenes:**
      - Ch 1: Data discovery
      - Ch 7: Late-night break-in attempt
      - Ch 15: Marcus visits — first alliance discussion
      - Ch 27: Return for final evidence collection
```

### Relationships Section

**Generated for:** Fiction with 5+ named characters

**Contains:**
- Relationship pairs with evolution timeline
- Relationship type (ally, adversary, mentor, romantic, familial)
- Key turning points in each relationship
- Relationship matrix (who connects to whom)

**Codex format:**
```yaml
type: section
name: Relationships
description: "12 key relationships between 14 characters"

children:
  - type: relationship
    name: "Elena & Marcus"
    source: generated
    attributes:
      characters: [Elena Vasquez, Marcus Chen]
      type: adversary_to_ally
      turning_point: chapter-15
    content: |
      ## Elena Vasquez & Marcus Chen

      **Phase 1: Adversaries (Ch 1-9)**
      Elena sees Marcus as a corporate fixer. Marcus sees Elena as a
      liability to manage. Their first meeting (Ch 5) is confrontational.

      **Phase 2: Reluctant Respect (Ch 10-14)**
      Marcus discovers the Blackwood Report and begins questioning his
      role. Elena notices his hesitation but doesn't trust it.

      **Turning Point (Ch 15):**
      Marcus visits Coral Bay to warn Elena about corporate surveillance.
      First honest conversation. Trust begins.

      **Phase 3: Alliance (Ch 16-28)**
      Full partnership — Marcus provides legal strategy, Elena provides
      evidence. Their complementary skills (law + science) make them
      effective together.
```

### World Section (Fantasy/Sci-Fi Only)

**Generated for:** Fantasy, sci-fi, and speculative fiction atlas types

**Contains:**
- Magic system / technology rules
- Factions and political structures
- Artifacts and significant objects
- World history and lore

### Topic Map (Non-Fiction Only)

**Generated for:** Non-fiction, academic, and research atlas types

**Contains:**
- Key arguments and claims per chapter
- Source references and citations
- Topic hierarchy (main arguments → supporting points → evidence)
- Cross-references between chapters

### Imagery & Devices (Poetry Only)

**Generated for:** Poetry collection atlas types

**Contains:**
- Recurring imagery and symbols
- Literary devices used (with examples)
- Emotional arc across the collection
- Formal analysis (meter, rhyme scheme, structure)

---

## Style Variables and Conventions

Atlas files follow conventions that make them renderable across the ChapterWise ecosystem — on the web via `codex_shell.html`, in VS Code, or as standalone readers.

### Atlas-Specific Codex Attributes

Standard attributes that atlas files use:

```yaml
# On the atlas index
type: atlas                    # Tells renderers this is an atlas, not a manuscript
atlas_type: story              # story | script | nonfiction | research | poetry
source_project: "my-novel"    # Links back to the manuscript project
generated: "2026-02-27"       # When the atlas was built
generator: "atlas-recipe"     # What built it

# On atlas sections
source: generated              # "generated" (agent wrote it) or "user" (human wrote it)
significance: primary          # primary | secondary | minor (for filtering)

# On character nodes
role: protagonist              # protagonist | deuteragonist | antagonist | supporting | minor
first_appearance: chapter-01   # Chapter reference
chapters_present: 13           # Count for quick display

# On event nodes
act: 1                         # Act number (1, 2, 3)
significance: inciting_incident # Named story beat

# On theme nodes
prominence: primary            # primary | secondary | minor
peak_intensity: chapter-17     # Where the theme is strongest
```

### CSS Custom Properties for Atlas Rendering

Atlas files can include style variables that map to ChapterWise's `--codex-*` theme system. These are picked up by `_theme_injection.html` and `codex_theme_engine.js`.

**Atlas-specific style presets:**

```yaml
# In atlas/index.codex.yaml
style:
  preset: atlas-default    # or atlas-dark, atlas-academic, atlas-fantasy
```

Each preset defines:
```css
/* atlas-default */
--codex-atlas-accent: #4a9eff;
--codex-atlas-character-bg: #f0f7ff;
--codex-atlas-timeline-line: #d0d0d0;
--codex-atlas-theme-primary: #e74c3c;
--codex-atlas-theme-secondary: #3498db;
--codex-atlas-relationship-ally: #27ae60;
--codex-atlas-relationship-adversary: #e74c3c;
--codex-atlas-relationship-neutral: #95a5a6;
```

These variables are used by atlas-aware components in the Reader Recipe and by `codex_shell.html` when rendering atlas content on ChapterWise.app.

### Reader Recipe Integration Protocol

When the Reader Recipe detects `type: atlas` in the project index, it activates atlas-specific rendering:

1. **Character cards** — Grid layout with trait tags, arc summary, chapter count badge
2. **Timeline view** — Horizontal scrollable timeline with act dividers and event markers
3. **Theme heatmap** — Color-coded grid: chapters (x-axis) x themes (y-axis), intensity by shading
4. **Relationship web** — SVG diagram with connection lines colored by relationship type
5. **Cross-reference links** — Click a character name in the timeline → jump to their profile

All atlas components use the `--codex-atlas-*` variables, so custom themes apply consistently.

**The pipeline:**
```
Atlas Recipe → atlas/ folder (Codex project)
    ↓
Reader Recipe → styled reader with atlas-specific components
    ↓
ChapterWise.app renders it via codex_shell.html
    OR
Download as ZIP → self-contained HTML/CSS/JS
```

---

## File Naming Conventions

Atlas files use clean, slugified names consistent with ChapterWise conventions:

```
atlas/
├── index.codex.yaml              # Always present — atlas root
├── characters.codex.yaml         # Character profiles
├── timeline.codex.yaml           # Event timeline
├── themes.codex.yaml             # Theme analysis
├── plot-structure.codex.yaml     # Structural analysis
├── locations.codex.yaml          # Location profiles
└── relationships.codex.yaml      # Relationship analysis
```

For complex atlases with folders:
```
atlas/
├── index.codex.yaml
├── characters/
│   ├── protagonists.codex.yaml
│   ├── antagonists.codex.yaml
│   └── supporting-cast.codex.yaml
├── world/
│   ├── locations.codex.yaml
│   ├── factions.codex.yaml
│   └── magic-system.codex.yaml
├── plot/
│   ├── structure.codex.yaml
│   ├── timeline.codex.yaml
│   └── subplots.codex.yaml
└── themes/
    ├── major-themes.codex.yaml
    └── symbolism.codex.yaml
```

---

## Atlas Registration in Project Index

Every atlas is registered in the project's root `index.codex.yaml` via an `atlases` array. This is the canonical way for renderers (web, VS Code, Reader) to discover atlases.

### The `atlases` Array

```yaml
# my-novel/index.codex.yaml (project root)
type: project
name: "The Long Way Home"

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
  # ... manuscript content (not affected by atlases)
```

### Array Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | User-facing display name (customizable) |
| `path` | Yes | Relative folder path within the project |
| `atlas_type` | Yes | story, script, nonfiction, research, poetry (immersive: deferred) |
| `generated` | Yes | ISO 8601 timestamp of last generation/update |
| `generator` | Yes | Always `atlas-recipe` (for provenance) |
| `sections` | Yes | List of section slugs currently built |

### Multiple Atlases

A project can have any number of atlases. Each atlas entry in the `atlases` array corresponds to:
- One folder in the project (the `path`)
- One recipe folder in `.chapterwise/` (e.g., `atlas-recipe/`, `atlas-recipe-world/`)
- One `index.codex.yaml` with `type: atlas` inside the atlas folder

**Naming:** The atlas `name` is what users see. The `path` is the folder slug (derived from name, lowercase, hyphens). Users choose the name at creation time.

### How Renderers Use the Array

**ChapterWise.app (`index_tree_renderer.js`):**
- Reads `atlases` array from the project index
- Renders each atlas as a collapsible section in the project tree, separate from manuscript `children`
- Uses a distinct atlas icon (compass/map) to visually distinguish from manuscript content
- Each atlas section expands to show its child sections (characters, timeline, etc.)

**VS Code Extension:**
- Reads `atlases` array from root `index.codex.yaml`
- Renders atlas entries in a dedicated "Atlases" tree section
- Provides quick-access commands: "Open Atlas", "Update Atlas"

**Reader Recipe:**
- Detects `atlases` array when building a reader for the project
- Offers to include atlas sections in the reader navigation
- Activates atlas-specific components (character cards, timeline view, etc.)

### Schema Extension

The `atlases` array should be added to the Codex V1.2 schema (`codex-v1.2.schema.json`) as an optional top-level property:

```json
"atlases": {
  "type": "array",
  "description": "Registered atlas projects within this project",
  "items": {
    "type": "object",
    "required": ["name", "path", "atlas_type", "generated", "generator", "sections"],
    "properties": {
      "name": { "type": "string" },
      "path": { "type": "string" },
      "atlas_type": { "type": "string", "enum": ["story", "script", "nonfiction", "research", "poetry"] },
      "generated": { "type": "string", "format": "date-time" },
      "generator": { "type": "string" },
      "sections": { "type": "array", "items": { "type": "string" } }
    }
  }
}
```

---

## What the Atlas Enables

### On ChapterWise.app
- Browse atlas like any Codex project — tree navigation, search, theme switching
- Atlases appear in a dedicated section of the project tree (via `atlases` array), separate from manuscript content
- Multiple atlases show as separate collapsible sections with distinct icons
- Click character names → jump to chapter appearances
- Share atlas URL publicly or keep private

### In VS Code
- ChapterWise VS Code extension renders atlas files with the codex viewer
- Quick reference while editing — character details, timeline, themes
- Atlas updates appear in git diff after `/atlas --update`

### As Downloadable ZIP
- Self-contained Codex project — all `.codex.yaml` files
- Import into any ChapterWise-compatible tool
- Open in any text editor (it's just YAML)

### With Reader Recipe
- Build a custom styled atlas reader (HTML/CSS/JS)
- Atlas-specific components (character cards, timeline, relationship web)
- Custom fonts, colors, layouts via `--codex-*` variables
- Publishable as a standalone website

### For the Writer
- Quick reference during revision — "What chapter did Elena first meet Marcus?"
- Continuity checking — "Is the timeline consistent?"
- Beta reader guide — "Here's the atlas, it'll help you track all the characters"
- Series bible — "Here's everything about this world, for the sequel"
