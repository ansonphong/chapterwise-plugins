# Import Recipe — Pattern Scripts (The Cookbook)

## Philosophy

Pattern scripts are the heart of `chapterwise`. They serve two purposes:

1. **Runnable tools** — The agent can execute them directly for common formats
2. **Teaching materials** — The agent reads them to learn how converters work, then generates custom variants for unusual formats or manuscripts with quirks

Each pattern script is a complete, standalone Python program that converts one source format into Chapterwise-native output. They share common utilities from `patterns/common/` for consistent output.

## Design Principles

### Self-Contained
Each pattern script handles the full pipeline for its format: read source → extract text → detect structure → write output. No external orchestration required.

### Configurable Header
Every pattern script starts with a configuration block that the agent can modify:

```python
# === CONFIGURATION (Agent modifies this section) ===
CONFIG = {
    "chapter_pattern": r"^Chapter\s+[IVXLC]+",
    "part_pattern": r"^Part\s+[IVXLC]+",
    "special_sections": ["Prologue", "Epilogue"],
    "skip_sections": ["Dedication", "About the Author"],
    "output_format": "markdown",  # or "codex"
    "structure": "folders_per_part",  # or "flat"
}
# === END CONFIGURATION ===
```

The agent reads the pattern, understands the architecture, then tweaks the config block for the specific manuscript. For simple cases, this is all that's needed — no custom script generation.

### JSON Output Mode
All scripts support `--json` output for structured progress reporting:

```bash
python3 pdf_converter.py input.pdf output/ --json
```

Returns progress events the agent can parse:
```json
{"event": "start", "source": "input.pdf", "format": "pdf", "pages": 342}
{"event": "chapter", "name": "Chapter I", "words": 3200, "file": "chapter-01.md"}
{"event": "chapter", "name": "Chapter II", "words": 2800, "file": "chapter-02.md"}
{"event": "complete", "files": 31, "total_words": 87234}
```

### Common Interface
All pattern scripts accept the same CLI interface:

```bash
python3 <pattern>.py <source> <output_dir> [options]

Options:
  --json           JSON progress output
  --dry-run        Preview without writing files
  --config FILE    Load config from YAML file
  --verbose        Detailed progress
  --quiet          Errors only
```

**Stdin JSON mode (canonical for agent use):**
```bash
echo '{"source": "input.pdf", "output_dir": "output/", "json": true}' | python3 <pattern>.py
```
Pattern scripts support BOTH interfaces. The CLI form is a convenience wrapper; internally both resolve to the same functions. Agent-generated scripts should use stdin JSON for consistency with recipe infrastructure scripts.

---

## Bundled Patterns

### pdf_converter.py

**Purpose:** Extract text and structure from PDF files.
**Library:** PyMuPDF (`pip3 install pymupdf`)

**What it does:**
1. Opens PDF with PyMuPDF
2. Extracts text page by page, preserving paragraph boundaries
3. Detects chapter boundaries via configurable heading patterns
4. Handles common PDF artifacts: page numbers, headers/footers, hyphenation
5. Extracts document metadata (title, author) from PDF info dict
6. Outputs clean markdown files with frontmatter

**Challenges it handles:**
- Two-column layouts (detected via text block positions)
- Scanned PDFs (falls back to OCR note: "This appears to be a scanned PDF. Install `pytesseract` for OCR support.")
- Embedded images (extracted to `assets/` folder, referenced in markdown)
- Table of contents (parsed to validate chapter detection)

**Config options:**
```python
CONFIG = {
    "chapter_pattern": r"^Chapter\s+\d+",
    "part_pattern": None,
    "page_header_pattern": r"^\d+$",  # Strip page numbers
    "page_footer_pattern": None,
    "skip_pages": [1, 2],  # Title page, copyright
    "min_chapter_words": 500,  # Avoid false chapter breaks
}
```

### docx_converter.py

**Purpose:** Extract text, structure, and metadata from DOCX files.
**Library:** python-docx (`pip3 install python-docx`)

**What it does:**
1. Opens DOCX with python-docx
2. Walks paragraph tree, detecting headings by style (Heading 1, Heading 2, etc.)
3. Preserves bold/italic/underline as markdown formatting
4. Extracts document properties (title, author, creation date)
5. Handles tracked changes (uses accepted version)
6. Extracts comments as `<!-- COMMENT: ... -->` markers
7. Outputs clean markdown files with frontmatter

