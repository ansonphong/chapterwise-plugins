# ChapterWise Recipe System — Design Overview

**Date:** 2026-02-27
**Status:** Design Phase
**Plugin:** `chapterwise` (unified plugin, houses all four recipes)

## What It Is

A Claude Code plugin built around four recipes that transform manuscripts into ChapterWise-native projects, deeply analyzed content, comprehensive reference atlases, and custom reading experiences.

The agent acts as the chef. It analyzes your content, builds custom strategies (recipes), executes them, and saves them for reuse. A writer hands the agent a PDF, DOCX, Scrivener project, Ulysses export, or a folder of markdown, and the agent handles everything.

## The Recipe Metaphor (Internal Concept)

The user never sees the word "recipe." They just say "import this." But internally, the system is built around a cooking metaphor:

- **The recipe** = instructions for how to convert *this specific* manuscript
- **The ingredients** = the user's PDF, DOCX, Scrivener project, etc.
- **The kitchen tools** = bundled Python pattern scripts (PyMuPDF, python-docx, etc.)
- **The chef** = the AI agent

First import: the chef tastes the ingredients, interviews the client about preferences, writes a custom recipe, cooks, and plates. Then keeps the recipe card in the drawer.

Subsequent imports: the chef pulls out the recipe card and just cooks. Fast. No re-analysis.

The recipe is **agent memory** — a folder of artifacts (Python scripts, manifests, structure maps) that lets the agent remember how to handle this manuscript without re-discovering everything from scratch.

## Why This Matters

1. **First-impression wow factor** — "I gave it my PDF and it built me an entire writing project." No other writing tool does this, especially not with a local agent using your own API key.
2. **Agentic, not rigid** — Unlike the web app's `import_orchestrator.py` (3,139 lines of fixed pipeline), this system reasons about the import. It adapts to any format, any structure.
3. **Own your code, own your data** — Everything outputs to open formats (Markdown, YAML) in a git repo. No lock-in. The agent builds tools for you, not dependencies on us.
4. **Reusable** — The recipe folder means re-imports are instant. Keep writing in Scrivener, periodically re-import to get fresh analysis.
5. **Extensible** — Unknown format? The agent studies the existing patterns and writes a new converter on the fly.

## Four Recipes, Four Transformations

The plugin produces four distinct recipe types, each transforming the manuscript in a different way:

1. **Import Recipe** — Your manuscript is now structured codex data (Markdown/YAML, git-ready)
2. **Analysis Recipe** — Your manuscript is now deeply understood (intelligent module selection)
3. **Atlas Recipe** — Your manuscript is now a complete reference atlas (characters, timeline, themes, locations — synthesized across chapters, incrementally updatable)
4. **Reader Recipe** — Your manuscript is now a custom reading experience (standalone HTML/CSS/JS)

Plus two cross-cutting commands:
- **`/status`** — Show what recipes exist for this project and their state
- **`/pipeline`** — Run the full chain: Import → Analysis → Atlas → Reader

Each recipe is disposable, saveable, and re-runnable. The agent builds custom programs tailored to your specific content, not generic pipelines.

The recipes also chain together naturally:
```
Import → Analysis → Atlas → Reader
   ↓         ↓         ↓        ↓
  Codex    .json     Atlas    HTML/CSS
 project   results   (Codex)   reader
```

Import creates the project. Analysis produces per-chapter insights. Atlas synthesizes those insights into a cross-chapter reference. Reader builds a styled browsing experience for any of them — including the atlas itself.

## Quality Contract: Self-Validate, Then Report

Every recipe follows the same completion rule:
- Run validators before reporting success
- Auto-fix safe issues (self-healing)
- Surface only unresolved issues to the user with exact files/causes

Core validator scripts are shared across the system: `codex_validator.py` and `recipe_validator.py`.

## Relationship to Existing Systems

### Replaces / Consolidates
- `chapterwise-codex` plugin's `/import` command (folder import wizard)
- `chapterwise-codex` plugin's `/import-scrivener` command
- Associated Python scripts: `scrivener_import.py`, `scrivener_parser.py`, `scrivener_file_writer.py`, `rtf_converter.py`

