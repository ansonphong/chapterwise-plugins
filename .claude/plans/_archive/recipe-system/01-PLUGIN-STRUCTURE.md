# 01 — Plugin Structure (Unified `chapterwise` Plugin)

**Architecture Decision:** All plugins merge into one `chapterwise` plugin.

The previous `chapterwise`, `chapterwise-codex`, and `chapterwise-analysis` plugins are consolidated into a single unified plugin. All four recipe commands (import, analysis, atlas, reader) plus two cross-cutting commands (status, pipeline) live here alongside the existing codex tools.

**Why:** Claude Code loads commands individually — having 40+ command files doesn't bloat context. Scripts and patterns are files on disk until called. One install, everything works.

## File Layout

```
chapterwise/
├── .claude-plugin/
│   └── plugin.json                    # Unified identity (v2.0.0)
│
├── commands/                          # ALL skill commands (~21 files)
│   │
│   │ ─── Core Tools (from chapterwise + chapterwise-codex) ───
│   ├── insert.md                      # Insert content into codex
│   ├── format.md                      # Format codex files
│   ├── format-folder.md               # Batch format all files in folder
│   ├── format-regen-ids.md            # Regenerate all IDs
│   ├── explode.md                     # Split codex into separate files
│   ├── implode.md                     # Merge separate files into one codex
│   ├── convert-to-codex.md            # Markdown → Codex YAML
│   ├── convert-to-markdown.md         # Codex YAML → Markdown (Codex Lite)
│   ├── update-word-count.md           # Update word count metadata
│   ├── generate-tags.md               # Auto-generate tags from content
│   ├── lite.md                        # Create Codex Lite files
│   ├── diagram.md                     # Create Mermaid diagrams
│   ├── spreadsheet.md                 # Create spreadsheets in Codex format
│   ├── index.md                       # Index management
│   │
│   │ ─── Recipe Commands (new) ───
│   ├── import.md                      # Import any manuscript (PDF, DOCX, Scrivener, etc.)
│   ├── import-scrivener.md            # Alias → routes to import.md
│   ├── analysis.md                    # AI analysis with courses + recipes (replaces old)
│   ├── atlas.md                       # Build/update/manage story atlases
│   ├── reader.md                      # Build custom HTML reading experience
│   │
│   │ ─── Cross-Cutting Commands (new) ───
│   ├── status.md                      # Show project recipe state at a glance
│   └── pipeline.md                    # Run full chain: Import → Analysis → Atlas → Reader
│
├── modules/                           # Analysis modules (from chapterwise-analysis, ~31 files)
│   ├── _output-format.md              # Shared output format specification
│   ├── summary.md
│   ├── characters.md
│   ├── character_relationships.md
│   ├── story_beats.md
│   ├── three_act_structure.md
│   ├── heros_journey.md
│   ├── story_pacing.md
│   ├── writing_style.md
│   ├── language_style.md
│   ├── thematic_depth.md
│   ├── reader_emotions.md
│   ├── immersion.md
│   ├── jungian_analysis.md
│   ├── dream_symbolism.md
│   ├── psychogeography.md
│   ├── critical_review.md
│   ├── plot_holes.md
│   ├── plot_twists.md
│   ├── tags.md
│   ├── status.md
│   ├── self_awareness.md
│   ├── misdirection_surprise.md
│   ├── gag_analysis.md
│   ├── clarity_accessibility.md
│   ├── cultural_authenticity.md
│   ├── alchemical_symbolism.md
│   ├── story_strength.md
│   ├── four_weapons.md
│   ├── eight_stage.md
│   ├── rhythmic_cadence.md
│   ├── win_loss_wave.md
│   └── ai_detector.md
│
├── patterns/                          # Import converter patterns (the cookbook)
│   ├── pdf_converter.py               # PyMuPDF-based PDF text extraction
│   ├── docx_converter.py              # python-docx DOCX extraction
│   ├── scrivener_converter.py         # Scrivener .scriv project conversion
│   ├── ulysses_converter.py           # Ulysses .ulyz / exported sheets
│   ├── markdown_folder.py             # Folder of .md/.txt files
│   ├── html_converter.py              # BeautifulSoup HTML parsing
│   ├── plaintext_converter.py         # TXT with heuristic chapter detection
│   └── common/
│       ├── chapter_detector.py        # Shared chapter boundary detection
│       ├── codex_writer.py            # Writes .codex.yaml + index.codex.yaml
│       ├── structure_analyzer.py      # Analyzes doc structure, outputs structure_map
│       └── frontmatter_builder.py     # Generates YAML frontmatter for Codex Lite
│
├── scripts/                           # All utility scripts
│   │ ─── Analysis (from chapterwise-analysis) ───
│   ├── module_loader.py               # List/load/discover analysis modules
│   ├── staleness_checker.py           # Check if analysis results are fresh
│   ├── analysis_writer.py             # Write .analysis.json files
│   │
│   │ ─── Codex Tools (from chapterwise-codex) ───
│   ├── word_count.py                  # Word count utility
│   ├── tag_generator.py               # Tag extraction utility
│   │
│   │ ─── Recipe Infrastructure (new) ───
│   ├── recipe_manager.py              # Create / load / validate / discover recipe folders
│   ├── format_detector.py             # Detect source format from extension + content
│   ├── run_recipe.py                  # Execute a saved recipe (fast re-run path)
│   ├── codex_validator.py             # Validate and auto-fix .codex.yaml + .md files
│   └── recipe_validator.py            # Validate recipe manifests and cross-recipe consistency
│
├── schemas/
│   └── recipe.schema.yaml             # Shared schema for all recipe.yaml manifests
│
└── templates/                         # Reader recipe templates
    ├── minimal-reader/                # Clean, minimal reading experience
    │   ├── index.html
    │   ├── style.css
    │   └── reader.js
    └── academic-reader/               # Serif typography, footnotes, print-friendly
        ├── index.html
        ├── style.css
        └── reader.js
```

