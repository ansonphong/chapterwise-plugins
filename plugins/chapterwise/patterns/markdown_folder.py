#!/usr/bin/env python3
"""
markdown_folder.py — Import a folder of markdown/text/HTML files into a Chapterwise project.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/folder/", "output_dir": "/path/to/output/"}

Optional fields:
    "config": {
        "recursive": true,
        "file_types": [".md", ".txt", ".html"],
        "preserve_frontmatter": true,
        "structure": "mirror",
        "type_assignment": "auto",
        "ignore_patterns": [".git", "node_modules", ".obsidian", ".backups", "__pycache__", ".venv"]
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 150, "output_dir": "/path/to/output/"}

CLI usage:
    python3 markdown_folder.py /path/to/folder/ output/
"""

import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

CONFIG = {
    "recursive": True,
    "file_types": [".md", ".txt", ".html"],
    "preserve_frontmatter": True,
    "structure": "mirror",
    "type_assignment": "auto",
    "ignore_patterns": [".git", "node_modules", ".obsidian", ".backups", "__pycache__", ".venv"],
}

# ---------------------------------------------------------------------------
# Script directory — used to locate common/ utilities
# ---------------------------------------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def emit(event: dict) -> None:
    """Write a JSON progress event to stdout."""
    print(json.dumps(event, ensure_ascii=False), flush=True)


def word_count(text: str) -> int:
    """Return a rough word count for the given text."""
    return len(text.split())


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug."""
    slug = re.sub(r"[()&,.\[\]+]", "", title)
    slug = slug.replace(" ", "-")
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.lower().strip("-")
    return slug or "untitled"


def run_common(script_name: str, input_data: dict) -> dict:
    """
    Call one of the common/ utility scripts via subprocess.

    Args:
        script_name: filename inside common/, e.g. "codex_writer.py"
        input_data:  dict to serialise as JSON and pipe to the script's stdin

    Returns:
        Parsed JSON dict from the script's stdout.

    Raises:
        RuntimeError if the subprocess exits non-zero or stdout is not valid JSON.
    """
    script_path = os.path.join(script_dir, "common", script_name)
    result = subprocess.run(
        ["python3", script_path],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"{script_name} exited with code {result.returncode}: {stderr}"
        )
    stdout = result.stdout.strip()
    if not stdout:
        raise RuntimeError(f"{script_name} produced no output")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{script_name} output is not valid JSON: {exc}\nRaw: {stdout[:300]}"
        ) from exc


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple:
    """
    Extract YAML frontmatter from the top of a text file.

    Returns (frontmatter_dict, body_text).
    If no frontmatter is found, returns ({}, text).
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    fm_block = match.group(1)
    body = text[match.end():]
    fm = {}
    # Simple key: value parser (avoids yaml dependency for robustness)
    current_key = None
    current_list = None
    for line in fm_block.splitlines():
        # List item
        list_match = re.match(r"^  - (.+)$", line)
        if list_match and current_key is not None:
            if current_list is None:
                current_list = []
                fm[current_key] = current_list
            current_list.append(list_match.group(1).strip())
            continue
        # Key: value
        kv_match = re.match(r"^(\w[\w_-]*):\s*(.*)$", line)
        if kv_match:
            current_list = None
            current_key = kv_match.group(1)
            raw_val = kv_match.group(2).strip()
            if raw_val == "" or raw_val is None:
                # May be followed by list items
                fm[current_key] = None
            else:
                # Strip surrounding quotes if present
                if (raw_val.startswith('"') and raw_val.endswith('"')) or \
                   (raw_val.startswith("'") and raw_val.endswith("'")):
                    raw_val = raw_val[1:-1]
                fm[current_key] = raw_val

    return fm, body


# ---------------------------------------------------------------------------
# File type assignment
# ---------------------------------------------------------------------------

# Keywords that suggest specific ChapterWise document types
TYPE_KEYWORDS = {
    "character": [
        "character", "persona", "protagonist", "antagonist", "hero", "villain",
        "appearance", "motivation", "backstory", "biography",
    ],
    "location": [
        "location", "place", "setting", "world", "city", "town", "village",
        "geography", "map", "region", "landmark",
    ],
    "prologue": ["prologue"],
    "epilogue": ["epilogue"],
    "section": [
        "note", "notes", "outline", "synopsis", "summary", "research",
        "brainstorm", "ideas", "theme", "preface", "introduction", "afterword",
        "appendix",
    ],
}


def assign_type_from_frontmatter(fm: dict) -> str | None:
    """Read the 'type' field from existing frontmatter."""
    raw = fm.get("type") or fm.get("Type") or fm.get("TYPE")
    if raw:
        return str(raw).lower().strip()
    return None