**Challenges it handles:**
- Custom heading styles (detects by font size and weight, not just named styles)
- Embedded images (extracted from DOCX media, saved to `assets/`)
- Tables (converted to markdown tables)
- Footnotes/endnotes (converted to markdown footnote syntax)

**Config options:**
```python
CONFIG = {
    "heading_styles": ["Heading 1", "Heading 2"],  # Or auto-detect
    "chapter_level": 1,  # Which heading level marks chapters
    "preserve_comments": False,
    "preserve_tracked_changes": False,
    "extract_images": True,
}
```

### scrivener_converter.py

**Purpose:** Import Scrivener `.scriv` projects with full metadata preservation.
**Library:** Built-in XML parsing (no extra deps), striprtf for RTF content.

**Adapted from:** Existing `scrivener_import.py`, `scrivener_parser.py`, `scrivener_file_writer.py` in `chapterwise-codex`.

**What it does:**
1. Reads `.scrivx` file (XML) for binder structure
2. Walks the binder tree in document order
3. Reads RTF content from `Files/Data/<uuid>/content.rtf`
4. Converts RTF to clean markdown via striprtf (or pandoc if available)
5. Preserves Scrivener metadata:
   - Labels → `scrivener_label` frontmatter field
   - Status → `scrivener_status` frontmatter field
   - Keywords → `tags` field
   - Synopsis → `summary` field
   - Include in Compile → `compile` field
6. Generates hierarchical structure matching the Scrivener binder
7. Creates nested `index.codex.yaml` files for multi-book projects

**Config options:**
```python
CONFIG = {
    "preserve_labels": True,
    "preserve_status": True,
    "preserve_keywords_as_tags": True,
    "preserve_synopsis_as_summary": True,
    "skip_non_compile": False,  # Include or skip non-compile documents
    "container_types": ["act", "part", "book", "folder"],
    "content_types": ["chapter", "scene", "document"],
    "index_depth": 1,  # How many levels get their own index.codex.yaml
}
```

### ulysses_converter.py

**Purpose:** Import Ulysses writing app exports.
**Library:** Built-in (Ulysses exports as markdown or TextBundle).

**What it does:**
1. Detects Ulysses export format (TextBundle, markdown folder, .ulyz archive)
2. Reads sheet content (already markdown in Ulysses)
3. Preserves Ulysses metadata:
   - Keywords → `tags` field
   - Writing goals → `target_word_count` attribute
   - Groups → folder structure
   - Attachments → `assets/` folder
4. Handles Ulysses-specific markdown extensions (annotations, marked text)
5. Converts Ulysses markup to standard markdown

**Config options:**
```python
CONFIG = {
    "preserve_keywords": True,
    "preserve_writing_goals": True,
    "groups_as_folders": True,
    "convert_annotations_to_comments": True,  # Ulysses annotations → HTML comments
    "handle_marked_text": "bold",  # or "highlight", "strip"
}
```

### markdown_folder.py

**Purpose:** Import a folder of existing markdown/text files.
**Library:** Built-in.

**Adapted from:** Existing `/import` command in `chapterwise-codex`.

**What it does:**
1. Scans source directory recursively
2. Identifies file types (.md, .txt, .html, .rtf, .yaml, .json)
3. Reads existing frontmatter (YAML, TOML) and preserves it
4. Maps folder hierarchy to Chapterwise structure
5. Assigns types based on content analysis (character, location, chapter, etc.)
6. Generates clean filenames and proper hierarchy
7. Creates `index.codex.yaml` from folder structure

**Config options:**
```python
CONFIG = {
    "recursive": True,
    "file_types": [".md", ".txt", ".html"],
    "preserve_frontmatter": True,
    "structure": "mirror",  # "mirror" (keep source structure), "flat", "reorganize"
    "type_assignment": "auto",  # "auto" (AI-based), "from_frontmatter", "all_chapter"
    "ignore_patterns": [".git", "node_modules", ".obsidian", ".backups"],
}
```

### html_converter.py

**Purpose:** Convert HTML files or web page exports to Chapterwise format.
**Library:** BeautifulSoup (`pip3 install beautifulsoup4`)

