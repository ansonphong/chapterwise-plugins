#!/usr/bin/env python3
"""
chapter_detector.py — Detect chapter boundaries in text.

Input  (stdin):  {"text": "...", "hints": {"pattern": "^Chapter \\d+"}}
Output (stdout): {"chapters": [...], "detection_method": "...", "confidence": 0.0}
"""

import json
import re
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Pattern definitions (in priority order for auto-detection)
# ---------------------------------------------------------------------------

HEADING_PATTERNS: list[tuple[str, str, float]] = [
    # (regex, type-label, confidence)
    (r"^Chapter\s+\d+[.:)—\-]?\s*.*$",          "chapter",  0.98),
    (r"^CHAPTER\s+\d+[.:)—\-]?\s*.*$",           "chapter",  0.98),
    (r"^Chapter\s+[IVXLCDM]+[.:)—\-]?\s*.*$",    "chapter",  0.97),
    (r"^CHAPTER\s+[IVXLCDM]+[.:)—\-]?\s*.*$",    "chapter",  0.97),
    (r"^[IVXLCDM]{1,6}[.:)—\-]\s+.*$",           "chapter",  0.90),
    (r"^\d+\.\s+[A-Z].*$",                        "chapter",  0.85),
    (r"^Part\s+(?:\d+|[IVXLCDM]+)[.:)—\-]?\s*.*$", "section", 0.92),
    (r"^PART\s+(?:\d+|[IVXLCDM]+)[.:)—\-]?\s*.*$", "section", 0.92),
]

SPECIAL_SECTION_PATTERNS: list[tuple[str, str, float]] = [
    (r"^Prologue\b.*$",    "prologue",  0.96),
    (r"^PROLOGUE\b.*$",   "prologue",  0.96),
    (r"^Epilogue\b.*$",    "epilogue",  0.96),
    (r"^EPILOGUE\b.*$",   "epilogue",  0.96),
    (r"^Preface\b.*$",     "section",   0.88),
    (r"^Introduction\b.*$","section",   0.85),
    (r"^Afterword\b.*$",   "section",   0.88),
    (r"^Appendix\b.*$",    "section",   0.88),
]

SEPARATOR_PATTERN = re.compile(
    r"^(?:-{3,}|\*{3,}|={3,}|_{3,}|\f)$",
    re.MULTILINE,
)

BLANK_LINE_CLUSTER_RE = re.compile(r"(\n[ \t]*){3,}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chapter(
    start: int,
    end: int,
    title: str,
    confidence: float,
    chapter_type: str = "chapter",
) -> dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "title": title,
        "confidence": confidence,
        "type": chapter_type,
    }


def _infer_title(line: str) -> str:
    """Return a cleaned title from a heading line."""
    return line.strip()


def _avg_confidence(chapters: list[dict[str, Any]]) -> float:
    if not chapters:
        return 0.0
    return round(sum(c["confidence"] for c in chapters) / len(chapters), 4)


# ---------------------------------------------------------------------------
# Detection strategies
# ---------------------------------------------------------------------------

def _detect_with_custom_pattern(text: str, pattern: str) -> list[dict[str, Any]] | None:
    """Use a caller-supplied regex to find chapter boundaries."""
    try:
        rx = re.compile(pattern, re.MULTILINE)
    except re.error:
        return None

    matches = list(rx.finditer(text))
    if not matches:
        return None

    chapters: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(0).strip()
        chapters.append(_make_chapter(start, end, title, 0.90, "chapter"))

    # Prepend any text before the first match as an implicit section
    if matches[0].start() > 0:
        chapters.insert(
            0,
            _make_chapter(0, matches[0].start(), "(preamble)", 0.70, "section"),
        )

    return chapters or None


def _detect_heading_patterns(text: str) -> list[dict[str, Any]] | None:
    """Try all heading + special-section patterns, pick best set."""
    all_patterns = HEADING_PATTERNS + SPECIAL_SECTION_PATTERNS

    # Collect every match across all patterns
    raw: list[tuple[int, str, float, str]] = []  # (char_offset, title, conf, type)
    for pattern_str, ptype, conf in all_patterns:
        rx = re.compile(pattern_str, re.MULTILINE)
        for m in rx.finditer(text):
            raw.append((m.start(), m.group(0).strip(), conf, ptype))

    if not raw:
        return None

    # Deduplicate by offset (keep highest-confidence hit per offset)
    by_offset: dict[int, tuple[str, float, str]] = {}
    for offset, title, conf, ptype in raw:
        if offset not in by_offset or conf > by_offset[offset][1]:
            by_offset[offset] = (title, conf, ptype)

    sorted_offsets = sorted(by_offset)
    chapters: list[dict[str, Any]] = []

    # Prepend preamble if first heading doesn't start at 0
    if sorted_offsets[0] > 0:
        chapters.append(_make_chapter(0, sorted_offsets[0], "(preamble)", 0.70, "section"))

    for i, offset in enumerate(sorted_offsets):
        title, conf, ptype = by_offset[offset]
        end = sorted_offsets[i + 1] if i + 1 < len(sorted_offsets) else len(text)
        chapters.append(_make_chapter(offset, end, title, conf, ptype))

    return chapters or None


