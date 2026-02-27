# Import Recipe — Agent Workflow

## Process Overview

When the user says `/import my-novel.pdf`, the agent follows this workflow.

### Steps

```
/import my-novel.pdf
    |
    v
[1. Check for previous]  — Is there an existing recipe?
    |                        Yes → skip to Step 6
    v                        No  → continue
[2. Scan]                 — Detect format, sample content
    |
    v
[3. Interview]            — Ask about preferences (only what's relevant)
    |
    v
[4. Plan]                 — Generate converter script + structure map
    |
    v
[5. Prep]                 — Check dependencies, create output directory
    |
    v
[6. Convert]              — Cut, cook, season — build codex files
    |
    v
[7. Review]               — Verify output, present results
    |
    v
[8. Save]                 — Save recipe folder for next time (silent)
```

---

## Step 1: Check for Previous Import

Before doing anything, the agent looks for an existing recipe.

**Action:** Check if `.chapterwise/import-recipe/recipe.yaml` exists in the target directory.

**If recipe exists:**
- Load it. Compare source file hash to current file.
- If source unchanged: "Your project is already up to date."
- If source changed: Skip to Step 6 with the new source.
- If source structure changed significantly: Notify user, offer to rebuild.

**If no recipe:** Continue to Step 2.

---

## Step 2: Scan

The agent figures out what it's working with.

**Action:** Run `format_detector.py` to identify the source format.

```bash
echo '{"path": "'$SOURCE_PATH'"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/format_detector.py
```

**Returns:**
```json
{
  "format": "pdf",
  "confidence": 0.99,
  "file_size": 2450000,
  "mime_type": "application/pdf",
  "suggested_pattern": "pdf_converter.py"
}
```

**Then the agent samples the content.** It reads portions of the source to understand the structure:
- First 5-10 pages/sections (opening, front matter)
- A chunk from the middle (typical content)
- Last 5-10 pages/sections (ending, back matter)

The agent identifies:
- Document type (novel, short story collection, non-fiction, poetry, screenplay, reference)
- Chapter/section structure (headings, numbering scheme, breaks)
- Special sections (prologue, epilogue, dedication, appendices)
- Metadata (title, author, if detectable)
- Word count estimate

**Progress messaging (cooking verb + technical noun):**
> "Scanning structure... PDF, 342 pages."
> "Three-act novel, 28 chapters, Roman numeral headings."

---

## Step 3: Interview

The agent asks the writer about their preferences. Only questions that matter for *this* manuscript. Not a form — a conversation.

**The agent asks 1-3 questions max** using `AskUserQuestion`. Which questions depend on what was found in Step 2.

### Question: Structure

Only asked if the manuscript has a multi-level structure (parts + chapters, acts + scenes, etc.):

> "I found 28 chapters in 3 parts. How would you like them organized?"

Options:
- **Folders per part** (Recommended) — `part-1/chapter-01.md`, `part-2/chapter-05.md`
- **Flat files** — All chapters in one directory: `chapter-01.md`, `chapter-02.md`
- **Your own structure** — "Tell me how you'd like it"

### Question: Source App Metadata

Only asked if importing from Scrivener, Ulysses, or another app with rich metadata:

> "Your Scrivener project has labels (First Draft, Revised, Final) and keywords. Want me to preserve those?"

Options:
- **Yes, keep everything** (Recommended) — Labels, status, keywords become frontmatter fields and tags
- **Just keywords as tags** — Only keywords transfer, skip labels and status
- **No, start clean** — Fresh project without source app metadata

### Question: Format

Only asked if the agent can't determine the best format from context:

> "Output as Markdown (simple, portable, great for Git) or full Codex YAML (richer structure, more features)?"

Options:
- **Markdown** (Recommended for most) — Codex Lite `.md` files with YAML frontmatter
- **Codex YAML** — Full `.codex.yaml` files with nested structure

### Question: Non-Content Sections

Only asked if dedication, acknowledgements, author bio, etc. were found:

> "I found a dedication, author bio, and acknowledgements. Include those as sections?"

Options:
- **Capture as project metadata** (Recommended) — Goes into `index.codex.yaml` attributes
- **Include as sections** — Become their own files in the project
- **Skip them** — Don't include at all

**All answers saved to `preferences.yaml` in the recipe folder.**

---

## Step 4: Plan

The agent constructs the import strategy.

**Action:** The agent reads the appropriate pattern script from `patterns/`:

```bash
# Agent reads the pattern for guidance
cat ${CLAUDE_PLUGIN_ROOT}/patterns/pdf_converter.py
```

**Then the agent either:**

**A) Uses the pattern directly** — If the manuscript is straightforward and the pattern handles it:
```bash
cp ${CLAUDE_PLUGIN_ROOT}/patterns/pdf_converter.py .chapterwise/import-recipe/convert.py
# Agent modifies the config section at the top of the script
```

**B) Generates a custom variant** — If the manuscript has quirks:
The agent writes a new `convert.py` inspired by the pattern but tailored to this manuscript. For example:
- Custom heading regex for unusual chapter numbering
- Special handling for embedded images or footnotes
- Multi-pass extraction for complex layouts

**C) Creates from scratch** — If no pattern matches (unknown format):
The agent studies multiple pattern scripts to understand the converter architecture, then writes a completely new one. Uses the same interfaces (`codex_writer.py`, `frontmatter_builder.py`) so output is always consistent.

