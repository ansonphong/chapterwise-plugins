#!/usr/bin/env python3
"""
html_converter.py — Convert HTML files or web page exports into Chapterwise projects.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/file.html", "output_dir": "/path/to/output/"}

    source may also be a directory of .html files.

Optional fields:
    "config": {
        "chapter_pattern": "^Chapter\\s+\\d+",
        "heading_level": "h1",
        "strip_navigation": true,
        "strip_ads": true,
        "extract_images": true,
        "output_format": "markdown",
        "structure": "flat"
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 150, "output_dir": "/path/to/output/"}

CLI usage:
    python3 html_converter.py source.html output/
    python3 html_converter.py /path/to/html/folder/ output/

Library dependency:
    BeautifulSoup 4  (pip install beautifulsoup4)
"""

import json
import os
import re
import subprocess
import sys

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

CONFIG = {
    "chapter_pattern": r"^Chapter\s+\d+",
    "heading_level": "h1",
    "strip_navigation": True,
    "strip_ads": True,
    "extract_images": True,
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
# HTML noise stripping (heuristic)
# ---------------------------------------------------------------------------

# CSS selectors / tag+attribute patterns for elements to remove
NAV_SELECTORS = [
    "nav", "header", "footer",
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    ".nav", ".navigation", ".navbar", ".menu", ".breadcrumb", ".breadcrumbs",
    ".site-header", ".site-footer", ".page-header", ".page-footer",
    "#nav", "#navigation", "#navbar", "#menu", "#header", "#footer",
    "#site-header", "#site-footer",
]

AD_SELECTORS = [
    ".ad", ".ads", ".advert", ".advertisement", ".advertising",
    ".banner", ".sponsored", ".promo", ".promotion",
    "[class*='ad-']", "[id*='ad-']", "[class*='-ad']", "[id*='-ad']",
    "[class*='advert']", "[id*='advert']",
    ".sidebar", "#sidebar",
]


def strip_noise(soup: BeautifulSoup, strip_navigation: bool, strip_ads: bool) -> None:
    """
    Remove navigational and advertising elements from the parsed document in-place.
    """
    selectors = []
    if strip_navigation:
        selectors.extend(NAV_SELECTORS)
    if strip_ads:
        selectors.extend(AD_SELECTORS)

    for selector in selectors:
        for el in soup.select(selector):
            el.decompose()

    # Also strip <script> and <style> blocks regardless of settings
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()


# ---------------------------------------------------------------------------
# HTML → Markdown conversion
# ---------------------------------------------------------------------------

def node_to_markdown(node, extract_images: bool = True) -> str:
    """
    Recursively convert a BeautifulSoup node tree to Markdown text.

    Handles: headings, paragraphs, bold, italic, links, images, lists, tables,
    code blocks, blockquotes, horizontal rules.
    """
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)

    if not isinstance(node, Tag):
        return ""

    tag = node.name.lower() if node.name else ""
    children_md = "".join(node_to_markdown(c, extract_images) for c in node.children)

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        return f"\n\n{'#' * level} {children_md.strip()}\n\n"

    if tag == "p":
        stripped = children_md.strip()
        return f"\n\n{stripped}\n\n" if stripped else ""

    if tag in ("strong", "b"):
        stripped = children_md.strip()
        return f"**{stripped}**" if stripped else ""

    if tag in ("em", "i"):
        stripped = children_md.strip()
        return f"_{stripped}_" if stripped else ""

    if tag == "a":
        href = node.get("href", "").strip()
        text = children_md.strip() or href
        if href:
            return f"[{text}]({href})"
        return text

    if tag == "img":
        if not extract_images:
            return ""
        src = node.get("src", "").strip()
        alt = node.get("alt", "").strip()
        if src:
            return f"![{alt}]({src})"
        return ""

    if tag in ("ul", "ol"):
        items = []
        ordered = tag == "ol"
        for idx, li in enumerate(node.find_all("li", recursive=False), start=1):
            li_md = "".join(node_to_markdown(c, extract_images) for c in li.children).strip()
            prefix = f"{idx}." if ordered else "-"
            items.append(f"{prefix} {li_md}")
        return "\n\n" + "\n".join(items) + "\n\n" if items else ""

    if tag == "li":
        return f"- {children_md.strip()}\n"

    if tag in ("code", "tt"):
        return f"`{children_md}`"

    if tag == "pre":
        inner = node.get_text()
        return f"\n\n```\n{inner}\n```\n\n"

    if tag == "blockquote":
        lines = children_md.strip().splitlines()
        quoted = "\n".join(f"> {line}" for line in lines)
        return f"\n\n{quoted}\n\n"

    if tag == "hr":
        return "\n\n---\n\n"

    if tag in ("br",):
        return "  \n"

    if tag == "table":
        return _table_to_markdown(node)

    if tag in (
        "div", "section", "article", "main", "aside",
        "span", "body", "html", "head", "title",
        "figure", "figcaption", "caption",
        "thead", "tbody", "tfoot", "tr", "td", "th",
    ):
        return children_md

    # Unknown/structural tags — pass through children
    return children_md


