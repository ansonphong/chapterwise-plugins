# Chapterwise Insert Plugin - Design Document

**Date:** 2025-01-31
**Status:** Draft - Pending Approval
**Author:** Claude + Phong

---

## Overview

A Claude Code plugin for intelligently inserting notes into Chapterwise Codex manuscripts. The core value proposition: **finding the right location** in a manuscript is the most time-consuming part of note-taking workflow. This plugin uses semantic matching and hierarchical agent search to locate insertion points automatically.

---

## Plugin Structure

```
plugins/chapterwise-insert/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   └── insert.md                # Main skill definition
└── scripts/
    ├── insert_engine.py         # Core insertion logic
    ├── location_finder.py       # Semantic matching engine
    └── note_parser.py           # Parses notes, splits batches
```

**Single command:** `/insert` - handles all modes (single, batch, interactive, clipboard)

---

## Supported Formats

| Format | Extension | Structure | Insert Method |
|--------|-----------|-----------|---------------|
| **Codex** | `.codex.yaml` | YAML with `body` field, `children` array | YAML manipulation via `ruamel.yaml` |
| **Codex JSON** | `.codex.json` | JSON equivalent | JSON manipulation |
| **Codex Lite** | `.md` | YAML frontmatter + Markdown body | Text insertion after frontmatter |

---

## Core Features

### 1. Invocation Modes

```bash
# Single note (inline)
/insert "Elena drew her sword..." into chapter-23.codex.yaml

# Single note with instruction
/insert "after the battle - Elena drew her sword..." into ./manuscript/

# Batch from file
/insert notes.txt into ./manuscript/

# Interactive mode
/insert
> [starts interactive session]

# From clipboard
/insert --clipboard into ./manuscript/
```

### 2. Instruction Parsing

Notes can include location instructions that get separated from content:

**Input:**
```
this should go after the hyperborean incursion

Elena drew her sword, the blade catching moonlight...
```

**Result:**
- Instruction: `"this should go after the hyperborean incursion"` → used for location finding
- Content: `"Elena drew her sword..."` → the actual insert
- Instruction preserved in metadata, not in manuscript

### 3. Insert Markers (HTML Comments)

All inserts are wrapped with metadata markers:

```html
<!-- INSERT
time: 2024-01-27T10:30:00Z
source: notepad
instruction: "this should go after the hyperborean incursion"
confidence: 0.93
matched_after: "The hyperborean horde breached the northern wall..."
-->
Elena drew her sword, the blade catching moonlight...
<!-- /INSERT -->
```

