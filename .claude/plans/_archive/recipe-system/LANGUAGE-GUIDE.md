# Recipe System — Language Guide

**This is the single source of truth for all user-facing language in the recipe system.**

---

## THE MOST IMPORTANT RULE

**The cooking language is FLARE, not the main act.** The user experience is straightforward and functional first. You say "Import PDF" and it imports your PDF. Clear, direct, no-nonsense.

The cooking metaphors are a light, playful touch sprinkled on top of functional progress messages. They add personality without getting in the way. If a user isn't paying close attention, they just see a clear import happening. If they are paying attention, they notice the charming food language.

**Think of it like a good restaurant:** the food is the point. The decor is nice. The waiter doesn't narrate every bite.

### The Formula: One Cooking Word + One Data Word

Every progress message pairs a cooking verb with a real technical description. The cooking word adds personality. The data word tells you exactly what's happening. Together they're both charming and accurate.

**YES — cooking verb + technical description:**
```
"Scanning structure... PDF, 342 pages, three-act novel."
"Cutting chapters... 28 found."
"Cooking chapter 1: The Awakening (3,200 words)"
"Seasoning metadata... tags, summaries, word counts."
"Blending source files... 3 PDFs into one project."
"Simmering thematic analysis... 28 chapters."
"Done. 31 files, 87,234 words."
```

**NO — cooking word alone (what is it actually doing?):**
```
"Cutting..."
"Seasoning..."
"Simmering..."
```

**NO — too much theme, loses the data:**
```
"Tasting the ingredients... let me see what we're working with today!"
"Time to fire up all the burners in the kitchen!"
"Order up! Your meal is served! Bon appetit!"
```

**The formula:** `[cooking verb] [technical noun]... [real data]`
- "Cutting chapters..." — cooking verb + what's being cut
- "Seasoning metadata..." — cooking verb + what's being added
- "Slow roasting structure..." — cooking verb + what's being analyzed
- "Cooking chapter 5 (3,100 words)" — cooking verb + specific item + data

---

## Rule #1: Never Say "Recipe" to the User

The word "recipe" is an internal developer concept. The user never hears it.

| Don't Say | Say Instead |
|-----------|-------------|
| "Found your recipe from last time" | "I remember how this one goes" |
| "Want to use the recipe?" | "Same as last time, or start fresh?" |
| "Writing the recipe..." | *(say nothing, or just "Planning...")* |
| "The recipe needs adjusting" | "Your manuscript changed — let me re-read it" |
| "Recipe saved" | *(say nothing — save silently)* |

---

## Rule #2: Cooking Verb + Data Noun

Every progress message follows the formula: **cooking verb + technical noun + real data**.

The cooking verb replaces a boring technical verb. The technical noun says exactly what's being worked on. The data gives you numbers.

| Technical Action | Cooking Formula | Example |
|-----------------|----------------|---------|
| Analyzing document | Scanning + what | "Scanning structure... PDF, 342 pages." |
| Splitting into pieces | Cutting + what | "Cutting chapters... 28 found." |
| Converting a chapter | Cooking + which one | "Cooking chapter 3 (2,800 words)" |
| Adding metadata | Seasoning + what kind | "Seasoning metadata... tags, summaries, word counts." |
| Merging files | Blending + what | "Blending source files... 3 PDFs merged." |
| Background processing | Simmering + what | "Simmering thematic analysis... 28 chapters." |
| Deep analysis | Slow roasting + what | "Slow roasting structure... three-act, story beats." |
| Integrating app data | Mixing + what | "Mixing Scrivener labels into frontmatter..." |
| Light final touches | Sprinkling + what | "Sprinkling word counts and IDs..." |
| Entity extraction | Extracting + what | "Extracting entities... 14 characters, 8 locations." |
| Cross-chapter synthesis | Synthesizing + what | "Synthesizing character arcs... 14 characters." |
| Building connections | Weaving + what | "Weaving theme threads... 6 major themes." |
| Assembling output | Assembling + what | "Assembling atlas files... 6 sections." |
| Comparing versions | Scanning + what | "Scanning for changes... 4 chapters changed." |
| Combining results | Merging + what | "Merging entity changes... 2 added, 3 updated." |
| Updating in place | Patching + what | "Patching atlas files... 3 sections updated." |
| Finishing | Done + data | "Done. 31 files, 87,234 words." |

