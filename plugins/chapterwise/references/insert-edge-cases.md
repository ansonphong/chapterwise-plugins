# Insert Command — Edge Cases & Policies

## Content Edge Cases

| Scenario | Policy |
|----------|--------|
| Empty content | Skip with warning: "Note #3 has empty content, skipping" |
| Content > 10KB | Warn but proceed: "Large content (15KB) - consider splitting" |
| Binary/non-text | Reject: "Cannot insert binary content" |
| Contains INSERT markers | Escape existing markers to prevent nesting |
| Markdown in YAML body | Preserve as-is (YAML pipe syntax handles it) |
| Code blocks | Preserve formatting, indent appropriately for YAML |

## Matching Edge Cases

| Scenario | Policy |
|----------|--------|
| No instruction provided | Ask user: "Where should this be inserted?" |
| Instruction too vague | Request clarification: "'after the scene' - which scene?" |
| Multiple equal matches | Present all options to user |
| No matches found | Offer manual location input |
| File not found | List available files, let user choose |
| Chapter reference ambiguous | "Chapter 5" could be chapter-05.codex.yaml or chapter-5.md - ask |

## File System Edge Cases

| Scenario | Policy |
|----------|--------|
| File locked/read-only | Error: "Cannot write to file - check permissions" |
| Disk full | Error before write, preserve original |
| Backup directory missing | Create `.backups/` automatically |
| Path contains spaces | Handle with proper quoting |
| Symlinks | Follow symlinks, backup the actual file |
| Very large file (>1MB) | Warn, proceed with streaming approach |

## Batch Edge Cases

| Scenario | Policy |
|----------|--------|
| Empty batch file | "No notes found in batch file" |
| Invalid delimiter | Fall back to default `---` with warning |
| Mixed success/failure | Complete all possible, report failures |
| Duplicate instructions | Process each separately (may insert same location) |
| Circular references | Detect and warn (rare edge case) |

## Marker Edge Cases

| Scenario | Policy |
|----------|--------|
| Nested INSERT markers | Escape inner markers: `<!-- INSERT` → `<!-- [INSERT]` |
| Malformed existing markers | Attempt repair, warn user |
| Very old markers (>30 days) | Flag for review during accept |
| Markers in code blocks | Skip (they're likely examples) |
| Partial marker (unclosed) | Warn and skip |
