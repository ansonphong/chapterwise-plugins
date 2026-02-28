# ChapterWise Plugin Audit Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 34 issues identified in the plugin audit — 10 HIGH, 16 MEDIUM, 8 LOW — across 21 commands, 24 scripts, plugin.json, and plugin structure.

**Architecture:** Direct file edits to frontmatter, content, and structure. No new features — purely quality/compliance fixes. Changes are organized by blast radius: frontmatter-only edits first, then content fixes, then structural changes.

**Tech Stack:** Markdown command files, Python scripts, YAML plugin.json

**Working directory:** `/Users/phong/Projects/chapterwise-plugins/`

---

## Task 1: Shorten All Descriptions to <60 Characters

**Files:**
- Modify: `plugins/chapterwise/commands/import.md:2`
- Modify: `plugins/chapterwise/commands/analysis.md:2`
- Modify: `plugins/chapterwise/commands/atlas.md:2`
- Modify: `plugins/chapterwise/commands/reader.md:2`
- Modify: `plugins/chapterwise/commands/status.md:2`
- Modify: `plugins/chapterwise/commands/pipeline.md:2`
- Modify: `plugins/chapterwise/commands/insert.md:2`
- Modify: `plugins/chapterwise/commands/diagram.md:2`
- Modify: `plugins/chapterwise/commands/format.md:2`
- Modify: `plugins/chapterwise/commands/format-regen-ids.md:2`
- Modify: `plugins/chapterwise/commands/lite.md:2`
- Modify: `plugins/chapterwise/commands/convert-to-codex.md:2`
- Modify: `plugins/chapterwise/commands/convert-to-markdown.md:2`
- Modify: `plugins/chapterwise/commands/spreadsheet.md:2`
- Modify: `plugins/chapterwise/commands/import-scrivener.md:2`

**Step 1: Apply all description edits**

| File | Old | New |
|------|-----|-----|
| `import.md` | `"Import any manuscript, project, or content folder into a ChapterWise project"` (76c) | `"Import manuscripts and content into ChapterWise"` (49c) |
| `analysis.md` | `"Run AI analysis on Codex files with intelligent module selection"` (62c) | `"Analyze Codex files with intelligent module selection"` (53c) |
| `atlas.md` | `"Build a comprehensive atlas — characters, timeline, themes, locations, relationships"` (79c) | `"Build a story atlas from your manuscript"` (41c) |
| `reader.md` | `"Build a custom reading experience for your manuscript or atlas"` (63c) | `"Build a static HTML reader for your project"` (45c) |
| `status.md` | `"Show ChapterWise project status — recipes, analysis, atlases, reader state"` (72c) | `"Show project status and staleness overview"` (43c) |
| `pipeline.md` | `"Run the full ChapterWise pipeline — Import → Analysis → Atlas → Reader"` (72c) | `"Run full pipeline: Import, Analysis, Atlas, Reader"` (51c) |
| `insert.md` | `Intelligently insert notes into Chapterwise Codex manuscripts with semantic location finding` (80c) | `"Insert notes into Codex manuscripts by location"` (49c) |
| `diagram.md` | `Create Mermaid diagrams in Chapterwise Codex format (flowcharts, sequences, ER, state, gantt, mindmaps, and 15+ more)` (90c) | `"Create Mermaid diagrams in Codex format"` (40c) |
| `format.md` | `Convert content to Chapterwise Codex format and fix formatting issues` (63c) | `"Format content as Chapterwise Codex"` (36c) |
| `format-regen-ids.md` | `Auto-fix codex file and regenerate ALL IDs (useful for duplicating content)` (65c) | `"Regenerate all IDs in a codex file"` (35c) |
| `lite.md` | `Create Codex Lite files (Markdown with YAML frontmatter)` (56c) | `"Create Codex Lite Markdown with frontmatter"` (45c) |
| `convert-to-codex.md` | `Convert markdown or text files to Codex format` (48c) | `"Convert Markdown files to Codex YAML format"` (45c) |
| `convert-to-markdown.md` | `Convert Codex to Codex Lite (Markdown with YAML frontmatter)` (60c) | `"Convert Codex files to Markdown with frontmatter"` (50c) |
| `spreadsheet.md` | `Create and manage spreadsheets in Chapterwise Codex format` (59c) | `"Create spreadsheets in Codex format"` (36c) |
| `import-scrivener.md` | `"Import a Scrivener project (.scriv) into ChapterWise format"` (59c) | `"Import a Scrivener project into ChapterWise"` (45c) |

