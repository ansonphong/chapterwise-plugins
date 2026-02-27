# Phase 0: Scaffold — Unified Plugin

**Agent:** Managing Agent (runs first, before recipe agents)
**Goal:** Create the unified `chapterwise` plugin with all existing functionality + shared infrastructure for recipe agents.

---

## Prerequisites

- Working directory: `/Users/phong/Projects/chapterwise-plugins/`
- Git repo is clean (commit any pending changes first)

## Step-by-Step

### Step 1: Create unified plugin directory

```
plugins/chapterwise/                  # Build directly in final location
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── modules/
├── patterns/
│   └── common/
├── scripts/
├── schemas/
└── templates/
```

**plugin.json:**
```json
{
  "name": "chapterwise",
  "description": "Complete writing toolkit for ChapterWise — import any manuscript, run AI analysis, build story atlases, create custom readers. Supports PDF, DOCX, Scrivener, Ulysses, Markdown, and more.",
  "version": "2.0.0",
  "homepage": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

### Step 2: Copy existing files

**From `chapterwise/`:**
```
commands/insert.md    → commands/insert.md
commands/import.md    → SKIP (will be rewritten by Import Agent)
```

**From `chapterwise-codex/`:**
```
commands/format.md              → commands/format.md
commands/format-folder.md       → commands/format-folder.md
commands/format-regen-ids.md    → commands/format-regen-ids.md
commands/explode.md             → commands/explode.md
commands/implode.md             → commands/implode.md
commands/convert-to-codex.md    → commands/convert-to-codex.md
commands/convert-to-markdown.md → commands/convert-to-markdown.md
commands/update-word-count.md   → commands/update-word-count.md
commands/generate-tags.md       → commands/generate-tags.md
commands/lite.md                → commands/lite.md
commands/diagram.md             → commands/diagram.md
commands/spreadsheet.md         → commands/spreadsheet.md
commands/index.md               → commands/index.md
commands/import.md              → SKIP (old folder import wizard, replaced)
commands/import-scrivener.md    → SKIP (will be rewritten by Import Agent)
scripts/*.py                    → scripts/*.py (all of them)
```

**From `chapterwise-analysis/`:**
```
commands/analysis.md   → SKIP (will be rewritten by Analysis Agent)
modules/*.md           → modules/*.md (all 31+ module files)
scripts/*.py           → scripts/*.py (module_loader, staleness_checker, analysis_writer)
```

### Step 3: Update `${CLAUDE_PLUGIN_ROOT}` references

After copying, grep all `.md` and `.py` files for plugin root references. Since all files now live under one plugin, internal references should work as-is. Verify:

```bash
grep -r "CLAUDE_PLUGIN_ROOT" plugins/chapterwise/
```

All references should resolve correctly within the unified structure.

### Step 4: Build shared recipe scripts

#### `scripts/recipe_manager.py`

```python
#!/usr/bin/env python3
"""
Recipe Manager — Create, load, validate, and discover recipe folders.

Usage:
  # Create a new recipe folder
  echo '{"project_path": "./my-novel", "type": "import"}' | python3 recipe_manager.py create

  # Load an existing recipe
  echo '{"project_path": "./my-novel", "type": "import"}' | python3 recipe_manager.py load

  # List all recipes in a project
  echo '{"project_path": "./my-novel"}' | python3 recipe_manager.py list

  # Validate a recipe
  echo '{"recipe_path": "./my-novel/.chapterwise/import-recipe"}' | python3 recipe_manager.py validate

All input via stdin JSON, all output via stdout JSON.
"""
```

**Functions:**
- `create` — Create `.chapterwise/{type}-recipe/` directory with empty `recipe.yaml`
- `load` — Read and parse `recipe.yaml` from existing recipe folder
- `list` — Scan `.chapterwise/*/recipe.yaml` and return all discovered recipes
- `validate` — Check recipe.yaml against schema, verify referenced files exist
- `update` — Update specific fields in recipe.yaml (used after re-import/update)

**Recipe folder naming:**
- Import: `.chapterwise/import-recipe/`
- Analysis: `.chapterwise/analysis-recipe/`
- Atlas (default): `.chapterwise/atlas-recipe/`
- Atlas (named): `.chapterwise/atlas-recipe-{name}/`
- Reader: `.chapterwise/reader-recipe/`

#### `scripts/format_detector.py`

```python
#!/usr/bin/env python3
"""
Format Detector — Detect manuscript source format.

Usage:
  echo '{"path": "/path/to/file.pdf"}' | python3 format_detector.py

Output:
  {"format": "pdf", "confidence": 0.99, "details": {"pages": 342, "size_bytes": 2450000}}
"""
```

**Detection logic:**
1. File extension mapping (`.pdf`, `.docx`, `.scriv`, `.ulyz`, `.md`, `.txt`, `.html`, `.htm`)
2. Magic bytes check for ambiguous cases (PDF header, ZIP for DOCX/EPUB)
3. Directory detection (Scrivener is a `.scriv` folder, Ulysses is a `.ulyz` folder)
4. Content sniffing fallback (is this markdown? HTML? plain text?)

**Supported formats:**
```python
FORMAT_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".scriv": "scrivener",
    ".ulyz": "ulysses",
    ".md": "markdown",
    ".txt": "plaintext",
    ".html": "html",
    ".htm": "html",
    ".rtf": "rtf",
    ".epub": "epub",
    ".fdx": "final_draft",
    ".fountain": "fountain",
    ".latex": "latex",
    ".tex": "latex",
}
```

Return `"unknown"` with details for unrecognized formats.

#### `scripts/run_recipe.py`

```python
#!/usr/bin/env python3
"""
Run Recipe — Execute a saved recipe's convert.py or run.sh.

Usage:
  echo '{"recipe_path": ".chapterwise/import-recipe", "source_path": "new-draft.pdf"}' | python3 run_recipe.py

Output:
  {"success": true, "output_path": "./my-novel/", "files_created": 31, "files_updated": 5}
"""
```

**Logic:**
1. Read `recipe.yaml` from recipe path
2. If `run.sh` exists and is executable: run it with source_path as arg
3. Else if `convert.py` exists: run it with source_path and output_dir
4. Capture stdout/stderr, report success/failure

#### `scripts/codex_validator.py`

```python
#!/usr/bin/env python3
"""
Codex Validator — Validate and auto-fix .codex.yaml and .md files.

Usage:
  echo '{"path": "./my-novel/", "fix": true}' | python3 codex_validator.py

Output:
  {"valid": true, "issues": [], "fixes_applied": ["Added missing word_count to chapter-03.md"]}
"""
```

**Validation checks:**
- All .md files have valid YAML frontmatter with `type` and `name` fields
- All .codex.yaml files parse as valid YAML
- UUIDs are present and unique across the project
- `index.codex.yaml` children reference files that exist on disk
- No files in directory are missing from index (orphans)
- Word counts are populated and non-zero

**Auto-fix actions (when `fix: true`):**
- Add missing `type` field (inferred from content or filename)
- Add missing `name` field (from first heading or filename)
- Regenerate invalid/missing UUIDs
- Recalculate word counts from content
- Add orphan files to index

#### `scripts/recipe_validator.py`

```python
#!/usr/bin/env python3
"""
Recipe Validator — Validate recipe.yaml and cross-recipe consistency.

Usage:
  echo '{"recipe_path": ".chapterwise/import-recipe/"}' | python3 recipe_validator.py

Output:
  {"valid": true, "issues": [], "cross_recipe_issues": []}
"""
```

**Validation checks:**
- recipe.yaml parses as valid YAML with required fields (type, version, created)
- Referenced files (convert.py, structure_map.yaml) exist on disk
- Cross-recipe: chapter counts match between import and analysis recipes
- Cross-recipe: chapter hashes in atlas recipe match current files

### Step 5: Create recipe schema

#### `schemas/recipe.schema.yaml`

```yaml
# Recipe manifest schema — shared across all recipe types
type: object
required: [type, version, created]

