# Atlas Recipe — Update Atlas (Incremental Updates)

## Concept

The Update Atlas function is the Atlas Recipe's killer feature. Instead of rebuilding the entire atlas from scratch when the manuscript changes, it **diffs, patches, and re-synthesizes** — updating only what changed.

Write 10 more chapters? Update Atlas adds them. Rewrite chapter 5? Update Atlas re-profiles affected characters and patches the timeline. Delete a subplot? Update Atlas removes it cleanly.

The Atlas becomes a **living document** that evolves with the manuscript.

## How It's Triggered

- `/atlas --update` — Explicitly update the atlas
- After re-import: "Your manuscript has been re-imported. Want me to update the atlas too?"
- Automatically suggested: "I notice 5 chapters changed since the last atlas build. Want me to update?"

## The Update Pipeline

```
/atlas --update
    |
    v
[1. Diff]           — Compare chapter hashes, find what changed
    |
    v
[2. Re-Extract]     — Entity extraction on changed chapters only
    |
    v
[3. Re-Analyze]     — Per-chapter analysis on changed chapters only
    |
    v
[4. Merge Entities] — Combine new extractions with existing entity map
    |
    v
[5. Re-Synthesize]  — Only atlas sections affected by the changes
    |
    v
[6. Patch]          — Update atlas files in place, commit
```

---

## Step 1: Diff

**What the agent does:**
1. Reads the saved recipe at `.chapterwise/atlas-recipe/recipe.yaml`
2. Loads the per-chapter content hashes from `source.chapter_hashes`
3. Hashes current chapter content and compares

**Diff result categories:**

| Category | Meaning | Example |
|----------|---------|---------|
| `unchanged` | Content hash matches | Chapter 1 — same as last time |
| `modified` | Content hash differs | Chapter 5 — rewritten |
| `added` | New chapter not in recipe | Chapter 29 — new |
| `removed` | Chapter in recipe but not in project | Chapter 12 — deleted |
| `moved` | Same content, different position | Chapter 8 is now Chapter 9 |

**Output:**
```yaml
diff:
  unchanged: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
  modified: [5, 12]
  added: [29, 30]
  removed: []
  moved: []

  summary:
    total_chapters_now: 30
    total_chapters_before: 28
    chapters_changed: 4
    chapters_unchanged: 26
```

**Progress messaging:**
> "Scanning for changes... 4 chapters changed (2 modified, 2 new). 26 unchanged."

---

## Step 2: Re-Extract Entities

**What the agent does:**
1. Runs entity extraction (Pass 1) on **only the changed chapters** (modified + added)
2. Flags entities from removed chapters for cleanup

**For modified chapters:**
- Re-extract all entities from the new content
- Compare with previous extraction: new entities? Changed descriptions? Removed characters?

**For added chapters:**
- Full entity extraction — find all new characters, locations, events

**For removed chapters:**
- Mark all entities that ONLY appeared in removed chapters as candidates for removal
- Entities appearing in other chapters are kept

**Progress messaging:**
> "Re-extracting entities from 4 changed chapters..."
> "Found 2 new characters, 1 new location. 3 existing characters have updated descriptions."

---

## Step 3: Re-Analyze Changed Chapters

**What the agent does:**
1. Runs the same analysis modules from the original Pass 2 — but **only on changed chapters**
2. Uses parallel Task subagents for speed

**This is the big savings.** A full atlas on 28 chapters runs 280 module analyses. Updating 4 chapters runs only 40. That's 85% cheaper and 85% faster.

```
Original:  28 chapters x 10 modules = 280 analyses
Update:     4 chapters x 10 modules =  40 analyses  (86% saved)
```

**Progress messaging:**
> "Analyzing 4 changed chapters with 10 modules..."
> "Done. 40 module results collected."

---

## Step 4: Merge Entities

