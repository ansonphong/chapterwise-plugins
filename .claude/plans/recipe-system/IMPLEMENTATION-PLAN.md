# Recipe System — Implementation Plan

**Date:** 2026-02-27
**Status:** Ready for execution
**Target:** Merge all plugins into one `chapterwise` plugin, build all four recipes

---

## Architecture Decision: One Plugin

All existing plugins (`chapterwise`, `chapterwise-codex`, `chapterwise-analysis`) merge into a single `chapterwise` plugin. The four new recipes (Import, Analysis, Atlas, Reader) are added as commands within this unified plugin.

**Why:** Claude Code loads commands individually — having 40+ command files doesn't bloat context. Scripts and patterns are files on disk until called. One install, everything works.

## Final Plugin Structure

```
chapterwise/
├── .claude-plugin/
│   └── plugin.json                    # Unified identity
│
├── commands/                          # ALL skill commands
│   │
│   │ ─── Existing (from chapterwise + chapterwise-codex) ───
│   ├── insert.md                      # Existing: insert content into codex
│   ├── format.md                      # From codex: format codex files
│   ├── format-folder.md               # From codex: batch format
│   ├── format-regen-ids.md            # From codex: regenerate IDs
│   ├── explode.md                     # From codex: split codex into files
│   ├── implode.md                     # From codex: merge files into codex
│   ├── convert-to-codex.md            # From codex: markdown → codex
│   ├── convert-to-markdown.md         # From codex: codex → markdown
│   ├── update-word-count.md           # From codex: word count metadata
│   ├── generate-tags.md               # From codex: auto-tag content
│   ├── lite.md                        # From codex: create codex lite files
│   ├── diagram.md                     # From codex: mermaid diagrams
│   ├── spreadsheet.md                 # From codex: spreadsheet format
│   ├── index.md                       # From codex: index management
│   │
│   │ ─── New: Recipe Commands ───
│   ├── import.md                      # Recipe: unified import (PDF, DOCX, Scrivener, etc.)
│   ├── import-scrivener.md            # Alias: routes to import.md
│   ├── analysis.md                    # Recipe: analysis orchestration (from chapterwise-analysis)
│   ├── atlas.md                       # Recipe: atlas generation + update
│   ├── reader.md                      # Recipe: custom reader builder
│   ├── status.md                      # Cross-cutting: show project recipe state
│   └── pipeline.md                    # Cross-cutting: run full chain Import→Analysis→Atlas→Reader
│
├── modules/                           # Analysis modules (from chapterwise-analysis)
│   ├── _output-format.md              # Shared output format spec
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
├── patterns/                          # Import converter patterns
│   ├── pdf_converter.py
│   ├── docx_converter.py
│   ├── scrivener_converter.py
│   ├── ulysses_converter.py
│   ├── markdown_folder.py
│   ├── html_converter.py
│   ├── plaintext_converter.py
│   └── common/
│       ├── chapter_detector.py
│       ├── codex_writer.py
│       ├── structure_analyzer.py
│       └── frontmatter_builder.py
│
├── scripts/                           # All utility scripts
│   │ ─── Existing (from chapterwise-analysis) ───
│   ├── module_loader.py               # List/load analysis modules
│   ├── staleness_checker.py           # Check if analysis is fresh
│   ├── analysis_writer.py             # Write .analysis.json files
│   │
│   │ ─── Existing (from chapterwise-codex) ───
│   ├── word_count.py                  # Word count utility
│   ├── tag_generator.py               # Tag extraction
│   │
│   │ ─── New: Recipe Scripts ───
│   ├── recipe_manager.py              # Create/load/validate/update recipe folders
│   ├── format_detector.py             # Detect source format
│   ├── run_recipe.py                  # Execute saved recipe (fast re-run)
│   ├── codex_validator.py             # Validate and auto-fix codex files
│   └── recipe_validator.py            # Validate recipe.yaml + cross-recipe consistency
│
├── schemas/
│   └── recipe.schema.yaml             # Recipe manifest validation schema
│
└── templates/                         # Reader recipe templates
    ├── minimal-reader/                # Ships with v2.0.0
    ├── academic-reader/               # Ships with v2.0.0
    ├── portfolio-site/                # Future
    ├── interactive-fiction/            # Future
    ├── book-club/                     # Future
    └── chapbook/                      # Future
```

