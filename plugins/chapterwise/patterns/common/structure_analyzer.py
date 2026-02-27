#!/usr/bin/env python3
"""
structure_analyzer.py

JSON-in/JSON-out script that analyzes manuscript structure.

Input (stdin):
    {"text": "...", "format": "plaintext"}

Output (stdout):
    {
        "chapter_count": 3,
        "has_parts": true,
        "part_count": 2,
        "has_prologue": false,
        "has_epilogue": false,
        "word_count": 12,
        "structure_type": "multi_part",
        "special_sections": [],
        "detection_notes": "..."
    }
"""

import json
import re
import sys


# Patterns for detecting structural elements
CHAPTER_PATTERNS = [
    r"^\s*chapter\s+[\divxlcdmIVXLCDM]+\b",         # Chapter 1 / Chapter I
    r"^\s*chapter\s+\w+\b",                           # Chapter One / Chapter Two
    r"^\s*ch\.\s*\d+\b",                              # Ch. 1
    r"^\s*\d+\s*\.\s*[A-Z]",                          # 1. Title
    r"^\s*#+\s+chapter\b",                             # Markdown # Chapter
]

PART_PATTERNS = [
    r"^\s*part\s+[\divxlcdmIVXLCDM]+\b",             # Part I / Part 1
    r"^\s*part\s+\w+\b",                              # Part One / Part Two
    r"^\s*book\s+[\divxlcdmIVXLCDM]+\b",             # Book I / Book 1
    r"^\s*volume\s+[\divxlcdmIVXLCDM]+\b",           # Volume I / Volume 1
    r"^\s*section\s+[\divxlcdmIVXLCDM]+\b",          # Section I / Section 1
]

ACT_PATTERNS = [
    r"^\s*act\s+[\divxlcdmIVXLCDM]+\b",              # Act 1 / Act I
    r"^\s*act\s+\w+\b",                               # Act One / Act Two
]

SPECIAL_SECTION_PATTERNS = {
    "prologue":       r"^\s*prologue\b",
    "epilogue":       r"^\s*epilogue\b",
    "foreword":       r"^\s*foreword\b",
    "afterword":      r"^\s*afterword\b",
    "dedication":     r"^\s*dedication\b",
    "about_author":   r"^\s*about\s+the\s+author\b",
    "acknowledgements": r"^\s*acknowledgements?\b",
    "introduction":   r"^\s*introduction\b",
    "preface":        r"^\s*preface\b",
    "appendix":       r"^\s*appendix\b",
}


def compile_patterns(patterns):
    return [re.compile(p, re.IGNORECASE) for p in patterns]


COMPILED_CHAPTER = compile_patterns(CHAPTER_PATTERNS)
COMPILED_PART = compile_patterns(PART_PATTERNS)
COMPILED_ACT = compile_patterns(ACT_PATTERNS)
COMPILED_SPECIAL = {
    key: re.compile(pat, re.IGNORECASE)
    for key, pat in SPECIAL_SECTION_PATTERNS.items()
}


def matches_any(line, compiled_list):
    return any(pat.match(line) for pat in compiled_list)


def analyze_structure(text):
    """Analyze the structure of a manuscript text."""
    if not text or not text.strip():
        return {
            "chapter_count": 0,
            "has_parts": False,
            "part_count": 0,
            "has_prologue": False,
            "has_epilogue": False,
            "word_count": 0,
            "structure_type": "flat",
            "special_sections": [],
            "detection_notes": "Empty or blank text provided.",
        }

    lines = text.splitlines()

    chapter_count = 0
    part_lines = []
    act_lines = []
    found_special = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if matches_any(stripped, COMPILED_CHAPTER):
            chapter_count += 1
            continue

        if matches_any(stripped, COMPILED_PART):
            part_lines.append(stripped)
            continue

        if matches_any(stripped, COMPILED_ACT):
            act_lines.append(stripped)
            continue

        for key, pat in COMPILED_SPECIAL.items():
            if pat.match(stripped):
                found_special.add(key)
                break

    part_count = len(part_lines)
    act_count = len(act_lines)
    has_parts = part_count > 0
    has_acts = act_count > 0

    has_prologue = "prologue" in found_special
    has_epilogue = "epilogue" in found_special

    special_sections = sorted(found_special)

    # Rough word count from whitespace-split tokens
    word_count = len(text.split())

    # Determine structure type
    if has_acts and act_count >= 2:
        structure_type = "three_act"
    elif has_parts and part_count >= 2:
        structure_type = "multi_part"
    elif chapter_count > 0:
        structure_type = "flat"
    elif special_sections or chapter_count == 0:
        structure_type = "custom"
    else:
        structure_type = "flat"

    # Build detection notes
    notes_parts = []
    if has_parts:
        notes_parts.append(f"Found {part_count} parts with Part pattern.")
    if has_acts:
        notes_parts.append(f"Found {act_count} acts with Act pattern.")
    if chapter_count > 0:
        notes_parts.append(f"{chapter_count} chapter{'s' if chapter_count != 1 else ''} detected.")
    else:
        notes_parts.append("No chapters detected.")
    if special_sections:
        notes_parts.append(
            f"Special sections: {', '.join(special_sections)}."
        )

    detection_notes = " ".join(notes_parts) if notes_parts else "No structural elements found."

    return {
        "chapter_count": chapter_count,
        "has_parts": has_parts,
        "part_count": part_count,
        "has_prologue": has_prologue,
        "has_epilogue": has_epilogue,
        "word_count": word_count,
        "structure_type": structure_type,
        "special_sections": special_sections,
        "detection_notes": detection_notes,
    }


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            raise ValueError("No input received on stdin.")
        # First try strict parse; if it fails due to literal (raw) newlines
        # embedded inside a JSON string (common when piped from shell echo),
        # fall back to a lenient parse that allows control characters.
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = json.loads(raw, strict=False)
    except json.JSONDecodeError as exc:
        error = {"error": f"Invalid JSON input: {exc}"}
        sys.stdout.write(json.dumps(error) + "\n")
        sys.exit(1)
    except ValueError as exc:
        error = {"error": str(exc)}
        sys.stdout.write(json.dumps(error) + "\n")
        sys.exit(1)

    text = data.get("text", "")
    # "format" key is accepted but currently only plaintext processing is done
    # future formats (e.g. markdown, docx-extracted) can be handled here

    result = analyze_structure(text)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
