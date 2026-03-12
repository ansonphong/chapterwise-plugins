# 02 — The Recipe System

## Core Concept

The recipe is the agent's memory of how to import a specific manuscript. It's a self-contained folder with everything needed to re-run the import — no agent reasoning required on subsequent runs.

The user never sees the word "recipe" unless they go looking. To them, re-imports are just faster because the agent already knows what to do.

## Recipe Folder Structure

Saved to `.chapterwise/import-recipe/` inside the output project directory.

```
.chapterwise/import-recipe/
├── recipe.yaml            # Manifest: source info, strategy, user preferences
├── convert.py             # The custom converter script for this manuscript
├── structure_map.yaml     # Discovered structure: chapters, sections, types
├── preferences.yaml       # Writer's answers from the interview
├── run.sh                 # One-command re-run script
└── log.md                 # What the agent did, decisions it made, why
```

## recipe.yaml — The Manifest

```yaml
# Recipe manifest — describes the full import strategy
type: import
version: "1.0"
created: "2026-02-27T14:30:00Z"
updated: "2026-02-27T14:30:00Z"

source:
  path: "/Users/writer/Documents/my-novel.pdf"
  format: pdf
  size_bytes: 2_450_000
  page_count: 342
  word_count: 87_000
  hash: "a1b2c3d4"   # For detecting if source changed

manuscript:
  title: "The Long Way Home"
  author: "Jane Smith"
  type: literary_fiction
  structure: three_act
  chapter_count: 28
  has_prologue: true
  has_epilogue: true
  has_parts: true
  part_count: 3

strategy:
  base_pattern: "pdf_converter.py"
  custom_script: "convert.py"     # The generated/adapted script
  chapter_detection:
    method: "heading_pattern"
    pattern: "^Chapter [IVXLC]+"
    part_pattern: "^Part [IVXLC]+"
    special_sections:
      - name: "Prologue"
        type: section
      - name: "Epilogue"
        type: section
      - name: "Dedication"
        target: metadata           # Goes to project metadata, not a file
      - name: "About the Author"
        target: metadata

preferences:
  output_format: markdown          # markdown or codex
  structure: folders_per_part      # flat, folders_per_part, folders_per_act
  preserve_source_metadata: true   # Keep Scrivener labels, Ulysses keywords, etc.
  include_front_matter: false      # Dedication, copyright, etc. as files
  include_back_matter: false       # Author bio, acknowledgements as files

output:
  directory: "./my-novel/"
  file_count: 31
  index_file: "index.codex.yaml"
```

## structure_map.yaml — What the Agent Found

Captures the discovered manuscript structure in detail. This is the agent's "map" of the content.

```yaml
# Structure map — the agent's understanding of this manuscript
parts:
  - name: "Part I: Departure"
    starts_at_page: 5
    chapters:
      - name: "Chapter I"
        title: "The Awakening"
        starts_at_page: 7
        word_count: 3_200
        type: chapter
      - name: "Chapter II"
        title: "The Call"
        starts_at_page: 18
        word_count: 2_800
        type: chapter
      # ...

  - name: "Part II: Initiation"
    starts_at_page: 120
    chapters: [...]

  - name: "Part III: Return"
    starts_at_page: 248
    chapters: [...]

special_sections:
  - name: "Prologue"
    position: before_part_1
    starts_at_page: 1
    word_count: 1_500
    type: section

  - name: "Epilogue"
    position: after_part_3
    starts_at_page: 330
    word_count: 2_100
    type: section

metadata_sections:
  - name: "Dedication"
    page: iv
  - name: "About the Author"
    page: 340

detection_confidence: 0.95
detection_notes: "Clean chapter headings. Roman numerals throughout. Parts clearly marked."
```

## preferences.yaml — Writer's Choices

Saved separately so the agent can apply preferences across projects.

```yaml
# Writer preferences (from interview)
preferred_format: markdown
preferred_structure: folders_per_part
preserve_source_metadata: true
include_front_matter: false
include_back_matter: false

# Source-app-specific
scrivener:
  preserve_labels: true
  preserve_status: true
  preserve_keywords_as_tags: true
  preserve_compile_settings: false

ulysses:
  preserve_keywords: true
  preserve_writing_goals: true
  preserve_groups_as_folders: true
```

## run.sh — The Re-run Script

A simple bash script that re-executes the recipe without agent involvement.