**Artifacts generated:**
- `convert.py` — The custom converter script
- `structure_map.yaml` — The discovered manuscript structure
- `recipe.yaml` — The full manifest
- `run.sh` — One-command re-run script

**Progress messaging:**
> *(No user-facing message — this step is internal planning.)*

---

## Step 5: Prep

Make sure everything is ready before converting.

**Actions:**
1. Check Python dependencies — does the user have PyMuPDF / python-docx / etc.?
2. If missing: tell the user what to install and offer to install it
3. Create the output directory
4. If re-importing: create a backup of existing files in `.backups/`

**Progress messaging:**
> "Checking dependencies... all set."

---

## Step 6: Convert (Cut → Cook → Season)

Execute the conversion. This step maps to the user-facing phases: Cut, Cook, Season, Index.

**Action:** Run the converter script.

```bash
python3 .chapterwise/import-recipe/convert.py "$SOURCE_PATH" "$OUTPUT_DIR"
```

**What the converter does:**
1. Extract text/content from source file (format-specific)
2. Split into chapters/sections based on `structure_map.yaml`
3. For each chapter:
   - Clean the text (strip artifacts, fix encoding)
   - Generate frontmatter (type, name, summary, word count, tags)
   - Write the file (`.md` or `.codex.yaml`)
4. Generate `index.codex.yaml` with full hierarchy
5. Generate `.chapterwise/settings.json` for project settings

**Progress messaging (cooking verb + technical noun + real data):**

> "Cutting chapters... 28 found, plus prologue and epilogue."
> "Cooking chapter 1: The Awakening (3,200 words)"
> "Cooking chapter 2: The Call (2,800 words)"
> ...
> "Seasoning metadata... tags, summaries, word counts."
> "Building index..."
> "Done. 31 files, 87,234 words."

For large manuscripts, the agent uses parallel Task subagents:

> "Cooking chapters 1-28 in parallel..."
> "Chapters 1-14 done. 15-28 still running..."
> "All chapters processed."

---

## Step 7: Validate, Heal, and Review

Validate output, auto-fix issues, then present the result.

**Actions:**
1. Run `codex_validator.py` on the output directory with `fix: true`
   - Validates: frontmatter fields, UUIDs, word counts, index consistency, orphan/phantom files
   - Auto-fixes: missing fields, empty word counts, invalid UUIDs, orphan files added to index
2. Run `recipe_validator.py` on `.chapterwise/import-recipe/` to verify recipe integrity
3. Agent reads back 2-3 generated files to spot-check quality (chapter breaks, content completeness)
4. If codex_validator found and fixed issues: report briefly — "Cleaned up 2 formatting issues."
5. If unfixable issues remain: flag for user — "Chapter 3 needs manual review."
6. Agent presents the final result to the user

**Output summary:**

```
Import complete!

Source: my-novel.pdf (342 pages, ~87,000 words)
Output: ./my-novel/

Created:
  28 chapters
   1 prologue
   1 epilogue
   1 index.codex.yaml
  ─────────────────
  31 files total

Structure:
  my-novel/
  ├── index.codex.yaml
  ├── prologue.md
  ├── part-1-departure/
  │   ├── chapter-01-the-awakening.md
  │   ├── chapter-02-the-call.md
  │   └── ...
  ├── part-2-initiation/
  │   └── ...
  ├── part-3-return/
  │   └── ...
  └── epilogue.md

Next steps:
  1. Review the converted files
  2. git init && git add -A && git push
  3. Connect to ChapterWise.app or open in VS Code
  4. Run /analysis on any chapter
```

---

## Step 8: Save (Silent)

Save the recipe for next time.

**Action:** Write/update the recipe folder at `.chapterwise/import-recipe/`.

This happens silently. The user sees "Done." and the result summary. The recipe is saved in the background so the next import of this manuscript is instant.

---

## Re-Import Flow (Fast Path)

When the agent finds an existing recipe:

```
/import revised-draft.pdf
    |
    v
[1. Check for previous]  → Found!
    |
    v
[Source changed?]
    |
    Yes → [6. Convert] → [7. Review] → Done
    |
    No  → "Already up to date."
```

No interview. No analysis. No script generation. Straight to conversion.

**Progress messaging:**
> "I remember this one — picking up where we left off."
> "3 chapters changed. Cooking the updated ones..."
> "Done. Updated in 30 seconds."

---

## Error Handling

### Conversion Fails
- Agent reads the error, diagnoses the issue
- If it's a dependency problem: suggests installation
- If it's a content problem: adjusts the recipe (different heading pattern, different split strategy)
- Agent patches `convert.py` and retries
- Never silently loses content — if a chapter can't be extracted, it's flagged in the output

### Unknown Format
- Agent tries to detect format from file content (not just extension)
- If truly unknown: agent studies the pattern scripts, writes a custom converter
- If the agent can't figure it out: asks the user "What kind of file is this?"

### Partial Import
- If some chapters convert but others fail, the agent completes what it can
- Failed chapters are listed clearly: "3 chapters had issues — I've marked them for review"
- The recipe records which chapters need manual attention

### Permission / Access Errors
- Clear messaging: "I can't read this file. Check permissions?"
- Never modifies the source file under any circumstances
