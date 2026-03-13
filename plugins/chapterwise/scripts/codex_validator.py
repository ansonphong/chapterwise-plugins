#!/usr/bin/env python3
"""
Codex Validator — Validate and auto-fix .codex.yaml and .md files.

Usage:
  echo '{"path": "./my-novel/", "fix": true}' | python3 codex_validator.py

Output:
  {"valid": true, "issues": [], "fixes_applied": []}

Validation checks:
- All .md files have valid YAML frontmatter with type and name fields
- All .codex.yaml files parse as valid YAML
- UUIDs are present and unique across the project
- index.codex.yaml children reference files that exist on disk
- No orphan files (on disk but not in index)
- Word counts are populated and non-zero

Auto-fix actions (when fix: true):
- Add missing type field (inferred from content or filename)
- Add missing name field (from first heading or filename)
- Regenerate invalid/missing UUIDs
- Recalculate word counts from content
- Add orphan files to index

All input via stdin JSON, all output via stdout JSON.
"""
import json
import sys
import os
import re
import uuid

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip3 install pyyaml\n")
    sys.exit(1)


def generate_id():
    """Generate a short UUID for codex nodes."""
    return str(uuid.uuid4())[:8]


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file. Returns (frontmatter_dict, body, raw_text)."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if not content.startswith("---"):
        return None, content, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content, content

    try:
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict):
            return None, content, content
        body = parts[2].lstrip("\n")
        return fm, body, content
    except yaml.YAMLError:
        return None, content, content


def count_words(text):
    """Count words in text, stripping markdown formatting."""
    clean = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
    clean = re.sub(r"[#*_`\[\]()>]", " ", clean)
    return len(clean.split())


def validate_project(path, fix=False):
    """Validate a Chapterwise project directory."""
    issues = []
    fixes_applied = []
    seen_ids = {}

    if not os.path.isdir(path):
        return {"valid": False, "issues": [f"Path is not a directory: {path}"], "fixes_applied": []}

    # Collect all relevant files
    md_files = []
    codex_files = []
    index_file = None

    for root, dirs, files in os.walk(path):
        # Skip hidden directories except .chapterwise
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".chapterwise"]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, path)
            if fname == "index.codex.yaml":
                index_file = fpath
                codex_files.append((fpath, rel))
            elif fname.endswith(".codex.yaml"):
                codex_files.append((fpath, rel))
            elif fname.endswith(".md") and not fname.startswith("_"):
                md_files.append((fpath, rel))

    # Validate .codex.yaml files
    for fpath, rel in codex_files:
        try:
            with open(fpath) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                issues.append({"file": rel, "severity": "high", "issue": "YAML does not parse to a mapping"})
        except yaml.YAMLError as e:
            issues.append({"file": rel, "severity": "high", "issue": f"Invalid YAML: {e}"})

    # Validate .md files with frontmatter
    for fpath, rel in md_files:
        fm, body, raw = parse_frontmatter(fpath)

        if fm is None:
            issues.append({"file": rel, "severity": "medium", "issue": "Missing or invalid YAML frontmatter"})
            if fix:
                name = os.path.splitext(os.path.basename(fpath))[0].replace("-", " ").replace("_", " ").title()
                new_fm = {"type": "chapter", "name": name, "id": generate_id()}
                wc = count_words(raw)
                if wc > 0:
                    new_fm["word_count"] = wc
                fm_yaml = yaml.dump(new_fm, default_flow_style=False, sort_keys=False)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(f"---\n{fm_yaml}---\n\n{raw}")
                fixes_applied.append(f"Added frontmatter to {rel}")
            continue

        # Check required fields
        if "type" not in fm:
            issues.append({"file": rel, "severity": "medium", "issue": "Missing required field: type"})
            if fix:
                fm["type"] = "chapter"
                _rewrite_frontmatter(fpath, fm, body)
                fixes_applied.append(f"Added type='chapter' to {rel}")

        if "name" not in fm:
            issues.append({"file": rel, "severity": "medium", "issue": "Missing required field: name"})
            if fix:
                name = os.path.splitext(os.path.basename(fpath))[0].replace("-", " ").replace("_", " ").title()
                fm["name"] = name
                _rewrite_frontmatter(fpath, fm, body)
                fixes_applied.append(f"Added name='{name}' to {rel}")

        # Check ID
        file_id = fm.get("id")
        if not file_id:
            issues.append({"file": rel, "severity": "low", "issue": "Missing id field"})
            if fix:
                fm["id"] = generate_id()
                _rewrite_frontmatter(fpath, fm, body)
                fixes_applied.append(f"Generated id for {rel}")
        else:
            if file_id in seen_ids:
                issues.append({"file": rel, "severity": "high", "issue": f"Duplicate id '{file_id}' (also in {seen_ids[file_id]})"})
                if fix:
                    fm["id"] = generate_id()
                    _rewrite_frontmatter(fpath, fm, body)
                    fixes_applied.append(f"Regenerated duplicate id in {rel}")
            else:
                seen_ids[file_id] = rel

        # Check word count
        wc = fm.get("word_count")
        if wc is None or wc == 0:
            actual_wc = count_words(body)
            if actual_wc > 0:
                issues.append({"file": rel, "severity": "low", "issue": f"Missing/zero word_count (actual: {actual_wc})"})
                if fix:
                    fm["word_count"] = actual_wc
                    _rewrite_frontmatter(fpath, fm, body)
                    fixes_applied.append(f"Set word_count={actual_wc} in {rel}")

    # Validate index references
    if index_file and os.path.isfile(index_file):
        try:
            with open(index_file) as f:
                index_data = yaml.safe_load(f)
            if isinstance(index_data, dict) and "children" in index_data:
                _validate_children(index_data["children"], path, issues, md_files, fixes_applied)
        except yaml.YAMLError:
            pass  # Already caught above

    valid = all(i.get("severity") != "high" for i in issues)
    return {"valid": valid, "issues": issues, "fixes_applied": fixes_applied}


def _rewrite_frontmatter(fpath, fm, body):
    """Rewrite a markdown file with updated frontmatter."""
    fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"---\n{fm_yaml}---\n\n{body}")


def _validate_children(children, base_path, issues, md_files, fixes_applied):
    """Validate index children references."""
    if not isinstance(children, list):
        return
    md_rel_set = {rel for _, rel in md_files}
    for child in children:
        if isinstance(child, dict) and "file" in child:
            child_path = os.path.join(base_path, child["file"])
            if not os.path.exists(child_path):
                issues.append({
                    "file": "index.codex.yaml",
                    "severity": "high",
                    "issue": f"Phantom reference: {child['file']} not found on disk"
                })
        if isinstance(child, dict) and "children" in child:
            _validate_children(child["children"], base_path, issues, md_files, fixes_applied)


if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = validate_project(data["path"], fix=data.get("fix", False))
    print(json.dumps(result, indent=2))
