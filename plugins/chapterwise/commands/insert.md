---
description: "Insert notes into Codex manuscripts by location"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Task, AskUserQuestion
triggers:
  - insert into codex
  - insert note
  - add to manuscript
  - insert scene
  - batch insert
  - chapterwise insert
argument-hint: "[instruction or --batch notes.txt]"
---

# Chapterwise Insert

Intelligently insert notes, scenes, and content into Chapterwise Codex manuscripts. Uses semantic understanding to find the right location based on natural language instructions like "after the hyperborean incursion" or "when Elena first meets Marcus."

## When to Apply

Apply this command when the user asks to:
- Insert content into a codex file or manuscript
- Add notes to specific locations in their writing
- Process a notes file with multiple batch insertions
- Accept or undo pending inserts

## Invocation Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| **Single** | `/insert [instruction]` | Insert one note with location instruction |
| **Batch** | `/insert --batch notes.txt` | Process multiple notes from a file |
| **Interactive** | `/insert --interactive` | Step through each note with confirmation |
| **Clipboard** | `/insert --clipboard` | Read notes from system clipboard |
| **Dry-Run** | `/insert --dry-run` | Preview without making changes |
| **Accept** | `/insert --accept [file]` | Accept pending INSERT markers |
| **Undo** | `/insert --undo [file]` | Restore from backup |

## Command Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--batch <file>` | `-b` | Process notes from file (one per `---` delimiter) |
| `--target <dir>` | `-t` | Target directory to scan for codex files |
| `--dry-run` | `-d` | Show what would happen without making changes |
| `--accept` | `-a` | Accept all pending INSERT markers in file |
| `--accept-all` | | Accept all pending inserts in target directory |
| `--undo` | `-u` | Restore file from most recent backup |
| `--clipboard` | `-c` | Read notes from system clipboard |
| `--interactive` | `-i` | Confirm each insert before executing |
| `--no-backup` | | Skip backup creation (dangerous) |
| `--delimiter <str>` | | Custom delimiter for batch notes (default: `---`) |
| `--confidence <n>` | | Minimum confidence threshold (default: 50) |

---

## WORKFLOW

Follow these steps in order for every insert operation.

### Step 1: Parse the Request

Determine the mode of operation:

1. **Check for flags** in the user's command
2. **Detect mode:**
   - Has `--batch` or `-b` → Batch mode
   - Has `--accept` or `-a` → Accept workflow
   - Has `--undo` or `-u` → Undo workflow
   - Has `--clipboard` or `-c` → Read from clipboard
   - Otherwise → Single insert mode

3. **Extract target directory:**
   - Explicit: `--target ./manuscript`
   - Implicit: Look for `./manuscript/`, `./chapters/`, or current directory
   - Ask if ambiguous

### Step 2: Parse Notes

Use the note parser to separate instructions from content.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/note_parser.py <notes_file> --json
```

For single notes:
```bash
echo "<note_text>" | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/note_parser.py --single --json
```

**Output structure:**
```json
[
  {
    "index": 1,
    "instruction": "after the hyperborean incursion",
    "content": "Elena drew her sword, the blade catching the firelight...",
    "raw": "after the hyperborean incursion\n\nElena drew her sword..."
  }
]
```

**Instruction detection:**
- First paragraph before double-newline is checked for location hints
- Keywords: "after", "before", "in chapter", "when", "where", "near", "during"
- If no instruction detected, the entire text is treated as content

### Step 3: Scan Target Directory

Find all codex files and create an index for searching.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/location_finder.py scan <directory> --json
```

For each file, extract index data:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/location_finder.py index <file> --json
```

**Index structure:**
```json
{
  "file_path": "/path/to/chapter-05.codex.yaml",
  "file_type": "codex-yaml",
  "title": "Chapter 5: The Incursion",
  "summary": "The hyperborean forces attack the northern border...",
  "body_preview": "Dawn broke over the frozen plains...",
  "child_names": ["Scene 1: The Warning", "Scene 2: The Attack"],
  "word_count": 4523
}
```

Extract location hints from instructions:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/location_finder.py hints "<instruction>" --json
```

### Step 4: Hierarchical Agent Search

Use a two-pass search with Task agents for accurate location finding.

#### Pass 1: Coarse Scan (Dispatch Agent)

Spawn a Task agent to identify promising files:

**Agent Prompt:**
```
Search these codex files for content related to this instruction:

INSTRUCTION: "[instruction]"
CONTENT PREVIEW: "[first 100 chars]"

FILES TO SEARCH:
[list of files with index data]

Return JSON: { "promising_files": [...], "reason": "..." }
```

The agent should:
1. Read the file index data
2. Match keywords from instruction to file summaries, titles, and child names
3. Return 1-3 most promising file paths
4. Provide reasoning for selections

