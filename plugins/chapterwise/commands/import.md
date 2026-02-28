---
description: "Import manuscripts and content into ChapterWise"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - import
  - import pdf
  - import docx
  - import scrivener
  - import ulysses
  - import manuscript
  - import book
  - import project
  - import folder
  - digest
  - digest folder
  - import novel
argument-hint: "[path/to/file-or-folder]"
---

# ChapterWise Import

## Overview

Import any manuscript, project, or content folder into a structured ChapterWise project. This command detects the source format (PDF, DOCX, Scrivener, Ulysses, plain text, markdown folders), analyzes the manuscript structure, interviews the writer about preferences (first import only), converts everything into clean Codex files with metadata, validates the output, and saves the full configuration so re-imports are instant. The entire process is guided — the agent scans first, asks only the questions that matter, then executes the conversion with real-time progress.

---

## Step 1: Check for Existing Recipe

Before scanning or interviewing, check whether this project has been imported before.

**Action:** Load any saved import configuration for this project path.

```bash
echo '{"project_path": "TARGET_DIR", "type": "import"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py load
```

**If a previous import configuration is found:**

Report to the user with details from the saved config:

> "I remember this one — {title}, {chapters} chapters. Same approach, or start fresh?"

Use AskUserQuestion to present three options:
- **Same** — Re-run with saved settings (fast path, skip to Step 6)
- **Adjust** — Brief follow-up questions about what to change, then re-run
- **Start fresh** — Full interview, new approach from scratch

**If "Same" is chosen:** Skip directly to Step 6 via the fast re-run path. Run the saved converter using:

```bash
echo '{"recipe_path": "RECIPE_DIR"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_recipe.py
```

**If "Adjust" is chosen:** Ask only what the user wants different, update the saved preferences, then skip to Step 6.

**If "Start fresh" is chosen:** Continue to Step 2 as if no previous import exists.

**If no previous import found:** Continue to Step 2.

---

## Step 2: Detect Format

Identify the source format and gather basic file information.

**Action:** Run the format detector on the source path.

```bash
echo '{"path": "SOURCE_PATH"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/format_detector.py
```

The detector returns format type, confidence score, file size, MIME type, and suggested pattern script.

**Report to the user:**

> "Scanning structure... {format}, {details}."

For example:
- "Scanning structure... PDF, 342 pages."
- "Scanning structure... Scrivener project, 31 documents."
- "Scanning structure... folder of 45 markdown files."

**If the format is unknown or confidence is low:**

Use AskUserQuestion:

> "I don't recognize this format. What kind of file is this?"

Options:
- **Novel / manuscript** — Prose content with chapters
- **Short story collection** — Multiple standalone pieces
- **Non-fiction / reference** — Structured informational content
- **Other** — Let the user describe it

---

## Step 3: Scan Structure

Read the source content to understand its internal organization.

**Actions:**

1. Sample the source content — read the beginning (first 5-10 pages/sections), a chunk from the middle, and the end (last 5-10 pages/sections) to understand the full scope.

2. Run the structure analyzer on the sampled content:

```bash
echo '{"path": "SOURCE_PATH", "format": "DETECTED_FORMAT"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/structure_analyzer.py
```

3. Run chapter boundary detection:

```bash
echo '{"path": "SOURCE_PATH", "format": "DETECTED_FORMAT"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/chapter_detector.py
```

**Identify:**
- Document type (novel, short story collection, non-fiction, poetry, screenplay, reference)
- Chapter/section structure (headings, numbering scheme, breaks)
- Special sections (prologue, epilogue, dedication, appendices, author bio)
- Metadata (title, author, if detectable)
- Word count estimate
- Multi-level structure (parts containing chapters, acts containing scenes)

**Report to the user with real data:**

> "Three-act novel, 28 chapters, Roman numeral headings."
> "Prologue and epilogue detected."

Or for non-standard structures:

> "Short story collection, 12 stories, title headings with page breaks."
> "Non-fiction, 8 sections with subsections, numbered headings."

---

## Step 4: Interview (first import only)