properties:
  type:
    type: string
    enum: [import, analysis, atlas, reader]
  version:
    type: string
    pattern: "^\\d+\\.\\d+$"
  created:
    type: string
    format: date-time
  updated:
    type: string
    format: date-time

  source:
    type: object
    properties:
      project_path: { type: string }
      chapter_count: { type: integer }
      word_count: { type: integer }
      chapter_hashes: { type: object }

  # Type-specific sections — validated per type
  manuscript: { type: object }
  strategy: { type: object }
  preferences: { type: object }
  structure: { type: object }
  passes: { type: object }
  atlas: { type: object }
  output: { type: object }
  modules: { type: object }
  updates: { type: array }
```

### Step 6: Create template directory placeholders

```
templates/minimal-reader/README.md    → "Minimal reader template — built by Reader Agent"
templates/academic-reader/README.md   → "Academic reader template — built by Reader Agent"
```

### Step 7: Verify everything works

- Run any existing command via the new plugin path to verify nothing broke
- Check that `module_loader.py list` finds all analysis modules
- Check that all script imports resolve correctly
- Run a smoke check for `codex_validator.py` and `recipe_validator.py` JSON interfaces

### Step 8: Commit

```
feat: scaffold unified chapterwise plugin (v2.0.0)

Merge chapterwise, chapterwise-codex, and chapterwise-analysis into one plugin.
All existing commands preserved. Shared recipe infrastructure added.
```

---

## Output

After Phase 0, the unified plugin has:
- All existing commands working (insert, format, explode, implode, etc.)
- All analysis modules accessible
- All analysis scripts working
- Shared recipe scripts (recipe_manager, format_detector, run_recipe, codex_validator, recipe_validator)
- Recipe schema
- Empty pattern/template directories ready for recipe agents

The four recipe agents can now work in parallel — each building their command file + supporting files.