#### Pass 2: Deep Scan (Search Agent)

For each promising file, spawn a Task agent to find exact location:

**Agent Prompt:**
```
Search this codex file for the best location to insert content.

FILE: [filepath]
INSTRUCTION: "[instruction]"

Return JSON: { "candidates": [{ "line": 247, "insert_after": "...", "confidence": 87, "reason": "..." }] }
```

The agent should:
1. Read the full file content
2. Search for semantic matches to the instruction
3. Return 1-3 candidate locations with:
   - `line`: Line number for insertion
   - `insert_after`: The text/context this comes after
   - `confidence`: 0-100 confidence score
   - `reason`: Why this location was chosen

### Step 5: Confidence-Based UX

React to confidence scores appropriately:

| Confidence | Action |
|------------|--------|
| **95-100%** | Auto-insert with brief notification |
| **50-94%** | Present options, let user choose or confirm |
| **<50%** | Ask user for clarification or manual location |

**For high confidence (95%+):**
```
Inserting at line 247 in chapter-05.codex.yaml (97% confidence)
  → After: "...the hyperborean forces retreated beyond the ridge."
```

**For medium confidence (50-94%):**
```
Found 2 possible locations for "after the hyperborean incursion":

1. [87%] chapter-05.codex.yaml:247
   After: "...the hyperborean forces retreated beyond the ridge."

2. [72%] chapter-03.codex.yaml:156
   After: "...first reports of hyperborean movement reached the capital."

Choose location (1/2) or specify manually:
```

**For low confidence (<50%):**
```
Could not find a confident match for "after the hyperborean incursion"

Hints found:
- Keyword: "hyperborean incursion"
- Position: "after"

Please specify the location:
- File path:
- Line number or context:
```

### Step 6: Execute Insert

Use the insert engine to perform the actual insertion.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/insert_engine.py insert <file> \
  --content "<content>" \
  --line <line_number> \
  --instruction "<instruction>" \
  --confidence <0.0-1.0> \
  --matched "<matched_text>" \
  --source "notepad" \
  --json
```

**Options:**
- `--after` (default): Insert after the specified line
- `--before`: Insert before the specified line
- `--no-backup`: Skip backup (not recommended)
- `--no-markers`: Insert without INSERT markers (for --accept mode)

**INSERT Marker Format:**
```html
<!-- INSERT
time: 2024-01-15T10:30:00Z
source: notepad
instruction: "after the hyperborean incursion"
confidence: 0.87
matched_after: "...the hyperborean forces retreated beyond the ridge."
-->
Elena drew her sword, the blade catching the firelight...
<!-- /INSERT -->
```

### Step 7: Summary Report

After batch operations, display a summary:

```
╔══════════════════════════════════════════════════════════════════╗
║                    INSERT SUMMARY REPORT                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Batch: notes.txt  │  Target: ./manuscript/  │  Total: 12       ║
╠══════════════════════════════════════════════════════════════════╣
  #  │ STATUS   │ CONF │ FILE                    │ LINE │ MATCHED
 ────┼──────────┼──────┼─────────────────────────┼──────┼──────────
  1  │ ✓ AUTO   │  97% │ chapter-23.codex.yaml   │  847 │ "...retreated beyond"
  2  │ ✓ USER   │  73% │ chapter-05.codex.yaml   │  234 │ "...first light of"
  3  │ ✓ AUTO   │  99% │ chapter-12.codex.yaml   │  156 │ "...Marcus turned to"
  4  │ ✗ SKIP   │  42% │ -                       │    - │ User skipped
  5  │ ? PEND   │  65% │ chapter-08.codex.yaml   │  445 │ "...the courtyard"
 ────┼──────────┼──────┼─────────────────────────┼──────┼──────────
  ✓ Inserted: 3  │  ? Pending: 1  │  ✗ Skipped: 1
╚══════════════════════════════════════════════════════════════════╝

Backups saved to: ./manuscript/.backups/
Run `/insert --accept` to finalize pending inserts.
```

---

## ACCEPT WORKFLOW

When user runs `/insert --accept [file]`:

1. **Find pending inserts:**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/insert_engine.py list <file> --json
   ```

2. **Display pending inserts:**
   ```
   Found 3 pending inserts in chapter-05.codex.yaml:

   1. Line 247 [87%] - "after the hyperborean incursion"
      Content: "Elena drew her sword..."

   2. Line 312 [92%] - "when Marcus arrives"
      Content: "The gates swung open..."

   3. Line 445 [65%] - "near the fountain scene"
      Content: "Water splashed against..."

   Accept all? (y/n) or specify indices (1,3):
   ```

