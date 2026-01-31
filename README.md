# Chapterwise Claude Plugins

A collection of Claude Code plugins for working with Chapterwise Codex documents.

## Plugins

### chapterwise-codex
Skills for creating, validating, and managing Chapterwise Codex documents.

### chapterwise-insert
Intelligently insert notes into Chapterwise Codex manuscripts with semantic location finding. See [chapterwise-insert](#chapterwise-insert-plugin) below.

The Chapterwise Codex format is a perfectly recursive YAML/JSON specification for **any structured content** - stories, characters, budgets, technical specs, scripts, or literally anything else. This plugin provides Claude Code with the skills to work with Codex files.

## Installation

### Direct Install (Recommended)

```bash
/plugin install --source github ansonphong/chapterwise-codex-claude
```

### Via Marketplace (if available)

```bash
/plugin marketplace add ansonphong/chapterwise-marketplace
/plugin install chapterwise-codex@chapterwise-marketplace
```

### Local Development

```bash
claude --plugin-dir /path/to/chapterwise-codex-claude
```

## Skills Included

| Skill | Command | Description |
|-------|---------|-------------|
| **format** | `/chapterwise-codex:format` | Convert content to Codex V1.2 format, run auto-fixer |
| **explode** | `/chapterwise-codex:explode` | Extract children into separate files with include directives |
| **implode** | `/chapterwise-codex:implode` | Merge included files back into parent document |
| **index** | `/chapterwise-codex:index` | Generate index.codex.yaml for project structure |
| **lite** | `/chapterwise-codex:lite` | Create Codex Lite files (Markdown with YAML frontmatter) |

## Quick Start

### Create a Codex File

Just tell Claude what you want to create:

```
Create a codex file for my sci-fi story with characters and locations
```

Or invoke the format skill directly:

```
/chapterwise-codex:format
```

### Auto-Fix Existing Files

```bash
python skills/format/auto_fixer.py myfile.codex.yaml
```

### Modularize Large Files

```bash
# Extract characters and locations to separate files
python skills/explode/explode_codex.py story.codex.yaml --types character,location

# Merge them back later
python skills/implode/implode_codex.py story.codex.yaml
```

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

## Common Use Cases

### Storytelling
- Characters, locations, factions
- Plot outlines, scene breakdowns
- World-building documentation

### Business
- Budget allocation documents
- Pitch decks, presentations
- Asset registries

### Technical
- Architecture specifications
- API documentation
- Process workflows

### Personal
- Recipes, workout routines
- Meeting notes, research papers
- Any structured content

## Auto-Fixer Features

The auto-fixer ensures Codex file integrity:

- Adds missing `metadata.formatVersion`
- Generates UUIDs for nodes missing `id`
- Fixes invalid UUID formats
- Detects and fixes duplicate IDs
- Converts long strings to YAML pipe syntax
- Auto-calculates timecodes from durations
- Recovers malformed YAML/JSON

## Requirements

- Claude Code 1.0.33 or later
- Python 3.8+ (for helper scripts)
- PyYAML (`pip install pyyaml`)

---

## chapterwise-insert Plugin

Intelligently insert notes into Chapterwise Codex manuscripts by finding the right location using semantic matching and hierarchical agent search.

### The Problem

You write notes in a digital notepad - scenes, ideas, bullet points. The most time-consuming part is finding where each note belongs in your manuscript, especially in large multi-chapter projects.

### The Solution

`/insert` uses AI to semantically match your notes to the right location in your codex files:

```bash
# Insert a note with a location hint
/insert "after the hyperborean incursion - Elena drew her sword..." into ./manuscript/

# Batch insert from a file
/insert notes.txt into ./manuscript/

# Preview without writing
/insert --dry-run notes.txt into ./manuscript/
```

### Features

- **Semantic Matching**: Finds locations from vague instructions like "after the battle" or "when Elena speaks"
- **Hierarchical Search**: Uses parallel agents to search large manuscripts without context overflow
- **Confidence-Based UX**: Auto-inserts at high confidence (≥95%), shows options at medium (50-95%), asks at low (<50%)
- **Insert Markers**: Wraps inserts with HTML comments for review before accepting
- **Dual Format Support**: Works with both Codex (YAML) and Codex Lite (Markdown)
- **Batch Processing**: Insert multiple notes from a single file

### Insert Markers

Inserts are wrapped with metadata for review:

```html
<!-- INSERT
time: 2024-01-27T10:30:00Z
instruction: "after the hyperborean incursion"
confidence: 0.93
-->
Elena drew her sword, the blade catching moonlight...
<!-- /INSERT -->
```

Accept inserts after review:
```bash
/insert --accept ./manuscript/
```

### Commands

| Command | Description |
|---------|-------------|
| `/insert "text" into file` | Insert single note |
| `/insert notes.txt into folder/` | Batch insert from file |
| `/insert --clipboard into folder/` | Insert from clipboard |
| `/insert --accept path` | Accept pending inserts (remove markers) |
| `/insert --undo file` | Restore from backup |
| `/insert --dry-run ...` | Preview without writing |

---

## License

MIT License - see [LICENSE](LICENSE) file.

## Links

- [Chapterwise App](https://chapterwise.app)
- [Codex Format Specification](https://chapterwise.app/docs/codex/format)
- [Plugin Repository](https://github.com/ansonphong/chapterwise-codex-claude)
