# Agent 3: Atlas Recipe — Build Plan

**Agent type:** general-purpose (worktree isolation)
**Design docs:** `atlas-recipe/00-OVERVIEW.md` through `03-ATLAS-SECTIONS.md`
**Language rules:** `LANGUAGE-GUIDE.md` (Atlas Recipe + Atlas Update sections)

---

## What This Agent Builds

| # | File | Lines (est.) | Purpose |
|---|------|-------------|---------|
| 1 | `commands/atlas.md` | 600-800 | Atlas skill — the most complex command in the system |

**One file. But it's the biggest and most complex skill in the entire plugin.** It orchestrates a four-pass pipeline, manages incremental updates, handles multiple atlases per project, and coordinates parallel analysis agents.

---

## Why One File Is Enough

The atlas command doesn't need custom Python scripts because:
- **Pass 1 (entity extraction):** Claude reads chapters directly and extracts entities — no script needed
- **Pass 2 (analysis):** Reuses existing `module_loader.py`, `staleness_checker.py`, `analysis_writer.py`
- **Pass 3 (synthesis):** Claude synthesizes — this IS the LLM's job, no script needed
- **Writing output:** Reuses `codex_writer.py` from import patterns or Claude writes `.codex.yaml` directly
- **Recipe management:** Uses `recipe_manager.py` from Phase 0

The atlas is the most "agentic" recipe — almost entirely LLM reasoning with minimal script support.

---

## Build Order

### Step 1: Understand the existing infrastructure

Before writing, verify these scripts work and understand their APIs:
- `scripts/module_loader.py list` — What modules are available
- `scripts/staleness_checker.py` — How to check if analysis is fresh
- `scripts/analysis_writer.py` — How analysis results are saved
- `scripts/recipe_manager.py` — How to create/load recipes
- `patterns/common/codex_writer.py` — How to write codex files (if built by Import Agent)

### Step 2: Write `commands/atlas.md`

**This is a single, large skill file. Structure it as follows:**

```markdown
---
description: "Build a comprehensive atlas for your manuscript — characters, timeline, themes, locations, relationships"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - atlas
  - build atlas
  - generate atlas
  - story atlas
  - character atlas
  - chapterwise:atlas
argument-hint: "[--update] [--name 'name'] [--rebuild] [--delete] [--list] [--add-sections]"
---

**Migration note:** Deprecated stubs keep only namespaced triggers (for example `chapterwise-analysis:analysis`) to avoid collisions with unified plain triggers like `analysis`.

# ChapterWise Atlas

Build a comprehensive reference atlas from your manuscript — characters, timeline,
themes, plot structure, locations, and relationships — synthesized across all chapters.

## Command Routing

Route based on flags:
- No flags → Build new atlas (or extend existing)
- `--update` → Incremental update
- `--name "name"` → Named atlas
- `--rebuild` → Delete and rebuild
- `--delete` → Delete atlas
- `--list` → Show all atlases
- `--add-sections` → Add sections to existing atlas

---

## BUILD NEW ATLAS

### Step 1: Check Project State
[Find index.codex.yaml — verify this is a codex project]
[Count chapters and total word count]
[Check for existing atlases in index.codex.yaml atlases array]
[If atlas exists: "You have an atlas already. Update it, or build a new one?"]

### Step 2: Pass 0 — Scan and Structure Proposal
[Read 3-5 chapters to detect genre, POV, complexity]
[Detect manuscript type from import recipe if available]
[Propose atlas structure based on content complexity:]

Decision tree:
- < 5 characters → simple (flat files)
- 5-15 characters, no factions → standard (characters, timeline, themes, plot, locations)
- 15+ characters or has factions/magic/world → detailed (folders)

[Present structure with checkboxes for selective building]
[Progress: "Scanning manuscript... {genre}, {N} chapters, {words} words."]

### Step 3: Pass 1 — Entity Extraction
[CONTEXT WINDOW STRATEGY: chapter-by-chapter with merge]

For each chapter:
  1. Read chapter content
  2. Extract: characters mentioned, locations, objects, key events
  3. Note descriptions, traits, roles
  4. Include 500-token overlap from previous chapter

After all chapters:
  1. Deduplicate entities by name similarity
  2. Merge chapter_present lists
  3. Resolve description conflicts (keep most detailed)
  4. Identify protagonist and key relationships

[Use Task subagents for parallel extraction: batch chapters 7 at a time]
[Progress: "Extracting entities... {N} characters, {M} locations, {K} events found."]

### Step 4: Pass 2 — Per-Chapter Analysis
[Check for existing .analysis.json files first!]
[Use staleness_checker.py to verify freshness]

For each chapter without fresh analysis:
  1. Select modules based on atlas type (use module_loader.py recommend)
  2. Dispatch analysis via Task subagents (batch 7 chapters at a time)
  3. Each subagent runs the analysis modules and saves .analysis.json

[Report reuse: "Found existing analysis for {N} of {M} chapters. Re-analyzing {K} changed."]
[Progress: "Analyzing {N} chapters with {M} modules... running in parallel."]

### Step 5: Pass 3 — Synthesis and Assembly
[TWO-STAGE SYNTHESIS for context window management]

Stage 1: Condense per-chapter data
  For each entity type (characters, locations, themes, events):
    - Read all per-chapter analysis results referencing this entity
    - Create a condensed summary (200-500 tokens per entity)
    - Track chapter references

Stage 2: Run synthesizers in parallel
  Each synthesizer is a Task subagent:
  - CharacterSynthesizer: condensed character data → full profiles with arcs
  - TimelineSynthesizer: condensed events + story beats → chronological timeline
  - ThemeSynthesizer: condensed themes → theme analysis with evolution
  - StructureSynthesizer: condensed structure data → plot overview
  - LocationSynthesizer: condensed location data → location profiles
  - RelationshipSynthesizer: condensed relationship data → relationship matrix

Each synthesizer prompt includes:
  - The condensed entity data
  - The entity map from Pass 1
  - The project metadata (title, genre, structure)
  - Instructions for output format (.codex.yaml nodes)

[For 50+ chapters: add meta-synthesizer for cross-section consistency]
[Progress: "Synthesizing character arcs... {N} characters across {M} chapters."]
[Progress: "Building timeline... {N} events mapped."]

### Step 6: Write Atlas Files
[Write each section as a .codex.yaml file per Pass 0 structure]
[Write atlas index.codex.yaml with type: atlas]
[Register atlas in project root index.codex.yaml atlases array]

Atlas index format:
```yaml
type: atlas
name: "{atlas name}"
atlas_type: {story|script|nonfiction|research|poetry}
source_project: "{project name}"
generated: "{ISO 8601}"
generator: "atlas-recipe"

