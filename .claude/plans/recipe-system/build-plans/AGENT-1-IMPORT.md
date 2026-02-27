# Agent 1: Import Recipe — Build Plan

**Agent type:** general-purpose (worktree isolation)
**Design docs:** `import-recipe/00-OVERVIEW.md` through `05-SUPPORTED-SOURCES.md`
**Language rules:** `LANGUAGE-GUIDE.md` (Import Recipe section)

---

## What This Agent Builds

| # | File | Lines (est.) | Purpose |
|---|------|-------------|---------|
| 1 | `commands/import.md` | 400-500 | Main import skill — the brain |
| 2 | `commands/import-scrivener.md` | 20 | Alias → routes to import.md |
| 3 | `patterns/plaintext_converter.py` | 150 | Simplest converter — build first |
| 4 | `patterns/common/chapter_detector.py` | 200 | Shared chapter boundary detection |
| 5 | `patterns/common/codex_writer.py` | 250 | Write .codex.yaml + index.codex.yaml |
| 6 | `patterns/common/structure_analyzer.py` | 150 | Analyze document structure |
| 7 | `patterns/common/frontmatter_builder.py` | 100 | Generate YAML frontmatter |
| 8 | `patterns/pdf_converter.py` | 200 | PDF extraction via PyMuPDF |
| 9 | `patterns/docx_converter.py` | 180 | DOCX extraction via python-docx |
| 10 | `patterns/scrivener_converter.py` | 250 | Scrivener .scriv conversion |
| 11 | `patterns/ulysses_converter.py` | 180 | Ulysses .ulyz conversion |
| 12 | `patterns/markdown_folder.py` | 120 | Folder of .md/.txt files |
| 13 | `patterns/html_converter.py` | 150 | HTML parsing via BeautifulSoup |

---

## Build Order

### Step 1: Common utilities first

Build `patterns/common/` — these are used by ALL converters.

#### `chapter_detector.py`

```python
"""
Chapter Detector — Find chapter boundaries in text.

Input (stdin JSON):
  {"text": "full manuscript text", "hints": {"pattern": "^Chapter \\d+"}}

Output (stdout JSON):
  {
    "chapters": [
      {"title": "Chapter 1: The Beginning", "start_offset": 0, "end_offset": 3200, "word_count": 3200},
      ...
    ],
    "detection_method": "heading_pattern",
    "confidence": 0.95
  }
"""
```

**Detection methods (in priority order):**
1. `heading_pattern` — Regex on chapter headings (Chapter 1, Chapter I, CHAPTER ONE, etc.)
2. `separator_pattern` — Consistent separators (---, ***, blank lines with centered text)
3. `page_break` — Form feed characters or explicit page breaks
4. `heuristic` — Length-based splitting when no patterns found (target ~3000 words)

**Key patterns to detect:**
```python
CHAPTER_PATTERNS = [
    r'^Chapter\s+(\d+|[IVXLC]+)',           # Chapter 1, Chapter IV
    r'^CHAPTER\s+(\d+|[IVXLC]+)',           # CHAPTER 1
    r'^(\d+)\.\s+',                          # 1. Title
    r'^Part\s+(\d+|[IVXLC]+)',              # Part markers
    r'^Prologue|^Epilogue|^Introduction',    # Special sections
    r'^Act\s+(\d+|[IVXLC]+)',               # Screenplay acts
]
```

#### `codex_writer.py`

```python
"""
Codex Writer — Write chapter files + index.codex.yaml.

Input (stdin JSON):
  {
    "output_dir": "./my-novel/",
    "format": "markdown",           # "markdown" or "codex"
    "structure": "folders_per_part", # "flat", "folders_per_part"
    "chapters": [
      {"title": "Chapter 1", "content": "...", "part": "Part I", "word_count": 3200, "tags": []},
      ...
    ],
    "metadata": {"title": "My Novel", "author": "Jane Smith"}
  }

Output (stdout JSON):
  {"files_created": 31, "index_path": "index.codex.yaml", "total_words": 87234}
"""
```