Edit each file's `description:` line in the YAML frontmatter. Use the Edit tool on each file.

**Step 2: Verify all descriptions are under 60 chars**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise && for f in commands/*.md; do desc=$(grep '^description:' "$f" | head -1 | sed 's/description: *//; s/^"//; s/"$//'); len=${#desc}; if [ $len -gt 60 ]; then echo "FAIL $f ($len chars): $desc"; else echo "OK $f ($len)"; fi; done
```
Expected: All OK, zero FAIL.

**Step 3: Commit**

```bash
git add plugins/chapterwise/commands/*.md
git commit -m "fix: shorten all command descriptions to <60 chars"
```

---

## Task 2: Add Missing `argument-hint` to 14 Commands

**Files:**
- Modify: `plugins/chapterwise/commands/format.md` (frontmatter)
- Modify: `plugins/chapterwise/commands/explode.md`
- Modify: `plugins/chapterwise/commands/implode.md`
- Modify: `plugins/chapterwise/commands/lite.md`
- Modify: `plugins/chapterwise/commands/insert.md`
- Modify: `plugins/chapterwise/commands/diagram.md`
- Modify: `plugins/chapterwise/commands/spreadsheet.md`
- Modify: `plugins/chapterwise/commands/convert-to-codex.md`
- Modify: `plugins/chapterwise/commands/convert-to-markdown.md`
- Modify: `plugins/chapterwise/commands/generate-tags.md`
- Modify: `plugins/chapterwise/commands/update-word-count.md`
- Modify: `plugins/chapterwise/commands/format-folder.md`
- Modify: `plugins/chapterwise/commands/format-regen-ids.md`
- Modify: `plugins/chapterwise/commands/index.md`
- Modify: `plugins/chapterwise/commands/status.md`

**Step 1: Add argument-hint to each file's frontmatter**

Add `argument-hint:` line right before the closing `---` of each file's frontmatter:

| File | argument-hint value |
|------|-----|
| `format.md` | `"[file.codex.yaml]"` |
| `explode.md` | `"[file.codex.yaml] [--types type1,type2]"` |
| `implode.md` | `"[file.codex.yaml]"` |
| `lite.md` | `"[file.md]"` |
| `insert.md` | `"[instruction or --batch notes.txt]"` |
| `diagram.md` | `"[diagram-type] [description]"` |
| `spreadsheet.md` | `"[description or file.csv]"` |
| `convert-to-codex.md` | `"[input.md]"` |
| `convert-to-markdown.md` | `"[input.codex.yaml]"` |
| `generate-tags.md` | `"[file.codex.yaml or file.md]"` |
| `update-word-count.md` | `"[file_or_directory]"` |
| `format-folder.md` | `"[folder_path]"` |
| `format-regen-ids.md` | `"[file.codex.yaml]"` |
| `index.md` | `"[project_directory]"` |
| `status.md` | `""` |

**Step 2: Verify**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise && for f in commands/*.md; do if grep -q "argument-hint:" "$f"; then echo "OK $f"; else echo "MISSING $f"; fi; done
```
Expected: All OK.

**Step 3: Commit**

```bash
git add plugins/chapterwise/commands/*.md
git commit -m "fix: add argument-hint to all 14 commands missing it"
```

---

## Task 3: Fix "recipe" Leaks in User-Facing Text

**Files:**
- Modify: `plugins/chapterwise/commands/status.md:137`
- Modify: `plugins/chapterwise/commands/status.md:148`
- Modify: `plugins/chapterwise/commands/atlas.md:28`
- Modify: `plugins/chapterwise/commands/atlas.md:58`
- Modify: `plugins/chapterwise/commands/atlas.md:372`
- Modify: `plugins/chapterwise/commands/atlas.md:409`
- Modify: `plugins/chapterwise/commands/atlas.md:426`

**Step 1: Fix status.md user-facing text**

In `status.md`:

Line 137 — change:
```
| Everything fresh | "All recipes are up to date." |
```
to:
```
| Everything fresh | "Everything is up to date." |
```

Line 148 — change:
```
- Keep descriptions concise: one line per recipe
```
to:
```
- Keep descriptions concise: one line per step
```

**Step 2: Fix atlas.md "Reader Recipe" reference**

Line 28 — change:
```
Output is committed to the project git repo as native Codex files — browsable on ChapterWise.app, in VS Code, or as a standalone reader via the Reader Recipe.
```
to:
```
Output is committed to the project git repo as native Codex files — browsable on ChapterWise.app, in VS Code, or as a standalone reader via the /reader command.
```

**Step 3: Fix atlas.md heading**

Line 58 — change:
```
**If an existing atlas recipe is found:**
```
to:
```
**If an existing atlas configuration is found:**
```

**Step 4: Fix atlas.md generator metadata**

Line 372 — change:
```
generator: "atlas-recipe"
```
to:
```
generator: "chapterwise-atlas"
```

Line 409 — change:
```
    generator: atlas-recipe
```
to:
```
    generator: chapterwise-atlas
```

Line 426 — change:
```
Generated by atlas-recipe with claude-sonnet-4-6
```
to:
```
Generated by chapterwise-atlas with claude-sonnet-4-6
```

**Step 5: Verify no recipe leaks in user-facing text**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise
# Check status.md
grep -n "recipe" commands/status.md | grep -vi "recipe_manager\|recipe.yaml\|recipe.schema\|import-recipe\|analysis-recipe\|atlas-recipe\|reader-recipe\|recipe_path\|recipe_dir\|recipe_validator\|Never say"
# Check atlas.md generator fields
grep -n "generator:" commands/atlas.md
```
Expected: status.md returns no hits. atlas.md generator lines show "chapterwise-atlas".

**Step 6: Commit**

```bash
git add plugins/chapterwise/commands/status.md plugins/chapterwise/commands/atlas.md
git commit -m "fix: remove 'recipe' from user-facing text and metadata"
```

---

## Task 4: Fix Tool Usage Anti-Patterns in Commands

**Files:**
- Modify: `plugins/chapterwise/commands/analysis.md:127-129` (find → Glob)
- Modify: `plugins/chapterwise/commands/analysis.md:245` (cat → Read)
- Modify: `plugins/chapterwise/commands/atlas.md:89-91` (cat → Read)
- Modify: `plugins/chapterwise/commands/reader.md:69-70,88-89` (Glob pseudo-syntax)

**Step 1: Fix analysis.md — replace `find` with Glob**

Lines 126-129 — change:
```bash
find . -name "*.codex.yaml" -not -path "./.chapterwise/*" | head -100
find . -name "*.codex.md" -not -path "./.chapterwise/*" | head -100
```
to:
```
Use the Glob tool to find all codex files:
- Pattern: `**/*.codex.yaml` — exclude any paths under `.chapterwise/`
- Pattern: `**/*.codex.md` — exclude any paths under `.chapterwise/`
```

(Remove the bash code block wrapper since these are tool instructions, not bash commands.)

**Step 2: Fix analysis.md — replace `cat` with Read**

Line 245 — change:
```bash
cat ${CLAUDE_PLUGIN_ROOT}/modules/_output-format.md
```
to:
```
Read the output format spec at `${CLAUDE_PLUGIN_ROOT}/modules/_output-format.md`
```

**Step 3: Fix atlas.md — replace `cat` with Read**

Find the `cat index.codex.yaml` line (around line 89) and change to:
```
Read the project's `index.codex.yaml` to understand the manuscript structure.
```

**Step 4: Fix reader.md — replace Glob pseudo-syntax with prose**

Lines 68-71 — change:
```bash
# Find the index file, starting from the current directory
Glob: "**/index.codex.yaml"
```
to:
```
Use the Glob tool with pattern `**/index.codex.yaml` to locate the project index.
```

Lines 88-90 — change:
```bash
Glob: "**/*.md" + "**/*.codex.yaml" (excluding index.codex.yaml itself)
```
to:
```
Use the Glob tool to find all content files:
- Pattern: `**/*.md`
- Pattern: `**/*.codex.yaml`
Exclude `index.codex.yaml` itself from the results.
```

**Step 5: Verify no `find .` or `cat ` commands remain in instruction text**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise
grep -n "^find \.\|^cat " commands/analysis.md commands/atlas.md commands/reader.md
grep -n "^Glob:" commands/reader.md
```
Expected: No matches.

