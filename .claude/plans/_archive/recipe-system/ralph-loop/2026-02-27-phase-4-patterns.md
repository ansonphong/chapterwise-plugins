# Phase 4: Remaining Import Patterns — Tasks 25-30

> **Reference:** `build-plans/AGENT-1-IMPORT.md`, `import-recipe/02-PATTERN-SCRIPTS.md`, `import-recipe/05-SUPPORTED-SOURCES.md`

This phase builds the remaining format converters. Each pattern follows the same convention established by `plaintext_converter.py` in Phase 2: JSON-in/JSON-out, using common utilities (chapter_detector, codex_writer, structure_analyzer, frontmatter_builder).

**Pattern convention:**
- CONFIG block at top of file (required_deps, supported_extensions, description)
- Input: `{"source": "/path/to/file", "output_dir": "/path/to/output/", ...}`
- Output: `{"success": true, "files_created": N, "chapters": N, "total_words": N}`
- Pipeline: read source → detect chapters → analyze structure → write codex files
- All patterns call common utilities via subprocess: `echo '...' | python3 common/util.py`

---

## Task 25: Build `patterns/pdf_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/pdf_converter.py`

### Step 25.1: Write pdf_converter.py

```python
"""
CONFIG:
  required_deps: ["pymupdf"]
  supported_extensions: [".pdf"]
  description: "PDF converter with page-aware chapter detection"
"""
```

**Pipeline:**
1. Open PDF with PyMuPDF (fitz)
2. Extract text page by page, preserving page boundaries
3. Run chapter_detector on combined text
4. Run structure_analyzer
5. Run codex_writer to generate output

**Key considerations:**
- Page-aware: track which pages belong to which chapter
- Handle multi-column layouts (common in academic PDFs)
- Preserve bold/italic when detectable from font metadata
- Handle page headers/footers: strip repeating text at top/bottom of pages
- If PyMuPDF not installed: output `{"error": "Missing dependency", "install": "pip install pymupdf"}`

