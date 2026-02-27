#!/usr/bin/env python3
"""
scrivener_converter.py — Convert Scrivener 3 .scriv projects to Chapterwise projects.

JSON-in/JSON-out pattern script.

Input (stdin):
    {"source": "/path/to/Project.scriv", "output_dir": "/path/to/output/"}

Optional fields:
    "config": {
        "preserve_labels": True,
        "preserve_status": True,
        "preserve_keywords_as_tags": True,
        "preserve_synopsis_as_summary": True,
        "skip_non_compile": False,
        "container_types": ["act", "part", "book", "folder"],
        "content_types": ["chapter", "scene", "document"],
        "index_depth": 1,
        "output_format": "markdown",
        "structure": "flat"
    }

Output (stdout):
    {"event": "complete", "files": 3, "total_words": 150, "output_dir": "/path/to/output/"}

CLI usage:
    python3 scrivener_converter.py Project.scriv output/

Scrivener 3 format notes:
    - .scriv is a directory
    - Contains a .scrivx file (XML binder)
    - Document content lives under Files/Data/<uuid>/content.rtf (or content.txt)
    - BinderItem elements carry UUID, Title, Type, and optional MetaData
"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

CONFIG = {
    "preserve_labels": True,
    "preserve_status": True,
    "preserve_keywords_as_tags": True,
    "preserve_synopsis_as_summary": True,
    "skip_non_compile": False,
    "container_types": ["act", "part", "book", "folder"],
    "content_types": ["chapter", "scene", "document"],
    "index_depth": 1,
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
# RTF conversion
# ---------------------------------------------------------------------------

def rtf_to_text(rtf_bytes: bytes) -> str:
    """
    Convert RTF bytes to plain text using striprtf.

    Falls back to a naive regex strip if striprtf is not installed.
    Returns an empty string on any failure.
    """
    try:
        from striprtf.striprtf import rtf_to_text as _rtf_to_text
        # striprtf expects a string, not bytes
        try:
            rtf_str = rtf_bytes.decode("utf-8", errors="replace")
        except Exception:
            rtf_str = rtf_bytes.decode("latin-1", errors="replace")
        return _rtf_to_text(rtf_str)
    except ImportError:
        pass

    # Fallback: naive RTF tag stripping (best-effort)
    try:
        rtf_str = rtf_bytes.decode("utf-8", errors="replace")
    except Exception:
        rtf_str = rtf_bytes.decode("latin-1", errors="replace")

    # Remove RTF header and control words
    text = re.sub(r"\\[a-z]+[-\d]*\s?", " ", rtf_str)
    # Remove braces and remaining backslashes
    text = re.sub(r"[{}\\]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s{2,}", "\n", text)
    return text.strip()


def read_document_content(data_dir: str, uuid_str: str) -> str:
    """
    Read the content of a Scrivener document from its UUID folder.

    Preference order:
      1. content.txt  (plain text, already clean)
      2. content.rtf  (RTF, converted via striprtf)

    Returns empty string if neither file exists or on read error.
    """
    doc_dir = os.path.join(data_dir, uuid_str)

    # Try plain text first
    txt_path = os.path.join(doc_dir, "content.txt")
    if os.path.isfile(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            pass

    # Try RTF
    rtf_path = os.path.join(doc_dir, "content.rtf")
    if os.path.isfile(rtf_path):
        try:
            with open(rtf_path, "rb") as fh:
                raw = fh.read()
            return rtf_to_text(raw)
        except OSError:
            pass

    return ""


# ---------------------------------------------------------------------------
# .scrivx XML parsing
# ---------------------------------------------------------------------------

def find_scrivx(scriv_path: str) -> str:
    """
    Locate the .scrivx file inside the .scriv directory.

    Raises FileNotFoundError if none is found.
    """
    for entry in os.listdir(scriv_path):
        if entry.endswith(".scrivx"):
            return os.path.join(scriv_path, entry)
    raise FileNotFoundError(
        f"No .scrivx file found in {scriv_path}"
    )


def parse_metadata(binder_item: ET.Element) -> dict:
    """
    Extract MetaData from a <BinderItem> element.

    Reads:
      - MetaData/LabelID (label)
      - MetaData/StatusID (status)
      - MetaData/Keywords/Keyword elements (keywords list)
      - MetaData/IncludeInCompile (bool)
      - Synopsis (direct child of BinderItem or under MetaData)

    Returns a dict with any found values.
    """
    meta = {}

    # IncludeInCompile — look in MetaData subtree
    md_el = binder_item.find("MetaData")
    if md_el is not None:
        compile_el = md_el.find("IncludeInCompile")
        if compile_el is not None and compile_el.text is not None:
            meta["include_in_compile"] = compile_el.text.strip().lower() == "yes"

        label_el = md_el.find("LabelID")
        if label_el is not None and label_el.text:
            meta["label"] = label_el.text.strip()

        status_el = md_el.find("StatusID")
        if status_el is not None and status_el.text:
            meta["status"] = status_el.text.strip()

        # Keywords
        keywords = []
        kw_container = md_el.find("Keywords")
        if kw_container is not None:
            for kw_el in kw_container.findall("Keyword"):
                if kw_el.text:
                    keywords.append(kw_el.text.strip())
        if keywords:
            meta["keywords"] = keywords

    # Synopsis — may appear as a direct child or under MetaData
    synopsis_el = binder_item.find("Synopsis")
    if synopsis_el is None and md_el is not None:
        synopsis_el = md_el.find("Synopsis")
    if synopsis_el is not None and synopsis_el.text:
        meta["synopsis"] = synopsis_el.text.strip()

    return meta


def walk_binder(
    binder_item: ET.Element,
    data_dir: str,
    cfg: dict,
    depth: int = 0,
) -> list:
    """
    Recursively walk a <BinderItem> element (and its <Children>) in document
    order, building a flat list of document dicts.

    Each dict contains:
      title, type, uuid, content, word_count, depth,
      and optional: label, status, tags, summary, compile
    """
    items = []

    item_type_raw = binder_item.get("Type", "Text").lower()
    uuid_str = binder_item.get("UUID") or binder_item.get("ID", "")

    title_el = binder_item.find("Title")
    title = title_el.text.strip() if (title_el is not None and title_el.text) else "Untitled"

    metadata = parse_metadata(binder_item)

    # Determine include_in_compile status
    include_in_compile = metadata.get("include_in_compile", True)
    if cfg.get("skip_non_compile") and not include_in_compile:
        return []

    # Classify the binder item
    container_types_lower = [t.lower() for t in cfg.get("container_types", CONFIG["container_types"])]
    content_types_lower = [t.lower() for t in cfg.get("content_types", CONFIG["content_types"])]

    if item_type_raw in ("folder",):
        # Scrivener folders are structural containers
        doc_type = "folder"
    elif item_type_raw in container_types_lower:
        doc_type = item_type_raw
    elif item_type_raw == "text":
        doc_type = "chapter"
    else:
        doc_type = item_type_raw

    # Read actual content for Text items (and folders that also hold content)
    content = ""
    if uuid_str:
        content = read_document_content(data_dir, uuid_str)

    wc = word_count(content)

    # Build document dict
    doc: dict = {
        "title": title,
        "type": doc_type,
        "uuid": uuid_str,
        "content": content,
        "word_count": wc,
        "depth": depth,
        "compile": include_in_compile,
    }

    # Preserve metadata according to config
    if cfg.get("preserve_labels") and "label" in metadata:
        doc["scrivener_label"] = metadata["label"]

    if cfg.get("preserve_status") and "status" in metadata:
        doc["scrivener_status"] = metadata["status"]

    if cfg.get("preserve_keywords_as_tags") and metadata.get("keywords"):
        doc["tags"] = metadata["keywords"]

    if cfg.get("preserve_synopsis_as_summary") and "synopsis" in metadata:
        doc["summary"] = metadata["synopsis"]

    # Only include this item if it has content or is a structural container
    if content.strip() or doc_type in container_types_lower or doc_type == "folder":
        items.append(doc)

    # Recurse into children
    children_el = binder_item.find("Children")
    if children_el is not None:
        for child in children_el.findall("BinderItem"):
            items.extend(walk_binder(child, data_dir, cfg, depth=depth + 1))

    return items


def parse_scrivx(scrivx_path: str, data_dir: str, cfg: dict) -> list:
    """
    Parse the .scrivx XML file and return a flat ordered list of document dicts.

    Only items under the Draft/Manuscript binder section are included (the
    "Draft" folder is the Scrivener compile root). Falls back to the full
    binder if no Draft section is found.
    """
    tree = ET.parse(scrivx_path)
    root = tree.getroot()

    # Locate the Binder element
    binder = root.find("Binder")
    if binder is None:
        raise ValueError(f"No <Binder> element found in {scrivx_path}")

    # Find the Draft/Manuscript folder — Scrivener uses the first folder
    # whose Title is "Draft" or "Manuscript" (localised projects may differ).
    draft_item = None
    for item in binder.findall("BinderItem"):
        title_el = item.find("Title")
        title_text = (title_el.text or "").strip().lower() if title_el is not None else ""
        item_type = item.get("Type", "").lower()
        if item_type == "rootfolder" or title_text in ("draft", "manuscript"):
            draft_item = item
            break

    # If no explicit Draft root found, use the entire binder
    if draft_item is None:
        all_items: list = []
        for item in binder.findall("BinderItem"):
            all_items.extend(walk_binder(item, data_dir, cfg, depth=0))
        return all_items

    # Walk only the Draft section's children
    docs: list = []
    children_el = draft_item.find("Children")
    if children_el is not None:
        for child in children_el.findall("BinderItem"):
            docs.extend(walk_binder(child, data_dir, cfg, depth=0))

    return docs


# ---------------------------------------------------------------------------
# Structure building helpers
# ---------------------------------------------------------------------------

def classify_docs(docs: list, cfg: dict) -> tuple:
    """
    Separate the flat document list into:
      - special_sections: prologue, epilogue, front/back matter
      - chapters: regular content documents

    Returns (special_sections, chapters).
    """
    special_titles = {"prologue", "epilogue", "foreword", "preface", "afterword",
                      "introduction", "conclusion", "author's note", "dedication",
                      "acknowledgements", "acknowledgments"}
    specials = []
    chapters = []

    for doc in docs:
        title_lower = doc.get("title", "").lower()
        if title_lower in special_titles:
            specials.append(doc)
        else:
            chapters.append(doc)

    return specials, chapters


def flatten_for_writer(docs: list) -> list:
    """
    Prepare document dicts for codex_writer.py by ensuring the expected keys
    are present and removing internal-only keys.
    """
    result = []
    for doc in docs:
        item = {
            "title": doc.get("title", "Untitled"),
            "type": doc.get("type", "chapter"),
            "content": doc.get("content", ""),
            "word_count": doc.get("word_count", 0),
        }
        if doc.get("tags"):
            item["tags"] = doc["tags"]
        if doc.get("summary"):
            item["summary"] = doc["summary"]
        if doc.get("scrivener_label"):
            item["scrivener_label"] = doc["scrivener_label"]
        if doc.get("scrivener_status"):
            item["scrivener_status"] = doc["scrivener_status"]
        if "compile" in doc:
            item["compile"] = doc["compile"]
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# Main conversion pipeline
# ---------------------------------------------------------------------------

def convert(source: str, output_dir: str, config: dict) -> dict:
    """
    Full conversion pipeline:
      1. Locate and validate the .scriv directory
      2. Find and parse the .scrivx binder XML
      3. Walk the binder tree, reading RTF/text content
      4. Write output via codex_writer

    Returns the final result dict.
    """
    cfg = {**CONFIG, **config}

    emit({"event": "start", "source": source, "output_dir": output_dir})

    # --- Step 1: Validate source ---
    emit({"event": "progress", "step": 1, "message": "Validating Scrivener project"})

    if not os.path.isdir(source):
        raise FileNotFoundError(
            f"Source is not a directory (expected a .scriv folder): {source}"
        )
    if not source.endswith(".scriv"):
        emit({
            "event": "warning",
            "message": f"Source directory does not end in .scriv: {source}",
        })

    # Locate the data directory
    data_dir = os.path.join(source, "Files", "Data")
    if not os.path.isdir(data_dir):
        # Scrivener 2 used a different layout; emit a warning but continue
        data_dir_alt = os.path.join(source, "Files")
        if os.path.isdir(data_dir_alt):
            data_dir = data_dir_alt
            emit({
                "event": "warning",
                "message": "Using Files/ as data dir (may be Scrivener 2 format)",
            })
        else:
            raise FileNotFoundError(
                f"Could not locate document data directory inside {source}"
            )

    emit({"event": "progress", "step": 1, "message": "Project structure valid"})

    # --- Step 2: Parse .scrivx ---
    emit({"event": "progress", "step": 2, "message": "Parsing .scrivx binder"})
    scrivx_path = find_scrivx(source)
    emit({"event": "progress", "step": 2, "message": f"Found binder: {os.path.basename(scrivx_path)}"})

    docs = parse_scrivx(scrivx_path, data_dir, cfg)
    emit({
        "event": "progress",
        "step": 2,
        "message": f"Parsed {len(docs)} binder items",
    })

    # --- Step 3: Read content ---
    emit({"event": "progress", "step": 3, "message": "Reading document content"})
    total_chars = sum(len(d.get("content", "")) for d in docs)
    emit({
        "event": "progress",
        "step": 3,
        "message": f"Read {total_chars} characters across {len(docs)} documents",
    })

    # --- Classify documents ---
    special_sections, chapters = classify_docs(docs, cfg)

    # Derive project title from the .scriv directory name
    project_title = os.path.splitext(os.path.basename(source.rstrip("/")))[0]

    # Determine output structure
    structure = cfg.get("structure", "flat")

    # --- Step 4: Write output via codex_writer ---
    emit({"event": "progress", "step": 4, "message": "Writing output files"})

    writer_input = {
        "output_dir": output_dir,
        "format": cfg.get("output_format", "markdown"),
        "structure": structure,
        "chapters": flatten_for_writer(chapters),
        "special_sections": flatten_for_writer(special_sections),
        "metadata": {
            "title": project_title,
            "author": "",
            "source_file": source,
            "detection_method": "scrivener_binder",
            "word_count": sum(d.get("word_count", 0) for d in docs),
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
    # --- CLI mode: python3 scrivener_converter.py Project.scriv output/ ---
    if len(sys.argv) >= 3:
        source = sys.argv[1]
        output_dir = sys.argv[2]
        config: dict = {}
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
