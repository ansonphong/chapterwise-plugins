# Phase 5: Cross-Cutting Commands — Tasks 31-32

> **Reference:** `00-OVERVIEW.md` (cross-cutting commands section), `LANGUAGE-GUIDE.md` (Status Command + Pipeline Command sections)

These two commands tie the four recipes together. `/status` shows the project's recipe state at a glance. `/pipeline` runs the full chain (Import → Analysis → Atlas → Reader).

---

## Task 31: Write `commands/status.md`

**Files:**
- Create: `plugins/chapterwise/commands/status.md`

### Step 31.1: Read design references

Read the `/status` sections in:
- `LANGUAGE-GUIDE.md` — exact output format and examples
- `00-OVERVIEW.md` — purpose and behavior

### Step 31.2: Write status.md

**Structure (~100-150 lines):**

```markdown
---
description: "Show ChapterWise project status — recipes, analysis, atlases, reader state"
allowed-tools: Read, Grep, Glob, Bash
triggers:
  - status
  - chapterwise status
  - project status
  - chapterwise:status
---

# ChapterWise Status

## Overview
Show the current project's recipe state at a glance. Pure data — no cooking language.

## Step 1: Detect Project
  - Look for index.codex.yaml in current directory (or parent directories)
  - If not found: "No ChapterWise project found. Run /import to create one."

## Step 2: Gather Recipe State
  - Use recipe_manager.py list to discover all recipes:
    echo '{"project_path":"."}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py list
  - For each recipe found, load its details:
    echo '{"project_path":".","type":"import"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py load

## Step 3: Gather Project Metadata
  - Read index.codex.yaml for title, chapter count
  - Run word_count.py for total word count
  - Check for atlases array in index.codex.yaml

## Step 4: Check Staleness
  - For each recipe, check if source chapters have changed since last run
  - Mark as: ✓ (fresh), ⚠ (stale — chapters changed), ✗ (not done)
  - Include validator health: ✓ (clean), ⚠ (auto-fixed), ✗ (validation failed)

## Step 5: Display Status

Output format (from Language Guide):
```
{Title} — {chapters} chapters, {words} words

  Import     ✓  Imported {time_ago} ({format}, {structure})
  Analysis   ✓  {N} modules, all fresh
  Atlas      ✓  {atlas_name} — {N} sections, {characters} characters, {events} events
             ◌  {other_atlas} — not started
  Reader     ✗  No reader built

  .chapterwise/
    import-recipe/    recipe.yaml, convert.py, structure_map.yaml
    analysis-recipe/  recipe.yaml ({N} modules, last run {time_ago})
    atlas-recipe/     recipe.yaml ({atlas_name}, last updated {time_ago})
```

If chapters have changed:
```
  Analysis   ⚠  {N} chapters changed since last analysis
  Atlas      ⚠  {atlas_name} is stale — {N} chapters changed

  Tip: Run /atlas --update to refresh the atlas.
```

## Step 6: Suggest Next Steps
  - If no import: "Run /import to get started."
  - If import but no analysis: "Run /analysis to analyze your chapters."
  - If analysis but no atlas: "Run /atlas to build a reference atlas."
  - If atlas but no reader: "Run /reader to create a reading experience."
  - If all done and stale: "Run /atlas --update to refresh."

## Language Rules
  - No cooking language in status output — pure data display
  - Use symbols: ✓ ⚠ ✗ ◌
  - Show file tree of .chapterwise/ directory
  - One-line tips at the bottom
```

### Step 31.3: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/status.md && grep -q "recipe_manager" plugins/chapterwise/commands/status.md && ! grep -qi "order up\|bon appetit\|chef.s kiss" plugins/chapterwise/commands/status.md && echo PASS
```

---

## Task 32: Write `commands/pipeline.md`

**Files:**
- Create: `plugins/chapterwise/commands/pipeline.md`

### Step 32.1: Read design references

Read the `/pipeline` sections in:
- `LANGUAGE-GUIDE.md` — exact output format and step-by-step messaging
- `00-OVERVIEW.md` — purpose and behavior

### Step 32.2: Write pipeline.md

**Structure (~150-200 lines):**

```markdown
---
description: "Run the full ChapterWise pipeline — Import → Analysis → Atlas → Reader"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - pipeline
  - full pipeline
  - import analyze atlas reader
  - chapterwise:pipeline
argument-hint: "[source-file] [--skip-reader] [--skip-atlas]"
---

# ChapterWise Pipeline

## Overview
Run the full transformation chain with sensible defaults. One command to go from manuscript to complete ChapterWise project with analysis, atlas, and reader.

## Step 0: Parse Arguments
  - Source file/path from argument (required for first run)
  - --skip-reader: stop after atlas
  - --skip-atlas: stop after analysis
  - If no source and import recipe exists: use existing project

## Step 1: Import (calls import.md workflow)
  - Check for existing import recipe
  - If exists and source unchanged: "Import is fresh. Skipping."
  - If exists and source changed: "Source changed. Re-importing."
  - If new: run full import interview (abbreviated — use defaults where possible)
  - Progress: "Step 1/4: Import"
  - Post-step gate: run import validators (`codex_validator.py`, `recipe_validator.py`)

## Step 2: Analysis (calls analysis.md workflow)
  - Auto-detect genre from imported content
  - Use recommended modules (no interactive course picker — use defaults)
  - Progress: "Step 2/4: Analysis"
  - Progress: "{N} modules selected for {genre}."
  - Post-step gate: run `recipe_validator.py` on `.chapterwise/analysis-recipe/`

## Step 3: Atlas (calls atlas.md workflow)
  - Build default atlas (Story Atlas for fiction, Reference Atlas for nonfiction)
  - Use default sections based on genre
  - Progress: "Step 3/4: Atlas"
  - If --skip-atlas: skip this step, report "Skipping atlas."
  - Post-step gate: run atlas validators (`codex_validator.py`, `recipe_validator.py`)

## Step 4: Reader (calls reader.md workflow)
  - Build minimal reader by default
  - Progress: "Step 4/4: Reader"
  - If --skip-reader: skip this step, report "Skipping reader."
  - Post-step gate: validate reader output and run `recipe_validator.py` on `.chapterwise/reader-recipe/`

## Step 5: Summary
  - Report final state using /status output format
  - "Pipeline complete."
  - "{N} files created. Open reader/index.html to read."
  - Include validation summary: zero issues / auto-fixes applied / manual fixes needed

## Pipeline Defaults
  The pipeline uses sensible defaults to minimize interaction:
  - Import: flat structure, markdown format
  - Analysis: genre-recommended modules
  - Atlas: Story Atlas with all suggested sections
  - Reader: minimal template

## Error Handling
  - If any step fails: report the failure, ask if user wants to continue
  - Partial results are kept — user can re-run /pipeline to resume
  - Each step checks for existing recipe — skip if fresh

## Language Rules
  - Use "Step N/4: {name}" headers
  - Per-step progress follows each recipe's language rules
  - Final summary is data-oriented (like /status)
```

### Step 32.3: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/pipeline.md && grep -q "Step 1\|Step 2\|Step 3\|Step 4" plugins/chapterwise/commands/pipeline.md && ! grep -qi "order up\|bon appetit" plugins/chapterwise/commands/pipeline.md && echo PASS
```

---

## Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise/commands/status.md plugins/chapterwise/commands/pipeline.md
git commit -m "feat: /status and /pipeline cross-cutting commands

- status.md: project recipe state dashboard with staleness detection
- pipeline.md: full Import → Analysis → Atlas → Reader chain with defaults"
```
