---
description: Generate an index.codex.yaml for your project
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
disable-model-invocation: true
triggers:
  - generate index
  - create index
  - codex index
  - index codex
  - setup chapterwise project
---

# Chapterwise Codex Index Generator

Generate `index.codex.yaml` files that define project structure for Chapterwise Git projects. The index controls how content is discovered, organized, and displayed.

## When This Skill Applies

- User wants to create an index.codex.yaml for a project
- User wants to set up a Chapterwise Git project
- User mentions "generate index", "codex index", or similar
- User needs to configure include/exclude patterns

## Important Rules

1. **NEVER create `.index.codex.yaml` (hidden) files** - those are system-generated caches
2. **DO create `index.codex.yaml` (visible)** - these are user-controlled project definitions
3. **Type fields auto-detect** - never manually specify `type` on children
4. **Status doesn't inherit** - each item must explicitly set its own status

## Index File Location

Place `index.codex.yaml` at the **root of your Git repository**. This is the entry point for Chapterwise.

## Script Location

```
${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py
```

## Minimal Index (Auto-Discovery)

For most projects, start with this minimal index that auto-discovers content:

```yaml
metadata:
  formatVersion: "1.2"

id: index-root
type: index
title: "My Project"
summary: "Project description here"
status: private

patterns:
  include:
    - "**/*.codex.yaml"
    - "**/*.codex.json"
    - "**/*.md"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/.*"
    - "**/_ARCHIVE/**"
```

## Full Index Structure

```yaml
metadata:
  formatVersion: "1.2"
  documentVersion: "1.0.0"
  created: "2026-01-24T00:00:00Z"
  author: "Author Name"

id: index-root
type: index
title: "Display Title"
summary: "One-line project description"
status: private

# File discovery patterns (gitignore-like syntax)
patterns:
  include:
    - "**/*.codex.yaml"
    - "**/*.codex.json"
    - "**/*.md"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/.*"
    - "**/_ARCHIVE/**"
    - "**/dist/**"
    - "**/build/**"

# Display configuration
display:
  defaultView: "tree"      # tree, list, or grid
  sortBy: "order"          # order, name, modified, type
  groupBy: "folder"        # folder, type, custom, none
  showHidden: false

# Custom type styling (emoji/colors per type)
typeStyles:
  character:
    emoji: "👤"
    color: "#10B981"
  location:
    emoji: "📍"
    color: "#3B82F6"
  chapter:
    emoji: "📖"
    color: "#8B5CF6"

# Explicit folder structure (optional - omit for full auto-discovery)
children:
  - name: "Characters"
    order: 1
    emoji: "👥"
    children: []  # Auto-discover contents

  - name: "Locations"
    order: 2
    emoji: "🗺️"
    children: []

  - name: "Story"
    order: 3
    emoji: "📚"
    children: []
```

## Pattern Syntax Reference

| Pattern | Matches |
|---------|---------|
| `*.codex.yaml` | All codex files in root |
| `**/*.codex.yaml` | All codex files recursively |
| `docs/**/*.md` | Markdown in docs and subfolders |
| `!README.md` | Exclude specific file |
| `**/node_modules/**` | Exclude node_modules anywhere |

## Child Node Fields

| Field | Required | Default | Purpose |
|-------|----------|---------|---------|
| name | Yes | - | Folder/file name (no extension) |
| title | No | name | Display alternative |
| order | No | 999 | Sort position |
| emoji | No | typeStyles | Visual indicator |
| status | No | "private" | published/private/draft |
| featured | No | false | Highlight at top |
| hidden | No | false | Hide from views |
| children | No | auto | Nested items (folders only) |

## Status Values

- `"published"` - Visible to everyone
- `"private"` - Owner only (default)
- `"draft"` - Work in progress, owner only

**Status does NOT inherit.** Each item must explicitly set `status: published` to be public.

## Script Usage

```bash
# Generate index for current directory
python ${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py .

# Generate for specific path
python ${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py /path/to/project

# Preview without writing
python ${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py . --dry-run

# Include markdown files
python ${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py . --include-md

# Verbose output
python ${CLAUDE_PLUGIN_ROOT}/skills/index/index_generator.py . -v
```

## Workflow

1. **Ask** about project name and structure
2. **Generate** minimal or full index based on needs
3. **Run generator** to scan and populate children
4. **Run auto-fixer** on the generated index
5. **Commit** the index.codex.yaml file

## Common Use Cases

| Scenario | Approach |
|----------|----------|
| New project | Minimal index with auto-discovery |
| Existing content | Generate with `--scan` to detect structure |
| Curated order | Explicit children with `order` fields |
| Mixed | Explicit folders, auto-discover within |

## Remember

- `index.codex.yaml` = user-controlled (create this)
- `.index.codex.yaml` = system cache (never create)
- Types auto-detect from extensions
- Status must be set per-item
- Patterns use gitignore syntax