Ask the writer about their preferences. Only questions that are relevant to this specific manuscript. This is a conversation, not a form — 1-4 questions max.

**Skip this step entirely if re-importing with saved preferences.**

### Q1: Organization (ask if multi-level structure detected)

Use AskUserQuestion:

> "I found {N} chapters in {M} parts. How would you like them organized?"

Options:
- **Folders per part** (Recommended) — `part-1/chapter-01.md`, `part-2/chapter-05.md`
- **Flat files** — All chapters in one directory: `chapter-01.md`, `chapter-02.md`
- **Other** — "Tell me how you'd like it"

### Q2: Source metadata preservation (ask only if Scrivener or Ulysses detected)

Use AskUserQuestion:

> "Your {app} project has labels, status tags, and keywords. Preserve those?"

Options:
- **Yes, keep everything** (Recommended) — Labels, status, keywords become frontmatter fields and tags
- **Just keywords as tags** — Only keywords transfer, skip labels and status
- **Start clean** — Fresh project without source app metadata

### Q3: Format (ask if agent cannot determine best choice from context)

Use AskUserQuestion:

> "Output as Markdown (simple, portable, great for Git) or full Codex YAML (richer structure, more features)?"

Options:
- **Markdown (Codex Lite)** (Recommended for most) — `.md` files with YAML frontmatter
- **Codex YAML** — Full `.codex.yaml` files with nested structure

Default to Markdown if the user does not express a preference.

### Q4: Front/back matter (ask only if non-content sections detected in scan)

Use AskUserQuestion:

> "I found a dedication, author bio, and acknowledgements. Include those?"

Options:
- **As project metadata** (Recommended) — Goes into `index.codex.yaml` attributes
- **As their own files** — Become standalone sections in the project
- **Skip them** — Don't include at all

### Questions NOT asked

The agent figures these out automatically:
- File naming conventions (always clean, slugified)
- ID generation (always UUID)
- Word counts (always calculated)
- Tags (always generated from content)
- Summaries (always extracted from first paragraph)
- Index file (always generated)

---

## Step 5: Plan and Save Recipe

Create the import configuration folder and save all discovered information.

**Action 1:** Create the configuration folder.

```bash
echo '{"project_path": "TARGET_DIR", "type": "import"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py create
```

**Action 2:** Save the structure map with all discovered chapter boundaries, heading patterns, and document organization.

Write `structure_map.yaml` to the configuration folder with:
- Chapter boundaries (start/end positions, titles)
- Heading pattern (regex used for detection)
- Special sections (prologue, epilogue, front/back matter)
- Part/act groupings if multi-level
- Source file hash for change detection

**Action 3:** Save interview answers as `preferences.yaml`:

```yaml
output_format: markdown
structure: folders_per_part
preserve_source_metadata: true
include_front_matter: false
include_back_matter: false
```

**Action 4:** Update `recipe.yaml` with the full manifest — source path, format, structure map reference, preferences reference, converter script path, and timestamps.

This step is internal. No user-facing message needed.

---

## Step 6: Convert

Execute the conversion. This is where the source becomes a ChapterWise project.

### 6a. Check dependencies

Verify that required Python packages are installed for this format:
- PDF: PyMuPDF (`pymupdf`)
- DOCX: python-docx (`python-docx`)
- Scrivener: lxml (`lxml`)
- Ulysses: No extra dependencies
- Plain text / Markdown: No extra dependencies

**Report:**

> "Checking dependencies... all set."

Or if something is missing:

> "Missing PyMuPDF. Install with: `pip3 install pymupdf`"

Use AskUserQuestion to offer installation:
- **Install it** — Run `pip3 install {package}` automatically
- **I'll install manually** — Pause and wait for user to confirm

### 6b. Prepare output directory

Create the output directory structure based on the plan. If re-importing, create a backup of existing files in `.backups/` first.

### 6c. Run the converter

**For known formats with existing patterns:**

```bash
echo '{"source": "SOURCE_PATH", "output": "OUTPUT_DIR", "config": "RECIPE_DIR/preferences.yaml", "structure": "RECIPE_DIR/structure_map.yaml"}' | python3 ${CLAUDE_PLUGIN_ROOT}/patterns/{format}_converter.py
```