## plugin.json

```json
{
  "name": "chapterwise",
  "description": "Complete writing toolkit for ChapterWise — import any manuscript, run AI analysis, build story atlases, create custom readers. Supports PDF, DOCX, Scrivener, Ulysses, Markdown, and more.",
  "version": "2.0.0",
  "homepage": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

## Recipe Commands — Trigger Definitions

### commands/import.md

```yaml
---
description: "Import any manuscript, project, or content folder into a ChapterWise project"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - import
  - import pdf
  - import docx
  - import scrivener
  - import ulysses
  - import manuscript
  - import book
  - import project
  - import folder
  - digest
  - digest folder
  - import novel
argument-hint: "[path/to/file-or-folder]"
---
```

### commands/import-scrivener.md

```yaml
---
description: "Import a Scrivener project (.scriv) into ChapterWise format"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - scrivener import
  - scrivener to codex
  - convert scrivener
  - scriv to markdown
  - import .scriv
  - scrivener project
argument-hint: "[path/to/Project.scriv]"
---
```

### commands/analysis.md

```yaml
---
description: "Run AI analysis on Codex files with intelligent module selection"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - analysis
  - analysis summary
  - analysis characters
  - analysis list
  - analysis help
  - analyze
argument-hint: "[module] [file] [--flags]"
---
```

### commands/atlas.md

```yaml
---
description: "Build a comprehensive atlas — characters, timeline, themes, locations, relationships"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - atlas
  - build atlas
  - generate atlas
  - story atlas
  - character atlas
  - update atlas
argument-hint: "[--update] [--name 'name'] [--rebuild] [--delete] [--list] [--add-sections]"
---
```

### commands/reader.md

```yaml
---
description: "Build a custom reading experience for your manuscript or atlas"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - reader
  - build reader
  - codex reader
