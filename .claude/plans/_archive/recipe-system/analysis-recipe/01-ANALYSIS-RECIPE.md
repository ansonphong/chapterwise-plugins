# Analysis Recipe — Full Specification

## Concept

After the import is done — the manuscript is plated, the chapters are clean, the index is built — there's a natural follow-up: "Now analyze it."

The analysis recipe is a custom analysis plan the agent builds based on what it learned during import. It knows the manuscript type, structure, genre, and themes. So it recommends exactly which analysis modules to run, in what order, on which chapters.

Like the import recipe, the analysis recipe is saved for reuse. Re-import a revised draft? Re-run the same analysis plan.

## How It Works

### Offered Automatically After Import

After plating, the agent offers:

> "Your novel is imported — 28 chapters, 87,000 words. Want me to set up an analysis plan too?"

If yes, the agent creates `.chapterwise/analysis-recipe/recipe.yaml`.

### Or Triggered Independently

The writer can also say:
- `/import --analyze` — Import AND analyze in one go
- Or later: "Create an analysis plan for this project"

### The Agent Picks Modules Intelligently

The agent doesn't blindly run all 30+ modules. It knows what it imported:

**Literary fiction → prioritize:**
- `summary`, `characters`, `character_relationships` — the essentials
- `three_act_structure`, `story_beats`, `story_pacing` — structural analysis
- `writing_style`, `language_style`, `rhythmic_cadence` — craft
- `thematic_depth`, `reader_emotions`, `immersion` — depth
- `jungian_analysis`, `dream_symbolism` — if literary/psychological content detected

**Literary fiction → skip:**
- `gag_analysis` — not a comedy
- `win_loss_wave` — not a thriller/adventure
- `four_weapons` — not relevant

**Thriller → prioritize:**
- `story_pacing`, `plot_twists`, `misdirection_surprise` — tension and pace
- `win_loss_wave` — momentum tracking
- `story_beats`, `heros_journey` — plot structure

**Non-fiction / reference → prioritize:**
- `summary`, `tags`, `clarity_accessibility` — overview and usability
- `writing_style`, `language_style` — craft
- Skip most narrative modules

## Analysis Recipe Format

```yaml
# .chapterwise/analysis-recipe/recipe.yaml
version: "1.0"
created: "2026-02-27T15:00:00Z"

manuscript:
  title: "The Long Way Home"
  type: literary_fiction
  chapters: 28
  word_count: 87234

plan:
  # Quick taste — fast, high-value overview
  - name: "Quick taste"
    description: "Get the lay of the land"
    modules:
      - summary
      - characters
      - tags
    scope: all_chapters
    estimated_credits: 84  # 28 chapters x 3 modules

  # Slow roast — deep structural analysis
  - name: "Slow roast"
    description: "Deep structural understanding"
    modules:
      - three_act_structure
      - story_beats
      - story_pacing
      - heros_journey
    scope: root_only
    estimated_credits: 0  # Root-level analysis (free)

  # Spice rack — craft and style
  - name: "Spice rack"
    description: "Writing craft analysis"
    modules:
      - writing_style
      - language_style
      - rhythmic_cadence
      - clarity_accessibility
    scope: all_chapters
    estimated_credits: 112

  # Simmering — depth and psychology
  - name: "Simmering"
    description: "Thematic and psychological depth"
    modules:
      - thematic_depth
      - reader_emotions
      - immersion
      - jungian_analysis
      - character_relationships
      - dream_symbolism
    scope: all_chapters
    estimated_credits: 168

skipped:
  - module: gag_analysis
    reason: "Not a comedy — no humor-focused content detected"
  - module: win_loss_wave
    reason: "Literary fiction — not action/adventure focused"
  - module: four_weapons
    reason: "Not applicable to this genre"
  - module: ai_detector
    reason: "Not requested — human-written manuscript"

total_estimated_credits: 364
```

## Execution

### Run the Full Plan

> "Run my analysis plan"

The agent reads the analysis recipe and executes each course in order:

```
Scanning manuscript... literary fiction, character-driven.
17 modules selected, 4 skipped.

Quick taste... summary, characters, tags on 28 chapters.
  Cooking chapters in parallel...
  28/28 done.

Slow roasting structure... three-act, story beats, pacing.
  Done.

Spice rack... writing style, language, rhythm on 28 chapters.
  Cooking chapters in parallel...
  Done.

Simmering thematic analysis... emotions, Jungian, relationships.
  Done.

Done. 17 modules, 28 chapters. Results saved to .analysis.json.
```

### Run a Single Course

> "Just run the quick taste"

The agent runs only the first course of the plan.

### Run Specific Modules

> "Run character analysis on chapters 1-10"

The agent uses the recipe as context but runs exactly what's requested.

### Re-Run After Revision

> "I revised chapters 5-8. Re-run the analysis on those."

The agent checks staleness (via hash comparison from `staleness_checker.py`) and only re-analyzes chapters that changed.

## Integration with Analysis Infrastructure

The analysis recipe uses the unified plugin's modules. It doesn't duplicate them — it orchestrates them.

```
chapterwise (creates the recipe)
    ↓
.chapterwise/analysis-recipe/recipe.yaml
    ↓
chapterwise modules/ + scripts/ (executes the analysis)
```

The recipe knows *what* to analyze. The modules and scripts know *how* to analyze.

### Module Execution

Each module runs the same way it does today:
1. `module_loader.py` loads the module's `.md` prompt
2. `staleness_checker.py` checks if re-analysis is needed
3. Agent (Claude) performs the analysis inline
4. `analysis_writer.py` writes results to `.analysis.json`

The analysis recipe just automates the selection and ordering.

## Saving and Reuse

Like the import recipe, the analysis recipe is saved and reused:

**First analysis:** Agent builds the plan, executes it.
**Subsequent analysis:** Agent finds the existing plan, runs it on changed chapters only.
**Revised draft re-imported:** Agent runs the same analysis plan on the fresh import.

The two recipes work together:
1. Writer says "re-import my latest draft"
2. Import recipe re-runs → updated chapters
3. Agent offers: "Want me to re-run your analysis on the changed chapters?"
4. Analysis recipe re-runs on changed chapters only → fresh results

## Self-Validation and Self-Healing

Every analysis run ends with a validation pass before completion is reported:

1. Run `recipe_validator.py` on `.chapterwise/analysis-recipe/`
2. Validate each `.analysis.json` file has required keys (`module`, `version`, `sourceHash`, `result`)
3. Verify `sourceHash` still matches chapter content for files marked fresh

If issues are found, fix automatically when safe:
- Missing metadata fields in `.analysis.json` are restored
- Invalid JSON is regenerated from the in-memory analysis result
- Stale hash mismatches are marked for targeted re-analysis

If an issue cannot be auto-fixed, surface exact files and stop with actionable guidance.

## Credit Estimation

The recipe includes credit estimates so the writer knows the cost before committing:

> "Your analysis plan covers 17 modules across 28 chapters. Estimated cost: ~364 credits."
> "Want to run the full plan, or start with just the quick taste (84 credits)?"

This maps to the existing credit system:
- Chapter-level analysis: 1 credit per chapter per module
- Root-level analysis: free
- The recipe calculates totals based on scope and module count

For local Claude Code usage (BYOK — bring your own key), credits don't apply. The agent just runs everything using the writer's API key.
