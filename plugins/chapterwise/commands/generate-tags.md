---
description: Auto-generate tags from content in codex or markdown files
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - generate tags
  - auto tags
  - extract tags
  - create tags
  - tag extraction
argument-hint: "[file.codex.yaml or file.md]"
---

# Generate Tags

Automatically extract meaningful tags from content using text analysis.

**Supports both:**
- Full Codex files (`.codex.yaml`, `.codex.json`)
- Codex Lite / Markdown files (`.md` with YAML frontmatter)

## How It Works

1. Extracts text from `body` fields (Codex) or markdown body (Codex Lite)
2. Tokenizes with support for extended Latin characters
3. Filters out 200+ common stopwords and manuscript boilerplate
4. Analyzes word frequency with heading boost
5. Extracts meaningful bigrams (two-word phrases)
6. Returns top N tags with smart capitalization

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file> [options]
```

### Options

```bash
# Codex files
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --count 15
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --follow-includes

# Markdown (Codex Lite) files
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py chapter.md
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py chapter.md --count 5 --min-count 2

# Common options
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file> --min-count 5
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file> --format detailed
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file> --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file> -v
```

### Parameters

| Option | Default | Description |
|--------|---------|-------------|
| `--count N` | 10 | Maximum tags per entity |
| `--min-count N` | 3 | Minimum word occurrences to be a tag |
| `--format` | simple | `simple` (strings) or `detailed` (with counts) |
| `--follow-includes` | false | Process included files |
| `-d`, `--dry-run` | false | Preview without changes |

## Output Formats

### Simple (default)

```yaml
tags:
  - Roman
  - Senate
  - Awakening
  - Political Intrigue
```

### Detailed

```yaml
tags:
  - name: Roman
    count: 15
  - name: Senate
    count: 12
  - name: Awakening
    count: 8
```

## Algorithm Features

- **Heading Boost:** Words in markdown headings get 2x weight
- **Bigram Extraction:** Captures two-word phrases like "Roman Senate"
- **Redundancy Avoidance:** If "Roman Senate" is a tag, "Roman" and "Senate" won't be added separately
- **Smart Capitalization:** Tags are title-cased appropriately
- **Stopword Filtering:** Removes common words, manuscript terms (chapter, preface, etc.)

## Workflow

1. User asks to generate or extract tags
2. If no file specified, ask which file
3. Ask for preferences (count, format) if not obvious
4. Run tag generator
5. Report results: entities updated, total tags generated
6. If no tags generated, explain possible reasons (short content, low word frequency)

## Tips

- For short content, try `--min-count 1` or `--min-count 2`
- Use `--format detailed` to see which words occur most
- Run `--dry-run` first to preview the tags
- Use `--follow-includes` for projects with modular files

---

## Error Handling

| Situation | Response |
|-----------|----------|
| File not found | "File not found: {path}" |
| No body content to analyze | "No body text found in {path} — nothing to tag." |
| Content too short for meaningful tags | "Content is very short ({N} words). Try `--min-count 1` for results." |
| Invalid YAML/JSON syntax | "Cannot parse {path} — check for syntax errors." |
| Missing PyYAML dependency | "Missing PyYAML. Install with: `pip3 install pyyaml`" |

## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start | Scanning | "Scanning {file} for content..." |
| Processing | Reducing | "Reducing text to top {N} tags..." |
| Completion | Done | "Done. {N} tags generated for {file}." |
