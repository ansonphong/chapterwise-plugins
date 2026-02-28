---
description: "Create Codex Lite Markdown with frontmatter"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - codex lite
  - lite format
  - codex markdown
  - add codex frontmatter
  - chapterwise:lite
argument-hint: "[file.md]"
---

# Chapterwise Codex Lite Format

Add Chapterwise metadata to standard Markdown files using YAML frontmatter. Codex Lite is the **simplified format** for flat documents that don't need hierarchy.

## When to Apply

Apply this command when the user asks to:
- Add Chapterwise metadata frontmatter to a Markdown file
- Create a simple codex document without nested hierarchy
- Convert a plain Markdown file to Codex Lite format

## When to Use Codex Lite vs Full Codex

| Use Codex Lite | Use Full Codex |
|----------------|----------------|
| Simple documents | Complex hierarchies |
| Notes, articles | Scripts with acts/beats |
| Character profiles | Multi-level structures |
| Location descriptions | Budgets with line items |
| Any flat content | Anything with children |

## File Format

- **Extension:** `.md` (standard Markdown)
- **Frontmatter:** YAML between `---` delimiters at file start
- **Body:** Standard Markdown after closing `---`

## Script Location

```
${CLAUDE_PLUGIN_ROOT}/scripts/lite_helper.py
```

## All Fields Are Optional

A bare Markdown file with no frontmatter is valid Codex Lite. Add fields as needed.

## Template

```markdown
---
type: document
summary: "Brief one-line description"
tags: tag1, tag2, tag3
status: private
---

# Document Title

Your content here in standard Markdown...
```

## Available Fields

### Core Identity

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | Node category (character, location, chapter, note, etc.) |
| `name` | string | Display name |
| `title` | string | Alternative display title |
| `summary` | string | Brief description |
| `id` | string | Unique identifier (UUID recommended) |

### Organization

| Field | Type | Purpose |
|-------|------|---------|
| `tags` | string/array | Categories (comma-separated or YAML array) |
| `author` | string | Author name(s) |
| `last_updated` | string | ISO-8601 date |

### Publishing

| Field | Type | Purpose |
|-------|------|---------|
| `status` | string | `published`, `private`, or `draft` |
| `featured` | boolean | Highlight this item |

### Media

| Field | Type | Purpose |
|-------|------|---------|
| `image` | string | Cover image URL/path |
| `images` | array | Gallery of images |

### Advanced

| Field | Type | Purpose |
|-------|------|---------|
| `attributes` | array | Structured key-value metadata |
| `word_count` | integer | Auto-calculated by helper |

## Title Detection Priority

When displaying, Chapterwise uses this order:
1. `name` field in frontmatter
2. `title` field in frontmatter
3. First `# H1` heading in body
4. Filename (fallback)

## Common Types

- `character` - Person or entity
- `location` - Place or setting
- `chapter` - Story section
- `scene` - Story moment
- `note` - General note
- `concept` - Idea or theme
- `document` - Generic document
- `article` - Published writing

## Examples

### Character Profile

```markdown
---
type: character
summary: "A quantum physicist who discovers her memories span multiple timelines"
tags: protagonist, scientist, multiverse
status: draft
image: "/images/maya-chen.jpg"
---

# Maya Chen

## Background

Maya grew up in Vancouver...

## Personality

She's driven by curiosity...
```

### Location Description

```markdown
---
type: location
summary: "A convergence point between parallel timelines"
tags: setting, multiverse, key-location
---

# The Nexus

A shimmering void where realities overlap...
```

### Simple Note

```markdown
---
type: note
tags: research, quantum-mechanics
---

# Notes on Quantum Entanglement

Key concepts to explore...
```

## Script Usage

```bash
# Validate/fix a markdown file's frontmatter
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lite_helper.py document.md

# Process all markdown files in directory
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lite_helper.py /path/to/folder --recursive

# Preview without changes
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lite_helper.py document.md --dry-run

# Add missing frontmatter to bare markdown
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lite_helper.py document.md --init
```

## What the Helper Fixes

| Issue | Fix Applied |
|-------|-------------|
| Missing `id` | Generates UUID |
| Missing `name` | Extracts from H1 or filename |
| Missing `type` | Adds `type: document` |
| Invalid UUID | Regenerates valid UUID |
| Word count | Calculates and updates `word_count` |
| No frontmatter | Adds minimal frontmatter (with `--init`) |

## Workflow

1. **Create** markdown file with content
2. **Add** frontmatter with relevant fields
3. **Run** lite_helper.py to validate/fix
4. **Commit** the file

## Best Practices

- **Keep frontmatter minimal** - only include fields you need
- **Use H1 for title** - `name` field only when different from heading
- **Comma-separated tags** - simpler than YAML arrays
- **Status for visibility** - use `status: published` for public items
- **Attributes sparingly** - only for truly structured data

## Remember

- **All fields optional** - bare Markdown is valid
- **No hierarchy** - use full Codex for nested children
- **No relations** - use full Codex for entity relationships
- **Portable** - works with any Markdown renderer
