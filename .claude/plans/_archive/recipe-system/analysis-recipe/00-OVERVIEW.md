# Analysis Recipe — Overview

## What It Is

The Analysis Recipe is an intelligent analysis plan the agent builds after studying your manuscript. It recommends which of the 30+ analysis modules to run, in what order, grouped into courses that make sense for your specific work.

## The Idea

After importing (or on any existing ChapterWise project), the agent knows the genre, structure, POV count, themes, and complexity. It uses that knowledge to create a custom analysis strategy:

- A literary novel with 4 POV characters gets Character Arcs, Writing Style, Jungian Analysis
- A thriller gets Story Pacing, Plot Holes, Reader Emotions, Misdirection & Surprise
- A poetry collection gets Writing Style, Literary Devices, Emotional Dynamics
- A screenplay gets Story Beats, Dialogue Analysis, Story Pacing

The agent doesn't run all 30 modules blindly. It picks what matters.

## The Courses

Analysis is served in courses (like the cooking metaphor):

1. **Quick taste** — Summary, Characters, Tags. Fast, high-value overview. (~3 credits/chapter)
2. **Slow roast** — Structural analysis: Story Beats, Story Pacing, Hero's Journey, Three-Act. (Root-level, cheap)
3. **Spice rack** — Craft: Writing Style, Language, Rhythmic Cadence, Clarity. (~4 credits/chapter)
4. **Simmering** — Depth: Thematic, Emotional, Immersion, Jungian, Relationships, Dream Symbolism. (~6 credits/chapter)

Writers can run one course at a time or the full menu.

## Documents in This Directory

| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | This document |
| `01-ANALYSIS-RECIPE.md` | Full spec: module selection logic, recipe format, execution, re-analysis |

## Core Behaviors

- **Genre-aware**: Module selection adapts to literary fiction vs thriller vs romance vs non-fiction
- **Structure-aware**: Multi-POV, non-linear timeline, multiple subplots each trigger specific modules
- **Credit-transparent**: Shows estimated cost before running
- **Incremental**: Re-import a revised draft? Agent re-analyzes only changed chapters
- **Unified execution**: The recipe is the strategy. The analysis modules and scripts within the unified `chapterwise` plugin are the execution engine.
- **BYOK compatible**: With your own Claude API key, no credits needed. The agent runs analysis directly.
