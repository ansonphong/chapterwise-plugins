#!/usr/bin/env python3
"""
Discovers and loads analysis modules from:
1. Built-in: ${CLAUDE_PLUGIN_ROOT}/modules/
2. User global: ~/.claude/analyze/modules/
3. Project: ./.chapterwise/analysis-modules/
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def parse_module_frontmatter(filepath: Path) -> Optional[Dict]:
    """Parse YAML frontmatter from a module markdown file."""
    content = filepath.read_text()
    if not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    try:
        metadata = yaml.safe_load(parts[1])
        metadata['_filepath'] = str(filepath)
        metadata['_content'] = parts[2].strip()
        return metadata
    except yaml.YAMLError:
        return None


def discover_modules(plugin_root: str = None) -> Dict[str, Dict]:
    """
    Discover all available modules from all paths.
    Later paths override earlier (project > user > built-in).
    """
    modules = {}

    search_paths = []

    # 1. Built-in modules
    if plugin_root:
        search_paths.append(Path(plugin_root) / 'modules')

    # 2. User global modules
    user_modules = Path.home() / '.claude' / 'analyze' / 'modules'
    if user_modules.exists():
        search_paths.append(user_modules)

    # 3. Project modules
    project_modules = Path.cwd() / '.chapterwise' / 'analysis-modules'
    if project_modules.exists():
        search_paths.append(project_modules)

    for search_path in search_paths:
        if not search_path.exists():
            continue
        for md_file in search_path.glob('*.md'):
            if md_file.name.startswith('_'):
                continue  # Skip partials like _output-format.md

            metadata = parse_module_frontmatter(md_file)
            if metadata and 'name' in metadata:
                modules[metadata['name']] = metadata

    return modules


def list_modules(plugin_root: str = None) -> List[Dict]:
    """Return list of modules sorted by category then name."""
    modules = discover_modules(plugin_root)
    module_list = list(modules.values())

    return sorted(module_list, key=lambda m: (
        m.get('category', 'Other'),
        m.get('name', '')
    ))


def get_module(name: str, plugin_root: str = None) -> Optional[Dict]:
    """Get a specific module by name."""
    modules = discover_modules(plugin_root)
    return modules.get(name)


if __name__ == '__main__':
    import sys
    import json

    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '.')

    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            modules = list_modules(plugin_root)
            print(json.dumps(modules, indent=2))
        elif sys.argv[1] == 'get' and len(sys.argv) > 2:
            module = get_module(sys.argv[2], plugin_root)
            if module:
                print(json.dumps(module, indent=2))
            else:
                print(f"Module '{sys.argv[2]}' not found", file=sys.stderr)
                sys.exit(1)
    else:
        print("Usage: module_loader.py list | get <name>")