def _detect_separator_patterns(text: str) -> list[dict[str, Any]] | None:
    """Split on visual separator lines (---, ***, ===, form feeds)."""
    matches = list(SEPARATOR_PATTERN.finditer(text))
    if not matches:
        return None

    boundaries = [0] + [m.end() for m in matches] + [len(text)]
    chapters: list[dict[str, Any]] = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        chunk = text[start:end].strip()
        if not chunk:
            continue
        # Try to find a title from the first non-empty line of the chunk
        first_line = chunk.split("\n", 1)[0].strip()
        title = first_line if first_line else f"Section {i + 1}"
        chapters.append(_make_chapter(start, end, title, 0.80, "section"))

    return chapters if len(chapters) > 1 else None


def _detect_blank_line_clusters(text: str) -> list[dict[str, Any]] | None:
    """Split on 3+ consecutive blank lines."""
    matches = list(BLANK_LINE_CLUSTER_RE.finditer(text))
    if not matches:
        return None

    boundaries = [0] + [m.end() for m in matches] + [len(text)]
    chapters: list[dict[str, Any]] = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        chunk = text[start:end].strip()
        if not chunk:
            continue
        first_line = chunk.split("\n", 1)[0].strip()
        title = first_line[:80] if first_line else f"Section {i + 1}"
        chapters.append(_make_chapter(start, end, title, 0.65, "section"))

    return chapters if len(chapters) > 1 else None


def _fallback(text: str) -> list[dict[str, Any]]:
    """Return the entire text as a single chapter."""
    first_line = text.strip().split("\n", 1)[0].strip() if text.strip() else "(empty)"
    title = first_line[:80] if first_line else "(empty)"
    return [_make_chapter(0, len(text), title, 0.50, "chapter")]


# ---------------------------------------------------------------------------
# Main detection dispatcher
# ---------------------------------------------------------------------------

def detect_chapters(text: str, hints: dict[str, Any] | None = None) -> dict[str, Any]:
    if not text:
        return {
            "chapters": [],
            "detection_method": "none",
            "confidence": 0.0,
        }

    hints = hints or {}
    chapters: list[dict[str, Any]] | None = None
    method = "fallback"

    # 1. Caller-supplied regex hint
    if "pattern" in hints:
        chapters = _detect_with_custom_pattern(text, hints["pattern"])
        if chapters:
            method = "custom_pattern"

    # 2. Heading patterns (Chapter N, Roman numerals, numbered sections, etc.)
    if chapters is None:
        chapters = _detect_heading_patterns(text)
        if chapters:
            method = "heading_pattern"

    # 3. Visual separator lines
    if chapters is None:
        chapters = _detect_separator_patterns(text)
        if chapters:
            method = "separator_pattern"

    # 4. Blank-line clusters
    if chapters is None:
        chapters = _detect_blank_line_clusters(text)
        if chapters:
            method = "blank_line_cluster"

    # 5. Fallback
    if chapters is None:
        chapters = _fallback(text)
        method = "fallback"

    return {
        "chapters": chapters,
        "detection_method": method,
        "confidence": _avg_confidence(chapters),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            payload: dict[str, Any] = {}
        else:
            # Use strict=False so raw control characters (e.g. bare \n from shells
            # that expand \n inside echo) are tolerated inside JSON strings.
            payload = json.loads(raw, strict=False)
    except json.JSONDecodeError as exc:
        result = {
            "error": f"Invalid JSON input: {exc}",
            "chapters": [],
            "detection_method": "none",
            "confidence": 0.0,
        }
        print(json.dumps(result))
        sys.exit(1)

    text: str = payload.get("text", "")
    hints: dict[str, Any] = payload.get("hints", {})

    result = detect_chapters(text, hints)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
