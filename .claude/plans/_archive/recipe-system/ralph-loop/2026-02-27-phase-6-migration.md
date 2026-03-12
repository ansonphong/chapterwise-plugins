# Phase 6: Migration + Stubs — Tasks 33-35

> **Reference:** `01-PLUGIN-STRUCTURE.md` (Migration section), `build-plans/PHASE-2-4-INTEGRATION.md` (Phase 3: Migration)

This phase deprecates the old plugin directories. The old plugins (`chapterwise-codex`, `chapterwise-analysis`) still exist but their commands redirect users to the unified `chapterwise` plugin.

---

## Task 33: Create deprecation stubs for `chapterwise-codex`

**Files:**
- Modify: `plugins/chapterwise-codex/.claude-plugin/plugin.json`
- Modify: All `plugins/chapterwise-codex/commands/*.md` files

### Step 33.1: Update plugin.json

Add deprecation notice:

```json
{
  "name": "chapterwise-codex",
  "description": "DEPRECATED — All commands have moved to the unified 'chapterwise' plugin. Enable chapterwise instead.",
  "version": "1.99.0",
  "deprecated": true,
  "successor": "chapterwise"
}
```

### Step 33.2: Stub all command files

For each `.md` file in `chapterwise-codex/commands/`, replace the content with a redirect stub:

```markdown
---
description: "[original description] (MOVED to chapterwise plugin)"
triggers:
  - chapterwise-codex:[original-trigger-name]
---

This command has moved to the unified **chapterwise** plugin.

To use it:
1. Enable the `chapterwise` plugin (it includes all codex commands)
2. Disable the `chapterwise-codex` plugin to avoid conflicts

The command works the same way — just from the new plugin.
```

**Important:** Deprecated stubs use only their namespaced triggers (e.g., `chapterwise-codex:format`) to avoid collisions with the unified plugin's plain triggers. If a user invokes `/chapterwise-codex:format`, they get the redirect message. If they invoke `/format`, it routes to the unified plugin.

Commands to stub: `format.md`, `explode.md`, `implode.md`, `convert-to-codex.md`, `convert-to-markdown.md`, `lite.md`, `generate-tags.md`, `update-word-count.md`, `diagram.md`, `spreadsheet.md`, `format-folder.md`, `format-regen-ids.md`

**Do NOT stub `import.md` or `import-scrivener.md`** — these are already superseded by the unified plugin's recipe versions.

### Step 33.3: Verify

```bash
grep -q "deprecated" plugins/chapterwise-codex/.claude-plugin/plugin.json && \
grep -q "moved\|MOVED\|chapterwise plugin" plugins/chapterwise-codex/commands/format.md && \
grep -q "chapterwise-codex:format" plugins/chapterwise-codex/commands/format.md && \
! grep -q "^  - format$" plugins/chapterwise-codex/commands/format.md && echo PASS
```

---

## Task 34: Create deprecation stub for `chapterwise-analysis`

**Files:**
- Modify: `plugins/chapterwise-analysis/.claude-plugin/plugin.json`
- Modify: `plugins/chapterwise-analysis/commands/analysis.md`

### Step 34.1: Update plugin.json

```json
{
  "name": "chapterwise-analysis",
  "description": "DEPRECATED — Analysis has moved to the unified 'chapterwise' plugin with recipe integration, courses, and genre-aware selection.",
  "version": "1.99.0",
  "deprecated": true,
  "successor": "chapterwise"
}
```

### Step 34.2: Stub analysis.md

```markdown
---
description: "Run AI analysis on Codex files (MOVED to chapterwise plugin)"
triggers:
  - chapterwise-analysis:analysis
---

This command has moved to the unified **chapterwise** plugin with new features:
- **Course system**: Quick taste, Slow roast, Spice rack, Simmering
- **Genre-aware selection**: Automatic module recommendations
- **Recipe integration**: Saves analysis state for re-runs

To use it:
1. Enable the `chapterwise` plugin
2. Disable the `chapterwise-analysis` plugin to avoid conflicts
3. Run `/analysis` — all existing commands work the same way
```

### Step 34.3: Verify

```bash
grep -q "deprecated" plugins/chapterwise-analysis/.claude-plugin/plugin.json && \
grep -q "moved\|MOVED\|chapterwise plugin" plugins/chapterwise-analysis/commands/analysis.md && \
grep -q "chapterwise-analysis:analysis" plugins/chapterwise-analysis/commands/analysis.md && \
! grep -q "^  - analysis$" plugins/chapterwise-analysis/commands/analysis.md && echo PASS
```

---

## Task 35: Verify unified plugin's import.md is the recipe version

**Files:**
- Verify: `plugins/chapterwise/commands/import.md` (should be the Phase 2 recipe version)

### Step 35.1: Check that import.md contains recipe system features

The Phase 2 task wrote the recipe-based import.md. Verify it has recipe system concepts and is NOT the old folder wizard.

```bash
# Must have recipe system features
grep -q "recipe\|Recipe\|pattern\|Pattern\|chapter_detector\|codex_writer\|structure_analyzer" plugins/chapterwise/commands/import.md && echo "HAS RECIPE FEATURES"

# Must have proper triggers
grep -q "triggers:" plugins/chapterwise/commands/import.md && echo "HAS TRIGGERS"

# Must NOT have the old wizard language
! grep -qi "folder wizard\|folder mode\|batch mode" plugins/chapterwise/commands/import.md && echo "NO OLD WIZARD"

echo PASS
```

### Step 35.2: If old version found, flag for manual review

If the import.md is the old version (from the original chapterwise plugin), it should have been overwritten in Phase 2 Task 16. If not, re-run Task 16.

---

## Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise-codex/.claude-plugin/plugin.json plugins/chapterwise-codex/commands/ plugins/chapterwise-analysis/.claude-plugin/plugin.json plugins/chapterwise-analysis/commands/
git commit -m "chore: deprecate chapterwise-codex and chapterwise-analysis plugins

Both plugins now redirect to the unified chapterwise plugin (v2.0.0).
Old commands still match triggers but display migration instructions.
- chapterwise-codex: 12 command stubs
- chapterwise-analysis: 1 command stub"
```
