#!/usr/bin/env python3
"""
Recipe Validator — Validate recipe.yaml and cross-recipe consistency.

Usage:
  echo '{"recipe_path": ".chapterwise/import-recipe/"}' | python3 recipe_validator.py

Output:
  {"valid": true, "issues": [], "cross_recipe_issues": []}

Validation checks:
- recipe.yaml parses as valid YAML with required fields (type, version, created)
- Referenced files (convert.py, structure_map.yaml) exist on disk
- Cross-recipe: chapter counts match between import and analysis recipes
- Cross-recipe: chapter hashes in atlas recipe match current files

All input via stdin JSON, all output via stdout JSON.
"""
import json
import sys
import os
import hashlib

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip3 install pyyaml\n")
    sys.exit(1)

VALID_TYPES = ("import", "analysis", "atlas", "reader")
REQUIRED_FIELDS = ("type", "version", "created")


def validate_recipe(recipe_path):
    """Validate a single recipe folder."""
    issues = []
    yaml_file = os.path.join(recipe_path, "recipe.yaml")

    if not os.path.isfile(yaml_file):
        return {"valid": False, "issues": [{"severity": "critical", "issue": "recipe.yaml not found"}], "cross_recipe_issues": []}

    try:
        with open(yaml_file) as f:
            recipe = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {"valid": False, "issues": [{"severity": "critical", "issue": f"Invalid YAML: {e}"}], "cross_recipe_issues": []}

    if not isinstance(recipe, dict):
        return {"valid": False, "issues": [{"severity": "critical", "issue": "recipe.yaml is not a YAML mapping"}], "cross_recipe_issues": []}

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in recipe:
            issues.append({"severity": "high", "issue": f"Missing required field: {field}"})

    # Check type is valid
    rtype = recipe.get("type")
    if rtype and rtype not in VALID_TYPES:
        issues.append({"severity": "high", "issue": f"Invalid type: {rtype}"})

    # Check referenced files exist
    strategy = recipe.get("strategy", {})
    if isinstance(strategy, dict):
        for key in ("custom_script", "base_pattern"):
            filename = strategy.get(key)
            if filename:
                fpath = os.path.join(recipe_path, filename)
                if not os.path.isfile(fpath):
                    issues.append({"severity": "medium", "issue": f"Referenced file not found: {filename}"})

    # Check structure_map exists for import recipes
    if rtype == "import":
        smap = os.path.join(recipe_path, "structure_map.yaml")
        if recipe.get("manuscript") and not os.path.isfile(smap):
            issues.append({"severity": "low", "issue": "structure_map.yaml not found (expected for import recipes with manuscript data)"})

    # Cross-recipe validation
    cross_issues = _cross_validate(recipe_path, recipe)

    valid = all(i.get("severity") not in ("critical", "high") for i in issues)
    return {"valid": valid, "issues": issues, "cross_recipe_issues": cross_issues}


def _cross_validate(recipe_path, recipe):
    """Check consistency between this recipe and sibling recipes."""
    cross_issues = []
    chapterwise_dir = os.path.dirname(recipe_path)

    if not os.path.isdir(chapterwise_dir):
        return cross_issues

    rtype = recipe.get("type")

    # Load sibling recipes for cross-checking
    siblings = {}
    for entry in os.listdir(chapterwise_dir):
        sibling_yaml = os.path.join(chapterwise_dir, entry, "recipe.yaml")
        if os.path.isfile(sibling_yaml) and entry != os.path.basename(recipe_path):
            try:
                with open(sibling_yaml) as f:
                    siblings[entry] = yaml.safe_load(f)
            except (yaml.YAMLError, IOError):
                pass

    # Cross-check chapter counts between import and analysis
    if rtype == "analysis":
        import_recipe = siblings.get("import-recipe", {})
        if isinstance(import_recipe, dict):
            import_chapters = import_recipe.get("manuscript", {}).get("chapter_count")
            analysis_chapters = recipe.get("manuscript", {}).get("chapters")
            if import_chapters and analysis_chapters and import_chapters != analysis_chapters:
                cross_issues.append({
                    "severity": "medium",
                    "issue": f"Chapter count mismatch: import says {import_chapters}, analysis says {analysis_chapters}"
                })

    # Cross-check atlas chapter hashes
    if rtype == "atlas":
        source = recipe.get("source", {})
        if isinstance(source, dict) and source.get("chapter_hashes"):
            project_path = source.get("project_path")
            if project_path and os.path.isdir(project_path):
                stale = _check_hash_staleness(project_path, source["chapter_hashes"])
                if stale:
                    cross_issues.append({
                        "severity": "low",
                        "issue": f"{len(stale)} chapter(s) have changed since atlas was built: {', '.join(stale[:5])}"
                    })

    return cross_issues


def _check_hash_staleness(project_path, saved_hashes):
    """Compare saved chapter hashes with current file hashes."""
    stale = []
    for filename, saved_hash in saved_hashes.items():
        fpath = os.path.join(project_path, filename)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                current_hash = hashlib.md5(f.read()).hexdigest()[:8]
            if current_hash != saved_hash:
                stale.append(filename)
        else:
            stale.append(filename)
    return stale


if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = validate_recipe(data["recipe_path"])
    print(json.dumps(result, indent=2))