---

## Build Strategy: 5 Parallel Agents

The build is orchestrated by a **Managing Agent** that coordinates 4 **Recipe Agents** working in parallel. Each recipe agent works in a git worktree for isolation.

```
┌─────────────────────────────────────────────┐
│              MANAGING AGENT                  │
│                                              │
│  Phase 0: Scaffold (shared foundation)       │
│  Phase 1: Dispatch 4 recipe agents           │
│  Phase 2: Integration + cross-recipe testing │
│  Phase 3: Migration (old plugins → stubs)    │
│  Phase 4: Final QA                           │
└──────┬──────┬──────┬──────┬─────────────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
   ┌──────┐┌──────┐┌──────┐┌──────┐
   │IMPORT││ANALYS││ATLAS ││READER│
   │AGENT ││AGENT ││AGENT ││AGENT │
   └──────┘└──────┘└──────┘└──────┘
```

### Why Parallel Works

Each recipe agent builds:
1. One `commands/*.md` skill file
2. Its own scripts/patterns
3. Its own tests

The recipes share the scaffold (plugin.json, recipe_manager.py, format_detector.py) but don't share implementation. Each agent works in a worktree and merges when done.

### Why We Need a Managing Agent

- Builds the shared scaffold FIRST (Phase 0)
- Ensures consistent interfaces between recipes (the `.chapterwise/` folder contract, the `recipe.yaml` schema, the `.analysis.json` format)
- Runs integration tests AFTER all agents merge (Phase 2)
- Handles the migration of old plugins → stubs (Phase 3)

---

## Phase 0: Scaffold (Managing Agent, Sequential)

**Goal:** Create the unified plugin structure with shared infrastructure that all recipe agents depend on.

### Tasks

1. **Create unified plugin directory**
   - Create `chapterwise/` with `.claude-plugin/plugin.json`
   - Merge version to `2.0.0` (signals the unification)

2. **Move existing files**
   - Copy all `chapterwise-codex/commands/*.md` → `chapterwise/commands/`
   - Copy all `chapterwise-analysis/modules/*.md` → `chapterwise/modules/`
   - Copy all `chapterwise-analysis/commands/analysis.md` → (will be rewritten by Analysis Agent)
   - Copy all `chapterwise-analysis/scripts/*.py` → `chapterwise/scripts/`
   - Copy all `chapterwise-codex/scripts/*.py` → `chapterwise/scripts/`
   - Copy existing `chapterwise/commands/insert.md` → stays
   - Update all `${CLAUDE_PLUGIN_ROOT}` paths in scripts (should already be relative)

3. **Build shared scripts**
   - `scripts/recipe_manager.py` — Create/load/validate/discover recipe folders
     - `create_recipe(project_path, recipe_type, name=None) → recipe_path`
     - `load_recipe(project_path, recipe_type, name=None) → dict`
     - `list_recipes(project_path) → [dict]`
     - `validate_recipe(recipe_path) → {valid: bool, errors: []}`
   - `scripts/format_detector.py` — Detect source format from file extension + content sniffing
     - `detect_format(file_path) → {format, confidence, details}`
   - `scripts/run_recipe.py` — Execute a saved recipe's run.sh or convert.py
     - `run_recipe(recipe_path, source_path=None) → {success, output_path, files_changed}`
   - `scripts/codex_validator.py` — Validate codex output files and auto-fix issues
     - `validate_codex(project_path, fix=False) → {valid, issues, fixes_applied}`
   - `scripts/recipe_validator.py` — Validate recipe manifests and cross-recipe consistency
     - `validate_recipe(recipe_path) → {valid, issues, cross_recipe_issues}`

