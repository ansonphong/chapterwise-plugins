# Phase 1: Scaffold — Tasks 1-10

> **Reference:** `build-plans/PHASE-0-SCAFFOLD.md`, `01-PLUGIN-STRUCTURE.md`

## Task 1: Create unified plugin directory structure

**Files:**
- Create: `plugins/chapterwise/.claude-plugin/plugin.json`
- Create: `plugins/chapterwise/commands/` (directory)
- Create: `plugins/chapterwise/modules/` (directory)
- Create: `plugins/chapterwise/patterns/common/` (directory)
- Create: `plugins/chapterwise/scripts/` (directory)
- Create: `plugins/chapterwise/schemas/` (directory)
- Create: `plugins/chapterwise/templates/` (directory)

### Step 1.1: Create directories

```bash
cd /Users/phong/Projects/chapterwise-plugins
mkdir -p plugins/chapterwise/{.claude-plugin,commands,modules,patterns/common,scripts,schemas,templates/minimal-reader,templates/academic-reader}
```

### Step 1.2: Write plugin.json

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

### Step 1.3: Verify

```bash
ls plugins/chapterwise/.claude-plugin/plugin.json && echo PASS
```

---

## Task 2: Copy existing commands from chapterwise-codex

**Files:**
- Copy: `plugins/chapterwise-codex/commands/*.md` → `plugins/chapterwise/commands/`
- Skip: `import.md` and `import-scrivener.md` (will be rewritten)

### Step 2.1: Copy commands (excluding import files)

```bash
cd /Users/phong/Projects/chapterwise-plugins
for f in plugins/chapterwise-codex/commands/*.md; do
  base=$(basename "$f")
  if [[ "$base" != "import.md" && "$base" != "import-scrivener.md" ]]; then
    cp "$f" plugins/chapterwise/commands/
  fi
done
```

### Step 2.2: Verify

```bash
ls plugins/chapterwise/commands/format.md plugins/chapterwise/commands/explode.md plugins/chapterwise/commands/lite.md && echo PASS
```

---

## Task 3: Copy insert.md from current chapterwise plugin

**Files:**
- Copy: `plugins/chapterwise/commands/insert.md`

NOTE: The current `plugins/chapterwise/` already has `commands/insert.md` and `commands/import.md`. We're building the unified version in the same directory. `insert.md` stays as-is. The old `import.md` gets overwritten by the recipe version in Phase 2.

### Step 3.1: Verify insert.md is already there

```bash
ls plugins/chapterwise/commands/insert.md && echo PASS
```

If not present (because we created a new directory), copy it:
```bash
cp plugins/chapterwise/commands/insert.md plugins/chapterwise/commands/ 2>/dev/null || true
```

---

## Task 4: Copy analysis modules

**Files:**
- Copy: `plugins/chapterwise-analysis/modules/*.md` → `plugins/chapterwise/modules/`

### Step 4.1: Copy all module files

```bash
cp plugins/chapterwise-analysis/modules/*.md plugins/chapterwise/modules/
```

### Step 4.2: Verify

```bash
ls plugins/chapterwise/modules/summary.md plugins/chapterwise/modules/characters.md plugins/chapterwise/modules/_output-format.md && echo PASS
```

---

## Task 5: Copy scripts

**Files:**
- Copy: `plugins/chapterwise-analysis/scripts/*.py` → `plugins/chapterwise/scripts/`
- Copy: `plugins/chapterwise-codex/scripts/*.py` → `plugins/chapterwise/scripts/`

### Step 5.1: Copy from analysis

```bash
cp plugins/chapterwise-analysis/scripts/*.py plugins/chapterwise/scripts/
```

### Step 5.2: Copy from codex (skip __pycache__)

```bash
for f in plugins/chapterwise-codex/scripts/*.py; do
  cp "$f" plugins/chapterwise/scripts/
done
```

### Step 5.3: Verify

```bash
ls plugins/chapterwise/scripts/module_loader.py plugins/chapterwise/scripts/staleness_checker.py plugins/chapterwise/scripts/analysis_writer.py plugins/chapterwise/scripts/word_count.py && echo PASS
```

