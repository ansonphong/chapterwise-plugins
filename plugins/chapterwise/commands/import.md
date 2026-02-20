---
description: "Import a folder of content (markdown, text, wiki exports) into a Chapterwise project. Guided wizard that analyzes your content, helps you choose the best structure and format, and converts everything."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - import content
  - import to chapterwise
  - import project
  - import world bible
  - import wiki
  - import docs
  - bring into chapterwise
  - add existing content
argument-hint: "[path/to/content/folder]"
---

# Import Content to Chapterwise

Import a folder of existing content (markdown files, text files, wiki exports, docs) into a well-structured Chapterwise project. This skill guides you through the process step by step — analyzing your content, helping you choose the right structure and format, then executing the conversion.

## When This Skill Applies

- User has an existing folder of markdown/text content they want to bring into Chapterwise
- User is converting a wiki, world bible, reference docs, novel drafts, or any organized content
- User mentions "import", "bring into chapterwise", "convert my folder", or similar
- User points to a directory of `.md`, `.txt`, `.html`, or mixed content files

## What This Skill Is NOT

- **Single-file conversion** — use `/chapterwise-codex:convert-to-codex` instead
- **Scrivener import** — use `/chapterwise-codex:import-scrivener` instead
- **Creating new content from scratch** — use `/chapterwise-codex:format` instead

---

## Workflow

Follow these 6 steps in order. Every import goes through this process.

### Step 1: Discover

Scan the source directory to understand what we're working with.

**If no path provided as argument:**
- Ask the user for the path to their content folder

**Once path is known:**

1. List the top-level directory structure
2. Count files by type (`.md`, `.txt`, `.html`, `.rtf`, `.yaml`, `.json`, other)
3. Map the folder hierarchy (sections, subfolders, nesting depth)
4. Read 3-5 representative files to understand:
   - Content type (worldbuilding, novel, reference, mixed)
   - Whether files have frontmatter (YAML, TOML)
   - Average file length and depth
   - How content is organized (by topic, chronologically, flat)
5. Check for existing structure files (table of contents, sidebar config, navigation files, README)

**Present a summary to the user:**

```
Found: [X] files across [Y] folders
Types: [breakdown by extension]
Structure: [description of folder organization]
Content: [what kind of content this appears to be]
Sample files: [list 5-8 representative filenames]
```

### Step 2: Classify

Ask the user two questions to understand intent.

**Question 1 — What is this content?**

Use AskUserQuestion with these options:
- **World bible / Lore reference** — Worldbuilding, factions, magic systems, locations, characters, timelines
- **Novel / Manuscript** — Chapters, scenes, acts, story content meant to be read in order
- **Reference documentation** — Technical docs, guides, how-tos, knowledge base articles
- **Mixed project** — Combination of narrative, reference, and notes

**Question 2 — What's the goal?**

Use AskUserQuestion with these options:
- **Published reference** — A beautiful, browseable project to share with readers, collaborators, or the public
- **Private working tool** — A personal workspace for organizing, expanding, and referencing while creating
- **Tiered access** — Some sections public (lore, guides), some private (spoilers, drafts, working notes)
- **Showcase / demo** — Demonstrate what Chapterwise can do with this type of content

### Step 3: Structure

Based on what you found in Steps 1-2, propose **2-3 structural approaches** with trade-offs. Always include your recommendation and explain why.

**Common approaches (adapt to the specific content):**

| Approach | Best For | Description |
|----------|----------|-------------|
| **Section-per-file** | Wiki/lore with clear sections | Each major section becomes one file with children for sub-topics. Keeps related content together. |
| **File-per-page** | Large projects, granular control | Every source page becomes its own file. Index organizes them into folders. Maximum flexibility. |
| **Consolidated** | Small projects, quick reference | Fewer, richer files. Merge related pages into single documents with deep nesting. |

Use AskUserQuestion to let the user choose.

### Step 4: Format

This is a critical choice about data format. Present it clearly and honestly.

Use AskUserQuestion with this framing:

**"Would you like to keep your content in Markdown or convert to Codex format?"**

Options:

- **Markdown (Codex Lite)** — Your content stays as `.md` files with YAML frontmatter. Human-readable, editable in any text editor, Git-friendly. Chapterwise reads Markdown natively. Great if you want simplicity and maximum portability.

- **Codex format (.codex.yaml)** — Adds richer structure: nested children, typed attributes, relations between entries. Your data lives in YAML — an open standard. You can always convert back to Markdown if you need to. More powerful for complex, interconnected content like world bibles.

**Important:** Regardless of which format users choose, communicate this clearly:

> Either way, your content remains in open formats you control. No lock-in, no proprietary databases. Your files are plain text on your filesystem, in your Git repo. You always own your data.

### Step 5: Convert

Execute the conversion based on all decisions from Steps 1-4.

#### 5a. Create output directory

Ask where to output the converted project:
- Default: a new folder in the current directory named after the project
- Or let the user specify a path

#### 5b. Convert content files

**If Markdown (Codex Lite) was chosen:**

For each source file:
1. Read the source content
2. Extract or create YAML frontmatter with appropriate fields:
   - `type` — Assign a semantic type based on content (faction, character, concept, location, chapter, etc.)
   - `name` — Derive from filename, frontmatter title, or first H1
   - `summary` — First paragraph or existing description
   - `status` — Based on user's access tier decision (published/private/draft)
   - `tags` — Extract from content, existing frontmatter, or folder context
