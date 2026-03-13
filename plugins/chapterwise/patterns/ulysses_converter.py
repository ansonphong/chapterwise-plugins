#!/usr/bin/env python3
"""
ulysses_converter.py — Convert Ulysses writing app exports into Chapterwise projects.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/export/", "output_dir": "/path/to/output/"}

Optional fields:
    "config": {
        "preserve_keywords": true,
        "preserve_writing_goals": true,
        "groups_as_folders": true,
        "convert_annotations_to_comments": true,
        "handle_marked_text": "bold",
        "output_format": "markdown",
        "structure": "flat"
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 150, "output_dir": "/path/to/output/"}

CLI usage:
    python3 ulysses_converter.py /path/to/ulysses/export/ output/

Supported export formats:
    - .textbundle     (directory with text.md + assets/)
    - .ulyz           (ZIP archive containing TextBundles)
    - Markdown folder (directory of .md files, as exported by Ulysses)
"""

import json
import os
import re
import subprocess
import sys
import zipfile

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

CONFIG = {
    "preserve_keywords": True,
    "preserve_writing_goals": True,
    "groups_as_folders": True,
    "convert_annotations_to_comments": True,
    "handle_marked_text": "bold",
    "output_format": "markdown",
    "structure": "flat",
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
# Ulysses markup conversion
# ---------------------------------------------------------------------------

def convert_annotations(text: str) -> str:
    """
    Convert Ulysses annotation markup to HTML comments.
    ::annotation text:: → <!-- annotation text -->
    """
    return re.sub(r"::(.*?)::", lambda m: f"<!-- {m.group(1).strip()} -->", text)


def convert_marked_text(text: str, style: str) -> str:
    """
    Convert Ulysses marked text ||marked|| to bold or highlight.

    style="bold"      → **marked**
    style="highlight" → ==marked==  (works in many markdown flavours)
    style="italic"    → _marked_
    """
    if style == "bold":
        return re.sub(r"\|\|(.*?)\|\|", r"**\1**", text)
    if style == "highlight":
        return re.sub(r"\|\|(.*?)\|\|", r"==\1==", text)
    if style == "italic":
        return re.sub(r"\|\|(.*?)\|\|", r"_\1_", text)
    # Default: bold
    return re.sub(r"\|\|(.*?)\|\|", r"**\1**", text)


def convert_ulysses_markup(text: str, cfg: dict) -> str:
    """Apply all Ulysses-specific markup conversions."""
    if cfg.get("convert_annotations_to_comments", True):
        text = convert_annotations(text)
    handle_marked = cfg.get("handle_marked_text", "bold")
    text = convert_marked_text(text, handle_marked)
    return text


# ---------------------------------------------------------------------------
# Export format detection and reading
# ---------------------------------------------------------------------------

def detect_export_format(source: str) -> str:
    """
    Detect the Ulysses export format from the source path.

    Returns one of: "textbundle", "ulyz", "markdown_folder"
    """
    if os.path.isfile(source) and source.endswith(".ulyz"):
        return "ulyz"
    if os.path.isdir(source) and source.endswith(".textbundle"):
        return "textbundle"
    if os.path.isdir(source):
        return "markdown_folder"
    raise ValueError(
        f"Cannot detect Ulysses export format for: {source}\n"
        "Expected a .textbundle directory, .ulyz file, or a folder of .md files."
    )


def read_info_json(path: str) -> dict:
    """Read an info.json metadata file if it exists, return {} otherwise."""
    info_path = os.path.join(path, "info.json")
    if os.path.isfile(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def read_textbundle(bundle_path: str) -> dict:
    """
    Read a single .textbundle directory.

    Returns a dict with keys: title, content, keywords, writing_goal
    """
    # The main content file is text.md (or occasionally text.markdown)
    content = ""
    for candidate in ("text.md", "text.markdown", "text.txt"):
        candidate_path = os.path.join(bundle_path, candidate)
        if os.path.isfile(candidate_path):
            with open(candidate_path, "r", encoding="utf-8") as fh:
                content = fh.read()
            break

    info = read_info_json(bundle_path)
    title = info.get("title", os.path.basename(bundle_path).replace(".textbundle", ""))
    keywords = info.get("keywords", [])
    writing_goal = info.get("writingGoal", {})

    return {
        "title": title,
        "content": content,
        "keywords": keywords if isinstance(keywords, list) else [],
        "writing_goal": writing_goal if isinstance(writing_goal, dict) else {},
    }


def read_ulyz_archive(ulyz_path: str) -> list:
    """
    Extract and read sheets from a .ulyz ZIP archive.

    Returns a list of sheet dicts (same structure as read_textbundle).
    """
    sheets = []
    with zipfile.ZipFile(ulyz_path, "r") as zf:
        names = zf.namelist()
        # Find all info.json files to enumerate TextBundles inside the archive
        info_files = [n for n in names if n.endswith("/info.json") or n == "info.json"]
        bundle_dirs = set()
        for info_file in info_files:
            bundle_dirs.add(os.path.dirname(info_file))

        if not bundle_dirs:
            # Fallback: treat .md files at the top level as sheets
            md_files = sorted(n for n in names if n.endswith(".md"))
            for md_file in md_files:
                with zf.open(md_file) as fh:
                    content = fh.read().decode("utf-8", errors="replace")
                title = os.path.splitext(os.path.basename(md_file))[0]
                sheets.append({"title": title, "content": content, "keywords": [], "writing_goal": {}})
            return sheets

        for bundle_dir in sorted(bundle_dirs):
            info_path = f"{bundle_dir}/info.json" if bundle_dir else "info.json"
            info = {}
            if info_path in names:
                with zf.open(info_path) as fh:
                    try:
                        info = json.load(fh)
                    except json.JSONDecodeError:
                        pass

            title = info.get("title", bundle_dir.split("/")[-1].replace(".textbundle", ""))
            keywords = info.get("keywords", [])
            writing_goal = info.get("writingGoal", {})

            content = ""
            for candidate in ("text.md", "text.markdown", "text.txt"):
                candidate_path = f"{bundle_dir}/{candidate}" if bundle_dir else candidate
                if candidate_path in names:
                    with zf.open(candidate_path) as fh:
                        content = fh.read().decode("utf-8", errors="replace")
                    break

            sheets.append({
                "title": title,
                "content": content,
                "keywords": keywords if isinstance(keywords, list) else [],
                "writing_goal": writing_goal if isinstance(writing_goal, dict) else {},
            })
    return sheets


def read_markdown_folder(folder_path: str) -> list:
    """
    Read a folder of .md files exported by Ulysses.

    Returns a list of sheet dicts.
    """
    sheets = []
    try:
        entries = sorted(os.listdir(folder_path))
    except OSError:
        return sheets

    for entry in entries:
        if not entry.endswith((".md", ".markdown")):
            continue
        file_path = os.path.join(folder_path, entry)
        if not os.path.isfile(file_path):
            continue
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        title = os.path.splitext(entry)[0]
        sheets.append({"title": title, "content": content, "keywords": [], "writing_goal": {}})
    return sheets


# ---------------------------------------------------------------------------
# Sheet → chapter dict conversion
# ---------------------------------------------------------------------------

def sheet_to_chapter(sheet: dict, cfg: dict) -> dict:
    """Convert a Ulysses sheet dict into a codex_writer chapter dict."""
    content = convert_ulysses_markup(sheet.get("content", ""), cfg)

    # Strip a leading H1 that duplicates the title (common in Ulysses exports)
    title = sheet.get("title", "Untitled")
    lines = content.splitlines()
    if lines and lines[0].strip().lstrip("# ").strip() == title.strip():
        content = "\n".join(lines[1:]).lstrip("\n")

    tags = []
    if cfg.get("preserve_keywords", True):
        tags = sheet.get("keywords", [])

    chapter = {
        "title": title,
        "content": content,
        "word_count": word_count(content),
        "type": "chapter",
        "tags": tags,
    }

    # Embed writing goal as target_word_count metadata
    if cfg.get("preserve_writing_goals", True):
        writing_goal = sheet.get("writing_goal", {})
        goal_words = writing_goal.get("words") or writing_goal.get("goalValue")
        if goal_words:
            try:
                chapter["target_word_count"] = int(goal_words)
            except (TypeError, ValueError):
                pass

    return chapter


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full Ulysses conversion pipeline:
      1. Detect export format
      2. Read sheet content
      3. Convert Ulysses-specific markup
      4. Preserve metadata (keywords, writing goals)
      5. Write output via codex_writer

    Returns the final result dict.
    """
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    # --- Step 1: Detect export format ---
    emit({"event": "progress", "step": 1, "message": "Detecting Ulysses export format"})
    fmt = detect_export_format(source)
    emit({"event": "progress", "step": 1, "message": f"Detected format: {fmt}"})

    # --- Step 2: Read sheets ---
    emit({"event": "progress", "step": 2, "message": "Reading sheet content"})
    if fmt == "textbundle":
        sheets = [read_textbundle(source)]
    elif fmt == "ulyz":
        sheets = read_ulyz_archive(source)
    else:  # markdown_folder
        sheets = read_markdown_folder(source)

    if not sheets:
        raise ValueError(f"No readable sheets found in: {source}")
    emit({"event": "progress", "step": 2, "message": f"Read {len(sheets)} sheet(s)"})

    # --- Step 3 & 4: Convert markup and build chapter dicts ---
    emit({"event": "progress", "step": 3, "message": "Converting Ulysses markup and preserving metadata"})
    chapters = [sheet_to_chapter(s, cfg) for s in sheets]
    emit({"event": "progress", "step": 3, "message": f"Converted {len(chapters)} chapter(s)"})

    # Derive project title from source path
    project_title = os.path.splitext(os.path.basename(source.rstrip("/")))[0]

    # --- Step 5: Write output via codex_writer ---
    emit({"event": "progress", "step": 4, "message": "Writing output files"})
    writer_input = {
        "output_dir": output_dir,
        "format": cfg.get("output_format", "markdown"),
        "structure": cfg.get("structure", "flat"),
        "chapters": chapters,
        "special_sections": [],
        "metadata": {
            "title": project_title,
            "author": "",
            "source_file": source,
            "detection_method": f"ulysses_{fmt}",
            "word_count": sum(c.get("word_count", 0) for c in chapters),
        },
    }
    writer_result = run_common("codex_writer.py", writer_input)

    files_created = writer_result.get("files_created", 0)
    total_words = writer_result.get("total_words", 0)

    emit({"event": "progress", "step": 4, "message": f"Wrote {files_created} files"})

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
    # --- CLI mode: python3 ulysses_converter.py source output/ ---
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