argument-hint: "[project-path] [--template name]"
---
```

### commands/status.md

```yaml
---
description: "Show the state of all recipes for this project — what's been imported, analyzed, atlas'd, and built"
allowed-tools: Read, Grep, Glob, Bash
triggers:
  - status
  - project status
  - recipe status
  - chapterwise status
---
```

### commands/pipeline.md

```yaml
---
description: "Run the full chain: Import → Analysis → Atlas → Reader in sequence"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - pipeline
  - run pipeline
  - full pipeline
  - import analyze atlas reader
argument-hint: "[source-file] [--skip-reader]"
---
```

## Layers

### Layer 1: plugin.json — Identity
Minimal. Name, description, version. One plugin, one identity.

### Layer 2: commands/*.md — The Brain
Markdown files with YAML frontmatter. Natural language instructions for Claude. Each command is self-contained — Claude loads only the triggered command, not all of them.

### Layer 3: modules/*.md — Analysis Library
31 analysis modules, each a `.md` file with a system prompt and output format. The analysis and atlas commands reference these by name. Modules are loaded on demand by `module_loader.py`.

### Layer 4: patterns/*.py — The Cookbook
Real, runnable Python scripts for import conversion. Dual purpose:
1. **Tools** — Run directly for common formats
2. **Teaching materials** — The agent reads them to understand converter patterns, then generates custom variants for unusual formats

### Layer 5: scripts/*.py — Infrastructure
Stable utility scripts called by commands:
- Recipe management (create, load, validate, discover)
- Format detection
- Module loading, staleness checking, analysis writing
- Word counting, tag extraction

### Layer 6: templates/ — Reader Templates
HTML/CSS/JS templates for the reader recipe. Each template is a self-contained directory with index.html, style.css, and reader.js.

### Layer 7: schemas/ — Validation
YAML schema for recipe manifests. Used by `recipe_manager.py validate`.

## Dependencies

### Required
- Python 3.8+
- PyYAML (`pip3 install pyyaml`)

### Per-Format (Installed on Demand)
- **PDF**: PyMuPDF (`pip3 install pymupdf`)
- **DOCX**: python-docx (`pip3 install python-docx`)
- **Scrivener RTF**: striprtf (`pip3 install striprtf`)
- **HTML**: BeautifulSoup (`pip3 install beautifulsoup4`)

### Optional (Better Quality)
- pandoc (system install) — better RTF and DOCX conversion
- Calibre (system install) — EPUB and exotic format conversion

The agent checks for dependencies before conversion and tells the user what to install. No silent failures.

## Migration from Old Plugins

### What Moves

| Source Plugin | Files | Destination |
|--------------|-------|-------------|
| `chapterwise/` | `commands/insert.md` | `chapterwise/commands/insert.md` |
| `chapterwise-codex/` | `commands/*.md` (13 files) | `chapterwise/commands/*.md` |
| `chapterwise-codex/` | `scripts/*.py` | `chapterwise/scripts/*.py` |
| `chapterwise-codex/` | `commands/import.md` | REPLACED by recipe import.md |
| `chapterwise-codex/` | `commands/import-scrivener.md` | REPLACED by recipe import-scrivener.md |
| `chapterwise-analysis/` | `modules/*.md` (31 files) | `chapterwise/modules/*.md` |
| `chapterwise-analysis/` | `scripts/*.py` (3 files) | `chapterwise/scripts/*.py` |
| `chapterwise-analysis/` | `commands/analysis.md` | REPLACED by recipe analysis.md |

### Old Plugins Become Stubs

After migration, old plugins get deprecation notices:
- `plugin.json` → `"deprecated": true`
- All commands → one-liner redirecting to the unified plugin

### Backward Compatibility

All plain trigger names are preserved in the unified plugin (`/format`, `/analysis`, etc.). If users invoke old namespaced triggers like `/chapterwise-codex:format` or `/chapterwise-analysis:analysis`, deprecated stubs catch those and redirect.
