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
| `/pipeline` | Run full chain: import, analysis, atlas, reader |

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