**Step 6: Commit**

```bash
git add plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/reader.md
git commit -m "fix: replace find/cat/Glob-pseudosyntax with proper tool instructions"
```

---

## Task 5: Trim diagram.md — Remove Mermaid Syntax Reference

**Files:**
- Modify: `plugins/chapterwise/commands/diagram.md`

**Step 1: Read the full file to identify removable sections**

Read `plugins/chapterwise/commands/diagram.md`. Identify the Mermaid syntax reference sections (the detailed syntax for each of the 16 diagram types). Claude already knows Mermaid syntax — only the Codex output format, Phosphor icon usage, and workflow instructions are unique value.

**Step 2: Reduce triggers from 14 to 6**

Change triggers section from:
```yaml
triggers:
  - diagram
  - mermaid
  - flowchart
  - sequence diagram
  - class diagram
  - state diagram
  - er diagram
  - entity relationship
  - gantt chart
  - mindmap
  - timeline
  - gitgraph
  - architecture diagram
  - pie chart
```
to:
```yaml
triggers:
  - diagram
  - mermaid
  - codex diagram
  - create diagram
  - mermaid codex
  - chapterwise:diagram
```

**Step 3: Remove individual diagram type syntax sections**

Keep:
- The frontmatter
- The Codex output format section (how to wrap Mermaid in codex YAML)
- The supported diagram types list (just names, not full syntax)
- The Phosphor icon usage section
- The workflow section
- The best practices section