3. **Accept selected inserts:**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/insert_engine.py accept <file> --indices 1 2 3 --json
   ```

4. **Confirm completion:**
   ```
   ✓ Accepted 3 inserts in chapter-05.codex.yaml
     Backup: .backups/chapter-05_20240115_103000.codex.yaml
   ```

---

## UNDO WORKFLOW

When user runs `/insert --undo [file]`:

1. **Find backups:**
   ```bash
   ls -la <file_directory>/.backups/ | grep <filename_stem>
   ```

2. **Display available backups:**
   ```
   Available backups for chapter-05.codex.yaml:

   1. chapter-05_20240115_103000.codex.yaml (2 minutes ago)
   2. chapter-05_20240115_100000.codex.yaml (32 minutes ago)
   3. chapter-05_20240114_180000.codex.yaml (yesterday)

   Restore which backup? (1/2/3):
   ```

3. **Restore selected backup:**
   ```bash
   cp <backup_path> <original_path>
   ```

4. **Confirm restoration:**
   ```
   ✓ Restored chapter-05.codex.yaml from backup
     Backup used: chapter-05_20240115_103000.codex.yaml
   ```

---

## EDGE CASES & POLICIES

### Content Edge Cases

| Scenario | Policy |
|----------|--------|
| Empty content | Skip with warning: "Note #3 has empty content, skipping" |
| Content > 10KB | Warn but proceed: "Large content (15KB) - consider splitting" |
| Binary/non-text | Reject: "Cannot insert binary content" |
| Contains INSERT markers | Escape existing markers to prevent nesting |
| Markdown in YAML body | Preserve as-is (YAML pipe syntax handles it) |
| Code blocks | Preserve formatting, indent appropriately for YAML |

### Matching Edge Cases

| Scenario | Policy |
|----------|--------|
| No instruction provided | Ask user: "Where should this be inserted?" |
| Instruction too vague | Request clarification: "'after the scene' - which scene?" |
| Multiple equal matches | Present all options to user |
| No matches found | Offer manual location input |
| File not found | List available files, let user choose |
| Chapter reference ambiguous | "Chapter 5" could be chapter-05.codex.yaml or chapter-5.md - ask |

### File System Edge Cases

| Scenario | Policy |
|----------|--------|
| File locked/read-only | Error: "Cannot write to file - check permissions" |
| Disk full | Error before write, preserve original |
| Backup directory missing | Create `.backups/` automatically |
| Path contains spaces | Handle with proper quoting |
| Symlinks | Follow symlinks, backup the actual file |
| Very large file (>1MB) | Warn, proceed with streaming approach |

### Batch Edge Cases

| Scenario | Policy |
|----------|--------|
| Empty batch file | "No notes found in batch file" |
| Invalid delimiter | Fall back to default `---` with warning |
| Mixed success/failure | Complete all possible, report failures |
| Duplicate instructions | Process each separately (may insert same location) |
| Circular references | Detect and warn (rare edge case) |

### Marker Edge Cases

| Scenario | Policy |
|----------|--------|
| Nested INSERT markers | Escape inner markers: `<!-- INSERT` → `<!-- [INSERT]` |
| Malformed existing markers | Attempt repair, warn user |
| Very old markers (>30 days) | Flag for review during accept |
| Markers in code blocks | Skip (they're likely examples) |
| Partial marker (unclosed) | Warn and skip |

---

## SUPPORTED FORMATS

| Format | Extension | Detection | Body Location |
|--------|-----------|-----------|---------------|
| Codex YAML | `.codex.yaml`, `.codex.yml` | `type:` field | `body:` field (pipe syntax) |
| Codex Lite | `.md` with frontmatter | `---` at start | After frontmatter |
| Plain Markdown | `.md` without frontmatter | No `---` | Entire file |

---

## QUICK REFERENCE

### Single Insert
```bash
# Insert with instruction
/insert after Elena meets Marcus for the first time

She paused, recognizing something familiar in his eyes...

# Insert into specific file
/insert --target chapter-05.codex.yaml --line 247

New content here...
```

### Batch Insert
```bash
# Process notes file
/insert --batch notes.txt --target ./manuscript/

# Dry run first
/insert --batch notes.txt --dry-run

# Interactive mode (confirm each)
/insert --batch notes.txt --interactive
```

### Accept/Undo
```bash
# Accept pending inserts
/insert --accept chapter-05.codex.yaml

# Accept all in directory
/insert --accept-all ./manuscript/

# Undo last change
/insert --undo chapter-05.codex.yaml
```

### From Clipboard
```bash
# Insert from clipboard
/insert --clipboard --target ./manuscript/
```

---

## REMEMBER

1. **Always create backups** unless explicitly told not to
2. **Use INSERT markers** so users can review before accepting
3. **Confidence-based UX** - auto-insert only when very confident
4. **Report clearly** - show what was done and where
5. **Handle errors gracefully** - never leave files in inconsistent state
6. **Respect user intent** - when in doubt, ask