**What it does:**
1. Parses HTML with BeautifulSoup
2. Detects structure from heading hierarchy (h1, h2, h3)
3. Converts HTML to clean markdown (preserving links, images, tables)
4. Handles single-file HTML (one big file → split into chapters)
5. Handles multi-file HTML (folder of .html → one file each)
6. Strips navigation, ads, footers (heuristic detection)

### plaintext_converter.py

**Purpose:** Import plain text files with heuristic chapter detection.
**Library:** Built-in.

**What it does:**
1. Reads text file with encoding detection
2. Uses heuristics to find chapter boundaries:
   - Lines matching common patterns ("Chapter 1", "CHAPTER ONE", "I.", "Part One")
   - Blank line clusters (3+ consecutive blank lines often mark breaks)
   - Horizontal rules ("---", "***", "===")
3. Falls back to AI-assisted detection if heuristics fail
4. Outputs clean markdown files

---

## Common Utilities (patterns/common/)

### chapter_detector.py

Shared chapter boundary detection used by all patterns.

**Methods:**
- `detect_by_heading(text, pattern)` — Regex-based heading detection
- `detect_by_blank_lines(text, min_gap=3)` — Blank line cluster detection
- `detect_by_page_break(text)` — Form feed / page break detection
- `detect_combined(text, config)` — All methods combined with confidence scoring

**Returns:**
```python
[
    {"start": 0, "end": 1200, "title": "Prologue", "confidence": 0.95},
    {"start": 1200, "end": 4500, "title": "Chapter I: The Awakening", "confidence": 0.98},
    {"start": 4500, "end": 7200, "title": "Chapter II: The Call", "confidence": 0.97},
]
```

### codex_writer.py

Writes Chapterwise-native output files. Single source of truth for output format.

**Functions:**
- `write_markdown_file(path, frontmatter, body)` — Codex Lite `.md` file
- `write_codex_file(path, data)` — Full `.codex.yaml` file
- `write_index(path, project_info, children)` — `index.codex.yaml`
- `generate_id()` — UUID for codex nodes
- `slugify(title)` — Clean filename generation

### structure_analyzer.py

Analyzes document structure and outputs a structure map.

**Functions:**
- `analyze_text(text, config)` — Full structure analysis
- `detect_parts(text)` — Part/act detection
- `detect_front_matter(text)` — Dedication, copyright, foreword detection
- `detect_back_matter(text)` — Appendix, glossary, about the author detection
- `estimate_word_count(text)` — Word count per section

### frontmatter_builder.py

Generates YAML frontmatter for Codex Lite files.

**Functions:**
- `build_chapter_frontmatter(title, summary, word_count, tags, order=None, **extra)` — Standard chapter
- `build_section_frontmatter(title, section_type, **extra)` — Non-chapter sections
- `build_from_source_metadata(source_app, metadata)` — Preserve source app fields

---

## Fallback Creativity: On-the-Fly Script Generation

When no pattern matches the source format, the agent generates a converter from scratch.

### How It Works

1. Agent reads 2-3 pattern scripts to understand the converter architecture
2. Agent identifies what libraries could read the unknown format (Claude knows many file formats)
3. Agent writes a new `convert.py` using:
   - The same CONFIG block pattern
   - The same CLI interface
   - The same `codex_writer.py` and `frontmatter_builder.py` for output
   - Format-specific extraction logic
4. Agent explains to the user what it's doing: "This is a Final Draft (.fdx) file — I'll write a custom converter using XML parsing."
5. Agent runs the generated script

### Safety Rules
- Generated scripts only import standard library + well-known packages
- Generated scripts only read source and write to output directory
- Generated scripts follow the same CONFIG + CLI pattern as bundled scripts
- The agent reviews the generated script before running it
- If the script fails, the agent diagnoses and fixes, or asks for help

### Examples of Formats the Agent Could Handle On-the-Fly
- Final Draft (`.fdx`) — XML screenplay format
- Fountain (`.fountain`) — Plain text screenplay format
- EPUB (`.epub`) — ZIP of HTML files
- LaTeX (`.tex`) — TeX source
- OpenDocument (`.odt`) — ZIP of XML
- Google Docs export — HTML or DOCX
- Notion export — Markdown folder with specific structure
- Bear notes export — Markdown with Bear-specific extensions
- iA Writer — Markdown with content blocks

The agent doesn't need to know all these formats in advance. It just needs to understand the *pattern* of how a converter works, and it can figure out the rest.
