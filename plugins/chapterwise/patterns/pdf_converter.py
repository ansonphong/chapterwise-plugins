#!/usr/bin/env python3
"""
pdf_converter.py — Convert PDF files into Chapterwise projects.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/novel.pdf", "output_dir": "/path/to/output/"}

Optional fields:
    "config": {
        "chapter_pattern": "^Chapter\\s+\\d+",
        "part_pattern": null,
        "page_header_pattern": "^\\d+$",
        "page_footer_pattern": null,
        "skip_pages": [1, 2],
        "min_chapter_words": 500,
        "special_sections": ["Prologue", "Epilogue"],
        "skip_sections": ["Dedication", "About the Author"],
        "output_format": "markdown",
        "structure": "flat"
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 15000, "output_dir": "/path/to/output/"}

CLI usage:
    python3 pdf_converter.py source.pdf output/
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
    "page_header_pattern": r"^\d+$",
    "page_footer_pattern": None,
    "skip_pages": [1, 2],
    "min_chapter_words": 500,
    "special_sections": ["Prologue", "Epilogue"],
    "skip_sections": ["Dedication", "About the Author"],
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
# PDF text extraction
# ---------------------------------------------------------------------------

def _is_two_column(blocks: list) -> bool:
    """
    Heuristically detect two-column layout by inspecting x-positions of text
    blocks. If there are two clear clusters of x-origins separated by a gap,
    the page is likely two-column.

    Args:
        blocks: list of block dicts from page.get_text("dict")["blocks"]

    Returns:
        True if two-column layout is detected.
    """
    x_origins = []
    for block in blocks:
        if block.get("type") != 0:  # 0 = text block
            continue
        x0 = block.get("bbox", (0, 0, 0, 0))[0]
        x_origins.append(x0)

    if len(x_origins) < 4:
        return False

    x_origins_sorted = sorted(x_origins)
    page_width_approx = max(x_origins_sorted) if x_origins_sorted else 0
    if page_width_approx < 100:
        return False

    midpoint = page_width_approx / 2

    left_blocks = [x for x in x_origins if x < midpoint * 0.6]
    right_blocks = [x for x in x_origins if x > midpoint * 0.5]

    # Both columns should have a meaningful number of blocks
    if len(left_blocks) >= 2 and len(right_blocks) >= 2:
        # Check that right column starts well to the right of the left column
        if right_blocks and left_blocks:
            min_right = min(right_blocks)
            max_left = max(left_blocks)
            if min_right > max_left * 1.4:
                return True

    return False


def _extract_two_column_text(blocks: list) -> str:
    """
    Extract text from a two-column page by sorting blocks into left and right
    columns and reading each column top-to-bottom before concatenating.

    Args:
        blocks: list of block dicts from page.get_text("dict")["blocks"]

    Returns:
        Combined text with left column followed by right column.
    """
    text_blocks = [b for b in blocks if b.get("type") == 0]
    if not text_blocks:
        return ""

    x_origins = [b["bbox"][0] for b in text_blocks]
    midpoint = (max(x_origins) + min(x_origins)) / 2

    left_col = sorted(
        [b for b in text_blocks if b["bbox"][0] < midpoint],
        key=lambda b: b["bbox"][1],
    )
    right_col = sorted(
        [b for b in text_blocks if b["bbox"][0] >= midpoint],
        key=lambda b: b["bbox"][1],
    )

    def blocks_to_text(col_blocks: list) -> str:
        lines = []
        for block in col_blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                line_text = "".join(span.get("text", "") for span in spans)
                lines.append(line_text)
        return "\n".join(lines)

    left_text = blocks_to_text(left_col)
    right_text = blocks_to_text(right_col)
    combined = left_text
    if right_text:
        combined = combined + "\n" + right_text if combined else right_text
    return combined


def _line_matches_pattern(line: str, pattern: str) -> bool:
    """Return True if the stripped line matches the given regex pattern."""
    if not pattern:
        return False
    try:
        return bool(re.match(pattern, line.strip()))
    except re.error:
        return False


def extract_text_from_pdf(pdf_path: str, cfg: dict) -> tuple:
    """
    Open a PDF and extract plain text, stripping headers, footers, and page
    numbers. Returns a tuple of (full_text, metadata_dict, is_scanned).

    Two-column pages are handled by reading columns left-to-right.
    Images on purely-image pages trigger an OCR notice.

    Args:
        pdf_path:  Path to the PDF file.
        cfg:       Merged config dict.

    Returns:
        (text, metadata, is_scanned)
        text        — extracted text as a single string
        metadata    — dict with title/author/subject/creator
        is_scanned  — True if the PDF appears to contain scanned (image-only) pages
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF conversion. "
            "Install it with: pip install pymupdf"
        ) from exc

    skip_pages = set(cfg.get("skip_pages") or [])
    header_pattern = cfg.get("page_header_pattern") or ""
    footer_pattern = cfg.get("page_footer_pattern") or ""

    doc = fitz.open(pdf_path)

    # --- Extract document metadata ---
    raw_meta = doc.metadata or {}
    metadata = {
        "title": raw_meta.get("title", "") or "",
        "author": raw_meta.get("author", "") or "",
        "subject": raw_meta.get("subject", "") or "",
        "creator": raw_meta.get("creator", "") or "",
    }

    pages_text = []
    is_scanned = False
    scanned_page_count = 0

    for page_num, page in enumerate(doc, start=1):
        # Skip explicitly listed pages (1-based)
        if page_num in skip_pages:
            continue

        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        # Detect scanned pages: no text blocks but has image blocks
        text_blocks = [b for b in blocks if b.get("type") == 0]
        image_blocks = [b for b in blocks if b.get("type") == 1]
        raw_text_on_page = page.get_text("text").strip()

        if not raw_text_on_page and image_blocks:
            scanned_page_count += 1
            continue

        # Two-column layout detection
        if _is_two_column(blocks):
            page_text = _extract_two_column_text(blocks)
        else:
            page_text = page.get_text("text")

        # Strip headers and footers line by line
        lines = page_text.splitlines()
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if header_pattern and _line_matches_pattern(stripped, header_pattern):
                continue
            if footer_pattern and _line_matches_pattern(stripped, footer_pattern):
                continue
            cleaned_lines.append(line)

        pages_text.append("\n".join(cleaned_lines))

    doc.close()

    if scanned_page_count > 0:
        is_scanned = True

    full_text = "\n".join(pages_text)
    return full_text, metadata, is_scanned