```
Good:  "Cutting chapters... 28 found."          ← cooking verb + what + data
Good:  "Seasoning metadata... tags and summaries." ← cooking verb + what it is
Good:  "Mixing Scrivener labels into frontmatter..." ← cooking verb + actual technical process
Good:  "Done. 31 files, 87,234 words."           ← plain, no flare needed for "done"

Bad:   "Cutting..."                               ← what are you cutting?
Bad:   "Seasoning..."                              ← seasoning what?
Bad:   "Now let's add some seasoning!"             ← too theatrical
```

---

## Rule #3: Phase Names Per Recipe

### Import Recipe

| Phase | What Happens | Message |
|-------|-------------|---------|
| Scan | Detect format, sample content | "Scanning structure... PDF, 342 pages, three-act novel." |
| Interview | Ask preferences (first import only) | Plain questions, no flare |
| Prep | Check deps, set up output | "Checking dependencies... all set." |
| Cut | Split into chapters | "Cutting chapters... 28 found." |
| Cook | Convert each chapter | "Cooking chapter 1: The Awakening (3,200 words)" |
| Season | Add metadata | "Seasoning metadata... tags, summaries, word counts." |
| Index | Generate index.codex.yaml | "Building index..." |
| Done | Present result | "Done. 31 files, 87,234 words." |

### Analysis Recipe

| Phase | What Happens | Message |
|-------|-------------|---------|
| Scan | Read manuscript, pick modules | "Scanning manuscript... literary fiction, character-driven." |
| Plan | Select modules, estimate cost | "18 modules selected, 5 skipped." |
| Quick taste | Fast overview modules | "Quick taste... summary, characters, tags on 28 chapters." |
| Slow roast | Deep structural analysis | "Slow roasting structure... three-act, story beats, pacing." |
| Spice rack | Writing craft modules | "Spice rack... writing style, language, rhythm on 28 chapters." |
| Simmering | Depth/psychology modules | "Simmering thematic analysis... emotions, Jungian, relationships." |
| Done | Present results | "Done. 18 modules across 28 chapters." |

### Atlas Recipe

| Phase | What Happens | Message |
|-------|-------------|---------|
| Scan | Read manuscript, propose structure | "Scanning manuscript... literary fiction, 28 chapters, 87,000 words." |
| Select | User picks sections (or all) | "Building characters, timeline, themes. 3 of 6 sections selected." |
| Extract | Entity extraction (Haiku, free) | "Extracting entities... 14 characters, 8 locations, 47 events." |
| Reuse check | Check for existing analysis data | "Found existing analysis for 20 of 28 chapters. Re-analyzing 8 changed." |
| Analyze | Per-chapter deep analysis (parallel) | "Analyzing 8 chapters with 10 modules... running in parallel." |
| Synthesize | Cross-chapter synthesis | "Synthesizing character arcs... 14 characters across 28 chapters." |
| Assemble | Write atlas files, commit | "Assembling atlas files... 3 sections." |
| Done | Present result | "Done. Story Atlas — 3 files, 14 characters, 47 events mapped." |

### Atlas Management

| Action | Message |
|--------|---------|
| Named atlas | "What should I call this atlas? Default is 'atlas'." |
| Add sections | "Your atlas has characters and timeline. Adding themes and locations..." |
| Rebuild | "Rebuilding Story Atlas from scratch..." |
| Delete | "Delete the Story Atlas? This removes 6 files and can't be undone." |
| List | "2 atlases: Story Atlas (6 sections), World Atlas (4 sections)." |

### Atlas Update

| Phase | What Happens | Message |
|-------|-------------|---------|
| Diff | Compare chapter hashes | "Scanning for changes... 4 chapters changed, 26 unchanged." |
| Re-extract | Entities from changed chapters | "Re-extracting entities from 4 changed chapters..." |
| Re-analyze | Analysis on changed chapters only | "Analyzing 4 changed chapters with 10 modules..." |
| Merge | Combine new with existing | "Merging entity changes... 2 added, 3 updated, 0 removed." |
| Re-synthesize | Patch affected atlas sections | "Re-synthesizing 3 of 6 atlas sections..." |
| Patch | Update files in place, commit | "Patching atlas files... 3 sections updated, 3 preserved." |
| Done | Present result | "Done. Atlas updated in 45 seconds." |

### Reader Recipe

| Phase | What Happens | Message |
|-------|-------------|---------|
| Scan | Read project structure | "Scanning project... 31 files, 3 parts." |
| Scaffold | Build HTML/CSS/JS | "Building reader shell... HTML, CSS, navigation." |
| Wire | Add interactivity | "Wiring interactivity... search, theme toggle." |
| Done | Present result | "Done. Open index.html to preview." |

### Status Command

The `/status` command shows the project's recipe state at a glance. No cooking language here — pure data.

