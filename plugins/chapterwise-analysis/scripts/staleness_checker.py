#!/usr/bin/env python3
"""
Computes sourceHash for staleness detection.
Checks if existing analysis is fresh or stale.
"""
import hashlib
import yaml
from pathlib import Path
from typing import Optional, Tuple


def compute_source_hash(content: str) -> str:
    """Compute SHA-256 hash, return first 16 chars."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def get_analysis_file_path(source_path: Path) -> Path:
    """Convert source.codex.yaml -> source.analysis.codex.yaml"""
    name = source_path.name
    if name.endswith('.codex.yaml'):
        new_name = name.replace('.codex.yaml', '.analysis.codex.yaml')
    elif name.endswith('.codex.json'):
        new_name = name.replace('.codex.json', '.analysis.codex.json')
    else:
        new_name = name + '.analysis.yaml'
    return source_path.parent / new_name


def get_current_source_hash(source_path: Path) -> Optional[str]:
    """Read source file and compute its hash."""
    if not source_path.exists():
        return None
    content = source_path.read_text()
    return compute_source_hash(content)


def get_analysis_source_hash(analysis_path: Path) -> Optional[str]:
    """Read sourceHash from existing analysis file."""
    if not analysis_path.exists():
        return None

    try:
        content = yaml.safe_load(analysis_path.read_text())
        return content.get('sourceHash')
    except (yaml.YAMLError, AttributeError):
        return None


def get_module_latest_hash(analysis_path: Path, module_name: str) -> Optional[str]:
    """Get the sourceHash from the latest run of a specific module."""
    if not analysis_path.exists():
        return None

    try:
        content = yaml.safe_load(analysis_path.read_text())
        for child in content.get('children', []):
            if child.get('name') == module_name:
                history = child.get('history', [])
                if history:
                    return history[0].get('sourceHash')
        return None
    except (yaml.YAMLError, AttributeError, TypeError):
        return None


def is_analysis_stale(source_path: Path, module_name: str = None) -> Tuple[bool, str, Optional[str]]:
    """
    Check if analysis is stale for a source file.

    Returns: (is_stale, current_hash, existing_hash)
    """
    analysis_path = get_analysis_file_path(source_path)
    current_hash = get_current_source_hash(source_path)

    if current_hash is None:
        return (True, None, None)

    if module_name:
        existing_hash = get_module_latest_hash(analysis_path, module_name)
    else:
        existing_hash = get_analysis_source_hash(analysis_path)

    is_stale = current_hash != existing_hash
    return (is_stale, current_hash, existing_hash)


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: staleness_checker.py <source_file> [module_name]")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    module_name = sys.argv[2] if len(sys.argv) > 2 else None

    is_stale, current, existing = is_analysis_stale(source_path, module_name)

    result = {
        'source': str(source_path),
        'module': module_name,
        'isStale': is_stale,
        'currentHash': current,
        'existingHash': existing,
        'analysisFile': str(get_analysis_file_path(source_path))
    }
    print(json.dumps(result, indent=2))
