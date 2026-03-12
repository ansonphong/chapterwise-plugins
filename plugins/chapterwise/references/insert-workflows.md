# Insert Command — Secondary Workflows

## Accept Workflow

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
   Accepted 3 inserts in chapter-05.codex.yaml
   Backup: .backups/chapter-05_20240115_103000.codex.yaml
   ```

## Undo Workflow

When user runs `/insert --undo [file]`:

1. **Find backups:**
   ```bash
   ls -la <file_directory>/.backups/ | grep <filename_stem>
   ```

2. **Display available backups** with timestamps and let user choose.

3. **Restore selected backup:**
   ```bash
   cp <backup_path> <original_path>
   ```

## Summary Report Template

After batch operations, display a summary:

```
INSERT SUMMARY REPORT
Batch: notes.txt  |  Target: ./manuscript/  |  Total: 12

 #  | STATUS   | CONF | FILE                    | LINE | MATCHED
----+----------+------+-------------------------+------+----------
 1  | AUTO     |  97% | chapter-23.codex.yaml   |  847 | "...retreated beyond"
 2  | USER     |  73% | chapter-05.codex.yaml   |  234 | "...first light of"
 3  | SKIP     |  42% | -                       |    - | User skipped

Inserted: 3  |  Pending: 1  |  Skipped: 1
Backups saved to: ./manuscript/.backups/
Run `/insert --accept` to finalize pending inserts.
```

## Supported Formats

| Format | Extension | Detection | Body Location |
|--------|-----------|-----------|---------------|
| Codex YAML | `.codex.yaml`, `.codex.yml` | `type:` field | `body:` field (pipe syntax) |
| Codex Lite | `.md` with frontmatter | `---` at start | After frontmatter |
| Plain Markdown | `.md` without frontmatter | No `---` | Entire file |
