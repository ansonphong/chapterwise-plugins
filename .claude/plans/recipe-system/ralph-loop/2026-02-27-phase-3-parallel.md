# Phase 3: Parallel Recipe Build — Tasks 19-24

> **Reference:** `build-plans/AGENT-2-ANALYSIS.md`, `build-plans/AGENT-3-ATLAS.md`, `build-plans/AGENT-4-READER.md`

This phase dispatches 3 parallel agents (each in a worktree) to build the Analysis, Atlas, and Reader recipes simultaneously. All agents depend on Phase 1 (scaffold) and Phase 2 (import patterns + shared scripts).

**DISPATCH:** Launch all 3 agents simultaneously via `Task(subagent_type="general-purpose", isolation="worktree")`. Each agent receives its own task list below.

---

## Agent A: Analysis Recipe (Tasks 19-20)

**Design docs to read first:**
- `analysis-recipe/00-OVERVIEW.md`
- `analysis-recipe/01-ANALYSIS-RECIPE.md`
- `LANGUAGE-GUIDE.md` (Analysis section — course names, progress messaging)
- `build-plans/AGENT-2-ANALYSIS.md` (full build spec)

### Task 19: Rewrite `commands/analysis.md` with recipe integration

**Files:**
- Modify: `plugins/chapterwise/commands/analysis.md`

**Critical constraint:** Backward compatibility. These must keep working exactly as before:
- `/analysis summary file.codex.yaml` → runs summary module on file
- `/analysis list` → shows available modules
- `/analysis help characters` → shows module details
- `/analysis --all` → batch with parallel agents
- `--force`, `--node`, `--glob`, `--dry-run` flags

**What's new (additive):**
- `/analysis` (no args) → interactive course picker with AskUserQuestion
- `/analysis --plan` → genre-aware module recommendation
- Recipe saved to `.chapterwise/analysis-recipe/recipe.yaml`
- Re-analysis detection: "Fresh results exist — skip or re-run?"
- Course grouping: Quick taste → Slow roast → Spice rack → Simmering
- Language Guide progress messaging

**Structure (~350-450 lines):**
```
---
description/allowed-tools/triggers frontmatter
---

# ChapterWise Analysis

## Overview

## Command Routing
  ### `/analysis` (no args) — Interactive Course Picker
  ### `/analysis <module> [file]` — Direct Analysis (EXISTING, unchanged)
  ### `/analysis list` — Show Modules (updated with course groupings)
  ### `/analysis help <module>` — Module Details (EXISTING, unchanged)
  ### `/analysis --plan` — Genre-Aware Planning (NEW)

## Recipe Integration
  ### Saving Analysis Recipe
  ### Re-Analysis Detection

## Parallel Execution

## Validation and Self-Healing
  - Run recipe_validator.py on `.chapterwise/analysis-recipe/` after writing results
  - Validate `.analysis.json` payload shape before finishing
  - If fixable metadata issues are found, repair and continue; otherwise surface exact errors

## Error Handling

## Language Rules
```

**Triggers:**
```yaml
triggers:
  - analysis
  - analysis summary
  - analysis characters
  - analysis list
  - analysis help
  - chapterwise:analysis
argument-hint: "[module] [file] [--flags]"
```

### Step 19.1: Read existing analysis.md

Read the current `plugins/chapterwise/commands/analysis.md` (copied from chapterwise-analysis in Phase 1). Understand every feature, flag, and code path.

### Step 19.2: Read design docs

Read `analysis-recipe/00-OVERVIEW.md` and `01-ANALYSIS-RECIPE.md`. Understand course system, genre-aware selection, recipe saving.

### Step 19.3: Write the rewritten analysis.md

Preserve ALL existing functionality (backward compat). Add recipe layer on top:
- Interactive course picker via AskUserQuestion
- Genre-aware `--plan` flag
- Recipe creation/loading via `recipe_manager.py`
- Re-analysis detection via `staleness_checker.py`
- Course names from Language Guide
- Progress messaging: "Quick taste... summary, characters, tags on 28 chapters."

**Script calls use stdin JSON:**
```
echo '{"genre":"literary_fiction"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py recommend
echo '{"project_path":".","type":"analysis"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py create
```

