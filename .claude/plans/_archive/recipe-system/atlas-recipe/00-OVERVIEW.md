# Atlas Recipe — Overview

## What It Is

The Atlas Recipe is a multi-pass pipeline the agent runs to transform an imported manuscript into a complete **Atlas** — a comprehensive reference document containing character profiles, location maps, timelines, theme analysis, plot structure, and relationship networks. Everything a writer needs to understand their own story at a glance.

Think of it as the agent reading your entire book, then building you a detailed companion guide.

## The Idea

After import (or on any existing ChapterWise project), the agent knows the genre, structure, characters, and themes. The Atlas Recipe uses that knowledge to orchestrate a multi-pass analysis:

- **Pass 0:** Scan the manuscript, propose an atlas folder structure tailored to the content
- **Pass 1:** Extract entities — characters, locations, objects, factions, key events (fast, free)
- **Pass 2:** Deep per-chapter analysis using existing 32+ analysis modules (parallel, paid)
- **Pass 3:** Synthesize cross-chapter insights into cohesive atlas sections and assemble final files

The result: a folder of `.codex.yaml` files committed to the project's git repo, viewable on ChapterWise.app or in VS Code.

## What Makes It Different from Analysis Recipe

The **Analysis Recipe** runs individual modules and gives you per-chapter results — "Chapter 5 has these themes, this writing style, these characters."

The **Atlas Recipe** goes further — it **synthesizes** across chapters. It doesn't just tell you Character A appears in chapters 3, 7, and 12. It builds a full character profile with arc, relationships, evolution, and a timeline of their journey through the story. It cross-references everything.

| | Analysis Recipe | Atlas Recipe |
|---|---|---|
| **Output** | Per-chapter `.analysis.json` | Cross-chapter `.codex.yaml` atlas folder |
| **Scope** | Module results per chapter | Synthesized whole-manuscript understanding |
| **Characters** | Who appears in this chapter | Full profile, arc, relationships across all chapters |
| **Structure** | Story beats per chapter | Three-act map, hero's journey, pacing graph |
| **Reuse** | Re-run changed chapters | **Update Atlas** — incremental diffing |
| **Distribution** | Data files | Browsable, downloadable, publishable |

## The Update Atlas Function

The killer feature: after the initial Atlas generation, you don't rebuild from scratch when your manuscript changes. You run **Update Atlas**, which:

1. Detects which chapters changed (hash comparison)
2. Re-extracts entities only from changed chapters
3. Re-analyzes only changed chapters
4. Re-synthesizes only affected atlas sections
5. Patches the existing atlas in place

Write 10 more chapters? Update Atlas adds them. Rewrite chapter 5? Update Atlas re-profiles affected characters and updates the timeline. Delete a subplot? Update Atlas removes it from the atlas cleanly.

This makes the Atlas a **living document** that evolves with your manuscript.

## Documents in This Directory

| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | This document |
| `01-ATLAS-RECIPE.md` | Full spec: four-pass pipeline, multi-atlas support, selective sections, analysis reuse, context window strategy, git behavior, management commands, recipe format, atlas types |
| `02-UPDATE-ATLAS.md` | Incremental update system: diffing, patching, re-synthesis |
| `03-ATLAS-SECTIONS.md` | Section types, output format, atlas registration in `index.codex.yaml`, multi-atlas rendering, schema extension |

## Core Behaviors

- **Genre-aware**: A literary fiction atlas prioritizes characters and themes. A thriller atlas prioritizes plot structure and pacing. A non-fiction atlas prioritizes topic maps and references.
- **Structure-aware**: Multi-POV novels get per-POV character sections. Non-linear timelines get chronological reconstruction. Ensemble casts get relationship matrices.
- **Incremental**: Update Atlas diffs and patches — never rebuilds from scratch unless asked.
- **Tiered**: Pass 0-1 are free (scanning with agent, entity extraction with Haiku). Pass 2-3 are paid (deep analysis + synthesis).
- **Reuses existing analysis**: If `/analysis` was already run, the atlas reuses fresh `.analysis.json` data instead of re-running modules. Writers never pay twice.
- **Reuses existing modules**: All 32+ analysis modules from `chapterwise-analysis` are orchestrated, not duplicated.
- **Selective sections**: Users choose which atlas sections to build. Start with characters only, add more later. Each section can be added incrementally without rebuilding.
- **Multiple atlases per project**: A project can have multiple named atlases (e.g., "Story Atlas", "World Atlas"). Each is registered in the project's `index.codex.yaml` `atlases` array and displayed separately from manuscript content.
- **Output is native content**: Atlas files live in the project git repo as `.codex.yaml`. Browsable, downloadable, publishable through existing infrastructure. Registered in the project index for renderer discovery.
- **Follows the Language Guide**: Progress messages use `[cooking verb] [technical noun]... [real data]`. See `LANGUAGE-GUIDE.md`.
