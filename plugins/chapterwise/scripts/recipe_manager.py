#!/usr/bin/env python3
"""
Recipe Manager — Create, load, validate, and discover recipe folders.

Usage:
  echo '{"project_path": "./my-novel", "type": "import"}' | python3 recipe_manager.py create
  echo '{"project_path": "./my-novel", "type": "import"}' | python3 recipe_manager.py load
  echo '{"project_path": "./my-novel"}' | python3 recipe_manager.py list
  echo '{"recipe_path": ".chapterwise/import-recipe"}' | python3 recipe_manager.py validate
  echo '{"recipe_path": ".chapterwise/import-recipe", "updates": {"manuscript": {"title": "New Title"}}}' | python3 recipe_manager.py update

All input via stdin JSON, all output via stdout JSON.
"""
import json
import sys
import os

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip3 install pyyaml\n")
    sys.exit(1)

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

    now = datetime.now(timezone.utc).isoformat()
    recipe = {
        "type": rtype,
        "version": "1.0",
        "created": now,
        "updated": now,
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
    yaml_file = os.path.join(recipe_path, "recipe.yaml")

    if not os.path.isfile(yaml_file):
        return {"valid": False, "errors": ["recipe.yaml not found"]}

    with open(yaml_file) as f:
        recipe = yaml.safe_load(f)

    errors = []
    if not isinstance(recipe, dict):
        return {"valid": False, "errors": ["recipe.yaml is not a valid YAML mapping"]}

    if "type" not in recipe:
        errors.append("Missing required field: type")
    if "version" not in recipe:
        errors.append("Missing required field: version")
    if recipe.get("type") not in ("import", "analysis", "atlas", "reader"):
        errors.append(f"Invalid type: {recipe.get('type')}")

    # Check referenced files exist
    strategy = recipe.get("strategy", {})
    if isinstance(strategy, dict) and strategy.get("custom_script"):
        script_path = os.path.join(recipe_path, strategy["custom_script"])
        if not os.path.isfile(script_path):
            errors.append(f"Referenced script not found: {strategy['custom_script']}")

    return {"valid": len(errors) == 0, "errors": errors}


def update(data):
    """Update specific fields in an existing recipe.yaml."""
    recipe_path = data["recipe_path"]
    updates = data.get("updates", {})

    yaml_file = os.path.join(recipe_path, "recipe.yaml")
    if not os.path.isfile(yaml_file):
        return {"success": False, "error": "recipe.yaml not found"}

    with open(yaml_file) as f:
        recipe = yaml.safe_load(f)

    def deep_merge(base, override):
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(recipe, updates)
    recipe["updated"] = datetime.now(timezone.utc).isoformat()

    with open(yaml_file, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"success": True, "recipe_path": recipe_path}


def scan(data):
    """Scan a project directory for codex files and metadata."""
    project = data["project_path"]

    codex_files = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith('.codex.yaml') or f.endswith('.codex.md'):
                codex_files.append(os.path.relpath(os.path.join(root, f), project))

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
    recipe = {
        "type": rtype,
        "version": "1.0",
        "created": now,
        "updated": now,
    }

    for key in data:
        if key not in ("project_path", "type", "name"):
            recipe[key] = data[key]

    recipe_path = os.path.join(recipe_dir, "recipe.yaml")
    with open(recipe_path, "w") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return {"success": True, "recipe_path": recipe_path, "folder": recipe_dir}


def patch(data):
    """Patch specific fields in a recipe. Appends to arrays (like update history) rather than replacing."""
    project = data.get("project_path", ".")
    rtype = data.get("type", "atlas")
    patch_data = data.get("patch", {})

    name = data.get("name")
    folder_name = f"{rtype}-recipe"
    if name and rtype == "atlas":
        folder_name = f"atlas-recipe-{name}"

    recipe_path = os.path.join(project, ".chapterwise", folder_name, "recipe.yaml")
    if not os.path.isfile(recipe_path):
        return {"success": False, "error": "recipe.yaml not found"}

    with open(recipe_path) as f:
        recipe = yaml.safe_load(f)

    for key, value in patch_data.items():
        if key == "update_entry":
            if "updates" not in recipe:
                recipe["updates"] = []
            recipe["updates"].append(value)
        elif key == "chapter_hashes":
            recipe["chapter_hashes"] = value
        else:
            if isinstance(value, dict) and isinstance(recipe.get(key), dict):
                recipe[key].update(value)
            else:
                recipe[key] = value

    recipe["updated"] = datetime.now(timezone.utc).isoformat()

    with open(recipe_path, "w") as f:
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
        "scan": scan,
        "save": save,
        "patch": patch,
    }

    if cmd not in commands:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    result = commands[cmd](data)
    print(json.dumps(result, indent=2))