Remove:
- Individual syntax sections for each of the 16 diagram types (these are general Mermaid docs Claude already knows)

Target: Reduce from ~611 lines to ~120-150 lines.

**Step 4: Verify trimmed file has essential content**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise
wc -l commands/diagram.md
grep -q "triggers:" commands/diagram.md && echo "has triggers"
grep -q "codex" commands/diagram.md && echo "has codex format"
grep -q "Phosphor\|phosphor" commands/diagram.md && echo "has phosphor"
```
Expected: ~120-150 lines, all three checks pass.

**Step 5: Commit**

```bash
git add plugins/chapterwise/commands/diagram.md
git commit -m "refactor: trim diagram.md from 611 to ~130 lines — remove Mermaid syntax ref"
```

---

## Task 6: Fix Trigger Overlaps

**Files:**
- Modify: `plugins/chapterwise/commands/convert-to-codex.md` (triggers)
- Modify: `plugins/chapterwise/commands/lite.md` (triggers)
- Modify: `plugins/chapterwise/commands/format-folder.md` (triggers)
- Modify: `plugins/chapterwise/commands/update-word-count.md` (triggers)

**Step 1: Fix convert-to-codex.md trigger overlap with format.md**

Change triggers from:
```yaml
triggers:
  - convert to codex
  - markdown to codex
  - make codex
  - md to codex
  - upgrade to codex
```
to:
```yaml
triggers:
  - convert to codex
  - markdown to codex
  - md to codex
  - convert md to codex yaml
  - chapterwise:convert-to-codex
```

(Remove "make codex" and "upgrade to codex" which overlap with format.md)

**Step 2: Fix lite.md generic triggers**

Change triggers from:
```yaml
triggers:
  - codex lite
  - lite format
  - markdown frontmatter
  - add frontmatter
  - codex markdown
```
to:
```yaml
triggers:
  - codex lite
  - lite format
  - codex markdown
  - add codex frontmatter
  - chapterwise:lite
```

(Remove "markdown frontmatter" — too generic. Change "add frontmatter" to "add codex frontmatter".)

**Step 3: Fix format-folder.md**

Change triggers from:
```yaml
triggers:
  - fix folder
  - autofix folder
  - format folder
  - fix directory
  - fix all codex
  - batch fix
```
to:
```yaml
triggers:
  - fix codex folder
  - autofix codex folder
  - format codex folder
  - fix all codex files
  - batch fix codex
  - chapterwise:format-folder
```

(Add "codex" qualifier to prevent false-triggering on general folder operations.)

**Step 4: Fix update-word-count.md**

Change triggers from:
```yaml
triggers:
  - word count
  - update word count
  - count words
  - calculate words
  - word statistics