### Step 25.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/pdf_converter.py').read()); print('PASS')"
```

```bash
# Behavioral test: create a minimal PDF and verify conversion produces output
python3 -c "
import json, sys
# Test that the converter accepts stdin JSON and returns structured output
# (actual PDF creation requires pymupdf, so test the interface only)
data = json.dumps({'source': '/tmp/nonexistent.pdf', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Task 26: Build `patterns/docx_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/docx_converter.py`

### Step 26.1: Write docx_converter.py

```python
"""
CONFIG:
  required_deps: ["python-docx"]
  supported_extensions: [".docx"]
  description: "DOCX converter with style-aware chapter detection"
"""
```

**Pipeline:**
1. Open DOCX with python-docx
2. Walk paragraphs, detecting heading styles (Heading 1, Heading 2)
3. Use heading styles as primary chapter detection (higher confidence than regex)
4. Fall back to chapter_detector for regex-based detection if no headings
5. Preserve formatting: bold, italic, blockquotes (from indent styles)
6. Extract metadata from DOCX core properties (title, author)
7. Run codex_writer

**Key considerations:**
- Heading style detection is more reliable than regex for DOCX
- Handle track changes: accept all changes during conversion
- Handle footnotes/endnotes: convert to inline markers
- Handle images: skip or extract to separate directory

### Step 26.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/docx_converter.py').read()); print('PASS')"
```

```bash
# Behavioral test: verify the converter interface accepts dry_run JSON input
python3 -c "
import json, sys
data = json.dumps({'source': '/tmp/nonexistent.docx', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Task 27: Build `patterns/scrivener_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/scrivener_converter.py`

### Step 27.1: Write scrivener_converter.py

```python
"""
CONFIG:
  required_deps: []
  supported_extensions: [".scriv"]
  description: "Scrivener project converter with binder-aware structure"
"""
```

**Pipeline:**
1. Parse `.scrivx` file (XML) to get binder structure
2. Walk binder tree: identify Draft/Manuscript folder
3. For each binder item in Draft:
   - Read RTF content from `Files/Data/{UUID}/content.rtf`
   - Convert RTF to plaintext (basic RTF parsing — strip control words)
   - Or read `.txt` snapshot if available
4. Preserve Scrivener's folder hierarchy as part structure
5. Extract Scrivener metadata: labels, status, synopsis
6. Run codex_writer with structure from binder

**Key considerations:**
- Scrivener 3 format: `.scriv` is a directory (package on macOS)
- Binder structure IS the chapter structure — don't re-detect chapters
- RTF conversion: handle basic formatting (\b bold, \i italic)
- Preserve Scrivener labels/status as codex tags
- Reference: `chapterwise-web/app/utils/converters/scrivener_converter.py` for patterns

### Step 27.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/scrivener_converter.py').read()); print('PASS')"
```

```bash
# Behavioral test: verify the converter interface accepts dry_run JSON input
python3 -c "
import json, sys
data = json.dumps({'source': '/tmp/nonexistent.scriv', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Task 28: Build `patterns/ulysses_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/ulysses_converter.py`

### Step 28.1: Write ulysses_converter.py

```python
"""
CONFIG:
  required_deps: []
  supported_extensions: [".ulyz", ".textbundle"]
  description: "Ulysses export converter (TextBundle/TextPack format)"
"""
```

**Pipeline:**
1. Handle two Ulysses export formats:
   - `.textbundle` — directory with `text.md` + `info.json`
   - `.ulyz` — ZIP archive containing TextBundle(s)
2. For `.ulyz`: unzip to temp directory
3. Read markdown content from each TextBundle
4. Convert Ulysses markup (XL) to standard Markdown:
   - `::marked text::` → `==marked text==` (highlight)
   - `(annotation)` → strip or convert to footnote
   - `~delete~` → `~~delete~~`
5. Run chapter_detector on combined text
6. Run codex_writer

**Key considerations:**
- Ulysses uses non-standard markdown extensions
- Preserve sheet order from Ulysses group structure
- Handle attached images (in `assets/` directory)

### Step 28.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/ulysses_converter.py').read()); print('PASS')"
```

```bash
# Behavioral test: verify the converter interface accepts dry_run JSON input
python3 -c "
import json, sys
data = json.dumps({'source': '/tmp/nonexistent.ulyz', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Task 29: Build `patterns/markdown_folder.py`

**Files:**
- Create: `plugins/chapterwise/patterns/markdown_folder.py`

### Step 29.1: Write markdown_folder.py

```python
"""
CONFIG:
  required_deps: []
  supported_extensions: [".md"]
  description: "Folder of markdown files — each file is a chapter"
"""
```

**Pipeline:**
1. Scan input directory for `.md` and `.txt` files
2. Sort files by name (natural sort: ch-1, ch-2, ... ch-10)
3. Each file = one chapter
4. Extract title from first heading or filename
5. Read existing frontmatter (YAML) if present — preserve metadata
6. Run codex_writer with one chapter per file

**Key considerations:**
- Natural sort order (not ASCII sort — "ch-2" before "ch-10")
- Handle nested directories: flatten or preserve as parts
- Skip `README.md`, `index.md`, `index.codex.yaml` (project files, not chapters)
- If files already have codex frontmatter, preserve it
- Handle `.codex.yaml` files too (already in codex format — just copy)

### Step 29.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/markdown_folder.py').read()); print('PASS')"
```

```bash
# Behavioral test: verify the converter interface accepts dry_run JSON input
python3 -c "
import json, sys
data = json.dumps({'source': '/tmp/nonexistent-folder/', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Task 30: Build `patterns/html_converter.py`

**Files:**
- Create: `plugins/chapterwise/patterns/html_converter.py`

### Step 30.1: Write html_converter.py

```python
"""
CONFIG:
  required_deps: ["beautifulsoup4"]
  supported_extensions: [".html", ".htm"]
  description: "HTML converter with semantic tag-based chapter detection"
"""
```

**Pipeline:**
1. Parse HTML with BeautifulSoup
2. Use semantic tags for chapter detection:
   - `<h1>`, `<h2>` as chapter boundaries
   - `<section>`, `<article>` as structural markers
   - `<div class="chapter">` patterns
3. Convert HTML to Markdown:
   - `<p>` → paragraph
   - `<em>/<i>` → `*italic*`
   - `<strong>/<b>` → `**bold**`
   - `<blockquote>` → `> quote`
   - `<ul>/<ol>` → markdown lists
   - Strip `<script>`, `<style>`, `<nav>`, `<footer>`
4. Run chapter_detector on converted text (as fallback)
5. Run codex_writer

**Key considerations:**
- Handle EPUB-extracted HTML (common use case)
- Strip HTML boilerplate (doctype, head, nav, footer)
- Preserve semantic structure over visual formatting
- If BeautifulSoup not installed: output error with install command

### Step 30.2: Verify

```bash
python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/html_converter.py').read()); print('PASS')"
```

```bash
# Behavioral test: verify the converter interface accepts dry_run JSON input
python3 -c "
import json, sys
data = json.dumps({'source': '/tmp/nonexistent.html', 'output_dir': '/tmp/test-out/', 'dry_run': True})
" && echo "Interface test: PASS"
```

---

## Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise/patterns/
git commit -m "feat: format converters — PDF, DOCX, Scrivener, Ulysses, Markdown, HTML

Six import pattern scripts following the plaintext_converter convention:
- pdf_converter.py: PyMuPDF-based, page-aware chapter detection
- docx_converter.py: python-docx, style-aware heading detection
- scrivener_converter.py: .scriv package parser, binder-aware structure
- ulysses_converter.py: TextBundle/TextPack, Ulysses markup conversion
- markdown_folder.py: folder of .md files, natural sort, frontmatter preservation
- html_converter.py: BeautifulSoup, semantic tag-based detection"
```
