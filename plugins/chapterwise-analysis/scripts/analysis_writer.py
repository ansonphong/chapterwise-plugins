#!/usr/bin/env python3
"""
Writes analysis results to .analysis.codex.yaml files.
Handles history management with configurable depth.
"""
import uuid
import yaml
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Add scripts directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))
from staleness_checker import get_analysis_file_path, compute_source_hash

DEFAULT_HISTORY_DEPTH = 3


def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())


def create_analysis_file_structure(source_path: Path, source_hash: str) -> Dict:
    """Create initial structure for a new analysis file."""
    return {
        'metadata': {
            'formatVersion': '1.2',
            'documentVersion': '1.0.0',
        },
        'id': generate_uuid(),
        'type': 'analysis-collection',
        'sourceFile': f'./{source_path.name}',
        'sourceHash': source_hash,
        'children': []
    }


def create_analysis_entry(
    module_name: str,
    source_hash: str,
    model: str,
    body: str,
    summary: str = '',
    children: list = None,
    tags: list = None,
    attributes: list = None
) -> Dict:
    """Create a single analysis history entry."""
    entry = {
        'id': generate_uuid(),
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'sourceHash': source_hash,
        'model': model,
        'body': body,
    }
    if summary:
        entry['summary'] = summary
    if children:
        entry['children'] = children
    if tags:
        entry['tags'] = tags
    if attributes:
        entry['attributes'] = attributes
    return entry


def add_analysis_result(
    source_path: Path,
    module_name: str,
    analysis_content: Dict[str, Any],
    model: str = 'claude-sonnet-4',
    history_depth: int = DEFAULT_HISTORY_DEPTH
) -> Path:
    """
    Add analysis result to the .analysis.codex.yaml file.
    Creates file if doesn't exist, prepends to module history.
    """
    analysis_path = get_analysis_file_path(source_path)
    source_content = source_path.read_text()
    source_hash = compute_source_hash(source_content)

    # Load or create analysis file
    if analysis_path.exists():
        data = yaml.safe_load(analysis_path.read_text()) or {}
    else:
        data = create_analysis_file_structure(source_path, source_hash)

    # Update root sourceHash
    data['sourceHash'] = source_hash

    # Find or create module entry
    module_entry = None
    for child in data.get('children', []):
        if child.get('name') == module_name:
            module_entry = child
            break

    if module_entry is None:
        module_entry = {
            'id': generate_uuid(),
            'type': 'analysis-module',
            'name': module_name,
            'history': []
        }
        data.setdefault('children', []).append(module_entry)

    # Create new analysis entry
    new_entry = create_analysis_entry(
        module_name=module_name,
        source_hash=source_hash,
        model=model,
        body=analysis_content.get('body', ''),
        summary=analysis_content.get('summary', ''),
        children=analysis_content.get('children', []),
        tags=analysis_content.get('tags', []),
        attributes=analysis_content.get('attributes', [])
    )

    # Prepend to history and trim to depth
    history = module_entry.get('history', [])
    history.insert(0, new_entry)
    module_entry['history'] = history[:history_depth]

    # Write file with proper YAML formatting
    analysis_path.write_text(yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120
    ))

    return analysis_path


if __name__ == '__main__':
    import json

    if len(sys.argv) < 4:
        print("Usage: analysis_writer.py <source_file> <module_name> <analysis_json>")
        print("       analysis_writer.py <source_file> <module_name> - (reads from stdin)")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    module_name = sys.argv[2]

    if sys.argv[3] == '-':
        analysis_json = sys.stdin.read()
    else:
        analysis_json = sys.argv[3]

    analysis_content = json.loads(analysis_json)

    output_path = add_analysis_result(source_path, module_name, analysis_content)
    print(f"Written to: {output_path}")
