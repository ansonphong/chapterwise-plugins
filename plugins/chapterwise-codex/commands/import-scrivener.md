---
description: "Import Scrivener projects (.scriv) to Chapterwise Codex format. Converts RTF content to Markdown, preserves Scrivener metadata (labels, status, keywords), and generates index files."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion
triggers:
  - scrivener import
  - import scrivener
  - scrivener to codex
  - convert scrivener
  - scriv to markdown
  - import .scriv
  - scrivener project
disable-model-invocation: true
argument-hint: "[path/to/Project.scriv]"
---

# Import Scrivener Project

Import a Scrivener (.scriv) project into Chapterwise Codex format.

## Quick Start

```bash
# Preview what will be created (always do this first)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py /path/to/Project.scriv --dry-run

# Import to Markdown (Codex Lite) - recommended
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py /path/to/Project.scriv --format markdown

# Import to specific output directory
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py /path/to/Project.scriv --output ./imported

# Import with verbose progress
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py /path/to/Project.scriv --verbose
```

## Workflow

When user invokes this skill:

### Step 1: Identify the Scrivener Project

If path provided as argument:
- Validate it's a .scriv folder (contains .scrivx file and Files/Data directory)

If no path provided:
- Use Glob to find .scriv folders: `**/*.scriv`
- If multiple found, use AskUserQuestion to let user choose
- If none found, inform user and exit

### Step 2: Preview the Import

Always run dry-run first to show user what will be created:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py "$SCRIV_PATH" --dry-run
```

Show the user:
- Number of files that will be created
- Output directory location
- Format being used

### Step 3: Confirm Options

Use AskUserQuestion to confirm:
- **Output format**: Markdown (recommended), YAML, or JSON
- **Output location**: Current directory or custom path
- **Generate index files**: Yes (recommended) or No

### Step 4: Run Import

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scrivener_import.py "$SCRIV_PATH" \
  --format "$FORMAT" \
  --output "$OUTPUT_DIR" \
  --verbose
```

### Step 5: Report Results

Show user:
- Number of files created
- Output directory path
- Path to index file (if generated)
- Any warnings or errors
- Suggest opening in VS Code with ChapterWise Codex extension

## Command Reference

```
python3 scrivener_import.py <scriv_path> [options]

Positional:
  scriv_path              Path to .scriv folder

Options:
  --format, -f            Output format: markdown, yaml, json (default: markdown)
  --output, -o            Output directory (default: ./<ProjectName>)
  --rtf-method            RTF conversion: striprtf, pandoc, raw (default: striprtf)
  --generate-index        Generate index files (default: true)
  --no-index              Skip index generation
  --dry-run, -d           Preview without writing files
  --verbose, -v           Verbose output
  --json                  JSON progress output (for programmatic use)
  --quiet, -q             Minimal output (errors only)
```

## Output Formats

### Codex Lite (Markdown) - Recommended

Human-readable, Git-friendly Markdown with YAML frontmatter:

```markdown
---
type: chapter
name: "Chapter 1: The Awakening"
scrivener_label: "Chapter"
scrivener_status: "First Draft"
summary: "Protagonist discovers their powers"
---

# Chapter 1: The Awakening

Content converted from RTF...
```

**Best for:**
- Git version control
- Collaboration
- Reading in any Markdown editor
- Obsidian, Typora, VS Code

### Codex YAML (.codex.yaml)

Full Codex format with structured metadata:

```yaml
metadata:
  formatVersion: "1.2"
  created: "2026-01-31T..."
id: "uuid-here"
type: chapter
name: "Chapter 1: The Awakening"
attributes:
  - key: scrivener_label
    value: "Chapter"
  - key: scrivener_status
    value: "First Draft"
summary: "Protagonist discovers their powers"
body: |
  Content converted from RTF...
```

**Best for:**
- Complex hierarchical structures
- Programmatic access
- ChapterWise Codex VS Code extension

### Codex JSON (.codex.json)

Machine-readable JSON format (same structure as YAML).

**Best for:**
- API integration
- Programmatic processing

## Troubleshooting

### "No .scrivx file found"
- Selected folder is not a valid Scrivener project
- Make sure you select the .scriv folder itself (not a file inside it)
- On macOS, .scriv appears as a single file but is actually a package/folder

### "striprtf not installed"
- Install with: `pip3 install striprtf`
- Or use `--rtf-method raw` to skip conversion (keeps RTF formatting codes)

### "pandoc not found"
- Install pandoc for better RTF conversion quality
- macOS: `brew install pandoc`
- Or use default striprtf method (works without pandoc)

### RTF conversion quality issues
- Try `--rtf-method pandoc` for better formatting (requires pandoc installed)
- Complex formatting (tables, images) may not convert perfectly
- Original content is preserved, just formatting may be simplified

### Permission errors
- Ensure you have write access to the output directory
- Try specifying a different output location with `--output`

## Dependencies

### Required
- Python 3.8+
- PyYAML: `pip3 install pyyaml`

### Recommended
- striprtf: `pip3 install striprtf` (for RTF to text conversion)

### Optional (for better RTF quality)
- pandoc: Install from https://pandoc.org/installing.html

### Install all at once
```bash
pip3 install pyyaml striprtf
```

## Examples

```bash
# Import novel to current directory as Markdown
/chapterwise-codex:import-scrivener ~/Documents/MyNovel.scriv

# Import to specific folder with YAML format
/chapterwise-codex:import-scrivener ~/Documents/MyNovel.scriv --output ./imported --format yaml

# Preview first, then import
/chapterwise-codex:import-scrivener ~/Documents/MyNovel.scriv --dry-run
# (review output, then run without --dry-run)

# Import without generating index files
/chapterwise-codex:import-scrivener ~/Documents/MyNovel.scriv --no-index
```

## What Gets Preserved

From Scrivener:
- **Document hierarchy** (folders, subfolders, documents)
- **Labels** → `scrivener_label` field
- **Status** → `scrivener_status` field
- **Synopsis** → `summary` field
- **Keywords** → `tags` field
- **Include in Compile** flag
- **Document content** (converted from RTF)

## After Import

1. Open the output folder in VS Code
2. Install ChapterWise Codex extension (if not already)
3. Open the generated `index.codex.yaml` or `.index.codex.yaml`
4. Use the Navigator panel to browse your imported project