**For formats that need a custom converter:**

The agent reads 2-3 existing pattern scripts from `${CLAUDE_PLUGIN_ROOT}/patterns/` to understand the converter architecture, then writes a custom `convert.py` tailored to this manuscript. The custom script uses the same interfaces (`codex_writer.py`, `frontmatter_builder.py`) so output is consistent.

Save the custom converter in the configuration folder for re-use.

### 6d. Progress messaging

Report progress using cooking verb + technical noun + real data. Follow the Language Guide exactly.

> "Cutting chapters... {N} found."

Then for each chapter:

> "Cooking chapter 1: {title} ({word_count} words)"
> "Cooking chapter 2: {title} ({word_count} words)"

After all chapters:

> "Seasoning metadata... tags, summaries, word counts."
> "Building index..."

For large manuscripts (20+ chapters), use parallel Task subagents:

> "Cooking chapters 1-28 in parallel..."
> "Chapters 1-14 done. 15-28 still running..."
> "All 28 chapters processed."

### 6e. Generate index

Create `index.codex.yaml` with the full project hierarchy, type styles, and display configuration. This ties all converted files together into a navigable project.

---

## Step 7: Validate and Heal

Run validation on the converted output and auto-fix any issues.

**Action 1:** Validate the codex output.

```bash
echo '{"path": "OUTPUT_DIR", "fix": true}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_validator.py
```

The validator checks:
- Frontmatter fields (required fields present, correct types)
- UUIDs (valid format, no duplicates)
- Word counts (accurate, not zero)
- Index consistency (all files referenced, no orphans or phantoms)
- File naming conventions

With `fix: true`, the validator auto-corrects: missing fields, empty word counts, invalid UUIDs, and adds orphan files to the index.

**Action 2:** Validate the saved configuration integrity.

```bash
echo '{"recipe_path": "RECIPE_DIR"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_validator.py
```

This checks that the configuration folder is complete and internally consistent — structure map matches output, preferences are valid, converter script exists.

**Action 3:** Spot-check quality by reading 2-3 generated files to verify chapter breaks landed correctly and content is complete.

**If fixes were applied:**

> "Cleaned up {N} formatting issues."

Brief summary of what was auto-corrected (e.g., "Added missing word counts to 3 files, fixed 1 duplicate UUID").

**If unfixable issues remain:**

Stop and surface the exact files and errors to the user:

> "Chapter {N} needs manual review — {description of issue}."
> "{file_path}: {specific error}"

Do not silently skip unfixable problems.

---

## Step 8: Review and Save

Present the final result to the user and save the configuration for future re-imports.

**Action 1:** Present the output file tree.

```
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
```

**Action 2:** Report the summary.

> "Done. {N} files, {word_count} words."

**Action 3:** Update the configuration with output stats — total files, total word count, chapter count, timestamp.

**Action 4:** Suggest next steps:

1. Review the converted files
2. `git init && git add -A && git push`
3. Connect to ChapterWise.app or open in VS Code
4. Run `/analysis` on any chapter

---

## Re-Import (Fast Path)

When a previous import configuration is found (Step 1), the fast path avoids redundant work.

**Check source file hash against the saved hash.**

**If source is unchanged:**

> "Your import is already up to date."

Done. No work needed.

**If source content changed but structure is the same:**

Run the saved converter with updated source. Report only what changed.

> "Scanning changes... {N} chapters modified."
> "Cooking updated chapters..."
> "Seasoning metadata..."
> "Done. {N} files updated in {time}."

**If the structure changed (different chapter count, new parts, etc.):**

> "Your manuscript changed — {N} chapters now instead of {M}. Let me re-scan."

Re-run Steps 3 through 8 with the new structure. Preserve the user's preferences from the saved configuration (no re-interview needed unless structure changes affect the organization question).

---

## Fallback: Unknown Formats

When format_detector.py returns an unknown format or low confidence, the agent builds a custom converter.

**Process:**

