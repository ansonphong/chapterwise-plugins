#!/usr/bin/env python3
"""
codex_writer.py — JSON-in/JSON-out script that writes Chapterwise project output files.

Input (stdin): JSON with output_dir, format, structure, chapters, metadata, special_sections
Output (stdout): JSON with files_created, index_path, total_words
"""

import json
import os
import re
import sys
import uuid

import yaml


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug."""
    # Strip special characters
    slug = re.sub(r"[()&,.\[\]+]", "", title)
    # Spaces to hyphens
    slug = slug.replace(" ", "-")
    # Collapse multiple hyphens
    slug = re.sub(r"-{2,}", "-", slug)
    # Lowercase
    slug = slug.lower()
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def short_uuid() -> str:
    """Generate a short 8-character UUID hex string."""
    return uuid.uuid4().hex[:8]


def write_markdown_file(filepath: str, item: dict) -> None:
    """Write a single Markdown file with YAML frontmatter in Codex Lite format."""
    frontmatter = {
        "type": item.get("type", "chapter"),
        "name": item.get("title", ""),
        "id": short_uuid(),
        "word_count": item.get("word_count", 0),
    }

    tags = item.get("tags", [])
    if tags:
        frontmatter["tags"] = tags

    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).rstrip()

    content = item.get("content", "")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(frontmatter_yaml)
        f.write("\n---\n\n")
        f.write(content)
        if content and not content.endswith("\n"):
            f.write("\n")


def write_index_file(index_path: str, metadata: dict, children: list) -> None:
    """Write the index.codex.yaml file."""
    index_data = {
        "type": "project",
        "name": metadata.get("title", ""),
    }

    author = metadata.get("author", "")
    if author:
        index_data["author"] = author

    index_data["children"] = children

    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def main():
    raw = sys.stdin.read()
    data = json.loads(raw)

    output_dir = data["output_dir"]
    structure = data.get("structure", "flat")
    chapters = data.get("chapters", [])
    special_sections = data.get("special_sections", [])
    metadata = data.get("metadata", {})

    # All items to write (special sections first, then chapters)
    all_items = list(special_sections) + list(chapters)

    os.makedirs(output_dir, exist_ok=True)

    files_created = 0
    total_words = 0
    children = []

    for item in all_items:
        title = item.get("title", "untitled")
        slug = slugify(title)
        filename = f"{slug}.md"

        # Determine directory for this file
        if structure == "folders_per_part" and "part" in item:
            part_value = item["part"]
            part_slug = slugify(str(part_value))
            part_dir = os.path.join(output_dir, f"part-{part_slug}")
            os.makedirs(part_dir, exist_ok=True)
            filepath = os.path.join(part_dir, filename)
            relative_file = f"part-{part_slug}/{filename}"
        else:
            filepath = os.path.join(output_dir, filename)
            relative_file = filename

        write_markdown_file(filepath, item)
        files_created += 1
        total_words += item.get("word_count", 0)

        child_entry = {
            "file": relative_file,
            "type": item.get("type", "chapter"),
            "name": title,
        }
        children.append(child_entry)

    # Write index
    index_path = os.path.join(output_dir, "index.codex.yaml")
    write_index_file(index_path, metadata, children)
    files_created += 1

    result = {
        "files_created": files_created,
        "index_path": "index.codex.yaml",
        "total_words": total_words,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
