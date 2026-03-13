#!/usr/bin/env python3
"""
frontmatter_builder.py

Reads JSON from stdin and outputs YAML frontmatter (with --- delimiters)
for Codex Lite markdown files.

Input example:
    {"title": "Chapter 1", "word_count": 3200, "tags": ["adventure"], "summary": "A brief summary", "type": "chapter", "order": 1}

Output example:
    ---
    type: chapter
    name: "Chapter 1"
    id: a1b2c3d4
    word_count: 3200
    tags:
      - adventure
    summary: "A brief summary"
    ---
"""

import json
import sys
import uuid

VALID_TYPES = {"chapter", "prologue", "epilogue", "section", "part", "metadata"}


def generate_short_id() -> str:
    """Generate a short UUID (first 8 characters of a uuid4)."""
    return str(uuid.uuid4()).replace("-", "")[:8]


def quote_string(value: str) -> str:
    """Wrap a string value in double quotes for YAML output."""
    # Escape any existing double quotes inside the value
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def build_frontmatter(data: dict) -> str:
    """
    Build a YAML frontmatter block from the input dictionary.

    Field order:
      1. type
      2. name  (from input 'title')
      3. id    (generated short UUID)
      4. order (optional)
      5. word_count (optional)
      6. tags  (optional, list)
      7. summary (optional)
      8. any remaining extra fields
    """
    lines = ["---"]

    # --- Required fields ---

    # type
    raw_type = str(data.get("type", "chapter")).lower()
    doc_type = raw_type if raw_type in VALID_TYPES else "chapter"
    lines.append(f"type: {doc_type}")

    # name (from title)
    title = data.get("title", "")
    lines.append(f"name: {quote_string(str(title))}")

    # id
    doc_id = generate_short_id()
    lines.append(f"id: {doc_id}")

    # --- Optional well-known fields ---

    # order
    if "order" in data:
        lines.append(f"order: {data['order']}")

    # word_count
    if "word_count" in data:
        lines.append(f"word_count: {data['word_count']}")

    # tags (list)
    if "tags" in data:
        tags = data["tags"]
        if isinstance(tags, list):
            lines.append("tags:")
            for tag in tags:
                lines.append(f"  - {tag}")
        else:
            # Scalar tag value
            lines.append(f"tags: {tags}")

    # summary
    if "summary" in data:
        lines.append(f"summary: {quote_string(str(data['summary']))}")

    # --- Extra fields (anything not already consumed) ---
    known_keys = {"title", "type", "order", "word_count", "tags", "summary"}
    for key, value in data.items():
        if key in known_keys:
            continue
        # Render extra fields
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, str):
            lines.append(f"{key}: {quote_string(value)}")
        else:
            lines.append(f"{key}: {value}")

    lines.append("---")
    return "\n".join(lines)


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.stderr.write("Error: no input provided on stdin\n")
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Error: invalid JSON input: {exc}\n")
        sys.exit(1)

    if not isinstance(data, dict):
        sys.stderr.write("Error: input JSON must be an object (dict)\n")
        sys.exit(1)

    frontmatter = build_frontmatter(data)
    print(frontmatter)


if __name__ == "__main__":
    main()
