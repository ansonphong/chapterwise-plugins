# Agent 2: Analysis Recipe — Build Plan

**Agent type:** general-purpose (worktree isolation)
**Design docs:** `analysis-recipe/00-OVERVIEW.md`, `01-ANALYSIS-RECIPE.md`
**Language rules:** `LANGUAGE-GUIDE.md` (Analysis Recipe section)
**Existing code:** `chapterwise-analysis/` plugin (commands, modules, scripts)

---

## What This Agent Builds

| # | File | Lines (est.) | Purpose |
|---|------|-------------|---------|
| 1 | `commands/analysis.md` | 350-450 | Rewrite of existing analysis skill with recipe integration |
| 2 | `scripts/staleness_checker.py` | Verify/update | May need minor updates for recipe compatibility |
| 3 | `scripts/analysis_writer.py` | Verify/update | Document output schema |
| 4 | `scripts/module_loader.py` | Verify/update | Ensure it works from new location |

**This agent rewrites ONE command.** The existing `analysis.md` is the starting point, but it gets the recipe layer, course system, and genre-aware selection added on top.

---

## Critical Constraint: Backward Compatibility

The existing `/analysis summary file.codex.yaml` path **must still work exactly as before.** The recipe system is additive — it doesn't break any existing usage.

What stays the same:
- `/analysis summary file.codex.yaml` → runs summary module on file → saves `.analysis.json`
- `/analysis list` → shows available modules
- `/analysis help characters` → shows module details
- `/analysis --all` → batch with parallel agents
- `--force`, `--node`, `--glob`, `--dry-run` flags

What's new:
- `/analysis` (no args) → interactive course picker instead of flat module list
- `/analysis --plan` → genre-aware module selection
- Recipe saved to `.chapterwise/analysis-recipe/recipe.yaml`
- Re-analysis detection: "Fresh results exist — skip or re-run?"
- Course grouping: Quick taste → Slow roast → Spice rack → Simmering
- Language Guide progress messaging

---

## Build Order

### Step 1: Verify existing scripts work from new location

After Phase 0 copies the scripts to `chapterwise/scripts/`, verify:

```bash
# Module discovery
echo '{}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py list

# Staleness check
echo '{"file": "test.codex.yaml", "module": "summary"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/staleness_checker.py

# Analysis writing
echo '{"file": "test.codex.yaml", "module": "summary", "result": {}}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/analysis_writer.py
```

Fix any import path issues.

### Step 2: Document `.analysis.json` output schema

This is a gap identified in the audit. The analysis writer produces JSON but the schema is undocumented. Document it:

```json
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
```

Add this schema documentation as a comment block at the top of `analysis_writer.py`.

### Step 3: Add course groupings to module_loader.py

Update `module_loader.py` to support a `courses` command:

```bash
echo '{}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py courses
```

Output:
```json
{
  "courses": {
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
      "modules": ["thematic_depth", "reader_emotions", "jungian_analysis", "character_relationships", "dream_symbolism", "immersion"]
    }
  }
}
```

The course groupings are hardcoded in `module_loader.py` (not in individual module files) for simplicity.

### Step 4: Add genre-aware module selection

Add a `recommend` command to `module_loader.py`:

```bash
echo '{"genre": "literary_fiction"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py recommend
```

Output:
```json
{
  "recommended": ["summary", "characters", "character_relationships", "three_act_structure", "story_beats", "story_pacing", "writing_style", "thematic_depth", "reader_emotions", "immersion", "jungian_analysis", "tags"],
  "skipped": ["gag_analysis", "win_loss_wave", "four_weapons", "ai_detector"],
  "reason": "Literary fiction emphasizes character depth, thematic analysis, and writing craft."
}
```

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

### Step 5: Rewrite `commands/analysis.md`

**Structure of the rewritten analysis.md:**

