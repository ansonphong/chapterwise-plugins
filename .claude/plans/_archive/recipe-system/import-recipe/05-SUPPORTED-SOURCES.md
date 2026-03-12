# Import Recipe — Supported Sources

## Overview

ChapterWise Import supports three tiers of source formats:

1. **Bundled** — Pattern scripts included, optimized, tested
2. **On-the-fly** — No bundled script, but the agent can create one using pattern architecture
3. **Via external tools** — Agent uses pandoc, Calibre, or other tools as a first pass, then cleans up

## Tier 1: Bundled Patterns

These formats have dedicated pattern scripts. The agent can run them directly or adapt them.

### PDF (.pdf)
- **Pattern:** `pdf_converter.py`
- **Library:** PyMuPDF
- **Strengths:** Page-accurate extraction, heading detection by font metrics, embedded image extraction
- **Limitations:** Scanned PDFs need OCR (pytesseract); complex layouts may need manual review
- **Web app equivalent:** `convert_pdf_manuscript.py`

### DOCX (.docx)
- **Pattern:** `docx_converter.py`
- **Library:** python-docx
- **Strengths:** Perfect heading detection from Word styles, comments and track changes, embedded media
- **Limitations:** Custom styles may need config tweaks; heavily formatted docs may lose some layout
- **Web app equivalent:** `convert_docx_manuscript.py`

### Scrivener (.scriv)
- **Pattern:** `scrivener_converter.py`
- **Library:** Built-in XML + striprtf
- **Strengths:** Full binder structure, labels, status, keywords, synopsis, compile settings
- **Limitations:** Scrivener 3 format only (Scrivener 2 projects should be opened in Scrivener 3 first)
- **Web app equivalent:** None (agent-only feature)
- **Existing code:** Adapted from `chapterwise-codex` plugin's scrivener_import.py

### Ulysses (.ulyz, TextBundle, markdown export)
- **Pattern:** `ulysses_converter.py`
- **Library:** Built-in
- **Strengths:** Preserves keywords, writing goals, group structure, attachments
- **Limitations:** Ulysses-specific markup (annotations, marked text) converted to standard markdown
- **Web app equivalent:** None (agent-only feature)

### Markdown Files/Folders (.md)
- **Pattern:** `markdown_folder.py`
- **Library:** Built-in
- **Strengths:** Preserves existing frontmatter, mirrors folder structure, smart file sorting
- **Limitations:** Relies on existing structure (files = chapters)
- **Web app equivalent:** `convert_md_manuscript.py` (single file only; folder import is agent-only)
- **Handles:** Obsidian vaults, Bear exports, iA Writer projects, any markdown collection

### HTML (.html)
- **Pattern:** `html_converter.py`
- **Library:** BeautifulSoup
- **Strengths:** Heading-based structure, HTML-to-markdown conversion, multi-file handling
- **Limitations:** Web pages need cleanup (nav, ads, footers stripped heuristically)
- **Web app equivalent:** `convert_html_manuscript.py`

### Plain Text (.txt)
- **Pattern:** `plaintext_converter.py`
- **Library:** Built-in
- **Strengths:** Encoding detection, multiple chapter-heading heuristics, scene-break detection
- **Limitations:** No formatting preserved; chapter detection relies on consistent headings
- **Web app equivalent:** `convert_txt_manuscript.py`

## Tier 2: On-the-Fly (Agent-Generated Converters)

These formats don't have bundled scripts, but the agent can create custom converters using the pattern architecture. Claude knows these formats natively.

### Final Draft (.fdx)
- **Approach:** XML parsing with defusedxml
- **Structure:** Scene Headings as chapter boundaries
- **Preserves:** Action, dialogue, parenthetical, character, transition elements
- **Note:** The web app has `convert_fdx_manuscript.py` as reference

### Fountain (.fountain)
- **Approach:** Regex-based plain text parsing
- **Structure:** Scene headings (INT./EXT.) as boundaries
- **Preserves:** Screenplay formatting elements

### EPUB (.epub)
- **Approach:** ZIP extraction → HTML parsing per chapter file
- **Structure:** OPF spine order + HTML headings
- **Preserves:** Chapter order, text content, embedded images
- **Note:** Agent can also delegate to Calibre for better results

### LaTeX (.tex)
- **Approach:** Regex parsing of `\chapter{}`, `\section{}`, `\part{}` commands
- **Structure:** LaTeX sectioning commands as boundaries
- **Preserves:** Text content; strips LaTeX formatting
- **Note:** For complex LaTeX, the agent may use pandoc as an intermediate step

### RTF (.rtf)
- **Approach:** striprtf library or pandoc
- **Structure:** Heuristic heading detection (bold + large)
- **Web app equivalent:** `convert_rtf_manuscript.py` (uses unrtf)

### XML (.xml, .dita, DocBook)
- **Approach:** defusedxml parsing, format-specific element mapping
- **Structure:** DocBook chapters, DITA topics, or generic section elements
- **Web app equivalent:** `convert_xml_manuscript.py`