```
to:
```yaml
triggers:
  - update word count
  - count codex words
  - calculate word count
  - codex word statistics
  - chapterwise:update-word-count
```

(Remove bare "word count" — too generic.)

**Step 5: Verify no duplicate triggers across all commands**

Run:
```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise
grep -h "^  - " commands/*.md | sort | uniq -d
```
Expected: No output (zero duplicates).

**Step 6: Commit**

```bash
git add plugins/chapterwise/commands/convert-to-codex.md plugins/chapterwise/commands/lite.md plugins/chapterwise/commands/format-folder.md plugins/chapterwise/commands/update-word-count.md
git commit -m "fix: resolve trigger overlaps and remove generic triggers"
```

---

## Task 7: Rewrite "When This Skill Applies" Sections to Imperative

**Files:**
- Modify: `plugins/chapterwise/commands/format.md:17-23`
- Modify: `plugins/chapterwise/commands/explode.md` (similar section)
- Modify: `plugins/chapterwise/commands/implode.md` (similar section)
- Modify: `plugins/chapterwise/commands/lite.md` (similar section)
- Modify: `plugins/chapterwise/commands/spreadsheet.md` (similar section)

**Step 1: Fix format.md lines 17-23**

Change:
```markdown
## When This Skill Applies

- User wants to create/convert content for Chapterwise
- User mentions "codex format", "chapterwise", or "codex yaml/json"
- User wants to run the auto-fixer on a codex file
- User is structuring ANY content that benefits from hierarchy and metadata
```
to:
```markdown
## When to Apply

Apply this command when the user asks to:
- Create or convert content to Chapterwise Codex format
- Fix formatting issues in a `.codex.yaml` or `.codex.json` file
- Structure any content that benefits from hierarchy and metadata
```

**Step 2: Apply same pattern to explode, implode, lite, spreadsheet**

For each file, find the "When This Skill Applies" section and rewrite using:
- `## When to Apply` heading
- `Apply this command when the user asks to:` intro
- Imperative bullet points

**Step 3: Verify no "User wants" phrasing remains**

Run:
```bash
grep -rn "User wants\|User mentions\|User is " plugins/chapterwise/commands/*.md
```
Expected: No matches.

**Step 4: Commit**

```bash
git add plugins/chapterwise/commands/format.md plugins/chapterwise/commands/explode.md plugins/chapterwise/commands/implode.md plugins/chapterwise/commands/lite.md plugins/chapterwise/commands/spreadsheet.md
git commit -m "fix: rewrite 'When This Skill Applies' to imperative form"
```

---

## Task 8: Extract Atlas Section Schemas to References

**Files:**
- Modify: `plugins/chapterwise/commands/atlas.md` (remove lines ~810-1103)
- Create: `plugins/chapterwise/references/atlas-section-schemas.md`

**Step 1: Create the references directory**

```bash
mkdir -p /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise/references
```

**Step 2: Extract section schemas to reference file**

Read atlas.md lines 810-1103 (the "Atlas Section Types" section with all YAML schemas for Characters, Timeline, Themes, Plot Structure, Locations, Relationships, World, Topic Map, Imagery).

Write this content to `references/atlas-section-schemas.md` with a header:
```markdown
# Atlas Section Type Schemas

Full output format for each atlas section type, following the Codex node schema.
Reference this file when building or updating atlas sections.

[paste all section schemas here]
```

**Step 3: Replace the section in atlas.md with a reference pointer**

Replace the ~293 lines of schemas with:
```markdown
## Atlas Section Types

Full schemas for each section type are documented in the reference file:

Read `${CLAUDE_PLUGIN_ROOT}/references/atlas-section-schemas.md` for the complete YAML format for each section type: Characters, Timeline, Themes, Plot Structure, Locations, Relationships, World (fantasy), Topic Map (nonfiction), Imagery (poetry).

Each section follows the standard Codex node schema with section-specific `attributes` and `children` structures.
```

**Step 4: Verify atlas.md is significantly shorter**

Run:
```bash
wc -l plugins/chapterwise/commands/atlas.md
wc -l plugins/chapterwise/references/atlas-section-schemas.md
```
Expected: atlas.md ~900 lines (down from 1201), schemas file ~300 lines.

**Step 5: Commit**

```bash
git add plugins/chapterwise/commands/atlas.md plugins/chapterwise/references/atlas-section-schemas.md
git commit -m "refactor: extract atlas section schemas to references/ — atlas.md -25%"
```

---

## Task 9: Extract Shared Language Rules to References

**Files:**
- Create: `plugins/chapterwise/references/language-rules.md`
- Modify: `plugins/chapterwise/commands/import.md` (language rules section)
- Modify: `plugins/chapterwise/commands/analysis.md` (language rules section)
- Modify: `plugins/chapterwise/commands/atlas.md` (language rules section)
- Modify: `plugins/chapterwise/commands/reader.md` (language rules section)
- Modify: `plugins/chapterwise/commands/pipeline.md` (language rules section)
- Modify: `plugins/chapterwise/commands/status.md` (language rules section)

**Step 1: Create shared language rules reference**

Read the Language Rules sections from import.md, analysis.md, atlas.md, reader.md. Identify the common rules that repeat across all files. Write a consolidated `references/language-rules.md`:

```markdown
# ChapterWise Language Rules

These rules apply to ALL recipe commands. Read and follow them exactly.

## Core Rules

1. **Never say "recipe" to the user.** Internally it's the recipe system. Externally, just describe what's happening.
2. **No theatrical cooking language.** Never use: "order up", "bon appetit", "chef's kiss", "ready to serve", "plating", "garnish".
3. **Use cooking verbs naturally** in progress messages — scan, slice, season, simmer, fold, reduce. These are the action verbs, not metaphors.
4. **Report real data.** Every progress message includes actual numbers: chapter counts, word counts, file counts, module names.
5. **Phase names match the command.** Import: Scan/Slice/Season/Fold/Done. Analysis: courses. Atlas: Scan/Extract/Analyze/Synthesize/Assemble/Done.

## Progress Message Formula

`[cooking verb] [technical noun]... [real data]`

Examples:
- "Scanning structure... PDF, 342 pages, three-act novel."
- "Slicing chapters... 28 found across 3 parts."
- "Extracting entities... 14 characters, 8 locations across 28 chapters."

## Tool Usage

- Use the **Glob** tool for file discovery (never `find`)
- Use the **Read** tool for file reading (never `cat`)
- Use the **Grep** tool for content search (never `grep` or `rg`)
- Call scripts via stdin JSON: `echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py`
```

**Step 2: Replace duplicated sections in each command**

In each recipe command file, replace the full Language Rules section with:

```markdown
## Language Rules

Read and follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all messaging rules.

[Keep ONLY command-specific rules here, e.g., specific phase names for this command]
```

**Step 3: Verify**

Run:
```bash
ls plugins/chapterwise/references/language-rules.md && echo "EXISTS"
```

**Step 4: Commit**

```bash
git add plugins/chapterwise/references/language-rules.md plugins/chapterwise/commands/import.md plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/reader.md plugins/chapterwise/commands/pipeline.md plugins/chapterwise/commands/status.md
git commit -m "refactor: extract shared language rules to references/ — DRY across 6 commands"
```

---

## Task 10: Add `author` to plugin.json and Create Plugin README

**Files:**
- Modify: `plugins/chapterwise/.claude-plugin/plugin.json`
- Create: `plugins/chapterwise/README.md`

**Step 1: Add author field to plugin.json**

Edit plugin.json to add author:
```json
{
  "name": "chapterwise",
  "description": "Complete writing toolkit for ChapterWise — import any manuscript, run AI analysis, build story atlases, create custom readers. Supports PDF, DOCX, Scrivener, Ulysses, Markdown, and more.",
  "version": "2.0.0",
  "author": "Anson Phong",
  "homepage": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

**Step 2: Create plugin-level README.md**

Write a brief README listing all commands, grouped by category:

```markdown
# ChapterWise Plugin

Complete writing toolkit for ChapterWise. Import manuscripts, run AI analysis, build story atlases, create custom readers.

## Recipe Commands

| Command | Description |
|---------|-------------|
| `/import` | Import manuscripts (PDF, DOCX, Scrivener, etc.) |
| `/analysis` | Run AI analysis with 31 modules |
| `/atlas` | Build cross-chapter reference atlas |
| `/reader` | Generate static HTML reader |
| `/status` | Show project status dashboard |
| `/pipeline` | Run full chain: import → analysis → atlas → reader |

## Codex Utilities

| Command | Description |
|---------|-------------|
| `/format` | Format content as Codex YAML |
| `/explode` | Split codex into child files |
| `/implode` | Merge child files back |
| `/lite` | Create Codex Lite Markdown |
| `/insert` | Insert notes by semantic location |
| `/diagram` | Create Mermaid diagrams |
| `/spreadsheet` | Create codex spreadsheets |
| `/convert-to-codex` | Convert Markdown to Codex |
| `/convert-to-markdown` | Convert Codex to Markdown |
| `/generate-tags` | Auto-generate tags |
| `/update-word-count` | Update word counts |
| `/format-folder` | Batch fix codex folder |
| `/format-regen-ids` | Regenerate all IDs |
| `/index` | Generate index.codex.yaml |

## Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- Optional: PyMuPDF (PDF), python-docx (DOCX), beautifulsoup4 (HTML)
```

**Step 3: Commit**

```bash
git add plugins/chapterwise/.claude-plugin/plugin.json plugins/chapterwise/README.md
git commit -m "docs: add author to plugin.json and create plugin README"
```

---

## Task 11: Document Script Interface Convention

**Files:**
- Create: `plugins/chapterwise/scripts/README.md`

**Step 1: Create scripts README documenting which scripts use which interface**

```markdown
# Scripts Interface Guide

## stdin JSON → stdout JSON

These scripts accept JSON on stdin and return JSON on stdout:
- `recipe_manager.py` — `echo '{"project_path":".","type":"import"}' | python3 recipe_manager.py create`
- `format_detector.py` — `echo '{"path":"file.pdf"}' | python3 format_detector.py`
- `recipe_validator.py` — `echo '{"recipe_path":"..."}' | python3 recipe_validator.py`
- `codex_validator.py` — `echo '{"path":"...","fix":false}' | python3 codex_validator.py`
- `run_recipe.py` — `echo '{"recipe_path":"..."}' | python3 run_recipe.py`

## CLI (argparse)

These scripts use standard CLI arguments:
- `auto_fixer.py` — `python3 auto_fixer.py input.codex.yaml`
- `convert_format.py` — `python3 convert_format.py input.md output.codex.yaml`
- `explode_codex.py` — `python3 explode_codex.py input.codex.yaml`
- `implode_codex.py` — `python3 implode_codex.py input.codex.yaml`
- `index_generator.py` — `python3 index_generator.py /project/dir`
- `insert_engine.py` — `python3 insert_engine.py --file target.codex.yaml --note "text"`
- `lite_helper.py` — `python3 lite_helper.py input.codex.yaml`
- `location_finder.py` — `python3 location_finder.py search input.codex.yaml "query"`
- `scrivener_import.py` — `python3 scrivener_import.py Project.scriv output_dir`
- `tag_generator.py` — `python3 tag_generator.py input.codex.yaml`
- `word_count.py` — `python3 word_count.py input.codex.yaml`

## Library-Only (imported, no CLI)

- `analysis_writer.py` — Write .analysis.json files
- `staleness_checker.py` — Hash-based change detection
- `schema_validator.py` — Schema validation utilities
- `module_loader.py` — Module discovery (also has CLI: `python3 module_loader.py list|get|courses|recommend`)
- `note_parser.py` — Note parsing dataclass
```

**Step 2: Commit**

```bash
git add plugins/chapterwise/scripts/README.md
git commit -m "docs: document script interface conventions (stdin JSON vs argparse vs library)"
```

---

## Task 12: Verify `Task` and `AskUserQuestion` Tool Names

**Files:**
- Modify (if needed): `plugins/chapterwise/commands/insert.md:4`
- Modify (if needed): `plugins/chapterwise/commands/import-scrivener.md:4`
- Modify (if needed): `plugins/chapterwise/commands/import.md:3`
- Modify (if needed): `plugins/chapterwise/commands/analysis.md:3`
- Modify (if needed): `plugins/chapterwise/commands/atlas.md:3`
- Modify (if needed): `plugins/chapterwise/commands/reader.md:3`
- Modify (if needed): `plugins/chapterwise/commands/pipeline.md:3`

**Step 1: Check Claude Code documentation for valid allowed-tools names**

The standard Claude Code tools are: `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `NotebookEdit`, `NotebookRead`, `Agent`, `AskUserQuestion`, `Task`, `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`.

`AskUserQuestion` and `Task` ARE valid Claude Code tool names. `AskUserQuestion` is used for interactive questions. `Task` refers to the Task agent tool (subagent dispatch).

**Step 2: Verify — no changes needed**

These tool names are correct. Mark as verified, no code changes.

**Step 3: Commit (skip — no changes)**

---

## Task 13: Verify `index.md` disable-model-invocation Setting

**Files:**
- Review: `plugins/chapterwise/commands/index.md:4`

**Step 1: Read the file and understand the setting**

Read `plugins/chapterwise/commands/index.md`. Check if `disable-model-invocation: true` makes sense for this command.

`disable-model-invocation` prevents programmatic invocation — the command can only be triggered by user typing `/index`. For an index generation command that creates files, this safety measure is reasonable if the team wants to prevent accidental index overwrites.

**Step 2: Verify — likely intentional, no change unless user disagrees**

Flag for user review during execution. If they want programmatic invocation (e.g., from `/pipeline`), remove it.

---

## Task 14: Final Verification Pass

**Files:** All modified files from Tasks 1-11

**Step 1: Run full audit verification**

```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise

echo "=== Description lengths ==="
for f in commands/*.md; do
  desc=$(grep '^description:' "$f" | head -1 | sed 's/description: *//; s/^"//; s/"$//')
  len=${#desc}
  if [ $len -gt 60 ]; then echo "FAIL $f ($len)"; fi
done

echo "=== Missing argument-hint ==="
for f in commands/*.md; do
  if ! grep -q "argument-hint:" "$f"; then echo "MISSING $f"; fi
done

echo "=== Duplicate triggers ==="
grep -h "^  - " commands/*.md | sort | uniq -d

echo "=== Recipe in user text ==="
grep -rn "All recipes\|Reader Recipe" commands/*.md

echo "=== find/cat in instructions ==="
grep -n "^find \.\|^cat " commands/*.md

echo "=== Glob pseudo-syntax ==="
grep -n "^Glob:" commands/*.md

echo "=== Description violations ==="
grep -rn "User wants\|User mentions\|User is structuring" commands/*.md

echo "=== File counts ==="
wc -l commands/atlas.md commands/diagram.md

echo "=== References exist ==="
ls references/atlas-section-schemas.md references/language-rules.md 2>/dev/null && echo "REFS OK"
```

Expected: All checks pass with zero violations.

**Step 2: Run trigger collision check with deprecated stubs**

```bash
STUB_TRIGGERS=$(grep -h "^  - " ../chapterwise-codex/commands/*.md ../chapterwise-analysis/commands/*.md 2>/dev/null | sort)
UNIFIED_TRIGGERS=$(grep -h "^  - " commands/*.md 2>/dev/null | sort)
comm -12 <(echo "$STUB_TRIGGERS") <(echo "$UNIFIED_TRIGGERS") | head -5
```
Expected: No output (zero collisions).

**Step 3: Commit final verification**

```bash
git add -A
git commit -m "chore: plugin audit fixes complete — all 34 issues addressed"
```

---

## Summary

| Task | What | Issues Fixed | Severity |
|------|------|-------------|----------|
| 1 | Shorten descriptions | 15 files | HIGH |
| 2 | Add argument-hint | 14 files | MEDIUM |
| 3 | Fix "recipe" leaks | 7 edits | HIGH |
| 4 | Fix tool anti-patterns | 4 files | MEDIUM |
| 5 | Trim diagram.md | 1 file (-480 lines) | HIGH |
| 6 | Fix trigger overlaps | 4 files | HIGH+MEDIUM |
| 7 | Imperative rewrites | 5 files | MEDIUM |
| 8 | Extract atlas schemas | 1 new + 1 modified | HIGH+LOW |
| 9 | Extract language rules | 1 new + 6 modified | LOW (DRY) |
| 10 | plugin.json + README | 2 files | LOW |
| 11 | Script docs | 1 new file | MEDIUM |
| 12 | Verify tool names | 0 changes | HIGH (verified OK) |
| 13 | Verify index.md setting | 0 changes | MEDIUM (flagged) |
| 14 | Final verification | All files | Gate |

**Total: 34 issues addressed across 14 tasks.**