**Benefits:**
- Standard markdown (won't break renderers)
- Invisible in preview (clean reading experience)
- VS Code can detect and highlight
- Metadata preserved for review
- Easy to accept (just delete comment tags)

### 4. Confidence-Based UX Flow

```
┌─────────────────────────────────────────────┐
│           Analyze content + context         │
└─────────────────────┬───────────────────────┘
                      │
      ┌───────────────┴───────────────┐
      │  Confidence ≥ 95%             │
      │  ─────────────────            │
      │  Auto-insert + report         │
      │  "Inserted after [X]"         │
      └───────────────────────────────┘
                      │
      ┌───────────────┴───────────────┐
      │  Confidence 50-95%            │
      │  ─────────────────            │
      │  Show 2-3 candidates          │
      │  User picks A/B/C             │
      └───────────────────────────────┘
                      │
      ┌───────────────┴───────────────┐
      │  Confidence < 50%             │
      │  ─────────────────            │
      │  "Couldn't find match.        │
      │   Best guess: [X]             │
      │   Insert here? Or clarify?"   │
      └───────────────────────────────┘
```

---

## Hierarchical Agent Search

### The Problem

A full book could be 100k+ words - too much for one context window.

### The Solution: Two-Pass Fractal Search

**Pass 1: Coarse Scan (fast, parallel)**
- 5-10 agents, each handles multiple chapters
- Only reads: titles, names, summaries, first 500 chars of body
- Returns: "Chapters 23, 27 look promising"

**Pass 2: Deep Scan (focused, parallel)**
- 2-3 agents on promising chapters only
- Full content read
- Returns: exact line numbers, confidence, context snippets

### Chunking Strategy

| Chapters | Agents | Chapters per Agent |
|----------|--------|-------------------|
| 1-10     | 1-3    | ~3-5 each         |
| 11-30    | 4-6    | ~5-7 each         |
| 31-50    | 6-8    | ~6-8 each         |
| 50+      | 8-10   | ~5-10 each        |

Cap at ~10 parallel agents max.

### Agent Output Format

```json
{
  "candidates": [
    {
      "file": "chapter-23.codex.yaml",
      "line": 247,
      "insert_after": "The hyperborean horde breached...",
      "confidence": 87,
      "reason": "Matches 'hyperborean incursion' at line 245"
    }
  ]
}
```

---

## Matching Strategies

| Strategy | Example Match |
|----------|---------------|
| Exact phrase | "hyperborean incursion" → finds that phrase |
| Fuzzy match | "hyperborian incursion" → tolerates typos |
| Semantic keywords | "the invasion from the north" → matches hyperborean context |
| Structural | "chapter 5" → finds node with that title/name |
| Character anchor | "when Elena speaks" → finds dialogue by Elena |

---

## Batch Processing

### Batch File Format

```
This should go after the hyperborean incursion

Elena drew her sword, the blade catching moonlight.
The northern wind carried whispers of the battle to come.

---

In chapter 3, during the council meeting

"We cannot hold the eastern front," Lord Ashworth declared,
his voice echoing in the stone chamber.

---

Near the end, before the epilogue

Ten years had passed. The scars remained, but so did hope.
```

### Parsing Rules

1. `---` on its own line = note separator (primary)
2. Numbered lists (`1.`, `2.`) = separator (if obvious)
3. Clear headers = separator (if obvious)
4. Blank lines alone = **NOT** a separator (content may have spacing)
5. First paragraph before blank line = instruction (if reads like location hint)
6. Remaining content = actual insert text

### Custom Delimiter

```bash
/insert --delimiter "===" notes.txt into ./manuscript/
```

---

## Summary Report

```
╔══════════════════════════════════════════════════════════════════╗
║                    INSERT SUMMARY REPORT                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Batch: notes-to-insert.txt                                     ║
║  Target: ./manuscript/                                          ║
║  Total notes: 12                                                ║
╠══════════════════════════════════════════════════════════════════╣

  #  │ STATUS   │ CONF │ FILE                    │ LINE │ MATCHED
 ────┼──────────┼──────┼─────────────────────────┼──────┼──────────────────
  1  │ ✓ AUTO   │  97% │ chapter-23.codex.yaml   │  847 │ "hyperborean horde"
  2  │ ✓ PICKED │  89% │ chapter-03.codex.yaml   │  156 │ "council meeting"
  3  │ ✓ AUTO   │  96% │ chapter-48.md           │  412 │ "before epilogue"
  4  │ ✗ SKIP   │  23% │ -                       │    - │ No good match
  5  │ ⚠ DUP    │    - │ chapter-23.codex.yaml   │  847 │ Duplicate of #1

╠══════════════════════════════════════════════════════════════════╣
║  SUMMARY: ✓ Inserted: 9  ✗ Skipped: 2  ⚠ Duplicates: 1         ║
║  Backups: ./manuscript/.backups/2024-01-27T103000/              ║
╚══════════════════════════════════════════════════════════════════╝
```

### Status Codes

| Status | Meaning |
|--------|---------|
| `✓ AUTO` | Confidence ≥95%, auto-inserted |
| `✓ PICKED` | User picked from options (50-95%) |
| `✓ MANUAL` | User specified location manually (<50%) |
| `✗ SKIP` | User chose to skip |
| `⚠ DUP` | Duplicate detected, skipped |
| `⚠ ERROR` | File write failed |

---

## Command Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview without writing |
| `--clipboard` | Read from system clipboard |
| `--accept` | Remove INSERT markers (accept all in path) |
| `--accept-file FILE` | Accept inserts in specific file |
| `--undo` | Restore from last backup |
| `--as-child` | Force insert as child node (codex only) |
| `--as-text` | Force insert into body text |
| `--depth N` | Limit folder scan depth |
| `--delimiter STR` | Custom note delimiter for batch |
| `--no-backup` | Skip backup creation |

---

## Additional Features

### Accept/Cleanup Command

Remove INSERT markers after review:

```bash
/insert --accept chapter-23.codex.yaml     # Accept all in file
/insert --accept ./manuscript/              # Accept all in folder
```

### Undo/Rollback

```bash
/insert --undo chapter-23.codex.yaml       # Restore last backup
```

Backups auto-created at: `{folder}/.backups/{timestamp}/`

### Dry Run

```bash
/insert --dry-run notes.txt into ./manuscript/
```

Shows full summary report without writing files.

### Interactive Mode

```
> /insert
Starting interactive insert mode for: ./manuscript/
Paste note (end with '---done---'):

> [user pastes note]
> ---done---

Finding location... Found: chapter-23.codex.yaml, line 847 (91%)
Insert here? [Y/n/options]:

> y
✓ Inserted. Next note (or 'exit'):
```

---

## Edge Cases & Policies

### Content Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Same phrase, multiple locations** | All become candidates; use surrounding instruction context to disambiguate; ask user to pick if still ambiguous |
| **Very long note (10k+ words)** | Warn user; still insert; recommend `--as-child` for proper node structure |
| **Whitespace-only note** | Reject with message: "Note is empty. Skipping." |
| **Instruction-only, no content** | Warn: "No content found, only instruction. Did you mean to include content?" |
| **Note contains `---` delimiter** | Only split on `---` at start of line preceded by blank line; or user can specify `--delimiter` |
| **Note contains `<!-- -->`** | Use unique marker: `<!-- INSERT` / `<!-- /INSERT -->` to avoid collision |
| **Note has YAML-breaking chars** | Python escapes properly when writing to body field |

### Matching Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Non-English content** | Text-based matching still works; fuzzy match handles accents |
| **Time references** ("after the 3-year skip") | Look for narrative markers, chapter summaries mentioning time |
| **Meta references** ("in the flashback") | Scan for `type: flashback` or "flashback" in body/titles |
| **Ambiguous pronouns** ("after she betrayed him") | Low confidence; ask user to clarify with character names |
| **Contradictory hints** ("chapter 3" but content references ch.5) | Flag conflict; ask user which takes priority |
| **Multiple target hints** ("chapter 3 or maybe 4") | Find matches in both; present as options |
| **Case sensitivity** | Case-insensitive matching for all searches |
| **Typos in instruction** | Fuzzy matching with Levenshtein distance tolerance |

### File System Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **No codex files found** | Clear error: "No codex files found in [path]. Check the path?" |
| **File is read-only** | Error: "Cannot write to [file] - read-only. Fix permissions?" |
| **File locked by editor** | Retry once; if still locked, error with suggestion |
| **Circular includes** | Detect cycle; warn; do not infinite loop |
| **Binary/corrupted file** | YAML parse fails; skip file with warning |
| **Symbolic links** | Follow symlinks by default; `--no-follow-symlinks` flag available |
| **Very deep nesting (10+ levels)** | Still works; insert at matched depth; warn if unusually deep |
| **Mixed file encodings** | Detect encoding; convert to UTF-8; warn if conversion is lossy |
| **Empty file (metadata only)** | Create `body:` field if inserting text; confidence 100% (only one place) |

### Batch Processing Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Large batch (500+ notes)** | Process in chunks of 20; show progress; allow cancel |
| **Duplicate notes in batch** | Detect via content hash; warn: "Note 7 is duplicate of Note 3. Skip?" |
| **All notes fail to match** | Summary shows all failures; suggest: "Try more specific instructions" |
| **Partial batch failure** | Complete successful ones; report failures; offer retry for failed |
| **Batch file encoding issues** | Auto-detect encoding; convert to UTF-8 |
| **Multiple notes same location** | Ask user for ordering; or insert in batch-file order |

### Insert Marker Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **File already has INSERT markers** | Treat as "pending review"; don't insert inside another INSERT block |
| **Many unaccepted inserts** | Warn: "File has N unaccepted inserts. Accept them first?" |
| **Nested INSERT blocks** | Prevent; error if attempting to insert inside existing marker |

---

## Target Resolution Priority

When no explicit path provided:

1. **Explicit path** (best practice): `/insert into chapter-5.codex.yaml`
2. **Hints from instruction**: "in chapter 5", "Elena's arc" → parsed and used
3. **Current/selected document context**
4. **Last referenced document**
5. **Last folder → project root** (coldest fallback)

---

## Python Script Architecture

### insert_engine.py

```python
class InsertEngine:
    def insert(self, filepath, content, location, markers=True):
        """Main entry point for insertions."""
        format = self.detect_format(filepath)

        if format == 'codex-yaml':
            return self._insert_yaml(filepath, content, location, markers)
        elif format == 'codex-lite':
            return self._insert_markdown(filepath, content, location, markers)
        elif format == 'codex-json':
            return self._insert_json(filepath, content, location, markers)

    def _insert_yaml(self, filepath, content, location, markers):
        """Insert into .codex.yaml using ruamel.yaml."""
        # Preserves formatting, comments, structure
        # Handles body field (pipe syntax) vs children array
        # Returns: success, line_number, before_context, after_context

    def _insert_markdown(self, filepath, content, location, markers):
        """Insert into .md Codex Lite files."""
        # Simpler text manipulation after frontmatter
        # Preserves frontmatter intact

    def accept_inserts(self, filepath):
        """Remove INSERT markers, leaving clean content."""

    def create_backup(self, filepath):
        """Create timestamped backup before modification."""
```

### location_finder.py

```python
class LocationFinder:
    def find_candidates(self, instruction, content_preview, target_path):
        """Orchestrates hierarchical agent search."""
        # Pass 1: Coarse scan with parallel agents
        # Pass 2: Deep scan on promising files
        # Returns ranked candidates with confidence scores

    def parse_instruction(self, note_text):
        """Separate instruction from content."""
        # Returns: (instruction, content)
```

### note_parser.py

```python
class NoteParser:
    def parse_batch(self, filepath, delimiter='---'):
        """Parse batch file into individual notes."""
        # Handles delimiter detection
        # Separates instruction from content per note
        # Returns: List[Note]

    def parse_single(self, text):
        """Parse single note text."""
        # Separates instruction from content
        # Returns: Note(instruction, content)
```

---

## Implementation Phases

### Phase 1: Core Engine
- [ ] Plugin structure and manifest
- [ ] Basic insert_engine.py (single file, explicit location)
- [ ] Insert marker generation
- [ ] Backup system

### Phase 2: Smart Matching
- [ ] location_finder.py with agent orchestration
- [ ] Hierarchical two-pass search
- [ ] Confidence scoring
- [ ] Candidate presentation UX

### Phase 3: Batch & UX
- [ ] note_parser.py for batch files
- [ ] Summary report generation
- [ ] Interactive mode
- [ ] Clipboard support

### Phase 4: Polish
- [ ] Accept/cleanup command
- [ ] Undo functionality
- [ ] Edge case handling
- [ ] Documentation

---

## Open Questions

1. **Confidence thresholds** - Are 95% (auto) and 50% (show options) the right cutoffs?
2. **Max agents** - Is 10 parallel agents the right cap?
3. **Backup retention** - How long to keep backups? Auto-cleanup policy?

---

## Appendix: Skill Triggers

```yaml
triggers:
  - insert into codex
  - insert note
  - add to manuscript
  - insert scene
  - batch insert
  - chapterwise insert
```