```bash
#!/bin/bash
# Auto-generated re-run script for "The Long Way Home"
# Created: 2026-02-27
# Source: /Users/writer/Documents/my-novel.pdf
#
# Usage: ./run.sh [optional-new-source-file]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="${1:-/Users/writer/Documents/my-novel.pdf}"
OUTPUT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Re-importing from: $SOURCE"
echo "Output to: $OUTPUT_DIR"

python3 "$SCRIPT_DIR/convert.py" "$SOURCE" "$OUTPUT_DIR"

echo "Done. $OUTPUT_DIR is ready."
```

## log.md — Decision Log

Human-readable record of what the agent did and why. Useful for debugging or understanding the import later.

```markdown
# Import Log: The Long Way Home

**Source:** my-novel.pdf (342 pages, ~87,000 words)
**Date:** 2026-02-27 14:30 UTC
**Agent:** Claude (claude-opus-4-6)

## Decisions

### Format Detection
- Identified as PDF via file extension and magic bytes
- Selected `pdf_converter.py` as base pattern

### Structure Analysis
- Sampled pages 1-5, 170-175, 335-342
- Found Roman numeral chapter headings (Chapter I through Chapter XXVIII)
- Found Part markers (Part I, Part II, Part III)
- Found Prologue (page 1) and Epilogue (page 330)
- Found non-content pages: Dedication (page iv), About the Author (page 340)
- Confidence: 95%

### Writer Interview
- Writer chose: folder structure per part
- Writer chose: Markdown (Codex Lite) format
- Writer chose: exclude front/back matter as files

### Conversion
- Generated custom `convert.py` from `pdf_converter.py` pattern
- Split on heading patterns: `^Part [IVXLC]+` and `^Chapter [IVXLC]+`
- Created 31 content files (28 chapters + prologue + epilogue + 1 part-level overview)
- Generated `index.codex.yaml` with full hierarchy
- Total word count: 87,234

### Post-Processing
- Assigned types: chapter (28), section (2), overview (1)
- Generated summaries from first paragraph of each chapter
- Extracted tags from content
- Word counts populated per file
```

## The `.chapterwise/` Directory — All Recipes Coexist

All recipe artifacts live under `.chapterwise/` in the project root. Each recipe gets its own subfolder:

```
my-novel/
├── index.codex.yaml
├── chapters/
│   └── ...
├── atlas/                          # Atlas output (Codex project)
│   ├── index.codex.yaml
│   └── ...
└── .chapterwise/
    ├── settings.json               # Project-level settings
    ├── import-recipe/              # How this manuscript was imported
    │   ├── recipe.yaml
    │   ├── convert.py
    │   ├── structure_map.yaml
    │   ├── preferences.yaml
    │   ├── run.sh
    │   └── log.md
    ├── atlas-recipe/               # How the atlas was generated
    │   └── recipe.yaml             # Pass status, entity map, chapter hashes
    ├── atlas-recipe-world/         # Second atlas (custom name)
    │   └── recipe.yaml
    ├── analysis-recipe/            # Analysis module selections and results
    │   └── recipe.yaml
    └── reader-recipe/              # Reader build configuration
        └── recipe.yaml
```

**Naming convention:** The default atlas recipe folder is `atlas-recipe/`. When a project has multiple atlases, each gets a named folder: `atlas-recipe-{name}/` (e.g., `atlas-recipe-world/`, `atlas-recipe-characters/`).

**Discovery:** The agent scans `.chapterwise/` for `*/recipe.yaml` files to discover all existing recipes. Each recipe has a `type` field (`import`, `atlas`, `analysis`, `reader`) so the agent knows what it is.

**Independence:** Each recipe is self-contained. Deleting one doesn't affect the others. The atlas recipe references the import recipe's output (the manuscript chapters), but doesn't depend on the import recipe folder itself.

---

## Self-Validation and Self-Healing

Every recipe is self-correcting. After execution, the agent validates its own output and fixes issues automatically. The user never sees broken output.

### Validation Pipeline

After every recipe execution (import, analysis, atlas, reader), the agent runs a validation pass:

