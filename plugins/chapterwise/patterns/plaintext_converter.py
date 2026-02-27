#!/usr/bin/env python3
"""
plaintext_converter.py — Convert plain text files into Chapterwise projects.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/novel.txt", "output_dir": "/path/to/output/"}

Optional fields:
    "config": {
        "chapter_pattern": "^Chapter\\s+\\d+",
        "part_pattern": null,
        "special_sections": ["Prologue", "Epilogue"],
        "skip_sections": [],
        "output_format": "markdown",
        "structure": "flat",
        "min_chapter_words": 50
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 150, "output_dir": "/path/to/output/"}

CLI usage:
    python3 plaintext_converter.py source.txt output/
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
    "chapter_pattern": r"^Chapter\s+\d+",
    "part_pattern": None,
    "special_sections": ["Prologue", "Epilogue"],
    "skip_sections": [],
    "output_format": "markdown",
    "structure": "flat",
    "min_chapter_words": 1,
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


def read_text_file(path: str) -> str:
    """Read a text file, detecting encoding with a fallback to utf-8."""
    # Try common encodings in order
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as fh:
                return fh.read()
        except (UnicodeDecodeError, LookupError):
            continue
    # Final fallback: replace undecodable bytes
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def run_common(script_name: str, input_data: dict) -> dict:
    """
    Call one of the common/ utility scripts via subprocess.

    Args:
        script_name: filename inside common/, e.g. "chapter_detector.py"
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


def word_count(text: str) -> int:
    """Return a rough word count for the given text."""
    return len(text.split())


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug (mirrors codex_writer logic)."""
    slug = re.sub(r"[()&,.\[\]+]", "", title)
    slug = slug.replace(" ", "-")
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.lower().strip("-")
    return slug


# ---------------------------------------------------------------------------
# Chapter extraction
# ---------------------------------------------------------------------------

def extract_chapter_content(text: str, chapters: list) -> list:
    """
    Given detected chapter metadata (with start/end byte offsets) and the
    original text, attach 'content' and 'word_count' to each chapter dict.
    Returns a new list of enriched chapter dicts.
    """
    enriched = []
    for ch in chapters:
        start = ch.get("start", 0)
        end = ch.get("end", len(text))
        raw = text[start:end]

        # Strip the heading line itself from the body so the .md file starts
        # with body prose rather than repeating the title.
        lines = raw.splitlines()
        title_line = ch.get("title", "").strip()

        # The first non-empty line is always the heading — strip it.
        # Use the full first line as the chapter title (the detector may only
        # have captured a prefix like "Chapter 1" when the line reads
        # "Chapter 1: The Beginning").
        first_nonempty_idx = None
        for idx, line in enumerate(lines):
            if line.strip():
                first_nonempty_idx = idx
                break

        if first_nonempty_idx is not None:
            first_line = lines[first_nonempty_idx].strip()
            # Prefer the full first line as title when the detected title is
            # a proper prefix of it (e.g. custom_pattern matched "Chapter 1"
            # but the full line is "Chapter 1: The Beginning").
            if first_line.startswith(title_line):
                title_line = first_line
            body_lines = lines[first_nonempty_idx + 1:]
        else:
            body_lines = lines

        content = "\n".join(body_lines).strip()

        enriched.append({
            **ch,
            "title": title_line,
            "content": content,
            "word_count": word_count(content),
        })
    return enriched


def filter_chapters(chapters: list, min_words: int, skip_sections: list) -> tuple:
    """
    Split the detected chapters into:
      - special_sections: prologue, epilogue, etc. that should be treated separately
      - regular_chapters: chapters that meet the min word threshold

    skip_sections is a list of title substrings to ignore entirely.
    """
    special_types = {"prologue", "epilogue", "section"}
    specials = []
    regulars = []

    skip_lower = [s.lower() for s in (skip_sections or [])]

    for ch in chapters:
        title_lower = ch.get("title", "").lower()

        # Check skip list
        if any(skip in title_lower for skip in skip_lower):
            continue

        ch_type = ch.get("type", "chapter")

        if ch_type in special_types or ch.get("title", "") == "(preamble)":
            # Only keep specials that have meaningful content
            if ch.get("word_count", 0) > 0:
                specials.append(ch)
        else:
            # Apply minimum word filter to regular chapters
            if ch.get("word_count", 0) >= min_words:
                regulars.append(ch)

    return specials, regulars


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full conversion pipeline:
      1. Read source file
      2. Detect chapters (chapter_detector)
      3. Analyse structure (structure_analyzer)
      4. Write output (codex_writer)

    Returns the final result dict.
    """
    # --- Merge user config over defaults ---
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    # --- Step 1: Read source ---
    emit({"event": "progress", "step": 1, "message": "Reading source file"})
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Source file not found: {source}")
    text = read_text_file(source)
    emit({"event": "progress", "step": 1, "message": f"Read {len(text)} characters"})

    # --- Step 2: Detect chapters ---
    emit({"event": "progress", "step": 2, "message": "Detecting chapters"})
    hints = {}
    if cfg.get("chapter_pattern"):
        hints["pattern"] = cfg["chapter_pattern"]

    detector_input = {"text": text, "hints": hints}
    detector_result = run_common("chapter_detector.py", detector_input)

    raw_chapters = detector_result.get("chapters", [])
    detection_method = detector_result.get("detection_method", "unknown")
    emit({
        "event": "progress",
        "step": 2,
        "message": f"Detected {len(raw_chapters)} sections via '{detection_method}'",
    })

    # Enrich chapters with actual content
    enriched = extract_chapter_content(text, raw_chapters)

    # --- Step 3: Analyse structure ---
    emit({"event": "progress", "step": 3, "message": "Analysing structure"})
    structure_result = run_common(
        "structure_analyzer.py",
        {"text": text, "format": "plaintext"},
    )
    emit({
        "event": "progress",
        "step": 3,
        "message": structure_result.get("detection_notes", ""),
    })

    # --- Filter chapters ---
    special_sections, chapters = filter_chapters(
        enriched,
        min_words=cfg.get("min_chapter_words", 50),
        skip_sections=cfg.get("skip_sections", []),
    )

    # Derive project title from the source filename (stem)
    project_title = os.path.splitext(os.path.basename(source))[0]

    # Infer structure from analysis result
    structure = cfg.get("structure", "flat")
    if structure_result.get("has_parts") and structure_result.get("part_count", 0) >= 2:
        structure = "folders_per_part"

    # --- Step 4: Write output via codex_writer ---
    emit({"event": "progress", "step": 4, "message": "Writing output files"})

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
            "detection_method": detection_method,
            "word_count": structure_result.get("word_count", word_count(text)),
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
    # --- CLI mode: python3 plaintext_converter.py source.txt output/ ---
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
