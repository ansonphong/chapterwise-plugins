---
description: "Import a Scrivener project (.scriv) into ChapterWise format"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - scrivener import
  - scrivener to codex
  - convert scrivener
  - scriv to markdown
  - import .scriv
  - scrivener project
argument-hint: "[path/to/Project.scriv]"
---

# Scrivener Import

This is a Scrivener-specific import. Follow the full import workflow from `import.md` with these modifications:

1. **Skip format detection (Step 2)** — format is already known: Scrivener.
2. **Use `scrivener_converter.py`** as the pattern script (when available) or fall back to the agent generating a custom converter.
3. **Enable Scrivener metadata preservation** — labels, status, keywords, synopsis. Ask the writer which to keep during the interview (Step 4).
4. **Map Scrivener binder structure** to Chapterwise hierarchy:
   - Manuscript folder → root project
   - Sub-folders → parts or acts
   - Text documents → chapters or scenes
   - Research folder → skip (unless writer requests)

All other steps (recipe check, interview, conversion, validation, review) follow `import.md` exactly.