### Step 19.4: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/analysis.md && grep -q "courses" plugins/chapterwise/commands/analysis.md && grep -q "recipe_manager" plugins/chapterwise/commands/analysis.md && grep -q "recipe_validator.py" plugins/chapterwise/commands/analysis.md && ! grep -qi "order up\|bon appetit\|chef.s kiss" plugins/chapterwise/commands/analysis.md && echo PASS
```

---

### Task 20: Update `scripts/module_loader.py` with courses + recommend

**Files:**
- Modify: `plugins/chapterwise/scripts/module_loader.py`

### Step 20.1: Read existing module_loader.py

Understand current `list` command behavior.

### Step 20.2: Add `courses` command

Hardcode course groupings:
```python
COURSES = {
    "quick_taste": {
        "name": "Quick taste",
        "description": "Fast overview — summary, characters, tags",
        "modules": ["summary", "characters", "tags"]
    },
    "slow_roast": {
        "name": "Slow roast",
        "description": "Deep structural analysis",
        "modules": ["three_act_structure", "story_beats", "story_pacing", "heros_journey"]
    },
    "spice_rack": {
        "name": "Spice rack",
        "description": "Writing craft modules",
        "modules": ["writing_style", "language_style", "rhythmic_cadence", "clarity_accessibility"]
    },
    "simmering": {
        "name": "Simmering",
        "description": "Depth and psychology",
        "modules": ["thematic_depth", "reader_emotions", "jungian_analysis",
                     "character_relationships", "dream_symbolism", "immersion"]
    }
}
```

### Step 20.3: Add `recommend` command

Genre-to-module mapping:
```python
GENRE_MODULE_MAP = {
    "literary_fiction": {
        "include": ["summary", "characters", "character_relationships", "three_act_structure",
                     "story_beats", "story_pacing", "writing_style", "language_style",
                     "thematic_depth", "reader_emotions", "immersion", "jungian_analysis",
                     "dream_symbolism", "tags"],
        "skip": ["gag_analysis", "win_loss_wave", "four_weapons", "ai_detector"]
    },
    "thriller": {
        "include": ["summary", "characters", "story_pacing", "plot_twists",
                     "misdirection_surprise", "win_loss_wave", "story_beats",
                     "heros_journey", "reader_emotions", "tags"],
        "skip": ["jungian_analysis", "dream_symbolism", "rhythmic_cadence", "alchemical_symbolism"]
    },
    "fantasy": {
        "include": ["summary", "characters", "character_relationships", "psychogeography",
                     "story_beats", "thematic_depth", "tags", "writing_style",
                     "three_act_structure", "heros_journey"],
        "skip": ["gag_analysis"]
    },
    "nonfiction": {
        "include": ["summary", "tags", "clarity_accessibility", "writing_style",
                     "language_style", "thematic_depth", "critical_review"],
        "skip": ["characters", "character_relationships", "three_act_structure",
                 "story_beats", "heros_journey", "story_pacing", "plot_twists",
                 "misdirection_surprise", "gag_analysis", "four_weapons", "eight_stage"]
    },
    "poetry": {
        "include": ["writing_style", "language_style", "rhythmic_cadence",
                     "thematic_depth", "reader_emotions", "tags", "dream_symbolism"],
        "skip": ["story_beats", "three_act_structure", "plot_holes", "story_pacing",
                 "characters", "character_relationships", "gag_analysis"]
    }
}
```

Input: `{"genre": "literary_fiction"}`
Output: `{"recommended": [...], "skipped": [...], "reason": "..."}`

### Step 20.4: Add `.analysis.json` schema docs to `analysis_writer.py`

Add a docstring comment block at the top of `analysis_writer.py`:
```python
"""
Analysis Writer — writes .analysis.json output files.

OUTPUT SCHEMA:
{
    "module": "summary",
    "version": "1.0",
    "generated": "2026-02-27T15:00:00Z",
    "sourceHash": "a1b2c3d4",
    "model": "claude-sonnet-4-6",
    "result": {
        // Module-specific output — varies per module
        // See each module's .md file for its output format
    }
}
"""
```

### Step 20.5: Verify

```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise && echo '{}' | CLAUDE_PLUGIN_ROOT=. python3 scripts/module_loader.py courses 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'courses' in d else 'FAIL')"
```

---

## Agent B: Atlas Recipe (Task 21)

**Design docs to read first:**
- `atlas-recipe/00-OVERVIEW.md`
- `atlas-recipe/01-ATLAS-RECIPE.md`
- `atlas-recipe/02-UPDATE-ATLAS.md`
- `atlas-recipe/03-ATLAS-SECTIONS.md`
- `LANGUAGE-GUIDE.md` (Atlas section — scan/extract/analyze/synthesize phases)
- `build-plans/AGENT-3-ATLAS.md` (full build spec)

### Task 21: Write `commands/atlas.md` — the most complex skill

**Files:**
- Create: `plugins/chapterwise/commands/atlas.md`

This is the biggest single file in the plugin (~600-800 lines). It's primarily LLM orchestration — no custom Python scripts needed beyond the shared utilities.

**Structure:**
```
---
description/allowed-tools/triggers frontmatter
---