**What the agent does:**
1. Loads the existing entity map from the recipe
2. Applies the re-extraction results:
   - **New entities** → Add to entity map
   - **Updated entities** → Replace in entity map (new description, new chapter presence)
   - **Removed entities** → Remove from entity map (only if they appeared exclusively in removed chapters)
   - **Entities with new chapter appearances** → Update `chapters_present` arrays

**This is where the diff gets smart.** If Elena Vasquez appeared in chapters 1-28 and chapter 5 was rewritten, the agent doesn't discard her profile — it updates her chapter 5 data while preserving everything else.

**Merge rules:**

| Entity Situation | Action |
|-----------------|--------|
| Existed before, still exists | Update description and chapter list |
| New entity in added chapter | Add to entity map |
| Entity only in removed chapters | Remove from entity map |
| Entity in both removed and kept chapters | Keep, update chapter list |
| Character renamed in modified chapter | Agent detects rename, updates across all references |

**Progress messaging:**
> "Merging entity changes... 2 new characters added, 3 profiles updated, 0 removed."

---

## Step 5: Re-Synthesize Affected Sections

**This is the key insight.** The agent doesn't re-synthesize everything — it determines which atlas sections are affected by the changes and only re-runs those synthesizers.

### Affected Section Detection

| What Changed | Sections to Re-Synthesize |
|-------------|--------------------------|
| Character added/removed/modified | Characters, Relationships |
| New chapter added | Timeline, Plot Structure, Characters (if new character appearances) |
| Chapter rewritten (same characters) | Timeline, Themes (chapter-level changes) |
| Chapter removed | Timeline, Plot Structure, Characters (remove chapter references) |
| Location added/changed | Locations |
| Theme shift detected | Themes |

### Synthesis Strategy

**Full re-synthesis** (when >50% of chapters changed):
- Just rebuild all sections from scratch — faster than selective patching at that scale

**Selective re-synthesis** (when <50% of chapters changed):
- Only re-run affected synthesizers
- Preserve unchanged sections as-is
- Patch changed sections with new data

**The agent decides which strategy to use:**

```
4 of 30 chapters changed (13%) → Selective re-synthesis
18 of 30 chapters changed (60%) → Full re-synthesis
```

**Progress messaging (selective):**
> "Re-synthesizing 3 of 6 atlas sections..."
> "Updating character profiles... 2 new arcs added."
> "Patching timeline... 5 new events inserted."
> "Themes unchanged — skipping."

**Progress messaging (full):**
> "Too many changes for patching — rebuilding atlas from fresh analysis."
> "Synthesizing character arcs... 16 characters."
> "Building timeline... 52 events."
> "Done."

---

## Step 6: Patch Atlas Files

**What the agent does:**
1. Opens existing atlas `.codex.yaml` files
2. Patches changed sections in place (preserves file structure, IDs, user additions)
3. Writes new files for new sections
4. Removes sections for removed content
5. Updates `index.codex.yaml`
6. Commits to git with descriptive message

**Patch, don't overwrite.** If the user has manually edited atlas files (added notes, custom descriptions), the agent preserves those additions. Only agent-generated content gets updated.

**How the agent preserves user edits:**

Each atlas node has a `source` field:
```yaml
- type: character
  name: Elena Vasquez
  source: generated          # Agent wrote this — safe to update
  description: "Former marine biologist..."

- type: note
  name: "My notes on Elena"
  source: user               # User added this — NEVER overwrite
  content: "I want to make her more conflicted in the revision..."
```

The agent updates `source: generated` nodes and never touches `source: user` nodes.

**Git commit message:**
```
Update atlas: 2 characters updated, 2 chapters added, timeline patched

Changed chapters: 5, 12 (modified), 29, 30 (added)
Sections updated: characters, timeline, plot-structure
Sections unchanged: themes, locations, relationships
```

**Progress messaging:**
> "Patching atlas files... 3 sections updated, 3 preserved."
> "Committing changes..."
> "Done. Atlas updated — 2 characters updated, 5 timeline events added."

---

## Update Recipe Format

After an update, the recipe is patched (not rewritten):