def assign_type_from_content(title: str, body: str) -> str:
    """
    Heuristically assign a ChapterWise type based on title and body content.

    Returns one of: chapter, character, location, prologue, epilogue, section.
    """
    text_lower = (title + " " + body[:500]).lower()
    for doc_type, keywords in TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return doc_type
    # Default to chapter
    return "chapter"


def assign_type(fm: dict, title: str, body: str, mode: str) -> str:
    """Resolve the document type according to the type_assignment config mode."""
    if mode == "auto":
        # Frontmatter type takes priority; fall back to heuristic
        fm_type = assign_type_from_frontmatter(fm)
        if fm_type:
            return fm_type
        return assign_type_from_content(title, body)
    if mode == "frontmatter":
        fm_type = assign_type_from_frontmatter(fm)
        return fm_type or "chapter"
    # mode == "chapter" or anything else: always chapter
    return "chapter"


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------

def should_ignore(name: str, ignore_patterns: list) -> bool:
    """Return True if a file/directory name matches any ignore pattern."""
    return any(pattern in name for pattern in ignore_patterns)


def scan_directory(root: str, file_types: list, recursive: bool, ignore_patterns: list) -> list:
    """
    Scan a directory for files matching the given extensions.

    Returns a list of absolute file paths, sorted for deterministic ordering.
    """
    found = []
    file_types_set = set(ft.lower() for ft in file_types)

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in-place (prevents descending)
            dirnames[:] = [
                d for d in sorted(dirnames)
                if not should_ignore(d, ignore_patterns)
            ]
            for fname in sorted(filenames):
                if should_ignore(fname, ignore_patterns):
                    continue
                ext = os.path.splitext(fname)[1].lower()
                if ext in file_types_set:
                    found.append(os.path.join(dirpath, fname))
    else:
        try:
            entries = sorted(os.listdir(root))
        except OSError:
            return []
        for entry in entries:
            if should_ignore(entry, ignore_patterns):
                continue
            full_path = os.path.join(root, entry)
            if os.path.isfile(full_path):
                ext = os.path.splitext(entry)[1].lower()
                if ext in file_types_set:
                    found.append(full_path)
    return found


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read a file with encoding detection fallback."""
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as fh:
                return fh.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def strip_html_tags(html: str) -> str:
    """Strip HTML tags to produce plain text (minimal, no BeautifulSoup dependency)."""
    # Remove script/style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block-level elements with newlines
    text = re.sub(r"<(?:br|p|div|h[1-6]|li|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Folder hierarchy → ChapterWise structure mapping
# ---------------------------------------------------------------------------

def relative_folder(file_path: str, root: str) -> str:
    """
    Return the relative folder path of file_path under root,
    or '' if the file is directly in root.
    """
    rel = os.path.relpath(file_path, root)
    folder = os.path.dirname(rel)
    return folder if folder != "." else ""


def folder_to_part(folder: str) -> str | None:
    """Convert a relative folder path to a part label, or None if top-level."""
    if not folder:
        return None
    # Use the top-level directory name as the part
    top = folder.split(os.sep)[0]
    return top


# ---------------------------------------------------------------------------
# File → chapter dict conversion
# ---------------------------------------------------------------------------

def file_to_chapter(file_path: str, root: str, cfg: dict) -> dict:
    """Read a file and produce a codex_writer-compatible chapter dict."""
    raw = read_file(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # For HTML files, strip tags to get plain text
    if ext == ".html":
        raw = strip_html_tags(raw)

    # Parse frontmatter
    fm, body = parse_frontmatter(raw) if cfg.get("preserve_frontmatter", True) else ({}, raw)

    # Derive title: frontmatter > first H1 heading > filename stem
    title = (
        fm.get("title") or fm.get("name") or fm.get("Name") or ""
    )
    if not title:
        h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
    if not title:
        title = os.path.splitext(os.path.basename(file_path))[0]

    # Strip leading H1 from body if it duplicates the title
    body_stripped = re.sub(r"^#\s+.+\n?", "", body, count=1).lstrip("\n")
    if body_stripped.strip():
        body = body_stripped

    # Assign type
    type_mode = cfg.get("type_assignment", "auto")
    doc_type = assign_type(fm, title, body, type_mode)

    # Tags from frontmatter
    tags = fm.get("tags") or fm.get("keywords") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not isinstance(tags, list):
        tags = []

    chapter = {
        "title": title,
        "content": body,
        "word_count": word_count(body),
        "type": doc_type,
        "tags": tags,
    }

    # Mirror structure: preserve relative folder as "part" for folder grouping
    if cfg.get("structure", "mirror") == "mirror":
        part = folder_to_part(relative_folder(file_path, root))
        if part:
            chapter["part"] = part

    # Carry through any extra frontmatter fields that codex_writer understands
    for key in ("target_word_count", "summary", "order"):
        if key in fm and fm[key] is not None:
            try:
                chapter[key] = int(fm[key]) if key in ("target_word_count", "order") else fm[key]
            except (TypeError, ValueError):
                chapter[key] = fm[key]

    return chapter


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full markdown folder import pipeline:
      1. Scan source directory recursively
      2. Identify file types (.md, .txt, .html)
      3. Read existing YAML frontmatter and preserve it
      4. Map folder hierarchy to ChapterWise structure
      5. Assign types based on content or frontmatter
      6. Write output via codex_writer

    Returns the final result dict.
    """
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    if not os.path.isdir(source):
        raise FileNotFoundError(f"Source directory not found: {source}")

    # --- Step 1: Scan directory ---
    emit({"event": "progress", "step": 1, "message": "Scanning source directory"})
    file_paths = scan_directory(
        root=source,
        file_types=cfg.get("file_types", [".md", ".txt", ".html"]),
        recursive=cfg.get("recursive", True),
        ignore_patterns=cfg.get("ignore_patterns", []),
    )
    if not file_paths:
        raise ValueError(
            f"No files matching {cfg.get('file_types')} found in: {source}"
        )
    emit({"event": "progress", "step": 1, "message": f"Found {len(file_paths)} file(s)"})

    # --- Steps 2–5: Read, parse frontmatter, assign types ---
    emit({"event": "progress", "step": 2, "message": "Reading files and mapping structure"})
    chapters = []
    special_sections = []
    special_types = {"prologue", "epilogue"}

    for fp in file_paths:
        chapter = file_to_chapter(fp, source, cfg)
        if chapter["type"] in special_types:
            special_sections.append(chapter)
        else:
            chapters.append(chapter)

    emit({
        "event": "progress",
        "step": 2,
        "message": f"Processed {len(chapters)} chapter(s) and {len(special_sections)} special section(s)",
    })

    # Determine output structure
    structure = cfg.get("structure", "mirror")
    if structure == "mirror":
        # Check if any file has a part — if so, use folders_per_part
        has_parts = any(c.get("part") for c in chapters + special_sections)
        if has_parts:
            structure = "folders_per_part"
        else:
            structure = "flat"

    project_title = os.path.basename(source.rstrip("/\\")) or "Imported Project"

    # --- Step 6: Write output via codex_writer ---
    emit({"event": "progress", "step": 3, "message": "Writing output files"})
    writer_input = {
        "output_dir": output_dir,
        "format": cfg.get("output_format", "markdown"),
        "structure": structure,
        "chapters": chapters,
        "special_sections": special_sections,
        "metadata": {
            "title": project_title,
            "author": "",
            "source_file": source,
            "detection_method": "markdown_folder",
            "word_count": sum(c.get("word_count", 0) for c in chapters + special_sections),
        },
    }
    writer_result = run_common("codex_writer.py", writer_input)

    files_created = writer_result.get("files_created", 0)
    total_words = writer_result.get("total_words", 0)

    emit({"event": "progress", "step": 3, "message": f"Wrote {files_created} files"})

    result = {
        "event": "complete",
        "files": files_created,
        "total_words": total_words,
        "output_dir": output_dir,
    }
    emit(result)
    return result