# ChapterWise Atlas

## Overview

## Command Routing
  /atlas → Build a new atlas (interactive)
  /atlas --update → Update existing atlas
  /atlas --name "World Atlas" → Named atlas
  /atlas --rebuild → Full rebuild from scratch
  /atlas --delete → Delete an atlas
  /atlas --list → Show all atlases
  /atlas --add-sections → Add sections to existing atlas

## Step 1: Check for Existing Atlas Recipe
  - Load via recipe_manager.py
  - If found: "This project has a {name} atlas with {N} sections. Update or rebuild?"
  - If --update: jump to Update Pipeline

## Step 2: Scan Project (Pass 0)
  - Read index.codex.yaml to understand project structure
  - Count chapters, check for existing analysis data
  - Propose atlas structure: "I see 28 chapters. Suggested sections:"
  - Use AskUserQuestion to confirm/modify sections

## Step 3: Extract Entities (Pass 1)
  - Process chapters one at a time (context window management)
  - For each chapter: extract characters, locations, events, themes
  - Reuse .analysis.json if available (characters, summary modules)
  - Store entity lists in recipe folder

## Step 4: Analyze Cross-Chapter (Pass 2)
  - Dispatch parallel Task agents per chapter batch
  - Each agent: deep analysis of 5-7 chapters
  - Track relationships, timeline ordering, theme evolution

## Step 5: Synthesize Atlas (Pass 3)
  - Two-stage synthesis for large manuscripts:
    1. Condense: merge entity maps into summaries
    2. Synthesize: write full atlas sections
  - For each section (characters, timeline, themes, etc.):
    Write codex-format output with proper YAML structure

## Step 6: Write Atlas Files
  - Create atlas directory in project
  - Write each section as a codex file
  - Generate atlas index.codex.yaml with children array
  - Register atlas in project's main index.codex.yaml (atlases array)

## Step 7: Save Recipe
  - Save to .chapterwise/atlas-recipe/recipe.yaml
  - Include chapter hashes for future update detection
  - Save entity extraction results for incremental updates

## Update Pipeline (triggered by --update)
  1. Diff: compare chapter content hashes
  2. Re-Extract: only for changed chapters
  3. Re-Analyze: only affected relationships
  4. Merge: combine new + existing entity data
  5. Re-Synthesize: regenerate affected sections
  6. Patch: update atlas files, preserve user edits (source: user)

## Atlas Section Types
  Characters, Timeline, Themes, Plot Structure, Locations,
  Relationships, World (fantasy), Topic Map (nonfiction), Imagery (poetry)

## Context Window Strategy
  - Pass 1: chapter-by-chapter with 500-token overlap
  - Pass 3: condense entity maps → synthesize sections
  - Never load full manuscript into context

## Multi-Atlas Support
  - recipe_manager.py handles atlas-recipe-{name} folders
  - Register in index.codex.yaml atlases array
  - --name flag to specify which atlas

## Validation and Self-Healing
  - Run codex_validator.py on atlas output with `fix: true`
  - Run recipe_validator.py on the atlas recipe folder
  - If cross-section consistency issues are found, patch section files and re-validate

## Error Handling

## Language Rules
  Phase verbs: Scanning, Extracting, Analyzing, Synthesizing, Assembling
  Progress: "Extracting entities... 14 characters, 8 locations across 28 chapters."
  Never say "recipe" to user
```

**Triggers:**
```yaml
triggers:
  - atlas
  - build atlas
  - story atlas
  - character atlas
  - update atlas
  - atlas --update
  - atlas --list
  - chapterwise:atlas
