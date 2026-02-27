# Import Recipe — Overview

## What It Is

The Import Recipe is a disposable, custom-fit Python program the agent creates to convert any manuscript into a ChapterWise-native project. Not a generic pipeline. A bespoke conversion strategy built for your specific document.

## The Idea

You hand the agent a PDF, DOCX, Scrivener project, or any document. The agent:

1. Studies the document's structure, format, and quirks
2. Picks the closest pattern script from the bundled cookbook (or writes one from scratch)
3. Adapts it into a custom `convert.py` tailored to this manuscript
4. Runs it, producing a complete ChapterWise project with `index.codex.yaml`
5. Saves the recipe so re-imports of updated drafts are instant

The output is always the same: a GitHub-ready folder of Markdown/YAML files that ChapterWise.app, the VS Code extension, or any codex-compatible tool can read.

## Key Insight

The pattern scripts are both **tools** and **teaching materials**. For common formats (PDF, DOCX), the agent runs them with minor config tweaks. For unusual formats, the agent reads them to understand the architecture, then creates something new. The agent doesn't need a converter for every format in advance. It just needs to understand how converters work.

## Documents in This Directory

| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | This document |
| `01-AGENT-WORKFLOW.md` | Step-by-step: check previous → scan → interview → plan → prep → convert → review → save |
| `02-PATTERN-SCRIPTS.md` | Bundled converter patterns, common utilities, fallback creativity system |
| `03-INTERVIEW-AND-PREFERENCES.md` | How the agent interviews writers (1-3 questions max) and remembers preferences |
| `04-OUTPUT-FORMAT.md` | What the final ChapterWise project looks like (flat, folders-per-part, index structure) |
| `05-SUPPORTED-SOURCES.md` | Three tiers: bundled, on-the-fly, external tools. Format detection. Digest mode. |

## Core Behaviors

- **Disposable programs**: The `convert.py` is custom-fit and throwaway. Re-import? Agent writes a fresh one (or reuses if structure hasn't changed).
- **Safe by design**: Scripts only read source, write to output directory. No network, no system modification.
- **Re-import fast path**: Recipe saved at `.chapterwise/import-recipe/`. Next time, agent finds it and skips straight to conversion.
- **Fallback creativity**: Unknown format? Agent studies existing patterns and creates a new converter on the fly.
- **Keep writing in your old app**: Import doesn't replace your workflow. Keep writing in Scrivener/Word/whatever. Periodically re-import to get fresh analysis.