3. Clean up body content (strip old frontmatter, fix relative links)
4. Write to output directory with clean filenames

For section-per-file structure: create one `.md` per section, using H2/H3 headings for sub-topics within each file.

**If Codex format was chosen:**

For each section/file:
1. Read the source content
2. Create codex structure:
   - `metadata.formatVersion: "1.2"`
   - `type` — Semantic type for this content
   - `name`, `title`, `summary` — From source
   - `body` — Main prose content (pipe `|` for multiline)
   - `attributes` — Structured data extracted from tables, key-value pairs, frontmatter fields
   - `children` — Sub-sections become child nodes with their own type, name, body
   - `tags` — For discoverability
   - `status` — Based on access tier decision
3. Write `.codex.yaml` files to output directory

For section-per-file structure: each section file gets children for its sub-pages. Tables become attributes. Sub-headings become children.

**Smart type assignment:**

When analyzing content, assign types intelligently based on what the content describes:

| Content About | Suggested Type |
|---------------|---------------|
| Characters, people, NPCs | `character` |
| Places, cities, planets | `location` |
| Factions, organizations, groups | `faction` |
| Magic systems, technology, abilities | `concept` |
| History, timeline, events | `history` |
| Items, artifacts, equipment | `item` |
| Rules, laws, governance | `system` |
| Story structure, plot, arcs | `story` |
| Glossary, terminology | `reference` |
| Creatures, species, races | `species` |
| General overview, introduction | `overview` |

#### 5c. Generate index.codex.yaml

Create a root `index.codex.yaml` that ties everything together:

```yaml
metadata:
  formatVersion: "1.2"
  documentVersion: "1.0.0"
  created: "[ISO timestamp]"

id: index-root
type: index
title: "[Project Name]"
summary: "[Project description]"
status: private

patterns:
  include:
    - "**/*.codex.yaml"
    - "**/*.md"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/.*"

typeStyles:
  # Assign emoji + color per type used in this project
  character:
    emoji: "char-emoji"
    color: "#hex"
  # ... for each type used

display:
  defaultView: tree
  sortBy: order

children:
  # Ordered list of all top-level files/sections
  - name: "Section Name"
    order: 1
    status: published  # or private, based on user's tier decisions
    # ... for each section
```

Customize typeStyles based on what types were actually used in the conversion. Pick thematically appropriate emoji for the project's genre.

#### 5d. Run auto-fixer

If codex format was chosen, run auto-fixer on all generated files:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_fixer.py [output-directory] --recursive --verbose
```

#### 5e. Initialize git repo (optional)

If the output directory is not already in a git repo, ask the user:

> "Would you like me to initialize a Git repository? This is required for connecting to Chapterwise."

If yes:
```bash
cd [output-directory] && git init && git add -A && git commit -m "Initial import from [source name]"
```

### Step 6: Report

Present a clear summary of what was created:

```
Import complete!

Source: [source path] ([X] files)
Output: [output path]
Format: [Markdown / Codex YAML]
Structure: [description of chosen structure]

Created:
  [N] content files
  1 index.codex.yaml
  [list of section/file names with types]

Access tiers:
  Published: [list]
  Private: [list]

Next steps:
  1. Review the converted files — especially check that types and summaries look right
  2. Push to GitHub: git remote add origin <your-repo-url> && git push -u origin main
  3. Connect the repo in Chapterwise: [your-chapterwise-url] -> Projects -> Add Git Project
  4. Edit individual files anytime — they're plain [Markdown/YAML] in your repo
```

---

## Handling Edge Cases

### Source has no clear structure (flat folder of files)
- Propose grouping by content similarity
- Offer to read all files and suggest a logical organization
- Can create sections based on common themes, tags, or topics found in the content

### Source has mixed formats (.md, .txt, .html, .rtf)
- Convert all to the chosen output format
- Preserve content, strip format-specific markup
- Note any files that couldn't be cleanly converted

### Source has images or media
- Copy media files to output directory
- Update references in content files
- Note: Chapterwise handles images via URL references

### Source already has YAML frontmatter
- Preserve and migrate existing frontmatter fields
- Map common fields (title, description, tags, date) to codex equivalents
- Keep source-specific fields as attributes

### Very large projects (50+ files)
- Use Task tool with parallel agents to convert files concurrently
- Group conversion work by section to maintain context
- Report progress as sections complete

### Source is a git repo
- Note the remote URL for reference
- Do NOT modify the source — always create fresh output
- Suggest the user can set up the new repo as a separate project

---

## Tips

- **Always scan before converting** — understand what you're working with
- **Recommend section-per-file for world bibles** — it's the sweet spot for reference content
- **Recommend file-per-page for novels** — each chapter should be independently addressable
- **Match the source's mental model** — if the author organized it a certain way, preserve that intent
- **Assign types thoughtfully** — good type assignment makes the project navigable and enables typeStyles
- **Set status intentionally** — default to private, only publish what the user explicitly wants public

## Remember

- This is a **guided wizard**, not a batch script — take time at each step to get the user's input
- **Never modify the source directory** — always create fresh output
- **Data ownership is the core message** — open formats, no lock-in, user controls everything
- **Run auto-fixer** on codex output — it catches formatting issues you won't notice
- **The user's existing organization is valuable** — preserve their mental model unless they want to reshape it
