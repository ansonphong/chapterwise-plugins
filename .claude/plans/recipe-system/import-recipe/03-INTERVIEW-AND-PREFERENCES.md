# Import Recipe — Interview, Preferences, and Agent Language

## When to Interview

The agent only interviews the writer on **first import** when no recipe exists. The interview is a quick conversation — not a form. 1-3 questions max, only what's relevant.

### Decision Tree: Interview or Not?

```
Previous import exists?
├── Yes → "I remember how this one goes. Same as last time, or start fresh?"
│         ├── Same → Skip to Cook (no interview)
│         ├── Adjust → Brief follow-up questions only
│         └── Start fresh → Full interview
│
└── No → Interview (first import)
```

### Re-Import with Existing Memory

When a previous import exists, the agent asks ONE question:

> "I remember this one — three-act novel, 28 chapters, folders per part. Same approach, or start fresh?"

Options:
- **Same as last time** (Recommended) — Just cook. Fast.
- **Adjust a few things** — "What would you like different?" (agent updates silently)
- **Start fresh** — Full interview, new approach from scratch

---

## Interview Questions

### The Questions (Agent Picks What's Relevant)

The agent selects from this menu based on what it found in the source. Most imports need only 1-2 questions. A complex Scrivener project might need 3.

**Q1: Structure** (asked if multi-level structure detected)
> "I found 28 chapters in 3 parts. How would you like them organized?"
- Folders per part (Recommended)
- Flat files — all in one directory
- Your own structure — "Tell me how you'd like it"

**Q2: Source App Metadata** (asked if Scrivener/Ulysses/other app detected)
> "Your Scrivener project has labels, status tags, and keywords. Preserve those?"
- Yes, keep everything (Recommended)
- Just keywords as tags
- Start clean — no source metadata

**Q3: Format** (asked if agent can't determine best choice from context)
> "Markdown or full Codex YAML?"
- Markdown (Recommended for most) — simple, Git-friendly, readable anywhere
- Codex YAML — richer structure, more ChapterWise features

**Q4: Non-Content Sections** (asked if front/back matter detected)
> "Found a dedication and author bio. Include those?"
- As project metadata (Recommended)
- As their own files
- Skip them

### Questions NOT Asked

The agent figures these out automatically and doesn't bother the writer:
- File naming conventions (always clean, slugified)
- ID generation (always UUID)
- Word counts (always calculated)
- Tags (always generated from content)
- Summaries (always extracted from first paragraph)
- Index file (always generated)

---

## Agent Language: The Cooking Metaphor

The agent's progress messages use cooking language naturally — not forced, not every message, but enough that the metaphor comes through. The user is watching the agent work, and the language makes it feel alive.

**See `LANGUAGE-GUIDE.md` for the definitive language reference.**

### Example: Full Import Session

```
Scanning structure... PDF, 342 pages.
Three-act novel, 28 chapters, Roman numeral headings.

"How would you like the chapters organized?"
  → Folders per part

Checking dependencies... all set.
Cutting chapters... 28 found, plus prologue and epilogue.
Cooking chapter 1: The Awakening (3,200 words)
Cooking chapter 2: The Call (2,800 words)
...
Cooking chapter 28: Coming Home (4,100 words)
Seasoning metadata... tags, summaries, word counts.
Building index...
Done. 31 files, 87,234 words.
```

### Example: Re-Import

```
I remember this one — three-act novel, 28 chapters.
Same approach, or start fresh?
  → Same

Scanning changes... 3 chapters modified.
Cooking updated chapters...
Seasoning metadata...
Done. Updated in 30 seconds.
```

### Example: Errors

```
"Chapter 5 didn't convert cleanly — trying a different approach..."
"Missing PyMuPDF. Install with: pip3 install pymupdf"
"Your manuscript changed — 30 chapters now instead of 28. Re-scanning structure."
"3 chapters had issues — flagged for review."
```

### Language Rules

1. **Functional first** — The import works. Messages are clear. Data is shown.
2. **Cooking verbs as flare** — "Cutting" not "splitting", "Cooking" not "converting". That's the extent.
3. **80/20 rule** — 80% plain language, 20% cooking flare. If in doubt, go plain.
4. **NEVER say "recipe" to the user** — Internal concept only.
5. **Brief** — 5-15 words per progress message.
6. **Real data always** — Counts, names, word counts. Flare wraps information, never replaces it.
7. **No "Order up", no "Bon appetit"** — Too much. Just say "Done."
8. **No emojis.**
9. **See `LANGUAGE-GUIDE.md`** for the full reference.

---

## Preferences System

### Per-Project Preferences

Saved in the recipe folder at `.chapterwise/import-recipe/preferences.yaml`:

```yaml
# Writer's preferences for this project
output_format: markdown
structure: folders_per_part
preserve_source_metadata: true
include_front_matter: false
include_back_matter: false
```

### Per-Source-App Preferences

When importing from writing apps, app-specific preferences are captured:

```yaml
# Scrivener-specific preferences
scrivener:
  preserve_labels: true
  preserve_status: true
  preserve_keywords_as_tags: true
  skip_non_compile: false

# Ulysses-specific preferences
ulysses:
  preserve_keywords: true
  preserve_writing_goals: true
  groups_as_folders: true
  convert_annotations: true
```

### Global Preferences (Cross-Project)

If a writer imports multiple projects with the same preferences, the agent can detect the pattern and offer to use the same settings next time.

The agent reads previous recipe folders from other projects (if they exist in the same parent directory or are linked) and offers:

> "Last time you imported a Scrivener project, you chose markdown with folders per part and full metadata. Same this time?"

This is not a global config file — it's the agent noticing patterns across recipes. True agentic behavior.

---

## Edge Cases

### Writer Wants to Change Preferences Mid-Import
- Agent asks "Want me to redo the chapters I've already converted, or just apply the new preference going forward?"
- If redo: re-cook from the start with updated recipe
- If forward-only: continue with new preference, note the split in log.md

### Writer Doesn't Know What They Want
- Agent picks sensible defaults (markdown, auto-structure, preserve everything)
- Agent says: "I'll go with defaults — you can always re-import with different settings."
- The recipe captures defaults so they can be adjusted later

### Very Large Manuscripts (100+ chapters)
- Agent asks fewer questions — don't waste time on interview when there's a lot to process
- Agent uses parallel Task subagents for speed
- Progress reporting becomes more summary-oriented: "Cooking chapters 1-12... done."

### Multiple Source Files
- Writer says: "Import all these PDFs as one project"
- Agent interviews once for the whole project
- Each PDF gets its own section in the recipe
- Structure map spans all files
- Single `index.codex.yaml` ties everything together
