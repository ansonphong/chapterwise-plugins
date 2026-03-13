---
description: "Insert notes into Codex manuscripts by location"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent, AskUserQuestion
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

**Pre-flight check:** Before proceeding, verify that `${CLAUDE_PLUGIN_ROOT}` resolves to a
valid path containing the `scripts/` directory. If not, report an error:
"Cannot find ChapterWise plugin scripts. Is the plugin installed correctly?"

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

Use a two-pass search with Agent for accurate location finding.

#### Pass 1: Coarse Scan (Dispatch Agent)

Spawn an Agent to identify promising files:

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

For each promising file, spawn an Agent to find exact location:

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

See `${CLAUDE_PLUGIN_ROOT}/references/insert-marker-format.md` for INSERT marker HTML comment spec.

### Step 7: Summary Report

After batch operations, display a summary table with status, confidence, file, line, and matched text for each insert. See `${CLAUDE_PLUGIN_ROOT}/references/insert-workflows.md` for the full template.

---

## ADDITIONAL RESOURCES

For edge cases, secondary workflows, and format specs, consult:
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-edge-cases.md`** — All edge case tables and policies
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-workflows.md`** — Accept, Undo, Summary Report workflows
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-marker-format.md`** — INSERT marker HTML comment spec

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

---

## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start | Scanning | "Scanning manuscript for insert location..." |
| Processing | Folding | "Folding note into {file} at line {N}..." |
| Completion | Done | "Done. {N} notes inserted, {M} pending review." |