**Output formats:**
- **Markdown (Codex Lite):** `.md` files with YAML frontmatter
- **Codex YAML:** `.codex.yaml` files with full structure

**Structure options:**
- **flat:** All chapter files in root
- **folders_per_part:** `part-1-departure/chapter-01.md`, `part-2-initiation/chapter-02.md`

**File naming:** Slugified from title — lowercase, hyphens, no special chars. See `url_path_resolver.py` in chapterwise-web for reference.

#### `structure_analyzer.py`

```python
"""
Structure Analyzer — Analyze document structure, output structure_map.yaml.

Input (stdin JSON):
  {"text": "full manuscript text", "format": "pdf", "page_count": 342}

Output (stdout JSON):
  {
    "type": "three_act",
    "has_parts": true,
    "part_count": 3,
    "chapter_count": 28,
    "has_prologue": true,
    "has_epilogue": true,
    "special_sections": ["Dedication", "About the Author"],
    "estimated_word_count": 87000
  }
"""
```

#### `frontmatter_builder.py`

```python
"""
Frontmatter Builder — Generate YAML frontmatter for Codex Lite files.

Input (stdin JSON):
  {"title": "Chapter 1", "word_count": 3200, "tags": ["adventure"], "summary": "..."}

Output (stdout):
  ---
  title: Chapter 1
  word_count: 3200
  tags: [adventure]
  summary: "..."
  ---
"""
```

### Step 2: Plaintext converter (simplest)

#### `patterns/plaintext_converter.py`

```python
"""
Plaintext Converter — Convert .txt files to Codex project.

Usage as tool:
  echo '{"source": "novel.txt", "output_dir": "./my-novel/", "options": {...}}' | python3 plaintext_converter.py

Usage as teaching material:
  The agent reads this file to understand the converter pattern, then generates
  custom variants for unusual formats.

CONFIG:
  required_deps: []
  supported_extensions: [".txt"]
  description: "Plain text with heuristic chapter detection"
"""
```

**Pipeline:**
1. Read source file
2. Run `chapter_detector.py` on full text
3. Run `structure_analyzer.py` for metadata
4. Run `codex_writer.py` to generate output files
5. Return file manifest

### Step 3: PDF converter

#### `patterns/pdf_converter.py`

Same pattern as plaintext, but:
1. Check for PyMuPDF (`import fitz`)
2. Extract text page by page
3. Handle page headers/footers (strip repeated lines)
4. Detect chapter breaks that span page boundaries
5. Preserve basic formatting (bold headings, italics)

### Step 4: DOCX converter

#### `patterns/docx_converter.py`

1. Check for python-docx (`import docx`)
2. Extract paragraphs with style information
3. Use heading styles (Heading 1, Heading 2) for chapter detection
4. Preserve formatting (bold, italic, underline)
5. Handle tables, lists, footnotes

### Step 5: Scrivener converter

#### `patterns/scrivener_converter.py`

Adapted from existing `chapterwise-codex/scripts/scrivener_import.py`:
1. Parse `.scriv/` directory structure
2. Read `project.scrivx` XML for document tree
3. Extract RTF content from `Files/Docs/` (use striprtf)
4. Preserve Scrivener metadata (labels, status, keywords → tags)
5. Map Scrivener Binder structure to Codex folder structure

### Step 6: Ulysses, markdown folder, HTML converters

These follow the same CONFIG pattern. Each is 120-200 lines.

### Step 7: The main skill — `commands/import.md`

This is the **most important file**. It's the natural language instructions that tell Claude how to orchestrate the entire import workflow.

**Structure of import.md:**

