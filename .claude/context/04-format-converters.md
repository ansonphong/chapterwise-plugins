# Format Converters (7 converters + 4 common utilities)

All converters live in `plugins/chapterwise/patterns/`. They follow a JSON-in/JSON-out pattern and are invoked by the `/import` command after `format_detector.py` identifies the source format.

## Converters

| File | Format | Notes |
|------|--------|-------|
| `pdf_converter.py` | PDF | Requires PyMuPDF (fitz). Extracts text, detects chapters. |
| `docx_converter.py` | DOCX | Requires python-docx. Preserves heading structure. |
| `scrivener_converter.py` | Scrivener 3 (.scriv) | Parses .scrivx XML + RTF content files. |
| `ulysses_converter.py` | Ulysses export | Handles Ulysses writing app export bundles. |
| `html_converter.py` | HTML | Requires beautifulsoup4. Handles web page exports. |
| `plaintext_converter.py` | Plain text (.txt) | Chapter boundary detection via patterns. |
| `markdown_folder.py` | Markdown folder | Imports a folder of .md/.txt/.html files as chapters. |

## Common Utilities (`patterns/common/`)

| File | Role |
|------|------|
| `chapter_detector.py` | Detect chapter boundaries in extracted text. Input: `{text, hints}`. Output: `{chapters: [{title, start, end}]}`. |
| `structure_analyzer.py` | Analyze manuscript structure (act divisions, part groupings, section types). |
| `codex_writer.py` | Write Chapterwise project output files. Takes structured chapter data, produces `.codex.yaml` or `.codex.md` files. |
| `frontmatter_builder.py` | Build YAML frontmatter from JSON input for Codex Lite output. |

## Pipeline Flow

```
Source file
  → format_detector.py (identify format + confidence score)
  → appropriate converter (extract text, detect chapters)
  → chapter_detector.py (refine boundaries if needed)
  → structure_analyzer.py (identify acts, parts, sections)
  → codex_writer.py (produce output files in chosen format)
  → codex_validator.py (validate + auto-fix output)
```

## Converter Interface

All converters accept stdin JSON with at minimum `{source_path: "..."}` and return JSON with extracted chapter data, metadata, and structure. The `/import` command orchestrates this pipeline, using `recipe_manager.py` to track state across steps.

## Supported Source Formats (format_detector.py)

pdf, docx, doc, scrivener, ulysses, markdown, plaintext, html, rtf, epub, final_draft, fountain. Detection returns format name, confidence score (0-1), and format-specific details.