children:
  - type: section
    name: Characters
    src: characters.codex.yaml
  # ... per structure
```

Project index update:
```yaml
atlases:
  - name: "{atlas name}"
    path: {atlas-folder}/
    atlas_type: {type}
    generated: "{ISO 8601}"
    generator: atlas-recipe
    sections: [{list of section slugs}]
```

### Step 7: Git Behavior
[Ask before committing: "Atlas complete — {N} files ready. Commit?"]
[Commit message: "Add atlas: {name} ({N} sections, {N} characters, {N} events)"]
[Never auto-push]

### Step 8: Validate and Heal Atlas Output
[Run codex_validator.py on the atlas output directory with fix=true]
[Validates: atlas index.codex.yaml has type: atlas, all sections exist on disk, UUIDs unique]
[Validates: entity names consistent across sections (character "Elena" not "Elena Vasquez" in one section and "Elena V." in another)]
[Validates: chapter references point to real chapters in the manuscript]
[Auto-fixes: missing UUIDs, missing frontmatter fields, orphan section files]
[Run recipe_validator.py on .chapterwise/atlas-recipe/]
[If issues fixed: "Cleaned up 3 formatting issues in atlas files."]
[If unfixable: "The timeline section references chapter 29 which doesn't exist — review manually."]
[If clean: say nothing]

### Step 9: Save Recipe
[Create .chapterwise/atlas-recipe/recipe.yaml via recipe_manager.py]
[Save chapter hashes for update diffing]
[Save entity map for reuse]
[Progress: "Done. Atlas complete — {N} files, {N} characters, {N} events mapped."]

---

## UPDATE ATLAS (--update)

### Step 1: Load Existing Recipe
[Read .chapterwise/atlas-recipe/recipe.yaml]
[If no recipe: "No atlas found. Run /atlas to build one."]

### Step 2: Diff Chapters
[Hash current chapter content]
[Compare with recipe.source.chapter_hashes]
[Categorize: unchanged, modified, added, removed]
[If no changes: "Your manuscript hasn't changed since the last atlas build."]
[Progress: "Scanning for changes... {N} chapters changed, {M} unchanged."]

### Step 3: Re-Extract Entities (changed chapters only)
[Same as Pass 1 but only on modified + added chapters]
[Merge with existing entity map]
[Progress: "Re-extracting entities from {N} changed chapters..."]

### Step 4: Re-Analyze (changed chapters only)
[Same as Pass 2 but only on modified + added chapters]
[Progress: "Analyzing {N} changed chapters with {M} modules..."]

### Step 5: Determine Re-Synthesis Strategy
[If > 50% chapters changed: full re-synthesis]
[If < 50%: selective — only re-run affected synthesizers]

Affected section mapping:
- Character added/removed/modified → Characters, Relationships
- New chapters → Timeline, Plot Structure
- Location changes → Locations
- Theme shifts → Themes

### Step 6: Re-Synthesize Affected Sections
[Run only affected synthesizers]
[Preserve user edits (source: user nodes)]
[Progress: "Re-synthesizing {N} of {M} atlas sections..."]

### Step 7: Patch Atlas Files
[Update changed sections in place]
[Preserve source: user nodes]
[Update atlas index]
[Update project index (generated timestamp)]
[Commit: "Update atlas: {changes summary}"]

### Step 8: Validate Updated Atlas
[Run codex_validator.py on atlas directory with fix=true — same checks as build]
[Cross-validate: updated sections are consistent with preserved sections]
[Verify: user-edited nodes (source: user) were not corrupted during update]

### Step 9: Update Recipe
[Update chapter_hashes in recipe.yaml]
[Append to updates array]
[Progress: "Done. Atlas updated in {N} seconds."]

---

## MANAGEMENT COMMANDS

### --name "name"
[Set atlas.name and atlas.slug in recipe]
[Create folder at {slug}/ instead of atlas/]
[Recipe folder: .chapterwise/atlas-recipe-{slug}/]

### --rebuild
[Confirm: "This will delete and rebuild. User edits will be lost. Continue?"]
[Delete atlas folder + recipe + index entry]
[Run full build from Step 1]

### --delete
[Confirm: "Delete {name}? {N} files, can't be undone."]
[If multiple atlases: ask which one]
[Delete folder + recipe + remove from index]
[Commit deletion]

### --list
[Read project index.codex.yaml atlases array]
[Show: name, path, type, sections, generated date]

### --add-sections
[Load existing atlas]
[Show available sections not yet built]
[Let user select additional sections]
[Run only new synthesizers, preserve existing sections]

---

## ATLAS SECTION OUTPUT FORMATS

### Characters Section
[Full codex format from 03-ATLAS-SECTIONS.md]
[Include: name, description, role, traits, arc, key moments, relationships, chapter presence]

### Timeline Section
[Chronological events with chapter references]
[Include: event, chapter, characters involved, act, significance]

### Themes Section
[Major themes with chapter presence and evolution]
[Include: name, prominence, chapters, peak intensity, evidence]

### Plot Structure Section
[Three-act breakdown, turning points, pacing]

### Locations Section
[Location profiles with narrative significance]

### Relationships Section
[Relationship pairs with evolution, turning points, types]

---

## LANGUAGE RULES
[Reference LANGUAGE-GUIDE.md]
[Atlas phases: Scan, Extract, Analyze, Synthesize, Assemble]
[Atlas update phases: Diff, Re-extract, Re-analyze, Merge, Re-synthesize, Patch]
[Cooking verbs: extracting, synthesizing, weaving, assembling, merging, patching]
[Always pair with data noun: "Synthesizing character arcs... 14 characters."]
[Never say "recipe" to user]
[Never say "Order up" or theatrical lines]
```