4. **Create schema**
   - `schemas/recipe.schema.yaml` — Shared schema for all recipe.yaml manifests
     - Common fields: `type`, `version`, `created`, `updated`, `source`
     - Type-specific fields under `import`, `analysis`, `atlas`, `reader` keys

5. **Create template directories**
   - `templates/` with placeholder README files for each reader template

6. **Create patterns/common/ directory**
   - `patterns/common/__init__.py` — Package marker
   - These will be populated by the Import Agent

7. **Commit scaffold**

### Output
A working plugin with all existing functionality preserved (codex commands, analysis commands, insert) plus the shared infrastructure for all four recipe agents.

---

## Phase 1: Four Recipe Agents (Parallel)

Each agent gets a worktree, builds its recipe, and merges back.

---

### Agent 1: Import Recipe

**Design docs:** `import-recipe/00-OVERVIEW.md` through `05-SUPPORTED-SOURCES.md`

**Builds:**

| File | Purpose |
|------|---------|
| `commands/import.md` | Main import skill — full workflow instructions |
| `commands/import-scrivener.md` | Alias skill — routes to import.md |
| `patterns/pdf_converter.py` | PDF text extraction via PyMuPDF |
| `patterns/docx_converter.py` | DOCX extraction via python-docx |
| `patterns/scrivener_converter.py` | Scrivener .scriv project conversion |
| `patterns/ulysses_converter.py` | Ulysses .ulyz export conversion |
| `patterns/markdown_folder.py` | Folder of .md/.txt files |
| `patterns/html_converter.py` | HTML parsing via BeautifulSoup |
| `patterns/plaintext_converter.py` | Plain text with heuristic chapter detection |
| `patterns/common/chapter_detector.py` | Shared chapter boundary detection |
| `patterns/common/codex_writer.py` | Write .codex.yaml + index.codex.yaml |
| `patterns/common/structure_analyzer.py` | Analyze document structure |
| `patterns/common/frontmatter_builder.py` | Generate YAML frontmatter |

**The critical file: `commands/import.md`**

This is the brain — ~300-500 lines of markdown instructions that tell Claude:
- How to detect format and check for existing recipe
- How to interview the writer (first import only)
- How to select and run pattern scripts
- How to generate custom converters for unknown formats
- How to save the recipe for reuse
- How to handle re-imports
- Error handling, edge cases, progress messaging (per Language Guide)

**Test plan:**
- Import a plaintext file (simplest path)
- Import a PDF (most common path)
- Re-import the same file (recipe reuse path)
- Import an unknown format (fallback creativity path)

---

### Agent 2: Analysis Recipe

**Design docs:** `analysis-recipe/00-OVERVIEW.md`, `01-ANALYSIS-RECIPE.md`

**Builds:**

| File | Purpose |
|------|---------|
| `commands/analysis.md` | Rewrite of existing analysis.md with recipe system integration |
| `scripts/staleness_checker.py` | Already exists — verify it works with recipe system |
| `scripts/analysis_writer.py` | Already exists — verify output format |
| `scripts/module_loader.py` | Already exists — verify module discovery |

**Key changes to existing `analysis.md`:**
- Add recipe system: save module selections to `.chapterwise/analysis-recipe/recipe.yaml`
- Add "courses" concept: Quick taste / Slow roast / Spice rack / Simmering groupings
- Add genre-aware module selection (auto-pick modules based on manuscript type)
- Add re-analysis detection: "These results are fresh — skip or re-run?"
- Add Language Guide progress messaging
- Preserve ALL existing functionality (direct `/analysis summary file.codex.yaml` still works)

**The critical insight:** This agent rewrites an EXISTING command. It must preserve backward compatibility while adding the recipe layer on top.