def extract_images_from_pdf(pdf_path: str, assets_dir: str) -> list:
    """
    Extract embedded images from the PDF into the assets/ subdirectory.

    Returns a list of relative paths to saved images.

    Args:
        pdf_path:   Path to the PDF file.
        assets_dir: Directory where images will be saved.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []

    os.makedirs(assets_dir, exist_ok=True)
    saved = []

    doc = fitz.open(pdf_path)
    img_index = 0

    for page_num, page in enumerate(doc, start=1):
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            img_bytes = base_image.get("image")
            img_ext = base_image.get("ext", "png")
            if not img_bytes:
                continue

            img_index += 1
            filename = f"image_{page_num:04d}_{img_index:04d}.{img_ext}"
            img_path = os.path.join(assets_dir, filename)

            try:
                with open(img_path, "wb") as fh:
                    fh.write(img_bytes)
                saved.append(os.path.join("assets", filename))
            except OSError:
                continue

    doc.close()
    return saved


# ---------------------------------------------------------------------------
# Chapter extraction (mirrors plaintext_converter logic)
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

        lines = raw.splitlines()
        title_line = ch.get("title", "").strip()

        first_nonempty_idx = None
        for idx, line in enumerate(lines):
            if line.strip():
                first_nonempty_idx = idx
                break

        if first_nonempty_idx is not None:
            first_line = lines[first_nonempty_idx].strip()
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

        if any(skip in title_lower for skip in skip_lower):
            continue

        ch_type = ch.get("type", "chapter")

        if ch_type in special_types or ch.get("title", "") == "(preamble)":
            if ch.get("word_count", 0) > 0:
                specials.append(ch)
        else:
            if ch.get("word_count", 0) >= min_words:
                regulars.append(ch)

    return specials, regulars


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full PDF conversion pipeline:
      1. Open PDF and extract text (with header/footer stripping, two-column support)
      2. Extract embedded images to assets/
      3. Detect chapters (chapter_detector)
      4. Analyse structure (structure_analyzer)
      5. Write output (codex_writer)

    Returns the final result dict.
    """
    # --- Merge user config over defaults ---
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    # --- Step 1: Open PDF and extract text ---
    emit({"event": "progress", "step": 1, "message": "Opening PDF"})

    if not os.path.isfile(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    try:
        import fitz as _fitz  # noqa: F401 — check availability early
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF conversion. "
            "Install it with: pip install pymupdf"
        )

    text, pdf_metadata, is_scanned = extract_text_from_pdf(source, cfg)

    if is_scanned:
        emit({
            "event": "warning",
            "message": (
                "This PDF appears to contain scanned (image-only) pages. "
                "Install pytesseract for OCR support."
            ),
        })

    emit({
        "event": "progress",
        "step": 1,
        "message": f"Extracted {len(text)} characters from PDF",
    })

    # --- Step 1b: Extract embedded images ---
    assets_dir = os.path.join(output_dir, "assets")
    emit({"event": "progress", "step": 1, "message": "Extracting embedded images"})
    saved_images = extract_images_from_pdf(source, assets_dir)
    if saved_images:
        emit({
            "event": "progress",
            "step": 1,
            "message": f"Saved {len(saved_images)} image(s) to assets/",
        })

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
        min_words=cfg.get("min_chapter_words", 500),
        skip_sections=cfg.get("skip_sections", []),
    )

    # Derive project title: prefer PDF metadata title, fall back to filename stem
    project_title = (
        pdf_metadata.get("title", "").strip()
        or os.path.splitext(os.path.basename(source))[0]
    )
    project_author = pdf_metadata.get("author", "").strip()

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
            "author": project_author,
            "source_file": source,
            "detection_method": detection_method,
            "word_count": structure_result.get("word_count", word_count(text)),
            "pdf_subject": pdf_metadata.get("subject", ""),
            "pdf_creator": pdf_metadata.get("creator", ""),
        },
    }
    writer_result = run_common("codex_writer.py", writer_input)

    files_created = writer_result.get("files_created", 0)
    total_words = writer_result.get("total_words", 0)

    # Account for any extracted image files
    if saved_images:
        files_created += len(saved_images)

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
    # --- CLI mode: python3 pdf_converter.py source.pdf output/ ---
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