1. Read 2-3 existing pattern scripts from `${CLAUDE_PLUGIN_ROOT}/patterns/` to understand the converter architecture — input parsing, chapter splitting, codex file generation, frontmatter building.

2. Analyze the unknown source file directly — read its content, identify patterns, determine the best extraction strategy.

3. Write a custom `convert.py` that follows the same conventions as existing patterns:
   - Uses `codex_writer.py` for output generation
   - Uses `frontmatter_builder.py` for metadata
   - Accepts the same stdin JSON interface
   - Outputs the same file structure

4. Explain to the user:

> "This is a {format} file — I'll write a custom converter using {approach}."

5. Save the custom converter in the configuration folder so re-imports use it directly.

6. Test the converter on a small sample before running the full conversion. If the sample output looks wrong, adjust and retry.

---

## Error Handling

### Missing dependency

> "Missing {package}. Install with: `pip3 install {package}`"

Offer to install automatically via AskUserQuestion.

### Conversion failure on a chapter

> "Chapter {N} didn't convert cleanly — trying a different approach..."

The agent adjusts the converter (different heading pattern, different split strategy, different encoding) and retries. If the retry also fails, flag the chapter for manual review and continue with the remaining chapters.

### Format not recognized

> "I don't recognize this format. What kind of file is this?"

Use AskUserQuestion to let the user describe the format, then proceed to the unknown format fallback.

### Partial failure

> "{N} chapters had issues — flagged for review."

Complete everything that can be converted. List the failed chapters clearly with their specific errors. The configuration records which chapters need manual attention.

### Permission or access errors

> "Can't read this file. Check permissions?"

Never modify the source file under any circumstances.

### Structure mismatch on re-import

> "Your manuscript changed shape — let me re-scan."

Re-run structure analysis and update the saved configuration before converting.

---

## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared messaging rules.

**Import-specific phases:**

| Phase | Verb | Example |
|-------|------|---------|
| Detect/analyze | Scanning | "Scanning structure... PDF, 342 pages." |
| Split into chapters | Cutting | "Cutting chapters... 28 found." |
| Convert a chapter | Cooking | "Cooking chapter 3: Into the Woods (3,100 words)" |
| Add metadata | Seasoning | "Seasoning metadata... tags, summaries, word counts." |
| Merge files | Blending | "Blending source files... 3 PDFs into one project." |
| Generate index | Building | "Building index..." |
| Check deps | Checking | "Checking dependencies... all set." |
| Finish | Done | "Done. 31 files, 87,234 words." |

---

## Tool Usage Reference

**Script calls — always use stdin JSON piped to python3:**

```bash
# Format detection
echo '{"path": "SOURCE_PATH"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/format_detector.py

# Structure analysis
echo '{"path": "SOURCE_PATH", "format": "FORMAT"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/structure_analyzer.py

# Chapter boundary detection
echo '{"path": "SOURCE_PATH", "format": "FORMAT"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/chapter_detector.py

# Configuration management
echo '{"project_path": "DIR", "type": "import"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py load
echo '{"project_path": "DIR", "type": "import"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_manager.py create

# Fast re-run
echo '{"recipe_path": "RECIPE_DIR"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_recipe.py

# Validation
echo '{"path": "OUTPUT_DIR", "fix": true}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_validator.py
echo '{"recipe_path": "RECIPE_DIR"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/recipe_validator.py
```

**Pattern converter calls:**

```bash
echo '{"source": "SOURCE_PATH", "output": "OUTPUT_DIR", "config": "CONFIG_PATH", "structure": "STRUCTURE_PATH"}' | python3 ${CLAUDE_PLUGIN_ROOT}/patterns/{format}_converter.py
```

**User interaction — always use AskUserQuestion tool**, never inline prompts or bare text questions. Every question that requires a user decision must go through AskUserQuestion with clear labeled options.

**File operations — use Read, Write, Edit, Glob, Grep** as appropriate. Never modify the source files. Always create output in a separate directory.

**Parallel work — use Task tool** for large manuscripts (20+ chapters) to convert chapters concurrently. Each task is independent with no shared state.