All three plugins (`chapterwise`, `chapterwise-codex`, `chapterwise-analysis`) merge into a single unified `chapterwise` plugin (v2.0.0). See `01-PLUGIN-STRUCTURE.md` for the full layout.

### Reference Implementation
- `chapterwise-web/app/services/import_orchestrator.py` — The web app's import pipeline is the reference for what a converter needs to do (detect format, convert to intermediate, detect chapters, build codex). But the agent approach is fundamentally different: it's adaptive, not rigid.
- `chapterwise-web/app/utils/converters/` — The web app's 9 format converters provide implementation patterns the agent can learn from.

## Design Documents

### Top Level (Shared)
| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | This document. Big picture, philosophy, and document map. |
| `01-PLUGIN-STRUCTURE.md` | File layout, plugin.json, command definitions |
| `02-RECIPE-SYSTEM.md` | How recipes work: creation, storage, reuse, evolution |
| `10-DOCS-AND-THREE-PATHS.md` | Get Started page redesign: Cloud, Agentic, and CLI paths |
| `LANGUAGE-GUIDE.md` | **Single source of truth** for all user-facing language, cooking phases, verbs, and rules |

### Import Recipe (`import-recipe/`)
| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | Import recipe concept, key behaviors |
| `01-AGENT-WORKFLOW.md` | Step-by-step: check previous → scan → interview → plan → prep → convert → review → save |
| `02-PATTERN-SCRIPTS.md` | Bundled converter patterns, common utilities, fallback creativity |
| `03-INTERVIEW-AND-PREFERENCES.md` | How the agent interviews writers and remembers preferences |
| `04-OUTPUT-FORMAT.md` | What the final ChapterWise project looks like |
| `05-SUPPORTED-SOURCES.md` | Three tiers of format support, digest mode, format detection |

### Analysis Recipe (`analysis-recipe/`)
| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | Analysis recipe concept, course system, key behaviors |
| `01-ANALYSIS-RECIPE.md` | Full spec: module selection logic, recipe format, execution, re-analysis |

### Atlas Recipe (`atlas-recipe/`)
| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | Atlas recipe concept, Update Atlas, comparison to Analysis Recipe |
| `01-ATLAS-RECIPE.md` | Full spec: four-pass pipeline, multi-atlas support, selective sections, analysis data reuse, context window strategy, git behavior, management commands, atlas types, Codex integration, Reader pipeline |
| `02-UPDATE-ATLAS.md` | Incremental update system: diffing, patching, selective re-synthesis |
| `03-ATLAS-SECTIONS.md` | Section types, output format, atlas registration in index.codex.yaml, multi-atlas rendering, schema extension, style conventions, Reader integration protocol |

### Codex Reader Recipe (`reader-recipe/`)
| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | Reader recipe concept, "Reader not viewer", key behaviors |
| `01-READER-RECIPE.md` | Full spec: three levels, reference mapping, recipe format |
| `02-READER-ARCHITECTURE.md` | How a Codex Reader works: parsing, rendering, navigation, themes |
| `03-READER-TEMPLATES.md` | Template library: minimal, academic, portfolio, interactive fiction, chapbook |

### Build Plans (`build-plans/`)
| Doc | Purpose |
|-----|---------|
| `PHASE-0-SCAFFOLD.md` | Managing Agent: create unified plugin, move files, build shared scripts |
| `AGENT-1-IMPORT.md` | Import Agent: pattern scripts, common utils, import.md skill |
| `AGENT-2-ANALYSIS.md` | Analysis Agent: rewrite analysis.md with recipes, courses, genres |
| `AGENT-3-ATLAS.md` | Atlas Agent: four-pass pipeline, update system, multi-atlas, atlas.md skill |
| `AGENT-4-READER.md` | Reader Agent: reader.md skill, minimal + academic templates |
| `PHASE-2-4-INTEGRATION.md` | Managing Agent: integration tests, migration stubs, final QA |

### Master Plan
| Doc | Purpose |
|-----|---------|
| `IMPLEMENTATION-PLAN.md` | Master execution plan: architecture decision, 5-agent build strategy, phase order, success criteria |