1. **Schema validation** — `recipe_manager.py validate` checks recipe.yaml against `schemas/recipe.schema.yaml`
2. **Output validation** — Each recipe type has specific validators:
   - **Import**: Verify all files referenced in `index.codex.yaml` exist on disk; verify frontmatter is valid YAML; verify word counts are populated; verify no empty chapter files
   - **Analysis**: Verify `.analysis.json` files are valid JSON with required fields (`module`, `version`, `sourceHash`, `result`); verify sourceHash matches current chapter content
   - **Atlas**: Verify atlas `index.codex.yaml` has `type: atlas`; verify all sections referenced in index exist; verify entity names are consistent across sections; verify chapter references point to real chapters
   - **Reader**: Verify `index.html` exists and is valid HTML; verify all CSS/JS files referenced exist; verify TOC data matches project structure
3. **Codex format validation** — Run codex format checker on all generated `.codex.yaml` and `.md` files:
   - Required frontmatter fields present (`type`, `name`)
   - UUIDs are valid and unique
   - Parent-child relationships are consistent
   - No orphan files (in directory but not in index)
   - No phantom files (in index but not on disk)
4. **Cross-recipe consistency** — When multiple recipes exist:
   - Import recipe's chapter count matches analysis recipe's chapter count
   - Atlas recipe's chapter_hashes match current chapter files
   - Reader recipe's project structure matches current project

### Self-Healing Actions

When validation finds issues, the agent fixes them automatically:

| Issue | Auto-Fix |
|-------|----------|
| Missing frontmatter field | Add with sensible default |
| Empty word count | Recalculate from content |
| Orphan file (not in index) | Add to index at correct position |
| Phantom file (in index, missing on disk) | Remove from index, warn user |
| Invalid UUID | Regenerate with `generate_id()` |
| Stale analysis hash | Mark for re-analysis |
| Broken chapter reference in atlas | Update reference or remove with warning |
| Malformed YAML frontmatter | Attempt repair; if unrecoverable, flag for user |

### Validation Triggers

- **After every recipe execution** — Automatic, silent unless issues found
- **On re-import** — Validate existing project before merging changes
- **On `/status`** — Show validation state for each recipe
- **On demand** — Agent can run validation independently: "Validate this project"

### Implementation

Add to `scripts/`:
- **`codex_validator.py`** — Validates .codex.yaml and .md files against format rules
  - Input: `{"path": "./project/", "fix": true}` via stdin JSON
  - Output: `{"valid": true, "issues": [], "fixes_applied": []}` via stdout JSON
  - When `fix: true`, automatically repairs what it can
- **`recipe_validator.py`** — Validates recipe.yaml + referenced files
  - Input: `{"recipe_path": ".chapterwise/import-recipe/"}` via stdin JSON
  - Output: `{"valid": true, "issues": [], "cross_recipe_issues": []}` via stdout JSON

These scripts are called by every command's post-execution validation step. The command .md files include a "Validate" step after the main execution.

---

## Recipe Lifecycle

### Creation (First Import)
1. Agent analyzes source, interviews writer
2. Agent generates all recipe artifacts
3. Agent runs the recipe to produce the Chapterwise project
4. Recipe folder saved to `.chapterwise/import-recipe/`

### Reuse (Subsequent Imports)
1. Agent finds `.chapterwise/import-recipe/recipe.yaml`
2. Agent checks: has the source file changed? (hash comparison)
3. If unchanged: "Your import is already up to date."
4. If changed: Agent runs `run.sh` or `convert.py` with the new source
5. Output updated in place (new/changed chapters updated, structure preserved)

### Evolution (Structure Changed)
1. Agent runs recipe but detects mismatches (new chapters, different structure)
2. Agent reports: "Your manuscript structure has changed — I found 30 chapters now instead of 28."
3. Agent offers to patch the recipe or rebuild from scratch
4. Updated recipe saved

### Cross-Project Preferences
The `preferences.yaml` captures writer-level choices that can be applied to future projects. If a writer always wants Markdown format with folder structure, the agent can read preferences from a previous recipe and offer them as defaults for a new import.

## Safety Guardrails for Generated Scripts

The `convert.py` is generated by the agent — potentially from scratch for unknown formats. Safety rules:

1. **Read-only on source** — Scripts never modify the original manuscript file
2. **Write only to output directory** — All output goes to the designated project folder
3. **No network access** — Conversion scripts are local-only, no API calls
4. **No system commands** — Scripts use Python libraries, not shell commands
5. **Agent reviews before running** — For on-the-fly generated scripts, the agent explains what it will do before executing
6. **Backup on re-import** — Before overwriting existing files during re-import, the recipe creates a `.backups/` snapshot
