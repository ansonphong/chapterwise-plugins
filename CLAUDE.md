# ChapterWise Plugins — Project Instructions

## Project Overview

This is the ChapterWise Claude Code plugin — a complete writing toolkit for manuscript import, AI analysis, story atlas generation, and custom readers. The plugin lives at `plugins/chapterwise/`.

## Architecture

```
plugins/chapterwise/
├── .claude-plugin/plugin.json   # Plugin manifest
├── commands/                    # Slash commands (YAML frontmatter + markdown)
├── modules/                     # 32 analysis modules
├── scripts/                     # Python utilities (stdin JSON, stdout JSON)
├── patterns/                    # Format conversion patterns
├── templates/                   # Reader HTML templates
└── references/                  # Shared rules and principles
```

## Core Principles

Read `plugins/chapterwise/references/principles.md` before working on any command. Key principles:

1. **LLM Judgment, User Override** — The agent makes smart decisions but always yields to user preferences. Preference cascade: plugin defaults → `.claude/chapterwise.local.md` → command variant → prompt language.
2. **Clean Defaults, Rich Options** — Commands work with zero config. First run produces useful output without asking questions.
3. **Data Over Flare** — Progress messages include real data. No theatrical language. See `references/language-rules.md`.

## Plans

All implementation plans and design documents go in `.claude/plans/`.

When creating new plans, always use: `.claude/plans/YYYY-MM-DD-<topic>.md` or `.claude/plans/<topic>/` for multi-file plans.

When a plan has been fully executed and all its tasks are complete, move it to `.claude/plans/_archive/`. This keeps the active plans folder clean and scannable. Multi-file plan directories (e.g., `recipe-system/`) get moved as a whole folder.

## Conventions

- **Commands** are markdown files with YAML frontmatter in `commands/`. Auto-discovered — no manifest registration needed.
- **Scripts** use stdin/stdout JSON: `echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py`
- **Never say "recipe" to the user.** The recipe system is internal only.
- **Cooking verbs in progress messages** — scan, slice, source, distill, gather, assemble. Not metaphors — action verbs paired with technical nouns and real data.
- **Validation after output** — run `codex_validator.py` after generating codex files, `recipe_validator.py` after saving recipes. Silent on success.
- **User preferences** persist in `.claude/chapterwise.local.md` (in the user's project, not this repo). YAML frontmatter for config, markdown body for notes.

## Modular Rules

See `.claude/rules/` for topic-specific rules that load contextually when working with matching files.