```
> /status

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

**Status icons:** `✓` complete, `◌` in progress / partial, `✗` not started, `⚠` stale (manuscript changed since last run)

**Stale detection example:**
```
> /status

  Import     ✓  Imported 2 weeks ago
  Analysis   ⚠  5 chapters changed since last analysis
  Atlas      ⚠  Story Atlas is stale — 5 chapters changed
  Reader     ✓  Built 1 week ago (minimal template)

  Tip: Run /atlas --update to refresh the atlas.
```

### Pipeline Command

The `/pipeline` command runs the full chain with sensible defaults:

```
> /pipeline my-novel.pdf

Step 1/4: Import
  Scanning structure... PDF, 342 pages, three-act novel.
  Cutting chapters... 28 found.
  Done. 31 files, 87,234 words.

Step 2/4: Analysis
  18 modules selected for literary fiction.
  Quick taste... done. Slow roasting structure... done.
  Done. 18 modules across 28 chapters.

Step 3/4: Atlas
  Extracting entities... 14 characters, 8 locations.
  Analyzing 28 chapters... running in parallel.
  Synthesizing... 6 sections.
  Done. Story Atlas complete.

Step 4/4: Reader
  Building minimal reader...
  Done. Open reader/index.html to preview.

Pipeline complete. All saved.
```

---

## Rule #4: Parallel Agents

When using parallel Task subagents, describe what's being parallelized:

```
"Cooking chapters 1-28 in parallel..."
"Chapters 1-14 done. 15-28 still running..."
"All 28 chapters processed."
```

For analysis:
```
"Running summary, characters, tags on 28 chapters in parallel..."
"Simmering thematic analysis across 28 chapters..."
```

The word "parallel" is clear enough. No need for "burners" or kitchen metaphors for parallelism.

### Technical Implementation

Parallel agents use Claude Code's `Task` tool with `subagent_type` for independent work:

```
# Parallel chapter conversion (import)
Task 1: Chapters 1-7
Task 2: Chapters 8-14
Task 3: Chapters 15-21
Task 4: Chapters 22-28

# Parallel analysis
Task 1: Run summary on all chapters
Task 2: Run characters on all chapters
Task 3: Run writing_style on all chapters
```

Each task is independent — no shared state. Results collected after all tasks finish.

---

## Rule #5: Re-Import Language

When a previous import exists:

**First touch:**
> "I remember this one — three-act novel, 28 chapters. Same approach, or start fresh?"

**Same:**
> "Picking up where we left off..."
> "Cutting... 2 new chapters detected."
> "Cooking the updated chapters..."
> "Done. 30 chapters, 5 changed."

**Start fresh:**
> "Starting over. Scanning..."
> *(Full workflow)*

**Structure changed:**
> "Your manuscript changed — 30 chapters now instead of 28. Let me re-scan."

---

## Rule #6: Error Language

Keep errors clear and functional. A touch of cooking language is fine but clarity wins.

| Error | Message |
|-------|---------|
| Missing dependency | "Missing PyMuPDF. Install with: `pip3 install pymupdf`" |
| Conversion failure | "Chapter 5 didn't convert cleanly — trying a different approach..." |
| Format unknown | "I don't recognize this format. What kind of file is this?" |
| Partial failure | "3 chapters had issues — flagged for review." |
| Permission error | "Can't read this file. Check permissions?" |
| Structure mismatch | "Your manuscript changed shape — let me re-scan." |

---

## Rule #7: Analysis Course Names

The analysis recipe groups modules into "courses." These names have a cooking touch but stay descriptive:

| Course | What It Covers | The Name Is |
|--------|---------------|-------------|
| **Quick taste** | summary, characters, tags | Descriptive — a quick first look |
| **Slow roast** | structure, story beats, pacing | Descriptive — deep, takes time |
| **Spice rack** | writing style, language, craft | Descriptive — the craft tools |
| **Simmering** | thematic depth, emotions, psychology | Descriptive — deep background analysis |

These are the only "branded" cooking names in the system. Everything else is just verbs.

---

## Tone Summary

1. **Cooking verb + data noun.** Every message pairs a cooking word with a technical description. "Seasoning metadata" not just "Seasoning."
2. **Describe the actual process.** The user should always know what's happening technically. The cooking word is flavor on real information.
3. **Brief.** 5-15 words per progress message.
4. **Real data always.** Counts, names, word counts alongside every cooking verb.
5. **No theatrical lines.** No "Order up", no "Bon appetit", no "Chef's kiss."
6. **No emojis.** The words do the work.
7. **No "recipe" to the user.** Internal concept only.
8. **Plain when plain is better.** "Checking dependencies" doesn't need a cooking word. "Done. 31 files." is just "Done."
9. **The cooking language is discovered, not announced.** The user notices "oh, it says 'cutting chapters' instead of 'splitting document' — that's nice" rather than feeling like they're in a themed experience.

---

## Quick Reference: A Real Import Session

What the user actually sees:

```
> /import my-novel.pdf

