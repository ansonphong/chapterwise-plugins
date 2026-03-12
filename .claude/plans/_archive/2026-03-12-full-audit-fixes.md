# Full Audit Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 19 issues identified in the comprehensive project audit — broken tests, missing scripts, stale docs, git hygiene, inconsistent conventions, and missing error handling across commands.

**Architecture:** Grouped into 10 tasks ordered by dependency: git hygiene first (unblocks clean commits), then critical script/test fixes, then documentation, then convention alignment across all commands. Each task is independently committable.

**Tech Stack:** Python 3, pytest, Claude Code plugin conventions (YAML frontmatter + markdown commands)

---

### Task 1: Git Hygiene — .DS_Store and .gitignore

Fixes audit issue **#6**.

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore**

Add these lines to `.gitignore`:

```
__pycache__/
.DS_Store
**/.DS_Store
```

**Step 2: Remove tracked .DS_Store files**

Run: `git rm --cached .DS_Store .claude/.DS_Store`

**Step 3: Verify**

Run: `git status`
Expected: Both `.DS_Store` files show as deleted (from tracking). `.gitignore` shows as modified.

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore .DS_Store files and remove from tracking"
```

---

### Task 2: Fix Broken Tests — Wrong Import Path

Fixes audit issue **#1**.

**Files:**
- Modify: `tests/test_schema_validator.py:8`
- Modify: `tests/test_schema_examples.py:11`

**Step 1: Fix import path in test_schema_validator.py**

Change line 8 from:
```python
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise-codex' / 'scripts'))
```
To:
```python
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise' / 'scripts'))
```

**Step 2: Fix import path in test_schema_examples.py**

Change line 11 from:
```python
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise-codex' / 'scripts'))
```
To:
```python
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise' / 'scripts'))
```

**Step 3: Run tests to verify they pass**

Run: `python3 -m pytest tests/ -v`

Note: `test_schema_validator.py` requires the `jsonschema` package. If not installed, install with `pip3 install jsonschema`. Tests should now at least import successfully. Some tests may still fail if schemas or validators have drifted — that's OK, we just need the imports to work. Fix any remaining test failures.

**Step 4: Commit**

```bash
git add tests/test_schema_validator.py tests/test_schema_examples.py
git commit -m "fix: correct import path in tests (chapterwise-codex → chapterwise)"
```

---

### Task 3: Fix Root plugin.json — Wrong Name and Stale Metadata

Fixes audit issue **#7**. There are TWO plugin.json files — the root `.claude-plugin/plugin.json` is stale; the inner `plugins/chapterwise/.claude-plugin/plugin.json` is correct.

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Update root plugin.json**

Replace the entire contents of `.claude-plugin/plugin.json` with:

```json
{
  "name": "chapterwise",
  "description": "Complete writing toolkit for ChapterWise — import any manuscript, run AI analysis, build story atlases, generate research, create custom readers. Supports PDF, DOCX, Scrivener, Ulysses, Markdown, and more.",
  "version": "2.0.0",
  "author": {
    "name": "Anson Phong"
  },
  "homepage": "https://chapterwise.app",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

**Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "fix: update root plugin.json — correct name, description, author, URLs"
```

---

### Task 4: Fix CLAUDE.md Module Count and codex-format.md Relations Field

Fixes audit issues **#17** and **#19**.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/rules/codex-format.md`

**Step 1: Fix module count in CLAUDE.md**

There are 32 analysis modules (not 31). Change the architecture diagram line from:

```
├── modules/                     # 31 analysis modules
```
To:
```
├── modules/                     # 32 analysis modules
```

**Step 2: Fix relations field in codex-format.md**

Change line 18 from:
```json
  "relations": [{ "target": "other-id", "type": "references" }]
```
To:
```json
  "relations": [{ "targetId": "other-id", "kind": "references" }]
```

This matches the actual format used in `format.md` and `atlas-section-schemas.md`.

**Step 3: Commit**

```bash
git add CLAUDE.md .claude/rules/codex-format.md
git commit -m "fix: correct module count (32) and relations field (targetId/kind)"
```

---

### Task 5: Rewrite README.md

Fixes audit issue **#8**.

**Files:**
- Modify: `README.md`

**Step 1: Rewrite README.md**

Replace the entire README with an accurate description of the current project. Content should include:

- Project name: **ChapterWise Claude Plugin**
- One-line description matching plugin.json
- Installation: `claude plugin add --source github ansonphong/chapterwise-claude-plugins`
- Commands table listing ALL 23 commands with their triggers and one-line descriptions. Read each command file's YAML frontmatter `description` field to get the accurate description. Group commands by category:
  - **Core Pipeline:** `/import`, `/analysis`, `/atlas`, `/reader`, `/research`, `/research:deep`
  - **Manuscript Tools:** `/insert`, `/status`, `/pipeline`, `/index`
  - **Format Tools:** `/format`, `/explode`, `/implode`, `/markdown`, `/convert-to-codex`, `/convert-to-markdown`
  - **Utilities:** `/generate-tags`, `/update-word-count`, `/format-folder`, `/format-regen-ids`, `/diagram`, `/spreadsheet`
  - **Specialized:** `/import-scrivener`
- Codex Format overview (keep existing, it's accurate)
- Requirements: Python 3.8+, PyYAML
- Links: chapterwise.app, correct GitHub repo
- License: MIT

Do NOT include old paths like `skills/format/auto_fixer.py`. All scripts are at `plugins/chapterwise/scripts/`.

**Step 2: Verify no stale references**

Run: `grep -n 'chapterwise-codex' README.md`
Expected: No matches. If any remain, fix them.

Run: `grep -n 'skills/' README.md`
Expected: No matches referring to the old `skills/` path structure.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README to reflect current plugin architecture"
```

---

### Task 6: Fix Script Interface Inconsistencies

Fixes audit issues **#4** and **#5**. Rather than refactoring the scripts (which would break `analysis.md` and other commands that call them), update the rules and README to document the actual mixed interface pattern.

**Files:**
- Modify: `.claude/rules/scripts.md`

**Step 1: Update scripts.md to document actual conventions**

Replace the content of `.claude/rules/scripts.md` with:

```markdown
# Rules: Writing Scripts

Applies when creating or modifying files in `plugins/chapterwise/scripts/`.

## Conventions

- All scripts output JSON to stdout
- Error output goes to stderr, never stdout (stdout is for data only)
- Scripts must work without external dependencies beyond Python stdlib + PyYAML
- Include a `if __name__ == "__main__":` block
- Exit code 0 on success, non-zero on failure
- Follow existing script patterns — check `analysis_writer.py` or `module_loader.py` for reference

## Input Conventions

Scripts use one of two input patterns:

### Pattern A: stdin JSON (preferred for new scripts)

```bash
echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py [action]
```

Used by: `recipe_manager.py`, `module_loader.py`, `codex_validator.py`, `format_detector.py`

### Pattern B: Positional arguments + optional stdin

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py SOURCE_FILE MODULE_NAME
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py SOURCE_FILE MODULE_NAME - < data.json
```

Used by: `staleness_checker.py`, `analysis_writer.py`, `explode_codex.py`, `implode_codex.py`

**New scripts should use Pattern A.** Existing Pattern B scripts are stable and should not be refactored unless there's a functional reason.
```

**Step 2: Commit**

```bash
git add .claude/rules/scripts.md
git commit -m "docs: document actual script input conventions (stdin JSON + positional args)"
```

---

### Task 7: Add Missing recipe_manager.py Subcommands

Fixes audit issues **#2** and **#15**. The `atlas.md` command calls `scan`, `save`, and `patch` on `recipe_manager.py`, but only `create`, `load`, `list`, `validate`, `update` exist.

**Files:**
- Modify: `plugins/chapterwise/scripts/recipe_manager.py`

**Step 1: Add `scan` subcommand**

Add after the `list_recipes` function (line 97):

```python
def scan(data):
    """Scan a project directory for codex files and metadata."""
    project = data["project_path"]

    codex_files = []
    for root, dirs, files in os.walk(project):
        # Skip .chapterwise and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith('.codex.yaml') or f.endswith('.codex.md'):
                codex_files.append(os.path.relpath(os.path.join(root, f), project))

    # Try to read index for metadata
    index_path = os.path.join(project, 'index.codex.yaml')
    index_data = {}
    if os.path.isfile(index_path):
        with open(index_path) as fh:
            index_data = yaml.safe_load(fh) or {}

    return {
        "project_path": project,
        "codex_files": sorted(codex_files),
        "file_count": len(codex_files),
        "index_found": os.path.isfile(index_path),
        "title": index_data.get("name", index_data.get("title")),
        "type": index_data.get("type"),
    }
```

**Step 2: Add `save` subcommand**

Add after the `scan` function:

```python
def save(data):
    """Save a full recipe with all metadata (used by atlas after build)."""
    project = data.get("project_path", ".")
    rtype = data["type"]
    atlas_data = data.get("atlas", {})
    name = atlas_data.get("name") or data.get("name")

    folder_name = f"{rtype}-recipe"
    if name and rtype == "atlas":
        slug = atlas_data.get("slug", name.lower().replace(" ", "-"))
        if slug != "atlas":
            folder_name = f"atlas-recipe-{slug}"

    recipe_dir = os.path.join(project, ".chapterwise", folder_name)
    os.makedirs(recipe_dir, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    # Build recipe from all provided data
    recipe = {
        "type": rtype,
        "version": "1.0",
        "created": now,
        "updated": now,
    }

    # Merge all extra fields from data (chapter_hashes, entity_map, passes, structure, etc.)
    for key in data:
        if key not in ("project_path", "type", "name"):
            recipe[key] = data[key]

    recipe_path = os.path.join(recipe_dir, "recipe.yaml")
    with open(recipe_path, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"success": True, "recipe_path": recipe_path, "folder": recipe_dir}
```

**Step 3: Add `patch` subcommand**

Add after the `save` function:

```python
def patch(data):
    """Patch specific fields in a recipe without replacing the whole file.
    Similar to update but designed for incremental atlas updates —
    appends to arrays (like update history) rather than replacing them."""
    project = data.get("project_path", ".")
    rtype = data.get("type", "atlas")
    patch_data = data.get("patch", {})

    # Find the recipe
    name = data.get("name")
    folder_name = f"{rtype}-recipe"
    if name and rtype == "atlas":
        folder_name = f"atlas-recipe-{name}"

    recipe_path = os.path.join(project, ".chapterwise", folder_name, "recipe.yaml")
    if not os.path.isfile(recipe_path):
        return {"success": False, "error": "recipe.yaml not found"}

    with open(recipe_path) as f:
        recipe = yaml.safe_load(f)

    # Apply patches
    for key, value in patch_data.items():
        if key == "update_entry":
            # Append to updates array
            if "updates" not in recipe:
                recipe["updates"] = []
            recipe["updates"].append(value)
        elif key == "chapter_hashes":
            # Replace chapter hashes wholesale
            recipe["chapter_hashes"] = value
        else:
            # Deep merge for other keys
            if isinstance(value, dict) and isinstance(recipe.get(key), dict):
                recipe[key].update(value)
            else:
                recipe[key] = value

    recipe["updated"] = datetime.now(timezone.utc).isoformat()

    with open(recipe_path, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"success": True, "recipe_path": recipe_path}
```

**Step 4: Register all three new commands in the dispatch table**

Update the `commands` dict at the bottom of the file (around line 164) to include:

```python
    commands = {
        "create": create,
        "load": load,
        "list": list_recipes,
        "validate": validate,
        "update": update,
        "scan": scan,
        "save": save,
        "patch": patch,
    }
```

**Step 5: Run basic smoke test**

Run: `echo '{"project_path": "."}' | python3 plugins/chapterwise/scripts/recipe_manager.py scan`
Expected: JSON output with `codex_files`, `file_count`, etc.

Run: `echo '{"project_path": "."}' | python3 plugins/chapterwise/scripts/recipe_manager.py list`
Expected: JSON output (should still work as before).

**Step 6: Commit**

```bash
git add plugins/chapterwise/scripts/recipe_manager.py
git commit -m "feat: add scan, save, patch subcommands to recipe_manager.py"
```

---

### Task 8: Fix Missing Scripts Referenced by import.md

Fixes audit issue **#3**. The `import.md` command references `structure_analyzer.py` and `chapter_detector.py` which don't exist. These are thin wrappers — the actual logic lives in `patterns/common/structure_analyzer.py` and `patterns/common/chapter_detector.py`.

**Files:**
- Check: `plugins/chapterwise/patterns/common/structure_analyzer.py`
- Check: `plugins/chapterwise/patterns/common/chapter_detector.py`
- Possibly create: `plugins/chapterwise/scripts/structure_analyzer.py`
- Possibly create: `plugins/chapterwise/scripts/chapter_detector.py`

**Step 1: Check if the pattern files exist**

Run: `ls plugins/chapterwise/patterns/common/`

If `structure_analyzer.py` and `chapter_detector.py` exist in `patterns/common/`, create thin wrapper scripts in `scripts/` that import and delegate to the pattern versions, following the stdin JSON convention.

If they don't exist anywhere, the `import.md` command references are aspirational — the import command works because the agent reads the prompt and does the structure analysis itself (the scripts are called but the agent can fall through to doing it inline). In this case:

**Option A (if patterns exist):** Create stdin JSON wrappers in `scripts/`.

**Option B (if patterns don't exist):** Update `import.md` to remove the script references and document that the agent performs structure analysis and chapter detection inline. Replace lines 109 and 115 with comments indicating the agent handles these steps directly.

Check which option applies and execute accordingly.

**Step 2: Commit**

```bash
git add plugins/chapterwise/scripts/ plugins/chapterwise/commands/import.md
git commit -m "fix: resolve missing structure_analyzer.py and chapter_detector.py references"
```

---

### Task 9: Add principles.md Reference to All Major Commands

Fixes audit issue **#11**. Only `/research` and `/research:deep` reference `principles.md`. The 6 major commands that reference `language-rules.md` should also reference `principles.md`.

**Files:**
- Modify: `plugins/chapterwise/commands/analysis.md`
- Modify: `plugins/chapterwise/commands/atlas.md`
- Modify: `plugins/chapterwise/commands/import.md`
- Modify: `plugins/chapterwise/commands/reader.md`
- Modify: `plugins/chapterwise/commands/status.md`
- Modify: `plugins/chapterwise/commands/pipeline.md`

**Step 1: Add principles.md reference to each command**

In each of the 6 files listed above, find the line that references `language-rules.md`:

```
Read and follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md`
```

And add a line BEFORE it:

```
Read and follow `${CLAUDE_PLUGIN_ROOT}/references/principles.md` — especially **LLM Judgment, User Override**.
```

If the command has a different pattern for referencing language-rules.md (e.g., a "Language Rules" section header instead of inline), add the principles reference in the Overview or top-level section of the command, before any step-by-step instructions begin.

**Step 2: Verify**

Run: `grep -l 'principles.md' plugins/chapterwise/commands/*.md | wc -l`
Expected: 8 (the 6 major commands + research + research-deep)

**Step 3: Commit**

```bash
git add plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/import.md plugins/chapterwise/commands/reader.md plugins/chapterwise/commands/status.md plugins/chapterwise/commands/pipeline.md
git commit -m "chore: add principles.md reference to all major commands"
```

---

### Task 10: Add Error Handling and Language Rules to Utility Commands

Fixes audit issues **#9** and **#10**. These 13 commands are missing Error Handling and/or Language Rules sections:

Commands missing **both** Error Handling and Language Rules:
- `convert-to-codex.md`
- `convert-to-markdown.md`
- `diagram.md`
- `explode.md`
- `format-folder.md`
- `format-regen-ids.md`
- `format.md`
- `generate-tags.md`
- `implode.md`
- `import-scrivener.md`
- `index.md`
- `spreadsheet.md`
- `update-word-count.md`

Commands missing **only** Language Rules:
- `insert.md` (has Error Handling but no Language Rules table)
- `markdown.md` (has neither section header)

**Step 1: Read each command file**

For each command listed above, read the file to understand what it does, what can go wrong, and what progress phases it has.

**Step 2: Add Error Handling section**

For each command missing an Error Handling section, add one at the end of the file (before any closing notes). Use a table format:

```markdown
## Error Handling

| Situation | Response |
|-----------|----------|
| File not found | "File not found: {path}" |
| Invalid codex format | "Not a valid Codex file: {path}. Run /format first." |
| ... | ... |
```

Tailor the errors to each command's specific failure modes. Common patterns:
- File not found
- Invalid input format
- No codex files in directory
- Write permission errors
- Missing dependencies (PyYAML)

**Step 3: Add Language Rules section**

For each command missing a Language Rules section, add one. Use the table format:

```markdown
## Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start | Scanning | "Scanning {filename}..." |
| Processing | Formatting | "Formatting 12 nodes..." |
| Completion | Done | "Done. {filename} updated." |
```

Tailor the phases and verbs to each command. Use cooking-adjacent verbs where natural (scanning, slicing, folding, assembling). For simple utility commands, 2-3 phases is sufficient.

**Step 4: Commit in batches**

Commit utility commands in groups to keep commits focused:

```bash
# Format tools
git add plugins/chapterwise/commands/format.md plugins/chapterwise/commands/format-folder.md plugins/chapterwise/commands/format-regen-ids.md plugins/chapterwise/commands/explode.md plugins/chapterwise/commands/implode.md
git commit -m "chore: add Error Handling and Language Rules to format commands"

# Conversion tools
git add plugins/chapterwise/commands/convert-to-codex.md plugins/chapterwise/commands/convert-to-markdown.md plugins/chapterwise/commands/markdown.md
git commit -m "chore: add Error Handling and Language Rules to conversion commands"

# Utility tools
git add plugins/chapterwise/commands/generate-tags.md plugins/chapterwise/commands/update-word-count.md plugins/chapterwise/commands/index.md plugins/chapterwise/commands/diagram.md plugins/chapterwise/commands/spreadsheet.md plugins/chapterwise/commands/import-scrivener.md plugins/chapterwise/commands/insert.md
git commit -m "chore: add Error Handling and Language Rules to utility commands"
```

---

### Task 11: Add Research Schema

Fixes audit issue **#13**.

**Files:**
- Create: `schemas/research-v1.2.schema.json`

**Step 1: Create the research schema**

Model it after `schemas/analysis-v1.2.schema.json` but adapted for the research output format defined in `plugins/chapterwise/commands/research.md`. Read both the analysis schema and the research command data model section to produce an accurate schema.

Key differences from analysis schema:
- `type` must be `"research"` (not `"analysis"`)
- Has `credits` object with `models` array and `webSources` array
- Attributes include `topic`, `depth`, `sources`, `context`
- Children use `research-section` and `research-entry` types

**Step 2: Update codex-format.md rule**

Add `research-v1.2.schema.json` to the validation section:

```markdown
- Schema files live in `schemas/` (codex-v1.2.schema.json, analysis-v1.2.schema.json, research-v1.2.schema.json)
```

**Step 3: Commit**

```bash
git add schemas/research-v1.2.schema.json .claude/rules/codex-format.md
git commit -m "feat: add research-v1.2 schema for /research output validation"
```

---

### Task 12: Document Schema Resolution Path

Fixes audit issue **#12**.

**Files:**
- Modify: `.claude/rules/codex-format.md`

**Step 1: Add schema resolution documentation**

Add to the Validation section of `codex-format.md`:

```markdown
## Schema Resolution

Schema files are at the **repository root** in `schemas/`:

```
schemas/
├── codex-v1.2.schema.json
├── analysis-v1.2.schema.json
└── research-v1.2.schema.json
```

The `schema_validator.py` script resolves schemas relative to itself:
`Path(__file__).parent.parent.parent.parent / 'schemas'`
(from `plugins/chapterwise/scripts/` → repo root → `schemas/`)

When invoking validation from commands, use:
```bash
echo '{"path": "./output/", "fix": true}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_validator.py
```

The validator finds schemas automatically — no path argument needed.
```

**Step 2: Commit**

```bash
git add .claude/rules/codex-format.md
git commit -m "docs: document schema file resolution path"
```

---

### Task 13: Final Push and Verify

**Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v`

All tests should pass. If any fail, fix them before pushing.

**Step 2: Verify no stale references remain**

Run: `grep -r 'chapterwise-codex' --include='*.py' --include='*.md' --include='*.json' . | grep -v '.git/' | grep -v '_archive/'`

Expected: No matches outside of archived plans. If any remain, fix them.

**Step 3: Push all commits**

Run: `git push`

**Step 4: Final status check**

Run: `git log --oneline -15`

Verify all commits are clean and descriptive.