argument-hint: "[--update] [--name 'Atlas Name'] [--rebuild] [--list]"
```

### Step 21.1: Read all atlas design docs (listed above)

### Step 21.2: Write atlas.md

Follow the structure above. Key implementation details:
- All script calls use stdin JSON: `echo '...' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py load`
- Use AskUserQuestion for section selection
- Use Task agents for parallel chapter processing in Pass 2
- Reuse `.analysis.json` data when available (check before re-extracting)
- Two-stage synthesis for manuscripts with >20 chapters
- `source: generated` vs `source: user` tracking for update preservation

### Step 21.3: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/atlas.md && grep -q "\-\-update" plugins/chapterwise/commands/atlas.md && grep -q "Pass 0\|Pass 1\|Pass 2\|Pass 3" plugins/chapterwise/commands/atlas.md && grep -q "codex_validator.py" plugins/chapterwise/commands/atlas.md && grep -q "recipe_validator.py" plugins/chapterwise/commands/atlas.md && ! grep -qi "order up\|bon appetit\|chef.s kiss" plugins/chapterwise/commands/atlas.md && echo PASS
```

---

## Agent C: Reader Recipe (Tasks 22-24)

**Design docs to read first:**
- `reader-recipe/00-OVERVIEW.md`
- `reader-recipe/01-READER-RECIPE.md`
- `reader-recipe/02-READER-ARCHITECTURE.md`
- `reader-recipe/03-READER-TEMPLATES.md`
- `LANGUAGE-GUIDE.md` (Reader section)
- `build-plans/AGENT-4-READER.md` (full build spec)

### Task 22: Write `commands/reader.md`

**Files:**
- Create: `plugins/chapterwise/commands/reader.md`

**Structure (~300-400 lines):**
```
---
description/allowed-tools/triggers frontmatter
---

# ChapterWise Reader

## Overview

## Command Routing
  /reader → Build interactive reader (guided)
  /reader --template minimal → Use specific template
  /reader --template academic → Academic reading experience
  /reader --atlas "Story Atlas" → Build reader for atlas content

## Step 1: Scan Project
  - Read index.codex.yaml
  - Detect content type: manuscript, analysis, atlas, mixed
  - Count chapters, words, sections

## Step 2: Choose Template
  - Present options via AskUserQuestion:
    "What kind of reading experience?"
    [Minimal — clean, fast] [Academic — serif, footnotes, research]
  - If --template flag: skip this step

## Step 3: Configure Reader
  - Title, author, cover color
  - Navigation: sidebar, sequential, or both
  - Theme support: light/dark toggle
  - Search: enable/disable full-text search

## Step 4: Build Reader
  - Copy template files to output directory
  - Parse all codex/markdown content
  - Generate JSON manifest for the JS reader
  - Write HTML pages or single-page app
  - Progress: "Building reader... 28 chapters, 87K words."

## Step 5: Atlas-Specific Rendering
  - Character cards with description, traits, relationships
  - Timeline view (if timeline section exists)
  - Theme section with chapter references
  - Cross-reference links between atlas entries

## Step 6: Save Recipe + Output
  - Save to .chapterwise/reader-recipe/recipe.yaml
  - Report: "Reader built. Open reader/index.html to read."

## Step 7: Validate and Heal
  - Validate generated reader assets and links
  - Run recipe_validator.py on `.chapterwise/reader-recipe/`
  - Auto-fix broken relative paths and missing metadata where possible

## Error Handling

## Language Rules
```

**Triggers:**
```yaml
triggers:
  - reader
  - build reader
  - codex reader
  - reading experience
  - reader --template
  - chapterwise:reader
argument-hint: "[--template minimal|academic] [--atlas 'Atlas Name']"
```

### Step 22.1: Read all reader design docs (listed above)

### Step 22.2: Study existing codex rendering in chapterwise-web

Look at how the web app renders codex content to understand the data structures. Key files:
- `chapterwise-web/app/static/js/index_tree_renderer.js` — JS rendering logic
- `chapterwise-web/app/static/js/codex_content_renderer.js` — Content rendering

### Step 22.3: Write reader.md

Follow the structure above. Key:
- Template files are at `${CLAUDE_PLUGIN_ROOT}/templates/{template-name}/`
- Use `codex_writer.py` JSON parsing for content
- Atlas rendering uses section-type-specific card layouts
- All CSS uses `--codex-*` custom properties for theming