```markdown
---
description: "Import any manuscript into a ChapterWise project"
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
argument-hint: "[path/to/file-or-folder]"
---

# ChapterWise Import

## Overview
[What this command does — one paragraph]

## Step 1: Check for Existing Recipe
[Look for .chapterwise/import-recipe/recipe.yaml]
[If found: "I remember this one — {details}. Same approach, or start fresh?"]
[If same: jump to Step 6 (fast path)]

## Step 2: Detect Format
[Run format_detector.py]
[If unknown: explain what you see, ask what kind of file]

## Step 3: Scan Structure
[Run structure_analyzer.py or read pattern script for format-specific analysis]
[Report: "Scanning structure... {format}, {pages/files}, {type}"]

## Step 4: Interview (First Import Only)
[Ask 3-4 questions per interview spec]
[Q1: Structure — flat files or folders per part?]
[Q2: Source app metadata — preserve or strip?]
[Q3: Format — Markdown (Codex Lite) or full Codex YAML?]
[Q4: Non-content — include front/back matter?]

## Step 5: Write Recipe
[Create .chapterwise/import-recipe/]
[Save recipe.yaml, preferences.yaml, structure_map.yaml]

## Step 6: Convert (Prep + Cook + Season)
[Check dependencies — install prompts if missing]
[Run pattern converter]
[For parallel: split chapters into batches, use Task agents]
[Progress: "Cutting chapters... N found"]
[Progress: "Cooking chapter N: Title (word_count words)"]
[Progress: "Seasoning metadata... tags, summaries, word counts"]

## Step 7: Build Index
[Generate index.codex.yaml]
[Progress: "Building index..."]

## Step 8: Validate and Heal
[Run codex_validator.py on the output directory with fix=true]
[This auto-fixes: missing frontmatter fields, empty word counts, orphan files, invalid UUIDs]
[Run recipe_validator.py on .chapterwise/import-recipe/]
[If issues found and fixed: report briefly — "Fixed 2 formatting issues."]
[If issues found and NOT fixable: warn user — "Chapter 3 has an encoding issue — review manually."]
[If clean: say nothing — validation is invisible when it passes]

## Step 9: Review and Save
[Present file tree with counts]
[Progress: "Done. N files, N words."]
[Save recipe for reuse]
[Suggest next steps: git, /analysis, /atlas]

## Error Handling
[Format-specific errors with clear messages]
[Missing deps: exact install command]
[Partial failures: flag chapters that failed, continue with rest]

## Re-Import (Fast Path)
[Load recipe.yaml → check source hash → run convert.py]
[If structure changed: offer to patch or rebuild]

## Fallback Creativity
[When no pattern exists: read existing patterns, understand the converter pattern, generate custom converter]
[Save generated converter as convert.py in recipe folder]

## Language Rules
[Reference LANGUAGE-GUIDE.md — cooking verb + data noun formula]
[Never say "recipe" to user]
```

### Step 8: Import-Scrivener alias

```markdown
---
description: "Import a Scrivener project (.scriv)"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - scrivener import
  - import scrivener
  - scriv to markdown
argument-hint: "[path/to/Project.scriv]"
---

This is a Scrivener import. Follow the main import workflow from `import.md`
with format pre-set to Scrivener. Skip format detection.
```

---

## Testing Checklist

After building, verify these scenarios work:

- [ ] `/import test.txt` — Plaintext file with chapter headings
- [ ] `/import novel.pdf` — PDF with Roman numeral chapters
- [ ] `/import manuscript.docx` — DOCX with heading styles
- [ ] `/import ./my-novel/` — Folder of markdown files
- [ ] Re-import: run `/import test.txt` again → "I remember this one..."
- [ ] Recipe reuse: verify `.chapterwise/import-recipe/` was created and contains recipe.yaml
- [ ] Unknown format: `/import weird.format` → agent generates custom converter
- [ ] `format_detector.py` correctly identifies all supported formats
- [ ] `chapter_detector.py` finds chapters in test text
- [ ] `codex_writer.py` produces valid index.codex.yaml
- [ ] Validation: `codex_validator.py` passes on import output (no issues)
- [ ] Self-healing: deliberately corrupt a frontmatter field, re-run validator with fix=true, verify it's repaired

---

## Dependencies on Phase 0

This agent assumes Phase 0 has already:
- Created the unified plugin directory structure
- Built `scripts/recipe_manager.py`
- Built `scripts/format_detector.py`
- Created `patterns/common/` directory

---

## What This Agent Does NOT Build

- Analysis, atlas, or reader commands (other agents)
- `scripts/recipe_manager.py` (Phase 0)
- `scripts/format_detector.py` (Phase 0)
- Web app integration
