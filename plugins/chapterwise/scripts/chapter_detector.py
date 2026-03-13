#!/usr/bin/env python3
"""
chapter_detector.py — Thin wrapper for the import command.

Accepts the path-based stdin interface used by import.md and delegates
to the real implementation in patterns/common/chapter_detector.py.

Input  (stdin):  {"path": "/path/to/file", "format": "plaintext", "hints": {"pattern": "..."}}
Output (stdout): JSON chapter detection result
"""

import json
import os
import sys

# Resolve the patterns/common directory relative to this script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_ROOT = os.path.dirname(_SCRIPT_DIR)
_COMMON_DIR = os.path.join(_PLUGIN_ROOT, "patterns", "common")

# Add patterns/common to the import path so we can import the real module
sys.path.insert(0, _COMMON_DIR)

from chapter_detector import detect_chapters  # noqa: E402


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            raise ValueError("No input received on stdin.")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = json.loads(raw, strict=False)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    path = data.get("path", "")
    if not path:
        print(json.dumps({"error": "Missing 'path' in input."}))
        sys.exit(1)

    if not os.path.exists(path):
        print(json.dumps({"error": f"File not found: {path}"}))
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except (IOError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read file: {exc}"}))
        sys.exit(1)

    hints = data.get("hints", {})
    result = detect_chapters(text, hints)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