def _table_to_markdown(table_node) -> str:
    """Convert an HTML <table> to a Markdown table."""
    rows = table_node.find_all("tr")
    if not rows:
        return ""

    md_rows = []
    for row in rows:
        cells = row.find_all(["th", "td"])
        cell_texts = [c.get_text(separator=" ").strip().replace("|", "\\|") for c in cells]
        md_rows.append("| " + " | ".join(cell_texts) + " |")

    if not md_rows:
        return ""

    # Insert separator after header row
    header = md_rows[0]
    col_count = header.count("|") - 1
    separator = "| " + " | ".join(["---"] * col_count) + " |"
    if len(md_rows) == 1:
        return f"\n\n{header}\n{separator}\n\n"
    return f"\n\n{md_rows[0]}\n{separator}\n" + "\n".join(md_rows[1:]) + "\n\n"


def html_to_markdown(html: str, extract_images: bool = True) -> str:
    """Parse an HTML string and convert its body to Markdown."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup
    md = node_to_markdown(body, extract_images)
    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


# ---------------------------------------------------------------------------
# Structure detection and chapter splitting
# ---------------------------------------------------------------------------

def detect_heading_level(soup: BeautifulSoup, preferred: str) -> str:
    """
    Confirm which heading level is actually present in the document.

    Falls back through h1→h2→h3 if the preferred level has no headings.
    """
    for level in (preferred, "h1", "h2", "h3"):
        if soup.find(level):
            return level
    return preferred


def split_by_headings(soup: BeautifulSoup, heading_level: str, cfg: dict) -> list:
    """
    Split the parsed HTML into chapters by the specified heading level.

    Returns a list of dicts with keys: title, html_content
    """
    headings = soup.find_all(heading_level)
    if not headings:
        # No matching headings found — treat entire body as one chapter
        return [{"title": "Document", "html_content": str(soup)}]

    chapters = []
    chapter_pattern = cfg.get("chapter_pattern", "")
    pattern_re = re.compile(chapter_pattern, re.IGNORECASE) if chapter_pattern else None

    for i, heading in enumerate(headings):
        title = heading.get_text(separator=" ").strip()

        # If a chapter_pattern is set, skip headings that don't match
        if pattern_re and not pattern_re.search(title):
            continue

        # Collect all sibling nodes between this heading and the next
        content_nodes = []
        node = heading.next_sibling
        next_heading = headings[i + 1] if i + 1 < len(headings) else None

        while node is not None:
            if next_heading and node == next_heading:
                break
            if hasattr(node, "name") and node.name == heading_level:
                break
            content_nodes.append(str(node))
            node = node.next_sibling

        html_content = "".join(content_nodes)
        chapters.append({"title": title, "html_content": html_content})

    return chapters if chapters else [{"title": "Document", "html_content": str(soup)}]


def split_single_html(html: str, cfg: dict) -> list:
    """
    Parse a single HTML file and split it into chapter dicts.

    Returns a list of dicts: {title, html_content}
    """
    soup = BeautifulSoup(html, "html.parser")
    strip_noise(soup, cfg.get("strip_navigation", True), cfg.get("strip_ads", True))

    preferred_level = cfg.get("heading_level", "h1")
    actual_level = detect_heading_level(soup, preferred_level)

    chapters = split_by_headings(soup, actual_level, cfg)
    return chapters


# ---------------------------------------------------------------------------
# Source handling — single file vs. folder
# ---------------------------------------------------------------------------

def read_html_file(path: str) -> str:
    """Read an HTML file with encoding detection."""
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as fh:
                return fh.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def collect_html_files(source: str) -> list:
    """
    If source is a single file, return [source].
    If source is a directory, return sorted list of .html/.htm files inside.
    """
    if os.path.isfile(source):
        return [source]
    if os.path.isdir(source):
        files = []
        for entry in sorted(os.listdir(source)):
            if entry.lower().endswith((".html", ".htm")):
                files.append(os.path.join(source, entry))
        return files
    raise FileNotFoundError(f"Source not found: {source}")


# ---------------------------------------------------------------------------
# HTML chapter dict → codex_writer chapter dict
# ---------------------------------------------------------------------------

def html_chapter_to_codex(html_chapter: dict, cfg: dict) -> dict:
    """Convert an HTML chapter dict to a codex_writer-compatible chapter dict."""
    title = html_chapter.get("title", "Untitled")
    html_content = html_chapter.get("html_content", "")

    # Convert HTML fragment to Markdown
    fragment_soup = BeautifulSoup(html_content, "html.parser")
    md = node_to_markdown(fragment_soup, cfg.get("extract_images", True))
    md = re.sub(r"\n{3,}", "\n\n", md).strip()

    # Infer type from title
    title_lower = title.lower()
    if "prologue" in title_lower:
        doc_type = "prologue"
    elif "epilogue" in title_lower:
        doc_type = "epilogue"
    else:
        doc_type = "chapter"

    return {
        "title": title,
        "content": md,
        "word_count": word_count(md),
        "type": doc_type,
        "tags": [],
    }


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full HTML conversion pipeline:
      1. Detect single-file vs multi-file HTML
      2. Parse HTML with BeautifulSoup
      3. Strip navigation, ads, footers (heuristic)
      4. Detect structure from heading hierarchy
      5. Convert HTML to clean Markdown
      6. Write output via codex_writer

    Returns the final result dict.
    """
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    # --- Step 1: Collect HTML files ---
    emit({"event": "progress", "step": 1, "message": "Detecting source structure"})
    html_files = collect_html_files(source)
    if not html_files:
        raise ValueError(f"No HTML files found at: {source}")
    is_multi_file = len(html_files) > 1
    emit({
        "event": "progress",
        "step": 1,
        "message": f"Found {len(html_files)} HTML file(s) ({'multi-file' if is_multi_file else 'single-file'})",
    })

    # --- Steps 2–5: Parse and convert ---
    emit({"event": "progress", "step": 2, "message": "Parsing HTML and detecting structure"})

    all_html_chapters = []

    if is_multi_file:
        # Multi-file: each file is treated as one chapter (named by its <title> or filename)
        for html_file in html_files:
            html = read_html_file(html_file)
            soup = BeautifulSoup(html, "html.parser")
            strip_noise(soup, cfg.get("strip_navigation", True), cfg.get("strip_ads", True))

            # Use <title> tag or filename as chapter title
            title_tag = soup.find("title")
            file_stem = os.path.splitext(os.path.basename(html_file))[0]
            title = title_tag.get_text().strip() if title_tag else file_stem

            body = soup.body or soup
            all_html_chapters.append({"title": title, "html_content": str(body)})
    else:
        # Single file: split by heading hierarchy
        html = read_html_file(html_files[0])
        all_html_chapters = split_single_html(html, cfg)

    emit({
        "event": "progress",
        "step": 2,
        "message": f"Detected {len(all_html_chapters)} chapter(s)",
    })

    emit({"event": "progress", "step": 3, "message": "Converting HTML to Markdown"})
    chapters = []
    special_sections = []
    special_types = {"prologue", "epilogue"}

    for html_ch in all_html_chapters:
        codex_ch = html_chapter_to_codex(html_ch, cfg)
        if codex_ch["type"] in special_types:
            special_sections.append(codex_ch)
        else:
            chapters.append(codex_ch)

    emit({
        "event": "progress",
        "step": 3,
        "message": f"Converted {len(chapters)} chapter(s) and {len(special_sections)} special section(s)",
    })

    # Derive project title
    if os.path.isfile(source):
        project_title = os.path.splitext(os.path.basename(source))[0]
    else:
        project_title = os.path.basename(source.rstrip("/\\")) or "HTML Import"

    # --- Step 6: Write output via codex_writer ---
    emit({"event": "progress", "step": 4, "message": "Writing output files"})
    writer_input = {
        "output_dir": output_dir,
        "format": cfg.get("output_format", "markdown"),
        "structure": cfg.get("structure", "flat"),
        "chapters": chapters,
        "special_sections": special_sections,
        "metadata": {
            "title": project_title,
            "author": "",
            "source_file": source,
            "detection_method": "html_converter",
            "word_count": sum(c.get("word_count", 0) for c in chapters + special_sections),
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
    # --- CLI mode: python3 html_converter.py source.html output/ ---
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
