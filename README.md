# ChapterWise Claude Plugin

Complete writing toolkit for ChapterWise — import any manuscript, run AI analysis, build story atlases, create custom readers. Supports PDF, DOCX, Scrivener, Ulysses, Markdown, and more.

## Installation

### Direct Install (Recommended)

```bash
/plugin install --source github ansonphong/chapterwise-claude-plugins
```

### Local Development

```bash
claude --plugin-dir /path/to/chapterwise-plugins
```

## Commands

### Core Pipeline

| Command | Description |
|---------|-------------|
| `/import` | Import manuscripts and content into ChapterWise |
| `/analysis` | Analyze Codex files with intelligent module selection |
| `/atlas` | Build a story atlas from your manuscript |
| `/reader` | Build a static HTML reader for your project |
| `/research` | Research any topic and generate structured codex reference files |
| `/research:deep` | Deep research — generate a multi-document compendium on any topic |

### Manuscript Tools

| Command | Description |
|---------|-------------|
| `/insert` | Insert notes into Codex manuscripts by location |
| `/status` | Show project status and staleness overview |
| `/pipeline` | Run full pipeline: Import, Analysis, Atlas, Reader |
| `/index` | Generate an index.codex.yaml for your project |

### Format Tools

| Command | Description |
|---------|-------------|
| `/format` | Format content as Chapterwise Codex |
| `/explode` | Split a codex file into separate child files |
| `/implode` | Merge separate codex files back into one document |
| `/markdown` | Create Markdown files with ChapterWise frontmatter |
| `/convert-to-codex` | Convert Markdown files to Codex YAML format |
| `/convert-to-markdown` | Convert Codex files to Markdown with frontmatter |

### Utilities

| Command | Description |
|---------|-------------|
| `/generate-tags` | Auto-generate tags from content in codex or markdown files |
| `/update-word-count` | Update word count metadata in codex files |
| `/format-folder` | Auto-fix all codex files in a folder |
| `/format-regen-ids` | Regenerate all IDs in a codex file |
| `/diagram` | Create Mermaid diagrams in Codex format |
| `/spreadsheet` | Create spreadsheets in Codex format |

### Specialized

| Command | Description |
|---------|-------------|
| `/import-scrivener` | Import a Scrivener project into ChapterWise |

## Codex Format Overview

Every Codex file has this structure:

```yaml
metadata:
  formatVersion: "1.2"
  documentVersion: "1.0.0"

id: "unique-uuid"
type: "any-type"  # character, location, chapter, recipe, meeting, etc.
name: "Display Name"
summary: "One-line description"
status: draft

body: |
  Extended content in Markdown...

attributes:
  - key: some_key
    value: "some value"
    dataType: string

children:
  - id: "child-uuid"
    type: "child-type"
    name: "Child Name"
    # ...same structure recursively
```

## Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)

## License

MIT License - see [LICENSE](LICENSE) file.

## Links

- [ChapterWise App](https://chapterwise.app)
- [Plugin Repository](https://github.com/ansonphong/chapterwise-claude-plugins)