**Test plan:**
- Run `/analysis summary` on a codex file (existing path — must still work)
- Run `/analysis` with no args (new interactive picker with courses)
- Run `/analysis --all` (batch with parallel agents)
- Verify `.analysis.json` output format is documented and consistent

---

### Agent 3: Atlas Recipe

**Design docs:** `atlas-recipe/00-OVERVIEW.md` through `03-ATLAS-SECTIONS.md`

**Builds:**

| File | Purpose |
|------|---------|
| `commands/atlas.md` | Atlas skill — four-pass pipeline + update + management |

**This agent builds ONE file — but it's the most complex skill in the system.** The `atlas.md` command must instruct Claude to:

- Run Pass 0: Scan manuscript, propose structure, ask for confirmation
- Run Pass 1: Entity extraction chapter-by-chapter with merge (context window strategy)
- Run Pass 2: Dispatch analysis modules in parallel (reusing existing analysis data)
- Run Pass 3: Two-stage synthesis (condense → synthesize) with parallel synthesizers
- Selective section building (user picks which sections)
- Multiple atlases per project (naming, registration in index.codex.yaml)
- Update Atlas: diff, re-extract, re-analyze, merge, re-synthesize, patch
- Management: `--rebuild`, `--delete`, `--list`, `--add-sections`
- Git behavior: ask before commit, descriptive messages
- All progress messaging per Language Guide

**Dependencies:** This agent needs the analysis scripts (`staleness_checker.py`, `module_loader.py`, `analysis_writer.py`) to be working. These are built in Phase 0 (moved from existing plugin) and refined by Agent 2.

**Test plan:**
- Run `/atlas` on a project with a few chapters
- Run `/atlas --update` after modifying a chapter
- Run `/atlas --name "world"` for multi-atlas
- Run `/atlas --add-sections` to extend existing atlas
- Verify atlas registration in project's `index.codex.yaml`

---

### Agent 4: Reader Recipe

**Design docs:** `reader-recipe/00-OVERVIEW.md` through `03-READER-TEMPLATES.md`

**Builds:**

| File | Purpose |
|------|---------|
| `commands/reader.md` | Reader skill — build custom reading experience |
| `templates/minimal-reader/` | Minimal HTML/CSS reader template |
| `templates/academic-reader/` | Academic-styled reader template |

**Start with two templates** (minimal + academic). The others (portfolio, interactive fiction, book club, chapbook) come later.

**The `commands/reader.md` skill must instruct Claude to:**
- Scan project structure (detect manuscript vs atlas vs both)
- If atlas detected: activate atlas-specific components (character cards, timeline, etc.)
- Choose template or build custom
- Parse codex files into HTML
- Apply theme variables from `--codex-*` system
- Build navigation (table of contents, next/prev, search)
- Save reader recipe for rebuilds
- Progress messaging per Language Guide

**Test plan:**
- Run `/reader` on a codex project (basic path)
- Run `/reader` on an atlas project (atlas-specific rendering)
- Verify the output is valid HTML that opens in a browser

---

## Phase 2: Integration (Managing Agent, Sequential)

After all 4 agents merge their worktrees:

1. **Cross-recipe flow test:** Import → Analysis → Atlas → Reader
   - Import a test manuscript
   - Run analysis on it
   - Build an atlas (should reuse analysis data)
   - Build a reader for the atlas

2. **Recipe discovery test:** Verify `recipe_manager.py list_recipes()` finds all four recipe types

3. **Shared script compatibility:** Ensure all agents' commands call scripts with consistent interfaces

4. **Language Guide compliance check:** Grep all `.md` files for violations (theatrical lines, "recipe" leaks, cooking verbs without data nouns)

5. **plugin.json verification:** Ensure the merged plugin.json is correct

6. **Self-validation gate (required):**
   - Run `codex_validator.py` on generated project output (`fix: false` first, then `fix: true` if needed)
   - Run `recipe_validator.py` on every discovered recipe folder (`import`, `analysis`, `atlas`, `reader`)
   - Release is blocked until validators return clean output

