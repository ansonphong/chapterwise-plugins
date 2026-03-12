# Phase 2: Import Recipe — The First Real Deliverable — Tasks 11-18

> **Reference:** `build-plans/AGENT-1-IMPORT.md`, `import-recipe/01-AGENT-WORKFLOW.md`, `import-recipe/02-PATTERN-SCRIPTS.md`

This phase builds the import recipe end-to-end: common utilities, the plaintext converter, and the main `import.md` skill file. After this phase, `/import my-novel.txt` actually works.

---

## Task 11: Build `patterns/common/chapter_detector.py`

**Files:**
- Create: `plugins/chapterwise/patterns/common/chapter_detector.py`

### Step 11.1: Write chapter_detector.py

JSON-in/JSON-out. Detects chapter boundaries in text using heading patterns.

**Input:** `{"text": "...", "hints": {"pattern": "^Chapter \\d+"}}`
**Output:** `{"chapters": [...], "detection_method": "heading_pattern", "confidence": 0.95}`

**Detection methods (priority order):**
1. Heading patterns: `^Chapter \d+`, `^CHAPTER \d+`, `^Part \d+`, Roman numerals
2. Separator patterns: `---`, `***`, form feeds
3. Heuristic: equal-length splitting (~3000 words) when no patterns found

**Key:** Include part detection, prologue/epilogue detection, and special section markers.

### Step 11.2: Verify

```bash
echo '{"text":"Chapter 1: Hello World\nSome text here about things.\n\nChapter 2: Goodbye\nMore text about other things."}' | python3 plugins/chapterwise/patterns/common/chapter_detector.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('chapters',[]))>=2 else 'FAIL')"
```

---

## Task 12: Build `patterns/common/codex_writer.py`

**Files:**
- Create: `plugins/chapterwise/patterns/common/codex_writer.py`

### Step 12.1: Write codex_writer.py

**Input:**
```json
{
  "output_dir": "./my-novel/",
  "format": "markdown",
  "structure": "flat",
  "chapters": [
    {"title": "Chapter 1", "content": "...", "word_count": 3200, "tags": [], "part": null}
  ],
  "metadata": {"title": "My Novel", "author": "Jane Smith"}
}
```

**Output:** `{"files_created": 31, "index_path": "index.codex.yaml", "total_words": 87234}`

**What it does:**
1. Create output directory
2. For each chapter: write a `.md` file (Codex Lite) or `.codex.yaml`
3. Generate `index.codex.yaml` with children array referencing all files
4. Apply file naming: slugified from title, lowercase, hyphens
5. If `structure: "folders_per_part"`: create `part-N-name/` directories

**File naming convention (match url_path_resolver.py):**
- Strip special chars: `()&,.[]+`
- Spaces to hyphens
- Collapse multiple hyphens
- Lowercase

### Step 12.2: Verify

```bash
echo '{"output_dir":"/tmp/test-codex-writer","format":"markdown","structure":"flat","chapters":[{"title":"Chapter 1","content":"Hello world.","word_count":2},{"title":"Chapter 2","content":"Goodbye.","word_count":1}],"metadata":{"title":"Test Novel"}}' | python3 plugins/chapterwise/patterns/common/codex_writer.py && ls /tmp/test-codex-writer/index.codex.yaml && echo PASS
```

---

## Task 13: Build `patterns/common/structure_analyzer.py`

**Files:**
- Create: `plugins/chapterwise/patterns/common/structure_analyzer.py`

### Step 13.1: Write structure_analyzer.py

Scans text to determine manuscript structure: type, part count, chapter count, special sections.

**Input:** `{"text": "...", "format": "pdf", "page_count": 342}`
**Output:** `{"type": "three_act", "has_parts": true, "part_count": 3, "chapter_count": 28, ...}`

### Step 13.2: Verify

```bash
echo '{"text":"Part I\nChapter 1\nText here\nChapter 2\nMore text\nPart II\nChapter 3\nEven more text"}' | python3 plugins/chapterwise/patterns/common/structure_analyzer.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('chapter_count',0)>=2 else 'FAIL')"
```

---

## Task 14: Build `patterns/common/frontmatter_builder.py`

**Files:**
- Create: `plugins/chapterwise/patterns/common/frontmatter_builder.py`

### Step 14.1: Write frontmatter_builder.py

**Input:** `{"title": "Chapter 1", "word_count": 3200, "tags": ["adventure"], "summary": "..."}`
**Output:** YAML frontmatter block on stdout

