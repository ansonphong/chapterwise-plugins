---
description: "Import a Scrivener project into ChapterWise"
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

---

## Error Handling

| Situation | Response |
|-----------|----------|
| .scriv bundle not found | "Scrivener project not found: {path}" |
| Missing .scrivx manifest | "No .scrivx file found inside {path} — is this a valid Scrivener project?" |
| Unsupported Scrivener version | "This looks like Scrivener {version}. Only Scrivener 3 projects are supported." |
| RTF conversion failure | "Cannot convert RTF document: {file} — try exporting as plain text from Scrivener first." |
| Missing PyYAML dependency | "Missing PyYAML. Install with: `pip3 install pyyaml`" |

## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start | Scanning | "Scanning Scrivener project..." |
| Processing | Assembling | "Assembling codex from {N} binder items..." |
| Completion | Done | "Done. {N} files imported from Scrivener project." |