```yaml
# Added to recipe.yaml after update
updates:
  - date: "2026-03-15T10:00:00Z"
    trigger: manual           # manual | post-import | auto-detected
    chapters_changed:
      modified: [5, 12]
      added: [29, 30]
      removed: []
    entities_changed:
      added: ["Dr. Rivera", "The Lighthouse"]
      updated: ["Elena Vasquez", "Marcus Chen", "Timeline"]
      removed: []
    sections_resynthesized: [characters, timeline, plot-structure]
    sections_preserved: [themes, locations, relationships]
    strategy: selective       # selective | full
    duration_seconds: 45
    credits_used: 140

  - date: "2026-04-01T14:00:00Z"
    trigger: post-import
    # ...
```

This creates a **history of atlas evolution** — the writer can see how their atlas grew alongside their manuscript.

---

## Edge Cases

### Massive Rewrite (>80% chapters changed)

> "Almost your entire manuscript changed — it'll be faster to rebuild the atlas from scratch. Rebuild, or try to patch?"

Options:
- **Rebuild** (Recommended) — Fresh atlas, clean data
- **Patch anyway** — Preserve user edits, update everything else

### Character Rename

The agent detects when a character's name changes across modified chapters:

> "It looks like 'Elena Vasquez' is now 'Elena Torres' in the revised chapters. Update the name across the entire atlas?"

Options:
- **Yes, update everywhere** (Recommended)
- **No, keep both** — Treat as separate characters

### Structural Change (Parts Added/Removed)

If the manuscript goes from 3 parts to 4 parts:

> "Your manuscript structure changed — 4 parts now instead of 3. The atlas plot structure needs rebuilding."

The agent automatically re-runs the StructureSynthesizer.

### Atlas File Manually Deleted

If the user deleted an atlas file:

> "The characters section is missing from the atlas folder. Regenerate it, or skip?"

### No Changes Detected

> "Your manuscript hasn't changed since the last atlas build. Nothing to update."

---

## Example: Full Update Session

```
> /atlas --update

Scanning for changes... 4 chapters changed (2 modified, 2 new). 26 unchanged.

Re-extracting entities from changed chapters...
Found 2 new characters, 1 new location. 3 existing characters updated.

Analyzing 4 changed chapters with 10 modules...
Done. 40 module results collected.

Merging entity changes...
Re-synthesizing 3 of 6 atlas sections...
Updating character profiles... 16 characters now (was 14).
Patching timeline... 5 new events inserted.
Updating plot structure... new chapters mapped.

Patching atlas files... 3 sections updated, 3 preserved.
Committing changes...

Done. Atlas updated in 45 seconds.

Changes:
  +2 characters (Dr. Rivera, The Lighthouse Keeper)
  +5 timeline events
  +2 chapters mapped (29, 30)
   3 sections unchanged (themes, locations, relationships)
```

---

## Example: Update After Re-Import

```
> /import revised-draft.pdf

I remember this one — three-act novel, 28 chapters.
Scanning changes... 5 chapters modified, 2 new.
Cooking updated chapters...
Done. 30 chapters, 7 changed.

You have an atlas for this project. Update it with the new chapters?
  [Update atlas]  [Skip]  [Rebuild from scratch]

Scanning for changes... 7 chapters affected.
Re-extracting entities...
Analyzing 7 changed chapters...
Re-synthesizing affected sections...
Done. Atlas updated in 60 seconds.
```

---

## Routine Update Workflow

The user's ideal workflow — write, re-import, update atlas, repeat:

```
Week 1:  /import draft-v1.pdf → /atlas              (full build)
Week 3:  /import draft-v2.pdf → /atlas --update      (incremental)
Week 5:  /import draft-v3.pdf → /atlas --update      (incremental)
Week 8:  /import final-draft.pdf → /atlas --update   (incremental)
```

Each update is faster and cheaper than the original build. The atlas accumulates knowledge across revisions, becoming more accurate and complete over time.

The recipe's `updates` array provides a complete history — the writer can see exactly how their story evolved across drafts.
