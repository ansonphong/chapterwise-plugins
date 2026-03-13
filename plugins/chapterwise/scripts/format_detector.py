#!/usr/bin/env python3
"""
Format Detector — Detect manuscript source format.

Usage:
  echo '{"path": "/path/to/file.pdf"}' | python3 format_detector.py

Output:
  {"format": "pdf", "confidence": 0.99, "details": {"extension": ".pdf", "size_bytes": 2450000}}

All input via stdin JSON, all output via stdout JSON.
"""
import json
import sys
import os

FORMAT_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".scriv": "scrivener",
    ".ulyz": "ulysses",
    ".md": "markdown",
    ".txt": "plaintext",
    ".html": "html",
    ".htm": "html",
    ".rtf": "rtf",
    ".epub": "epub",
    ".fdx": "final_draft",
    ".fountain": "fountain",
    ".latex": "latex",
    ".tex": "latex",
    ".odt": "opendocument",
}


def detect(path):
    """Detect the format of a file or directory."""
    if os.path.isdir(path):
        # Scrivener project (.scriv is a directory)
        if path.endswith(".scriv") or any(
            f.endswith(".scrivx") for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
        ):
            return {"format": "scrivener", "confidence": 0.99, "details": {"type": "directory"}}
        # Ulysses archive
        if path.endswith(".ulyz"):
            return {"format": "ulysses", "confidence": 0.99, "details": {"type": "directory"}}
        # Folder of markdown/text files
        files = os.listdir(path)
        md_count = len([f for f in files if f.endswith((".md", ".txt"))])
        html_count = len([f for f in files if f.endswith((".html", ".htm"))])
        if md_count > 0:
            return {"format": "markdown_folder", "confidence": 0.8, "details": {"file_count": md_count, "type": "directory"}}
        if html_count > 0:
            return {"format": "html_folder", "confidence": 0.7, "details": {"file_count": html_count, "type": "directory"}}
        return {"format": "unknown", "confidence": 0.0, "details": {"type": "directory"}}

    # File-based detection
    _, ext = os.path.splitext(path.lower())
    fmt = FORMAT_MAP.get(ext)

    if fmt:
        details = {"extension": ext}
        if os.path.exists(path):
            details["size_bytes"] = os.path.getsize(path)
        return {"format": fmt, "confidence": 0.95, "details": details}

    # Magic bytes fallback for files without recognized extensions
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                header = f.read(8)
            if header.startswith(b"%PDF"):
                return {"format": "pdf", "confidence": 0.99, "details": {"detected_by": "magic_bytes"}}
            if header.startswith(b"PK"):
                # ZIP-based — could be DOCX, EPUB, ODT
                return {"format": "docx", "confidence": 0.7, "details": {"detected_by": "magic_bytes", "note": "ZIP-based format — could be DOCX, EPUB, or ODT"}}
            if header.startswith(b"{\\rtf"):
                return {"format": "rtf", "confidence": 0.95, "details": {"detected_by": "magic_bytes"}}
        except (IOError, OSError):
            pass

    return {"format": "unknown", "confidence": 0.0, "details": {"extension": ext}}


if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = detect(data["path"])
    print(json.dumps(result, indent=2))