```markdown
---
description: "Run AI analysis on Codex files with intelligent module selection"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - analysis
  - analysis summary
  - analysis characters
  - analysis list
  - analysis help
  - chapterwise:analysis
argument-hint: "[module] [file] [--flags]"
---

**Migration note:** Deprecated stubs keep only namespaced triggers (for example `chapterwise-analysis:analysis`) to avoid collisions with unified plain triggers like `analysis`.

# ChapterWise Analysis

## Overview
[What this does — per-chapter AI analysis with 31 modules]

## Command Routing

### `/analysis` (no args) — Interactive Course Picker
1. Check for existing analysis recipe
2. If recipe exists: "You analyzed this before with {N} modules. Run again, or adjust?"
3. If no recipe: detect genre from project metadata or ask
4. Present course picker:
   "Which analysis courses?"
   [Quick taste] [Slow roast] [Spice rack] [Simmering] [All]
5. Confirm module selection
6. Run selected modules on all chapters (parallel)
7. Save recipe

### `/analysis <module> [file]` — Direct Analysis (EXISTING, unchanged)
[Exact same logic as current analysis.md — preserve fully]

### `/analysis list` — Show Modules (EXISTING, updated grouping)
[Show modules grouped by course instead of flat list]

### `/analysis help <module>` — Module Details (EXISTING, unchanged)

### `/analysis --plan` — Genre-Aware Planning (NEW)
1. Detect genre
2. Run module_loader.py recommend
3. Show: "{N} modules recommended, {M} skipped. Estimated: {courses}."
4. Let user adjust selection
5. Show estimated analysis time/cost

## Recipe Integration

### Saving Analysis Recipe
After running analysis, save to `.chapterwise/analysis-recipe/recipe.yaml`:
```yaml
type: analysis
version: "1.0"
created: "..."
modules_run: [summary, characters, tags, ...]
modules_skipped: [gag_analysis, ...]
genre: literary_fiction
chapters_analyzed: 28
course_selections: [quick_taste, slow_roast]
```

### Re-Analysis Detection
Before running any module, check staleness:
1. Run staleness_checker.py for each chapter/module
2. Report: "Found existing analysis for {N} of {M} chapters. {K} are stale."
3. Ask: "Re-analyze stale chapters only, or everything?"

## Parallel Execution
[For batch: spawn Task agents per chapter batch]
[Progress: "Quick taste... summary, characters, tags on 28 chapters."]
[Progress: "Running in parallel... done."]

## Validation and Self-Healing

After every analysis run (whether single module or full course batch), validate output:

1. **Validate .analysis.json files:**
   - Each file is valid JSON with required fields: `module`, `version`, `generated`, `sourceHash`, `result`
   - `sourceHash` matches the current chapter content hash (via `staleness_checker.py`)
   - `result` is non-empty and matches the module's expected output shape

2. **Cross-check with recipe:**
   - If analysis recipe exists, verify module counts match
   - If import recipe exists, verify chapter count matches

3. **Auto-heal:**
   - Missing `sourceHash` → recalculate from chapter content
   - Missing `generated` timestamp → add current time
   - Stale results (hash mismatch) → mark for re-analysis, don't silently serve stale data

4. **Report:**
   - Clean: say nothing (validation invisible)
   - Fixed: "Refreshed 2 stale results."
   - Unfixable: "Chapter 5 analysis is corrupted — re-running summary module."

Run `recipe_validator.py` on `.chapterwise/analysis-recipe/` after saving.

## Error Handling
[Same as existing, plus recipe-specific errors]

## Language Rules
[Course names: Quick taste, Slow roast, Spice rack, Simmering]
[Progress: cooking verb + data noun per Language Guide]
[Never say "recipe" to user]
```

---

## Testing Checklist

- [ ] `/analysis summary test.codex.yaml` — Direct analysis (backward compatible)
- [ ] `/analysis list` — Module list with course groupings
- [ ] `/analysis` (no args) — Interactive course picker
- [ ] `/analysis --plan` — Genre-aware recommendation
- [ ] `/analysis --all` — Batch parallel analysis
- [ ] Recipe created at `.chapterwise/analysis-recipe/recipe.yaml`
- [ ] Re-analysis: running again detects fresh results
- [ ] `module_loader.py list` works from new location
- [ ] `module_loader.py courses` returns course groupings
- [ ] `module_loader.py recommend` returns genre-specific recommendations
- [ ] `staleness_checker.py` correctly identifies stale vs fresh results
- [ ] Validation: corrupt an .analysis.json file, run analysis again → agent detects and re-runs
- [ ] Self-healing: delete sourceHash from .analysis.json, run staleness check → hash regenerated

---

## Dependencies on Phase 0

- All `modules/*.md` files copied to unified plugin
- All `scripts/*.py` files copied and working
- `recipe_manager.py` available for recipe creation/loading

## Dependencies on Other Agents

- **Import Agent** may run first → creates project with genre metadata the analysis agent reads
- **Atlas Agent** depends on analysis output → `.analysis.json` schema must be documented here

---

## What This Agent Does NOT Build

- Import, atlas, or reader commands
- New analysis modules (existing 31 modules are unchanged)
- Web app integration