---

## Testing Checklist

- [ ] `/atlas` on a project with 3-5 chapters → builds atlas
- [ ] Atlas `index.codex.yaml` has `type: atlas` and proper structure
- [ ] Project `index.codex.yaml` has `atlases` array with entry
- [ ] `.chapterwise/atlas-recipe/recipe.yaml` created
- [ ] `/atlas --update` after modifying a chapter → incremental update
- [ ] `/atlas --name "world"` → creates named atlas at `world/`
- [ ] `/atlas --list` → shows all atlases
- [ ] `/atlas --add-sections` → extends existing atlas
- [ ] `/atlas --delete` → removes atlas cleanly
- [ ] Analysis reuse: if `/analysis` was run first, atlas skips fresh results
- [ ] Parallel execution: subagents run entity extraction and synthesis in batches
- [ ] Context window: large manuscripts don't exceed limits (chapter-by-chapter strategy)
- [ ] Validation: atlas output passes codex_validator with zero issues
- [ ] Self-healing: remove a UUID from characters.codex.yaml, run validator → UUID regenerated
- [ ] Cross-reference: rename a character in one section, validator flags inconsistency

---

## Dependencies on Phase 0

- `scripts/recipe_manager.py` — recipe creation/loading
- `scripts/module_loader.py` — module discovery and recommendation
- `scripts/staleness_checker.py` — freshness checking
- `scripts/analysis_writer.py` — writing analysis results

## Dependencies on Other Agents

- **Import Agent** creates the codex project structure the atlas reads
- **Analysis Agent** documents `.analysis.json` schema the atlas consumes
- Atlas can work independently if the project already exists and has chapter files

---

## What This Agent Does NOT Build

- Import, analysis, or reader commands
- Python scripts (this is pure LLM orchestration)
- Atlas-specific CSS or rendering (that's the Reader Recipe)
- Web app atlas pipeline (separate project)
