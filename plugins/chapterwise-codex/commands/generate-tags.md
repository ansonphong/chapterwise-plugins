---
description: Auto-generate tags from content in codex files
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
triggers:
  - generate tags
  - auto tags
  - extract tags
  - create tags
  - tag extraction
---

# Generate Tags

Automatically extract meaningful tags from the body content of codex files using text analysis.

## How It Works

1. Extracts text from `body` fields in the codex
2. Tokenizes with support for extended Latin characters
3. Filters out 200+ common stopwords and manuscript boilerplate
4. Analyzes word frequency with heading boost
5. Extracts meaningful bigrams (two-word phrases)
6. Returns top N tags with smart capitalization

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py <file.codex.yaml> [options]
```

### Options

```bash
# Basic usage (generates up to 10 tags per entity)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml

# Generate more tags
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --count 15

# Require more occurrences before tagging
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --min-count 5

# Output with counts (detailed format)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --format detailed

# Also process included files
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --follow-includes

# Preview without changes
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml --dry-run

# Verbose output
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tag_generator.py story.codex.yaml -v
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