### Step 14.2: Verify

```bash
echo '{"title":"Chapter 1","word_count":3200,"tags":["adventure"]}' | python3 plugins/chapterwise/patterns/common/frontmatter_builder.py | grep -q "^---" && echo PASS
```

---

## Task 15: Build `patterns/plaintext_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/plaintext_converter.py`

### Step 15.1: Write plaintext_converter.py

The simplest end-to-end converter. Proves the entire pipeline works.

**Pipeline:**
1. Read source .txt file
2. Call chapter_detector to find boundaries
3. Call structure_analyzer for metadata
4. Call codex_writer to generate output

**CONFIG block** (at top of file — the agent reads this to understand what the pattern does):
```python
"""
CONFIG:
  required_deps: []
  supported_extensions: [".txt"]
  description: "Plain text with heuristic chapter detection"
"""
```

### Step 15.2: Verify with real test

```bash
echo "Chapter 1: The Beginning\nOnce upon a time there was a story.\n\nChapter 2: The Middle\nThen things happened in the middle.\n\nChapter 3: The End\nAnd finally it was over." > /tmp/test-novel.txt
echo '{"source":"/tmp/test-novel.txt","output_dir":"/tmp/test-import/"}' | python3 plugins/chapterwise/patterns/plaintext_converter.py
ls /tmp/test-import/index.codex.yaml && echo PASS
```

---

## Task 16: Write `commands/import.md` — THE MAIN IMPORT SKILL

**Files:**
- Create: `plugins/chapterwise/commands/import.md`

**BEFORE WRITING, READ:**
- `import-recipe/01-AGENT-WORKFLOW.md` — Full step-by-step workflow
- `import-recipe/03-INTERVIEW-AND-PREFERENCES.md` — Interview questions and decision tree
- `import-recipe/02-PATTERN-SCRIPTS.md` — How patterns work, fallback creativity
- `LANGUAGE-GUIDE.md` — Progress messaging rules

### Step 16.1: Write import.md

This is the brain of the import recipe — ~400-500 lines of markdown instructions for Claude.

**Structure:**
```
---
description/allowed-tools/triggers frontmatter
---

# ChapterWise Import

## Overview (what this does, one paragraph)

## Step 1: Check for Existing Recipe
  - Look for .chapterwise/import-recipe/recipe.yaml via recipe_manager.py load
  - If found: "I remember this one — {title}, {chapters} chapters. Same approach, or start fresh?"
  - If same: skip to Step 6 (fast path via run_recipe.py)
  - If fresh: continue to Step 2

## Step 2: Detect Format
  - Run format_detector.py
  - Report: "Scanning structure... {format}, {details}."
  - If unknown: ask what kind of file

## Step 3: Scan Structure
  - For supported formats: run the appropriate pattern's structure analysis
  - For plaintext: run structure_analyzer.py
  - Report findings: chapters, parts, special sections

## Step 4: Interview (first import only)
  - Q1: "How would you like the chapters organized?" [Folders per part] [Flat files]
  - Q2: Preserve source app metadata? (only for Scrivener/Ulysses)
  - Q3: Format — Markdown or Codex YAML? (default: Markdown)
  - Q4: Include front/back matter? (only if detected)
  - Use AskUserQuestion tool for each

## Step 5: Plan and Save Recipe
  - Create recipe folder via recipe_manager.py create
  - Save structure_map.yaml
  - Save preferences.yaml
  - Write recipe.yaml manifest

## Step 6: Convert (Prep + Cook + Season)
  - Check dependencies (pip packages for the format)
  - Run pattern converter
  - For parallel: batch chapters with Task agents
  - Progress messaging per Language Guide:
    "Checking dependencies... all set."
    "Cutting chapters... {N} found."
    "Cooking chapter {N}: {title} ({word_count} words)"
    "Seasoning metadata... tags, summaries, word counts."

## Step 7: Build Index
  - Generate index.codex.yaml via codex_writer.py
  - "Building index..."

## Step 8: Validate and Heal
  - Run codex_validator.py on output directory with fix=true
  - Run recipe_validator.py on .chapterwise/import-recipe/
  - If fixes were applied: report concise cleanup summary
  - If unfixable issues remain: stop and surface exact files/errors

## Step 9: Review and Save
  - Present file tree
  - "Done. {N} files, {words} words."
  - Save recipe (update recipe.yaml with output stats)
  - Suggest next steps:
    "Next steps:"
    "  Run /analysis for AI-powered literary analysis"
    "  Run /atlas to build a comprehensive reference atlas"
    "  git init && git add -A && git push"

## Re-Import (Fast Path)
  - recipe found → check source hash → if changed: run convert.py
  - "I remember this one — {details}. Same approach, or start fresh?"
  - If structure changed: "Your manuscript changed — {N} chapters now instead of {M}."

## Fallback Creativity (unknown formats)
  - Read existing pattern scripts to understand the converter pattern
  - Generate custom converter.py for the unknown format
  - Save in recipe folder
  - Explain what it's doing before running

## Error Handling
  - Missing dependency: exact pip install command
  - Conversion failure: "Chapter {N} didn't convert cleanly — trying different approach..."
  - Format unknown: "I don't recognize this format. What kind of file is this?"
  - Partial failure: "3 chapters had issues — flagged for review."

## Language Rules
  - Follow LANGUAGE-GUIDE.md strictly
  - Cooking verb + technical noun: "Cutting chapters... 28 found."
  - Never say "recipe" to user
  - No theatrical lines
```