---

## Phase 3: Migration (Managing Agent, Sequential)

1. **Stub old plugins:**
   - `chapterwise-codex/commands/*.md` → Each gets a one-liner: "This command has moved to the `chapterwise` plugin. Use `/command` instead."
   - `chapterwise-analysis/commands/analysis.md` → Same stub
   - Old `plugin.json` files get `"deprecated": true`

2. **Update documentation:**
   - Update any README files referencing old plugin names
   - Update `10-DOCS-AND-THREE-PATHS.md` if needed

3. **Verify backward compatibility:**
   - Unified plugin keeps plain triggers (e.g., `/format`, `/analysis`)
   - Deprecated stubs keep only namespaced triggers (`/chapterwise-codex:*`, `/chapterwise-analysis:*`) and redirect
   - No trigger collisions are allowed between stubs and unified commands

---

## Phase 4: Final QA (Managing Agent)

1. **Full end-to-end test** with a real manuscript
2. **Verify all existing commands still work** (format, explode, implode, etc.)
3. **Verify all new commands work** (import, atlas, analysis with recipes, reader)
4. **Run final validator sweep:** `codex_validator.py` + `recipe_validator.py` across the full project
5. **Clean up:** Remove any duplicate files, fix any path issues

---

## Execution Order Summary

```
Phase 0: Scaffold          ─── Managing Agent ─── 1 session
         │
         ▼
Phase 1: Build recipes     ─── 4 Agents in parallel ─── each in worktree
         │
         ▼
Phase 2: Integration       ─── Managing Agent ─── 1 session
         │
         ▼
Phase 3: Migration         ─── Managing Agent ─── 1 session
         │
         ▼
Phase 4: Final QA          ─── Managing Agent ─── 1 session
```

**Estimated sessions:** 5-6 (Phase 0 + 4 parallel + integration/migration/QA)

---

## What This Plan Does NOT Cover

These are intentionally deferred:

1. **Web app integration** — The Atlas pipeline in `chapterwise-web` (the 14 master plan docs) is a separate project. This plan builds the Claude Code plugin only.
2. **Credit/monetization** — BYOK (bring your own key) only for the plugin. No credit system.
3. **Reader template library** — Only minimal + academic templates. Others come later.
4. **Advanced atlas features** — Relationship web SVG, theme heatmap rendering — these are Reader Recipe enhancements, not core.
5. **CI/CD** — No automated testing pipeline yet.

---

## Remaining Questions (Resolved)

| Question | Resolution |
|----------|-----------|
| One plugin or many? | One: `chapterwise` |
| Where do atlas commands live? | `commands/atlas.md` in the unified plugin |
| `/digest` command? | Alias trigger for `/import` on folders — listed in `import.md` trigger set |
| `.analysis.json` schema? | Defined by existing `analysis_writer.py` — Agent 2 documents it |
| `immersive` atlas type? | Deferred — not in v1, can be added later |
| Concurrent recipe execution? | Not handled in v1 — recipes run sequentially |

---

## Files in This Plan Directory

| File | Purpose |
|------|---------|
| `IMPLEMENTATION-PLAN.md` | **This document** — master execution plan |
| `00-OVERVIEW.md` | Design overview, four recipes, philosophy |
| `01-PLUGIN-STRUCTURE.md` | File layout for the new unified plugin |
| `02-RECIPE-SYSTEM.md` | How recipes work (creation, reuse, evolution) |
| `LANGUAGE-GUIDE.md` | User-facing language rules |
| `import-recipe/*.md` | Import recipe design (6 docs) |
| `analysis-recipe/*.md` | Analysis recipe design (2 docs) |
| `atlas-recipe/*.md` | Atlas recipe design (4 docs) |
| `reader-recipe/*.md` | Reader recipe design (4 docs) |
| `10-DOCS-AND-THREE-PATHS.md` | Documentation redesign |
