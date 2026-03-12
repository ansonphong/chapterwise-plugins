# Import Recipe — Output Format

## What You Get

Every import produces the same thing: a complete, git-ready Chapterwise project. Regardless of source format, the output is consistent and immediately usable.

## Project Structure: Flat

For simpler manuscripts without parts/sections:

```
my-novel/
├── index.codex.yaml
├── prologue.md
├── chapter-01-the-awakening.md
├── chapter-02-the-call.md
├── chapter-03-into-the-woods.md
├── ...
├── chapter-28-coming-home.md
├── epilogue.md
└── .chapterwise/
    ├── settings.json
    └── import-recipe/
        ├── recipe.yaml
        ├── convert.py
        ├── structure_map.yaml
        ├── preferences.yaml
        ├── run.sh
        └── log.md
```

## Project Structure: Folders Per Part

For multi-part novels, anthologies, or structured manuscripts:

```
my-novel/
├── index.codex.yaml
├── prologue.md
├── part-1-departure/
│   ├── index.codex.yaml          # Part-level index
│   ├── chapter-01-the-awakening.md
│   ├── chapter-02-the-call.md
│   ├── chapter-03-into-the-woods.md
│   └── ...
├── part-2-initiation/
│   ├── index.codex.yaml
│   ├── chapter-10-the-crossing.md
│   └── ...
├── part-3-return/
│   ├── index.codex.yaml
│   ├── chapter-20-the-road-back.md
│   └── ...
├── epilogue.md
└── .chapterwise/
    ├── settings.json
    └── import-recipe/
        └── ...
```

## index.codex.yaml — The Master Index

The root index ties everything together. It's the entry point for ChapterWise.app, the VS Code extension, and the codex reader.

```yaml
metadata:
  formatVersion: "1.2"
  documentVersion: "1.0.0"
  created: "2026-02-27T14:30:00Z"

id: index-root
type: index
title: "The Long Way Home"
summary: "A literary novel in three parts about finding your way back."
status: private

attributes:
  - key: author
    value: "Jane Smith"
  - key: word_count
    value: 87234
  - key: chapter_count
    value: 28
  - key: imported_from
    value: "my-novel.pdf"
  - key: imported_date
    value: "2026-02-27"

patterns:
  include:
    - "**/*.codex.yaml"
    - "**/*.md"
  exclude:
    - "**/.git/**"
    - "**/.chapterwise/**"
    - "**/.*"

typeStyles:
  chapter:
    emoji: "scroll-emoji"
    color: "#4A90D9"
  section:
    emoji: "bookmark-emoji"
    color: "#7B68EE"
  index:
    emoji: "book-emoji"
    color: "#2E8B57"

display:
  defaultView: tree
  sortBy: order

children:
  - include: ./prologue.md
  - include: ./part-1-departure/index.codex.yaml
  - include: ./part-2-initiation/index.codex.yaml
  - include: ./part-3-return/index.codex.yaml
  - include: ./epilogue.md
```

## Chapter File: Codex Lite (Markdown)

The default and recommended output format. Clean markdown with YAML frontmatter.

```markdown
---
type: chapter
name: "Chapter I: The Awakening"
summary: "Elena wakes in an unfamiliar city with no memory of how she arrived."
word_count: 3200
order: 1
tags:
  - elena
  - awakening
  - mystery
  - urban
status: private
---

# Chapter I: The Awakening

The morning light filtered through curtains Elena didn't recognize. She lay still,
cataloging sensations: the scratch of unfamiliar sheets, the distant hum of traffic
on streets she couldn't name, the faint smell of coffee from somewhere below.

She sat up slowly, and the room swam into focus...

[Full chapter content, clean markdown]
```

## Chapter File: Codex YAML (Alternative)

For writers who want richer structure:

```yaml
metadata:
  formatVersion: "1.2"
  created: "2026-02-27T14:30:00Z"

id: "ch01-the-awakening"
type: chapter
name: "Chapter I: The Awakening"
summary: "Elena wakes in an unfamiliar city with no memory of how she arrived."
status: private
order: 1
tags:
  - elena
  - awakening
  - mystery
  - urban

attributes:
  - key: word_count
    value: 3200
    dataType: int
  - key: pov_character
    value: "Elena"
  - key: location
    value: "Unknown city"
  - key: time_period
    value: "Morning, Day 1"

body: |
  The morning light filtered through curtains Elena didn't recognize. She lay still,
  cataloging sensations: the scratch of unfamiliar sheets, the distant hum of traffic
  on streets she couldn't name, the faint smell of coffee from somewhere below.

  She sat up slowly, and the room swam into focus...

  [Full chapter content]
```

## .chapterwise/settings.json

Project-level settings committed to git. Shared across all ChapterWise tools.

```json
{
  "project": {
    "name": "The Long Way Home",
    "author": "Jane Smith",
    "type": "novel"
  },
  "import": {
    "source_format": "pdf",
    "source_app": null,
    "imported_date": "2026-02-27",
    "recipe_version": "1.0"
  },
  "display": {
    "defaultView": "tree",
    "sortBy": "order"
  }
}
```

## File Naming Conventions

All output files follow consistent naming:

| Content | Filename Pattern | Example |
|---------|-----------------|---------|
| Chapter | `chapter-NN-slug.md` | `chapter-01-the-awakening.md` |
| Part index | `part-N-slug/index.codex.yaml` | `part-1-departure/index.codex.yaml` |
| Prologue | `prologue.md` | `prologue.md` |
| Epilogue | `epilogue.md` | `epilogue.md` |
| Appendix | `appendix-slug.md` | `appendix-character-guide.md` |
| Master index | `index.codex.yaml` | `index.codex.yaml` |

**Slugification rules** (matching `url_path_resolver.py`):
- Lowercase
- Spaces → hyphens
- Strip special characters: `()&,.[]+`
- Collapse multiple hyphens
- No trailing hyphens

## What the Output Enables

Once the import is complete, the writer can immediately:

### 1. Push to Git
```bash
cd my-novel
git init && git add -A && git commit -m "Import from PDF"
git remote add origin https://github.com/user/my-novel.git
git push -u origin main
```

### 2. Connect to ChapterWise.app
- Go to chapterwise.app → Projects → Add Git Project
- Paste the GitHub URL
- ChapterWise reads the `index.codex.yaml` and renders everything

### 3. Open in VS Code
- Install the ChapterWise Codex extension
- Open the project folder
- The Navigator panel shows the full tree from `index.codex.yaml`

### 4. Run Analysis
```
/analysis summary chapter-01-the-awakening.md
/analysis --all characters
```

### 5. Keep Writing
- Edit chapters directly in markdown
- The `.chapterwise/import-recipe/` is there for re-importing updated source files
- Source of truth can be the Chapterwise project OR the original manuscript — writer's choice

## Source App Metadata Preservation

When importing from writing apps, source-specific metadata is preserved in frontmatter:

### From Scrivener
```yaml
---
type: chapter
name: "Chapter 1"
scrivener_label: "Revised"
scrivener_status: "Second Draft"
scrivener_compile: true
tags:
  - mystery
  - elena
  - from-scrivener-keywords
---
```

### From Ulysses
```yaml
---
type: chapter
name: "Chapter 1"
ulysses_keywords:
  - mystery
  - elena
target_word_count: 3000
tags:
  - mystery
  - elena
---
```

Source app metadata uses namespaced keys (`scrivener_*`, `ulysses_*`) so it never conflicts with standard Chapterwise fields.