### JSON (.json)
- **Approach:** Parse structured JSON (including ChapterWise manuscript format)
- **Structure:** Tree traversal
- **Web app equivalent:** `convert_json_manuscript.py`

### OpenDocument (.odt)
- **Approach:** ZIP extraction → XML content parsing (content.xml)
- **Structure:** Heading styles similar to DOCX
- **Libraries:** Built-in XML or python-odf

### Google Docs (exported .docx or .html)
- **Approach:** Same as DOCX or HTML converter, with Google-specific cleanup
- **Note:** Agent detects Google Docs origin and adjusts (strips Google-specific spans, etc.)

### Notion Export (markdown folder)
- **Approach:** Same as markdown_folder.py, with Notion-specific cleanup
- **Note:** Strips Notion IDs from filenames, handles Notion's nested page structure

### Bear Notes Export (.md with Bear extensions)
- **Approach:** Markdown parsing with Bear tag syntax (`#tag/subtag`)
- **Note:** Bear tags converted to standard YAML tags in frontmatter

### iA Writer (.md with content blocks)
- **Approach:** Markdown parsing, resolving `/path/to/file.md` content block includes
- **Note:** Content blocks are inlined during import

## Tier 3: External Tool Delegation

For formats that are difficult to parse directly, the agent delegates to external tools as a pre-processing step, then applies the pattern architecture to the intermediate output.

### pandoc
- **When:** Complex RTF, LaTeX, EPUB, ODT, DocBook, or any format pandoc handles
- **How:** `pandoc input.file -t markdown -o intermediate.md`, then process with markdown_folder.py pattern
- **Install:** `brew install pandoc` / `apt install pandoc`

### Calibre (ebook-convert)
- **When:** EPUB, MOBI, AZW3, or any ebook format
- **How:** `ebook-convert input.epub output.txt`, then process with plaintext or markdown pattern
- **Install:** `brew install calibre` / Calibre app

### LibreOffice (soffice)
- **When:** Legacy formats (.doc, .wps, .pages), complex .odt
- **How:** `soffice --headless --convert-to docx input.doc`, then process with docx pattern
- **Install:** `brew install libreoffice` / LibreOffice app

### Tesseract (OCR)
- **When:** Scanned PDFs (no text layer detected)
- **How:** PyMuPDF extracts images → pytesseract OCR per page
- **Install:** `brew install tesseract` + `pip3 install pytesseract`

## Format Detection

The agent auto-detects format via `format_detector.py`:

1. **File extension** — First pass, usually sufficient
2. **Magic bytes** — PDF (`%PDF`), ZIP-based (EPUB, DOCX, ODT), XML declaration
3. **Content sampling** — Read first 1KB to distinguish ambiguous formats
4. **Folder structure** — `.scriv` directory pattern, Ulysses bundle, markdown collection

```python
# format_detector.py returns:
{
    "format": "scrivener",
    "confidence": 0.99,
    "details": "Found .scrivx file and Files/Data/ structure",
    "suggested_pattern": "scrivener_converter.py",
    "tier": 1  # bundled pattern available
}
```

## Digest Mode: Folder Import

The `/digest` command handles folder-level imports where the "source" is an entire project directory, not a single file.

### Supported Project Types

| Source | How It's Detected | Strategy |
|--------|-------------------|----------|
| Obsidian vault | `.obsidian/` folder present | Read folder structure, preserve wikilinks as tags |
| Scrivener project | `.scriv` extension, `.scrivx` file inside | Use scrivener_converter.py |
| Ulysses library | `.ulyz` files or Ulysses group structure | Use ulysses_converter.py |
| Markdown collection | Folder of `.md` files | Use markdown_folder.py |
| Mixed content | Multiple file types | Agent sorts by type, applies appropriate pattern per file |
| Web scrape | Folder of `.html` files | Use html_converter.py in multi-file mode |
| Notion export | Markdown folder with Notion-style filenames | markdown_folder.py + Notion cleanup |

### Digest Workflow

1. Agent scans the folder recursively
2. Categorizes files by type and role (content, assets, config, ignore)
3. Determines project structure (flat, hierarchical, mixed)
4. Interviews writer about organization preferences
5. Processes each content file with the appropriate pattern
6. Generates unified `index.codex.yaml` tying everything together

### What Gets Ignored

```python
IGNORE_PATTERNS = [
    ".git", ".svn", ".hg",           # Version control
    "node_modules", "__pycache__",    # Build artifacts
    ".obsidian", ".vscode",           # Editor config
    ".DS_Store", "Thumbs.db",         # OS artifacts
    ".chapterwise", ".backups",       # ChapterWise internals
    "*.pyc", "*.pyo",                 # Compiled Python
]
```

## Adding New Format Support

Because the agent can create converters on-the-fly, "adding support" for a new format doesn't require code changes. But for frequently requested formats, a new pattern script can be added:

1. Study the format's structure
2. Write a pattern script following the standard architecture (CONFIG block, CLI interface, shared utilities)
3. Add to `patterns/` directory
4. Update `format_detector.py` with detection rules
5. The agent automatically picks it up on next import