### Step 22.4: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/reader.md && grep -q "atlas" plugins/chapterwise/commands/reader.md && grep -q "template" plugins/chapterwise/commands/reader.md && grep -q "recipe_validator.py" plugins/chapterwise/commands/reader.md && ! grep -qi "order up\|bon appetit" plugins/chapterwise/commands/reader.md && echo PASS
```

---

### Task 23: Build `templates/minimal-reader/`

**Files:**
- Create: `plugins/chapterwise/templates/minimal-reader/index.html`
- Create: `plugins/chapterwise/templates/minimal-reader/style.css`
- Create: `plugins/chapterwise/templates/minimal-reader/reader.js`
- Create: `plugins/chapterwise/templates/minimal-reader/README.md`

The minimal reader is a clean, fast reading experience. Single-page app that loads codex content.

### Step 23.1: Write index.html

HTML shell with:
- `<nav>` sidebar (table of contents from index)
- `<main>` content area
- Theme toggle (light/dark)
- Search input
- `<script src="reader.js">` and `<link href="style.css">`
- Placeholder `{{MANIFEST}}` for build-time injection

### Step 23.2: Write style.css

CSS with `--codex-*` custom properties:
```css
:root {
  --codex-bg: #ffffff;
  --codex-text: #1a1a1a;
  --codex-accent: #2563eb;
  --codex-sidebar-bg: #f8f9fa;
  --codex-font-body: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --codex-font-size: 1.1rem;
  --codex-line-height: 1.75;
  --codex-max-width: 720px;
}

[data-theme="dark"] {
  --codex-bg: #1a1a1a;
  --codex-text: #e5e5e5;
  --codex-sidebar-bg: #0f0f0f;
}
```

Atlas-specific styles:
```css
.codex-character-card { ... }
.codex-timeline-entry { ... }
.codex-theme-section { ... }
```

### Step 23.3: Write reader.js

JavaScript for:
- Parse manifest JSON (chapters, atlas sections)
- Render markdown/codex content
- Sidebar navigation (click to jump)
- Sequential navigation (prev/next)
- Full-text search (basic client-side)
- Theme toggle (persist to localStorage)
- Keyboard navigation (←/→ arrows, /)

### Step 23.4: Verify

```bash
ls plugins/chapterwise/templates/minimal-reader/index.html plugins/chapterwise/templates/minimal-reader/style.css plugins/chapterwise/templates/minimal-reader/reader.js && echo PASS
```

---

### Task 24: Build `templates/academic-reader/`

**Files:**
- Create: `plugins/chapterwise/templates/academic-reader/index.html`
- Create: `plugins/chapterwise/templates/academic-reader/style.css`
- Create: `plugins/chapterwise/templates/academic-reader/reader.js`
- Create: `plugins/chapterwise/templates/academic-reader/README.md`

The academic reader is a serif-first, footnote-aware reading experience designed for literary study.

### Step 24.1: Write files

Same structure as minimal, but with:
- Serif fonts (Georgia, Crimson Text, etc.)
- Footnote/endnote support
- Citation capability
- Wider max-width for annotation margins
- Analysis sidebar (show .analysis.json data alongside text)
- Print-friendly styles

```css
:root {
  --codex-font-body: Georgia, 'Crimson Text', serif;
  --codex-font-size: 1.15rem;
  --codex-line-height: 1.85;
  --codex-max-width: 800px;
  --codex-annotation-width: 240px;
}
```

### Step 24.2: Verify

```bash
ls plugins/chapterwise/templates/academic-reader/index.html plugins/chapterwise/templates/academic-reader/style.css plugins/chapterwise/templates/academic-reader/reader.js && echo PASS
```

---

## Commit (after merging worktrees)

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/reader.md plugins/chapterwise/scripts/module_loader.py plugins/chapterwise/scripts/analysis_writer.py plugins/chapterwise/templates/
git commit -m "feat: analysis, atlas, and reader recipe commands + reader templates

- analysis.md: recipe integration, course system, genre-aware selection
- atlas.md: four-pass pipeline, update system, multi-atlas support
- reader.md: template-based reading experience builder
- module_loader.py: courses + recommend commands
- minimal-reader/: clean single-page reading template
- academic-reader/: serif, footnotes, analysis sidebar template"
```