---

## Task 6: Build recipe infrastructure scripts

**Files:**
- Create: `plugins/chapterwise/scripts/recipe_manager.py`
- Create: `plugins/chapterwise/scripts/codex_validator.py`
- Create: `plugins/chapterwise/scripts/recipe_validator.py`

### Step 6.1: Write recipe_manager.py

A JSON-in/JSON-out utility for recipe folder management.

**Commands:**
- `create` — Create `.chapterwise/{type}-recipe/` with empty `recipe.yaml`
- `load` — Read recipe.yaml from existing folder
- `list` — Discover all recipes in a project
- `validate` — Check recipe against schema

**Input/Output convention:** stdin JSON, stdout JSON. Command as first CLI arg.

```python
#!/usr/bin/env python3
"""Recipe Manager — Create, load, validate, discover recipe folders."""
import json, sys, os, yaml
from datetime import datetime, timezone

def create(data):
    """Create a new recipe folder with empty recipe.yaml."""
    project = data["project_path"]
    rtype = data["type"]  # import, analysis, atlas, reader
    name = data.get("name")  # For named atlases: atlas-recipe-{name}

    folder_name = f"{rtype}-recipe"
    if name and rtype == "atlas":
        folder_name = f"atlas-recipe-{name}"

    recipe_dir = os.path.join(project, ".chapterwise", folder_name)
    os.makedirs(recipe_dir, exist_ok=True)

    recipe = {
        "type": rtype,
        "version": "1.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    recipe_path = os.path.join(recipe_dir, "recipe.yaml")
    with open(recipe_path, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"recipe_path": recipe_path, "folder": recipe_dir, "created": True}

def load(data):
    """Load an existing recipe.yaml."""
    project = data["project_path"]
    rtype = data["type"]
    name = data.get("name")

    folder_name = f"{rtype}-recipe"
    if name and rtype == "atlas":
        folder_name = f"atlas-recipe-{name}"

    recipe_path = os.path.join(project, ".chapterwise", folder_name, "recipe.yaml")

    if not os.path.exists(recipe_path):
        return {"found": False, "recipe_path": recipe_path}

    with open(recipe_path) as f:
        recipe = yaml.safe_load(f)

    return {"found": True, "recipe_path": recipe_path, "recipe": recipe}

def list_recipes(data):
    """Discover all recipes in a project."""
    project = data["project_path"]
    chapterwise_dir = os.path.join(project, ".chapterwise")

    if not os.path.isdir(chapterwise_dir):
        return {"recipes": []}

    recipes = []
    for entry in sorted(os.listdir(chapterwise_dir)):
        recipe_path = os.path.join(chapterwise_dir, entry, "recipe.yaml")
        if os.path.isfile(recipe_path):
            with open(recipe_path) as f:
                recipe = yaml.safe_load(f)
            recipes.append({
                "folder": entry,
                "type": recipe.get("type", "unknown"),
                "created": recipe.get("created"),
                "updated": recipe.get("updated"),
            })

    return {"recipes": recipes}

def validate(data):
    """Validate a recipe.yaml against basic rules."""
    recipe_path = data["recipe_path"]

    if not os.path.isfile(os.path.join(recipe_path, "recipe.yaml")):
        return {"valid": False, "errors": ["recipe.yaml not found"]}

    with open(os.path.join(recipe_path, "recipe.yaml")) as f:
        recipe = yaml.safe_load(f)

    errors = []
    if "type" not in recipe:
        errors.append("Missing required field: type")
    if "version" not in recipe:
        errors.append("Missing required field: version")
    if recipe.get("type") not in ("import", "analysis", "atlas", "reader"):
        errors.append(f"Invalid type: {recipe.get('type')}")

    # Check referenced files exist
    if recipe.get("strategy", {}).get("custom_script"):
        script_path = os.path.join(recipe_path, recipe["strategy"]["custom_script"])
        if not os.path.isfile(script_path):
            errors.append(f"Referenced script not found: {recipe['strategy']['custom_script']}")

    return {"valid": len(errors) == 0, "errors": errors}

def update(data):
    """Update specific fields in an existing recipe.yaml."""
    recipe_path = data["recipe_path"]
    updates = data.get("updates", {})

    yaml_path = os.path.join(recipe_path, "recipe.yaml")
    if not os.path.isfile(yaml_path):
        return {"success": False, "error": "recipe.yaml not found"}

    with open(yaml_path) as f:
        recipe = yaml.safe_load(f)

    # Deep merge updates into recipe
    def deep_merge(base, override):
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(recipe, updates)
    recipe["updated"] = datetime.now(timezone.utc).isoformat()

    with open(yaml_path, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"success": True, "recipe_path": recipe_path}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    data = json.load(sys.stdin)

    commands = {
        "create": create,
        "load": load,
        "list": list_recipes,
        "validate": validate,
        "update": update,
    }

    if cmd not in commands:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    result = commands[cmd](data)
    print(json.dumps(result, indent=2))
```

