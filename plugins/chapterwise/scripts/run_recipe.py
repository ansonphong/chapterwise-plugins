#!/usr/bin/env python3
"""
run_recipe.py - Execute a saved ChapterWise import recipe.

Input (stdin JSON):
    {"recipe_path": ".chapterwise/import-recipe", "source_path": "new-draft.pdf"}

Output (stdout JSON):
    {"success": true, "output_dir": "./my-novel/", "message": "Recipe executed successfully"}
"""

import hashlib
import json
import os
import subprocess
import sys

try:
    import yaml
except ImportError:
    print(json.dumps({"success": False, "error": "PyYAML is not installed. Run: pip install pyyaml"}))
    sys.exit(1)


def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except OSError:
        return None


def load_recipe(recipe_path):
    """Load and parse recipe.yaml from the given recipe directory."""
    recipe_yaml_path = os.path.join(recipe_path, "recipe.yaml")
    if not os.path.isfile(recipe_yaml_path):
        return None, recipe_yaml_path
    with open(recipe_yaml_path, "r", encoding="utf-8") as f:
        recipe = yaml.safe_load(f)
    return recipe, recipe_yaml_path


def get_output_dir(recipe):
    """Extract output directory from recipe data."""
    try:
        return recipe.get("output", {}).get("directory", "./output/")
    except (AttributeError, TypeError):
        return "./output/"


def get_stored_hash(recipe):
    """Extract stored source hash from recipe data."""
    try:
        return recipe.get("source", {}).get("hash")
    except (AttributeError, TypeError):
        return None


def run_shell_script(run_sh_path, source_path):
    """Execute run.sh with source_path as an argument."""
    result = subprocess.run(
        ["/bin/sh", run_sh_path, source_path],
        capture_output=True,
        text=True,
    )
    return result


def run_python_converter(convert_py_path, source_path, output_dir):
    """Execute convert.py via python3 with JSON piped to stdin."""
    input_data = json.dumps({"source": source_path, "output_dir": output_dir})
    result = subprocess.run(
        [sys.executable, convert_py_path],
        input=input_data,
        capture_output=True,
        text=True,
    )
    return result


def main():
    # --- Read input ---
    try:
        raw = sys.stdin.read()
        params = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)

    recipe_path = params.get("recipe_path", "")
    source_path = params.get("source_path", "")

    if not recipe_path:
        print(json.dumps({"success": False, "error": "Missing required field: recipe_path"}))
        sys.exit(1)

    if not source_path:
        print(json.dumps({"success": False, "error": "Missing required field: source_path"}))
        sys.exit(1)

    # --- Load recipe.yaml ---
    recipe, recipe_yaml_path = load_recipe(recipe_path)
    if recipe is None:
        print(json.dumps({"success": False, "error": "recipe.yaml not found"}))
        sys.exit(1)

    # --- Determine output directory ---
    output_dir = get_output_dir(recipe)

    # --- Check source hash ---
    stored_hash = get_stored_hash(recipe)
    current_hash = compute_file_hash(source_path)

    if stored_hash is not None and current_hash is not None and stored_hash == current_hash:
        print(json.dumps({
            "success": True,
            "output_dir": output_dir,
            "message": "Already up to date",
        }))
        return

    # --- Determine converter to use ---
    run_sh_path = os.path.join(recipe_path, "run.sh")
    convert_py_path = os.path.join(recipe_path, "convert.py")

    if os.path.isfile(run_sh_path):
        result = run_shell_script(run_sh_path, source_path)
    elif os.path.isfile(convert_py_path):
        result = run_python_converter(convert_py_path, source_path, output_dir)
    else:
        print(json.dumps({"success": False, "error": "No converter found in recipe"}))
        sys.exit(1)

    # --- Handle converter result ---
    if result.returncode != 0:
        print(json.dumps({
            "success": False,
            "error": "Converter failed",
            "stderr": result.stderr,
        }))
        sys.exit(1)

    # --- Success ---
    response = {
        "success": True,
        "output_dir": output_dir,
        "message": "Recipe executed successfully",
    }
    if result.stdout.strip():
        response["stdout"] = result.stdout.strip()

    print(json.dumps(response))


if __name__ == "__main__":
    main()
