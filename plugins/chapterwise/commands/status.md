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

Show the current project's recipe state at a glance. Pure data, no cooking language. Displays what's been imported, analyzed, atlas'd, and built — plus staleness warnings and next-step suggestions.

## Step 1: Detect Project

Look for `index.codex.yaml` in the current directory, then parent directories up to 3 levels.

If not found:
> "No ChapterWise project found in this directory. Run /import to create one."

If found, use that directory as the project root for all subsequent steps.

## Step 2: Gather Recipe State

Discover all recipes in the project:

```bash
echo '{"project_path": "PROJECT_ROOT"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py list
```

For each recipe found, load its full details:

```bash
echo '{"project_path": "PROJECT_ROOT", "type": "TYPE"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py load
```

Build a state map:
- **Import recipe**: source format, chapter count, last import date
- **Analysis recipe**: module count, course coverage, last run date
- **Atlas recipe(s)**: name, section count, entity counts, last update date
- **Reader recipe**: template used, last build date

## Step 3: Gather Project Metadata

Read `index.codex.yaml` for:
- Project title and author
- Chapter count (from children array)
- Atlas count (from atlases array, if present)

Count total words using file metadata or by summing frontmatter word_count fields from chapter files.

## Step 4: Check Staleness

For each recipe, determine freshness:

- **Import**: compare source file hash (if source still exists)
- **Analysis**: check `.analysis.json` sourceHash against current chapter content hashes via `staleness_checker.py`
- **Atlas**: compare chapter_hashes in atlas recipe against current files
- **Reader**: compare project structure against reader manifest

**Status icons:**
- `✓` — complete and fresh
- `⚠` — stale (source chapters changed since last run)
- `✗` — not done / not started
- `◌` — in progress or partial

## Step 5: Display Status

Output the status in this exact format:

```
{Title} — {chapters} chapters, {words} words

  Import     {icon}  {description}
  Analysis   {icon}  {description}
  Atlas      {icon}  {description}
  Reader     {icon}  {description}

  .chapterwise/
    {recipe-folder}/  {file-list-summary}
    ...
```

**Examples:**

Fresh project:
```
The Long Way Home — 28 chapters, 87,234 words

  Import     ✓  Imported 3 days ago (PDF, folders per part)
  Analysis   ✓  18 modules, all fresh
  Atlas      ✓  Story Atlas — 6 sections, 14 characters, 47 events
             ◌  World Atlas — not started
  Reader     ✗  No reader built

  .chapterwise/
    import-recipe/    recipe.yaml, convert.py, structure_map.yaml
    analysis-recipe/  recipe.yaml (18 modules, last run 3 days ago)
    atlas-recipe/     recipe.yaml (Story Atlas, last updated 3 days ago)
```

Stale project:
```
The Long Way Home — 28 chapters, 87,234 words

  Import     ✓  Imported 2 weeks ago
  Analysis   ⚠  5 chapters changed since last analysis
  Atlas      ⚠  Story Atlas is stale — 5 chapters changed
  Reader     ✓  Built 1 week ago (minimal template)

  Tip: Run /atlas --update to refresh the atlas.
```

New project (import only):
```
The Long Way Home — 28 chapters, 87,234 words

  Import     ✓  Imported just now (PDF, flat structure)
  Analysis   ✗  Not started
  Atlas      ✗  Not started
  Reader     ✗  Not started
```

## Step 6: Suggest Next Steps

Based on the state, suggest the next logical action:

| State | Suggestion |
|-------|-----------|
| No import | "Run /import to get started." |
| Import only | "Run /analysis to analyze your chapters." |
| Import + analysis | "Run /atlas to build a reference atlas." |
| Import + analysis + atlas | "Run /reader to create a reading experience." |
| Everything fresh | "All recipes are up to date." |
| Stale analysis | "Run /analysis to refresh {N} changed chapters." |
| Stale atlas | "Run /atlas --update to refresh the atlas." |

Show the suggestion as a `Tip:` line at the bottom of the status output.

## Language Rules

- **No cooking language** in status output — this is a data dashboard
- Use status icons: ✓ ⚠ ✗ ◌
- Show the `.chapterwise/` file tree for transparency
- Keep descriptions concise: one line per recipe
- Time formatting: "just now", "3 days ago", "2 weeks ago", "last month"
- Never say "recipe" in the user-facing output — describe what was done, not the mechanism