### Step 6.2: Add `codex_validator.py` and `recipe_validator.py`

Create both validator scripts during this task:
- `codex_validator.py` validates project `.md` and `.codex.yaml` output and supports `fix: true` auto-repairs.
- `recipe_validator.py` validates `recipe.yaml`, referenced artifacts, and cross-recipe consistency.

Both scripts must follow the same stdin JSON → stdout JSON contract used by other shared scripts.

### Step 6.3: Verify

```bash
echo '{"project_path":"/tmp/test-recipe","type":"import"}' | python3 plugins/chapterwise/scripts/recipe_manager.py create >/dev/null && \
python3 -c "import ast; ast.parse(open('plugins/chapterwise/scripts/codex_validator.py').read()); ast.parse(open('plugins/chapterwise/scripts/recipe_validator.py').read()); print('PASS')"
```

---

## Task 7: Build `scripts/format_detector.py`

**Files:**
- Create: `plugins/chapterwise/scripts/format_detector.py`

### Step 7.1: Write format_detector.py

```python
#!/usr/bin/env python3
"""Format Detector — Detect manuscript source format."""
import json, sys, os

FORMAT_MAP = {
    ".pdf": "pdf", ".docx": "docx", ".doc": "doc",
    ".scriv": "scrivener", ".ulyz": "ulysses",
    ".md": "markdown", ".txt": "plaintext",
    ".html": "html", ".htm": "html", ".rtf": "rtf",
    ".epub": "epub", ".fdx": "final_draft", ".fountain": "fountain",
    ".latex": "latex", ".tex": "latex",
}

def detect(path):
    if os.path.isdir(path):
        # Check for Scrivener project
        if path.endswith(".scriv") or any(f.endswith(".scrivx") for f in os.listdir(path)):
            return {"format": "scrivener", "confidence": 0.99, "details": {"type": "directory"}}
        # Check for Ulysses
        if path.endswith(".ulyz"):
            return {"format": "ulysses", "confidence": 0.99, "details": {"type": "directory"}}
        # Folder of files
        md_count = len([f for f in os.listdir(path) if f.endswith((".md", ".txt"))])
        if md_count > 0:
            return {"format": "markdown_folder", "confidence": 0.8, "details": {"file_count": md_count}}
        return {"format": "unknown", "confidence": 0.0, "details": {"type": "directory"}}

    _, ext = os.path.splitext(path.lower())
    fmt = FORMAT_MAP.get(ext)

    if fmt:
        details = {"extension": ext, "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0}
        return {"format": fmt, "confidence": 0.95, "details": details}

    # Content sniffing fallback
    if os.path.exists(path):
        with open(path, "rb") as f:
            header = f.read(8)
        if header.startswith(b"%PDF"):
            return {"format": "pdf", "confidence": 0.99, "details": {"detected_by": "magic_bytes"}}
        if header.startswith(b"PK"):
            return {"format": "docx", "confidence": 0.7, "details": {"detected_by": "magic_bytes", "note": "Could be EPUB or other ZIP"}}

    return {"format": "unknown", "confidence": 0.0, "details": {"extension": ext}}

if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = detect(data["path"])
    print(json.dumps(result, indent=2))
```