# ---------------------------------------------------------------------------
# Entry point — supports both stdin JSON mode and CLI mode
# ---------------------------------------------------------------------------

def main() -> int:
    # --- CLI mode: python3 markdown_folder.py source/ output/ ---
    if len(sys.argv) >= 3:
        source = sys.argv[1]
        output_dir = sys.argv[2]
        config = {}
        if len(sys.argv) >= 4:
            try:
                config = json.loads(sys.argv[3])
            except json.JSONDecodeError:
                print(
                    json.dumps({"event": "error", "message": "Third argument is not valid JSON config"}),
                    flush=True,
                )
                return 1
        try:
            convert(source, output_dir, config)
            return 0
        except Exception as exc:
            print(json.dumps({"event": "error", "message": str(exc)}), flush=True)
            return 1

    # --- Stdin JSON mode ---
    raw = sys.stdin.read()
    if not raw.strip():
        print(
            json.dumps({"event": "error", "message": "No input received on stdin"}),
            flush=True,
        )
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"event": "error", "message": f"Invalid JSON input: {exc}"}), flush=True)
        return 1

    source = payload.get("source", "")
    output_dir = payload.get("output_dir", "")
    config = payload.get("config", {})

    if not source:
        print(json.dumps({"event": "error", "message": "Missing 'source' field"}), flush=True)
        return 1
    if not output_dir:
        print(json.dumps({"event": "error", "message": "Missing 'output_dir' field"}), flush=True)
        return 1

    try:
        convert(source, output_dir, config)
        return 0
    except Exception as exc:
        print(json.dumps({"event": "error", "message": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