**CRITICAL RULES FOR THIS FILE:**
- Every `${CLAUDE_PLUGIN_ROOT}` reference resolves to the plugin root
- All script calls use: `echo '...' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py`
- All pattern calls use: `echo '...' | python3 ${CLAUDE_PLUGIN_ROOT}/patterns/pattern.py`
- Import workflow must include a post-conversion validator pass (`codex_validator.py` + `recipe_validator.py`)
- Use AskUserQuestion for interview, not inline prompts
- Use Task agents for parallel chapter processing (7 chapters per batch)

### Step 16.2: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/import.md && grep -q "allowed-tools:" plugins/chapterwise/commands/import.md && grep -q "codex_validator.py" plugins/chapterwise/commands/import.md && grep -q "recipe_validator.py" plugins/chapterwise/commands/import.md && ! grep -qi "order up\|bon appetit\|chef.s kiss" plugins/chapterwise/commands/import.md && echo PASS
```

```bash
# Behavioral: verify import.md contains all required workflow steps
for STEP in "Check for Existing Recipe" "Detect Format" "Scan Structure" "Interview" "Plan" "Convert" "Validate and Heal" "Review" "Save Recipe"; do
  grep -q "$STEP" plugins/chapterwise/commands/import.md || echo "FAIL — missing step: $STEP"
done
echo "Workflow completeness: PASS"
```

---

## Task 17: Write `commands/import-scrivener.md`

**Files:**
- Create: `plugins/chapterwise/commands/import-scrivener.md`

### Step 17.1: Write the alias file

~20 lines. Routes to import.md with format pre-set.

```markdown
---
description: "Import a Scrivener project (.scriv) into ChapterWise format"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - scrivener import
  - scrivener to codex
  - convert scrivener
  - scriv to markdown
  - import .scriv
  - scrivener project
argument-hint: "[path/to/Project.scriv]"
---

This is a Scrivener import. Follow the main import workflow from `import.md` with the format pre-set to Scrivener. Skip format detection (Step 2).
```

### Step 17.2: Verify

```bash
grep -q "triggers:" plugins/chapterwise/commands/import-scrivener.md && echo PASS
```

---

## Task 18: Build `scripts/run_recipe.py`

**Files:**
- Create: `plugins/chapterwise/scripts/run_recipe.py`

### Step 18.1: Write run_recipe.py

Execute a saved recipe's convert.py or run.sh.

**Input:** `{"recipe_path": ".chapterwise/import-recipe", "source_path": "new-draft.pdf"}`
**Output:** `{"success": true, "output_path": "./my-novel/", "files_changed": 5}`

### Step 18.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/scripts/run_recipe.py').read()); print('PASS')"
```

---

## Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise/patterns/ plugins/chapterwise/commands/import.md plugins/chapterwise/commands/import-scrivener.md plugins/chapterwise/scripts/run_recipe.py
git commit -m "feat: import recipe — patterns, common utilities, and import.md skill

First working recipe: /import handles plaintext files end-to-end.
- chapter_detector.py: find chapter boundaries via heading patterns
- codex_writer.py: generate codex project files + index
- structure_analyzer.py: detect manuscript structure
- frontmatter_builder.py: YAML frontmatter for Codex Lite
- plaintext_converter.py: full pipeline for .txt files
- import.md: main import skill with recipe system integration
- import-scrivener.md: alias routing to import.md
- run_recipe.py: execute saved recipes"
```