Scanning structure... PDF, 342 pages.
Three-act novel, 28 chapters, Roman numeral headings.
Prologue and epilogue detected.

How would you like the chapters organized?
  [Folders per part]  [Flat files]  [Other]

Got it. Folders per part, markdown format.

Checking dependencies... all set.
Cutting chapters... 28 found, plus prologue and epilogue.
Cooking chapter 1: The Awakening (3,200 words)
Cooking chapter 2: The Call (2,800 words)
Cooking chapter 3: Into the Woods (3,100 words)
...
Cooking chapter 28: Coming Home (4,100 words)
Seasoning metadata... tags, summaries, word counts.
Building index...

Done. 31 files, 87,234 words.

  my-novel/
  ├── index.codex.yaml
  ├── prologue.md
  ├── part-1-departure/
  │   ├── chapter-01-the-awakening.md
  │   └── ...
  ├── part-2-initiation/
  │   └── ...
  ├── part-3-return/
  │   └── ...
  └── epilogue.md

Next steps:
  git init && git add -A && git push
  Connect to ChapterWise.app or open in VS Code
  Run /analysis on any chapter
```

**A Real Re-Import:**
```
> /import revised-draft.pdf

I remember this one — three-act novel, 28 chapters.
Same approach, or start fresh?
  [Same]  [Adjust]  [Start fresh]

Scanning changes... 3 chapters modified, 2 new.
Cooking updated chapters...
Seasoning metadata...
Done. 33 files updated in 25 seconds.
```

**A Real Analysis Run:**
```
> /analysis --plan

Scanning manuscript... literary fiction, character-driven.
18 modules selected, 5 skipped (not relevant to genre).

Quick taste... summary, characters, tags on 28 chapters.
  Running in parallel... done.
Slow roasting structure... three-act, story beats, pacing.
  Done.
Spice rack... writing style, language, rhythm on 28 chapters.
  Running in parallel... done.
Simmering thematic analysis... emotions, Jungian, relationships.
  Running in parallel... done.

Done. 18 modules across 28 chapters. Results in .analysis.json.
```

**A Real Atlas Build:**
```
> /atlas

Scanning manuscript... literary fiction, 28 chapters, 87,000 words.
Proposing atlas structure...

Here's the atlas I'd recommend:
  atlas/
    characters.codex.yaml
    timeline.codex.yaml
    themes.codex.yaml
    plot-structure.codex.yaml
    locations.codex.yaml
    relationships.codex.yaml

Build all sections, or pick specific ones?
  [Build all]  [Select sections]  [Characters only]

What should I call this atlas? Default is "atlas".
  [atlas]  [story-atlas]  [Custom name]

Extracting entities... 14 characters, 8 locations, 47 key events.
Found existing analysis for 20 of 28 chapters. Re-analyzing 8 changed.
80 module runs needed (200 reused from previous analysis).
Analyzing 8 chapters with 10 modules... running in parallel.

Synthesizing character arcs... 14 characters.
Building timeline... 47 events mapped.
Weaving theme threads... 6 major themes.
Assembling atlas files... 6 sections.

Done. Story Atlas — 6 files, 14 characters, 47 events mapped.
Commit to the project repo?
  [Commit]  [Save without committing]  [Review first]
```

**A Real Atlas Update:**
```
> /atlas --update

Scanning for changes... 4 chapters changed (2 modified, 2 new). 26 unchanged.
Re-extracting entities from changed chapters...
Analyzing 4 changed chapters...
Merging entity changes... 2 new characters, 3 updated.
Re-synthesizing 3 of 6 atlas sections...
Patching atlas files...

Done. Atlas updated in 45 seconds.
```

**Adding Sections to an Existing Atlas:**
```
> /atlas --add-sections

Your Story Atlas has: characters, timeline.
Available: themes, plot-structure, locations, relationships.

Which sections to add?
  [All remaining]  [Select]

Adding themes and locations...
Synthesizing theme threads... 6 major themes.
Synthesizing location profiles... 8 locations.
Assembling 2 new sections...

Done. Story Atlas updated — now 4 sections.
```

Notice: every message tells you what's happening technically. The cooking words are just there — "cutting chapters", "seasoning metadata", "slow roasting structure", "synthesizing character arcs", "weaving theme threads" — accurate descriptions with a little personality. That's the goal.
