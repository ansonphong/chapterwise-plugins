---
description: Auto-fix all codex files in a folder
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - fix codex folder
  - autofix codex folder
  - format codex folder
  - fix all codex files
  - batch fix codex
  - chapterwise:format-folder
argument-hint: "[folder_path]"
---

# Auto-Fix Folder

Run the auto-fixer on all codex files in a folder. Processes `.codex.yaml`, `.codex.yml`, `.codex.json`, and `.codex` files.

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py <folder_path> [options]
```

### Options

```bash
# Fix all codex files in a directory (non-recursive)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/folder

# Fix all codex files recursively (including subdirectories)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/folder --recursive

# Also include markdown files (Codex Lite)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/folder --recursive --include-md

# Dry run (preview fixes without making changes)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/folder --recursive --dry-run

# Fix current directory
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py .

# Verbose output
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/folder --recursive --verbose
```

### Common Flags

| Flag | Description |
|------|-------------|
| `-r`, `--recursive` | Process subdirectories |
| `-d`, `--dry-run` | Preview without changes |
| `-v`, `--verbose` | Detailed output |
| `--re-id` | Regenerate all IDs |
| `--include-md` | Also process `.md` files as Codex Lite |

## What It Fixes

Same fixes as single-file auto-fixer applied to all matching files:
- Missing metadata sections
- Invalid/missing UUIDs
- Duplicate IDs across files (within each file)
- Legacy field removal
- Attribute/relation structure fixes
- Long string formatting
- Timecode calculations

## Workflow

1. User asks to fix a folder or multiple files
2. If no folder specified, ask which folder (or use current directory)
3. Ask if recursive processing is desired
4. Run auto-fixer on the folder
5. Report summary: files processed, fixes applied, any errors

## Example Output

```
Processing directory: /path/to/codex-files
Recursive mode enabled

Found 15 codex file(s)

[1/15] Processing: chapter-01.codex.yaml
  Fixes applied (3):
    1. Added missing 'id' field
    2. Fixed invalid UUID
    3. Converted body to pipe syntax

[2/15] Processing: chapter-02.codex.yaml
  No fixes needed

...

============================================================
Summary:
  Successful: 15
  Failed: 0
  Total: 15
============================================================
```