### Step 7.2: Verify

```bash
echo '{"path":"README.md"}' | python3 plugins/chapterwise/scripts/format_detector.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d['format']=='markdown' else 'FAIL')"
```

---

## Task 8: Create `schemas/recipe.schema.yaml`

**Files:**
- Create: `plugins/chapterwise/schemas/recipe.schema.yaml`

### Step 8.1: Write schema

```yaml
# Recipe manifest schema — shared across all recipe types
type: object
required: [type, version, created]

properties:
  type:
    type: string
    enum: [import, analysis, atlas, reader]
    description: "Recipe type identifier"
  version:
    type: string
    pattern: "^\\d+\\.\\d+$"
    description: "Schema version"
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
      chapter_hashes:
        type: object
        additionalProperties: { type: string }

  manuscript:
    type: object
    properties:
      title: { type: string }
      author: { type: string }
      type: { type: string }
      structure: { type: string }

  strategy:
    type: object
    description: "Import recipe: conversion strategy"

  preferences:
    type: object
    description: "Import recipe: writer's choices"

  passes:
    type: object
    description: "Atlas recipe: four-pass status tracking"

  modules:
    type: object
    description: "Analysis recipe: module selections"

  atlas:
    type: object
    description: "Atlas recipe: name, slug, output path"
    properties:
      name: { type: string }
      slug: { type: string }
      output_path: { type: string }

  structure:
    type: object
    description: "Atlas recipe: proposed structure + sections"

  output:
    type: object
    properties:
      directory: { type: string }
      file_count: { type: integer }
      git_commit: { type: string }

  updates:
    type: array
    description: "Atlas recipe: update history"
    items: { type: object }
```

### Step 8.2: Verify

```bash
python3 -c "import yaml; yaml.safe_load(open('plugins/chapterwise/schemas/recipe.schema.yaml')); print('PASS')"
```

---

## Task 9: Create empty template and pattern directories

**Files:**
- Create: `plugins/chapterwise/patterns/common/__init__.py`
- Create: `plugins/chapterwise/templates/minimal-reader/.gitkeep`
- Create: `plugins/chapterwise/templates/academic-reader/.gitkeep`

### Step 9.1: Create markers

```bash
touch plugins/chapterwise/patterns/__init__.py
touch plugins/chapterwise/patterns/common/__init__.py
touch plugins/chapterwise/templates/minimal-reader/.gitkeep
touch plugins/chapterwise/templates/academic-reader/.gitkeep
```

### Step 9.2: Verify

```bash
ls -d plugins/chapterwise/templates/ plugins/chapterwise/patterns/common/ && echo PASS
```

---

## Task 10: Verify module_loader.py works from new location

**Files:**
- Modify: `plugins/chapterwise/scripts/module_loader.py` (if path fixes needed)

### Step 10.1: Test module discovery

```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise && CLAUDE_PLUGIN_ROOT=. python3 scripts/module_loader.py list
```

### Step 10.2: Fix paths if needed

The module_loader likely references `${CLAUDE_PLUGIN_ROOT}/modules/` to find `.md` files. Since modules are now at `modules/` relative to the plugin root, this should work. If it fails, update the module discovery path.

### Step 10.3: Verify

```bash
cd /Users/phong/Projects/chapterwise-plugins/plugins/chapterwise && CLAUDE_PLUGIN_ROOT=. python3 scripts/module_loader.py list 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d)>0 else 'FAIL')"
```

---

## Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add plugins/chapterwise/
git commit -m "feat: scaffold unified chapterwise plugin (v2.0.0)

Merge chapterwise, chapterwise-codex, and chapterwise-analysis into one plugin.
All existing commands, modules, and scripts copied. Shared recipe infrastructure added:
- recipe_manager.py: create/load/validate/discover recipes
- format_detector.py: detect manuscript format from extension + content
- codex_validator.py: validate and auto-fix codex output
- recipe_validator.py: validate recipe manifests + cross-recipe consistency
- recipe.schema.yaml: shared schema for recipe manifests"
```
