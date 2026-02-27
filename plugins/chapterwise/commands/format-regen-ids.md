---
description: Auto-fix codex file and regenerate ALL IDs (useful for duplicating content)
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - regenerate ids
  - regen ids
  - new ids
  - fresh ids
  - duplicate ids
---

# Regenerate All IDs

Regenerate ALL IDs in a codex file, even if they're already valid. This is useful when:
- Duplicating/forking content that needs unique IDs
- Ensuring completely fresh IDs after import
- Resetting IDs after copy/paste operations

## Usage

Run the auto-fixer with the `--re-id` flag:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py <file.codex.yaml> --re-id
```

### Options

```bash
# Regenerate IDs in a single file
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/file.codex.yaml --re-id

# Dry run (preview without changes)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/file.codex.yaml --re-id --dry-run

# Regenerate IDs in all files in a directory
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/directory --re-id --recursive

# Verbose output
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py /path/to/file.codex.yaml --re-id --verbose
```

## What Gets Regenerated

- All `id` fields on nodes/entities
- All `targetId` fields in relations

## Workflow

1. User asks to regenerate IDs or mentions duplicating content
2. If no file specified, ask which file
3. Run the auto-fixer with `--re-id` flag
4. Report the number of IDs regenerated
5. Warn user that relation targetIds now point to new IDs (may need manual update if referencing external files)
