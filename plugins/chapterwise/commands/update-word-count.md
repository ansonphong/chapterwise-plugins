---
description: Update word count metadata in codex files
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - update word count
  - count codex words
  - calculate word count
  - codex word statistics
  - chapterwise:update-word-count
argument-hint: "[file_or_directory]"
---

# Update Word Count

Count words in body fields and update the `word_count` attribute for all entities in a codex file.

## When to Use

- After editing body content in a codex file
- To get accurate word counts for manuscripts, chapters, or documents
- Before publishing or exporting content
- For tracking writing progress

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py <file_or_directory> [options]
```

### Options

```bash
# Update word count in a single file
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py story.codex.yaml

# Update word count in a markdown file (Codex Lite)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py chapter.md

# Process included files too
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py story.codex.yaml --follow-includes

# Process all files in a directory
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py /path/to/codex

# Process directory recursively
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py /path/to/codex --recursive

# Skip markdown files when processing directories
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py /path/to/codex -r --no-markdown

# Dry run (preview without changes)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py story.codex.yaml --dry-run

# Verbose output
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/word_count.py story.codex.yaml -v
```

### Flags

| Flag | Description |
|------|-------------|
| `-r`, `--recursive` | Process subdirectories |
| `--follow-includes` | Process included files |
| `-d`, `--dry-run` | Preview without changes |
| `--no-markdown` | Skip `.md` files in directories |
| `-v`, `--verbose` | Detailed output |

## How It Works

### For Codex Files (.codex.yaml)

1. Traverses the document tree recursively
2. For each entity with a `body` field:
   - Counts words (splits on whitespace)
   - Finds or creates a `word_count` attribute
   - Updates the value if changed

**Before:**
```yaml
type: chapter
name: The Beginning
body: |
  It was a dark and stormy night. The wind howled through
  the empty streets as Sarah made her way home.
```

**After:**
```yaml
type: chapter
name: The Beginning
body: |
  It was a dark and stormy night. The wind howled through
  the empty streets as Sarah made her way home.
attributes:
  - key: word_count
    name: Word Count
    value: 24
    dataType: int
```

### For Codex Lite Files (.md)

1. Parses YAML frontmatter
2. Counts words in the markdown body (after frontmatter)
3. Updates `word_count` in frontmatter

**Before:**
```markdown
---
type: document
name: My Chapter
---

Content goes here with many words...
```

**After:**
```markdown
---
type: document
name: My Chapter
word_count: 5
---

Content goes here with many words...
```

## Handling Includes

With `--follow-includes`, the script will:
1. Detect `include` directives in children
2. Load and process included files
3. Update word counts in those files too
4. Track visited files to avoid cycles

## Example Output

```
[DRY RUN] Updating word counts
File: story.codex.yaml

Entities updated: 12
Total words: 45,230

Files modified:
  - story.codex.yaml
  - chapters/ch01.codex.yaml
  - chapters/ch02.codex.yaml

Warnings:
  - Include file not found: chapters/deleted.codex.yaml
```

## Workflow

1. User asks to update word counts
2. If no file specified, ask which file or directory
3. Ask if include files should be processed
4. Run word counter
5. Report: entities updated, total words, files modified
6. List any warnings (missing includes, etc.)

---

## Error Handling

| Situation | Response |
|-----------|----------|
| File not found | "File not found: {path}" |
| No body content found | "No body fields found in {path} — nothing to count." |
| Include file missing | "Included file not found: {include_path} — skipping." |
| Invalid YAML/JSON syntax | "Cannot parse {path} — check for syntax errors." |
| Missing PyYAML dependency | "Missing PyYAML. Install with: `pip3 install pyyaml`" |

## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start | Scanning | "Scanning {file} for body fields..." |
| Processing | Reducing | "Reducing word counts... {N} entities found." |
| Completion | Done | "Done. {N} entities updated, {total} total words." |
