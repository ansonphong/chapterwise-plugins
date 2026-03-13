#!/usr/bin/env python3
"""
Location Finder for Chapterwise Insert
Scans directories for codex files, indexes them, and extracts location hints.
The actual semantic matching is done by Claude agents - this script provides helper functions.

Supports include directives: When a codex file contains `include: "./path/to/file.codex.yaml"`
in its children, this module follows those references to build a complete hierarchy.

Usage:
    python location_finder.py scan <directory> [--recursive] [--no-recursive]
    python location_finder.py index <file> [--no-follow-includes]
    python location_finder.py deep <path> [--files-only]
    python location_finder.py hints "instruction text"

Examples:
    python location_finder.py scan . --no-recursive
    python location_finder.py scan /path/to/project
    python location_finder.py index chapter1.codex.yaml
    python location_finder.py index story.codex.yaml --no-follow-includes
    python location_finder.py deep ./manuscript/  # Follow all includes
    python location_finder.py hints "after the hyperborean incursion in chapter 5"
"""

import os
import sys
import re
import json
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# Default directories to skip
DEFAULT_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', '.venv',
    'dist', 'build', '_archive', '.archive', '.claude',
    '.backups', 'backup', 'backups', '.DS_Store'
}


@dataclass
class Candidate:
    """A candidate location for inserting content."""
    file_path: str
    line_number: int
    insert_after: bool = True
    confidence: float = 0.0
    reason: str = ""


@dataclass
class FileIndex:
    """Index information for a codex file."""
    file_path: str
    file_type: str  # 'codex-yaml' or 'codex-lite'
    title: str = ""
    name: str = ""
    summary: str = ""
    body_preview: str = ""
    child_names: List[str] = field(default_factory=list)
    word_count: int = 0
    included_files: List[str] = field(default_factory=list)  # Files referenced via include directives


@dataclass
class LocationHints:
    """Extracted location hints from an instruction."""
    chapter: Optional[str] = None
    section: Optional[str] = None
    scene: Optional[str] = None
    position: Optional[str] = None  # 'after', 'before', 'beginning', 'end'
    keywords: List[str] = field(default_factory=list)
    character_refs: List[str] = field(default_factory=list)
    raw_instruction: str = ""


class LocationFinder:
    """
    Utility class for finding locations in Chapterwise projects.

    Provides helpers for:
    - Scanning directories for codex files
    - Indexing file contents for search
    - Extracting location hints from instructions
    """

    def __init__(self, skip_dirs: Optional[set] = None):
        """
        Initialize the location finder.

        Args:
            skip_dirs: Set of directory names to skip. Uses defaults if None.
        """
        self.skip_dirs = skip_dirs or DEFAULT_SKIP_DIRS
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> List[str]:
        """
        Scan a directory for codex files (.codex.yaml and .md with frontmatter).

        Args:
            directory: Path to directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of file paths found
        """
        root = Path(directory).resolve()

        if not root.exists():
            raise ValueError(f"Directory does not exist: {root}")

        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root}")

        files = []

        if recursive:
            for entry in root.rglob('*'):
                if entry.is_file() and self._should_include_file(entry, root):
                    files.append(str(entry))
        else:
            for entry in root.iterdir():
                if entry.is_file() and self._should_include_file(entry, root):
                    files.append(str(entry))

        # Sort by path for consistent output
        files.sort()
        return files

    def _should_include_file(self, path: Path, root: Path) -> bool:
        """Check if a file should be included in the scan."""
        # Check if any parent directory should be skipped
        for parent in path.relative_to(root).parents:
            if parent.name in self.skip_dirs:
                return False

        # Also check the immediate parent
        if path.parent.name in self.skip_dirs:
            return False

        name = path.name.lower()

        # Include .codex.yaml files
        if name.endswith('.codex.yaml') or name.endswith('.codex.yml'):
            return True

        # Include .md files with frontmatter
        if name.endswith('.md'):
            return self._has_frontmatter(path)

        return False

    def _has_frontmatter(self, path: Path) -> bool:
        """Check if a markdown file has YAML frontmatter."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Read first few bytes to check for frontmatter
                start = f.read(256)

            # Check for frontmatter delimiter
            if start.startswith('---'):
                # Look for closing delimiter
                rest = start[3:]
                if '\n---' in rest or '\r\n---' in rest:
                    return True

            return False

        except Exception:
            return False

    def index_file(
        self,
        file_path: str,
        follow_includes: bool = True
    ) -> Optional[FileIndex]:
        """
        Create a FileIndex from a codex file.

        Args:
            file_path: Path to the file to index
            follow_includes: Whether to follow include directives in YAML codex files

        Returns:
            FileIndex object or None if file cannot be indexed
        """
        path = Path(file_path)

        if not path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return None

        name_lower = path.name.lower()

        if name_lower.endswith('.codex.yaml') or name_lower.endswith('.codex.yml'):
            return self._index_codex_yaml(path, follow_includes=follow_includes)
        elif name_lower.endswith('.md'):
            return self._index_codex_lite(path)
        else:
            self.logger.warning(f"Unsupported file type: {file_path}")
            return None

    def _index_codex_yaml(
        self,
        path: Path,
        follow_includes: bool = True,
        visited: Optional[set] = None
    ) -> Optional[FileIndex]:
        """
        Extract index information from a YAML codex file.

        Args:
            path: Path to the codex file
            follow_includes: Whether to follow include directives
            visited: Set of already-visited paths (for cycle detection)

        Returns:
            FileIndex with child names from both inline children and included files
        """
        try:
            import yaml

            # Cycle detection
            if visited is None:
                visited = set()

            resolved_path = str(path.resolve())
            if resolved_path in visited:
                self.logger.debug(f"Skipping already-visited file: {path}")
                return None
            visited.add(resolved_path)

            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return None

            # Extract fields
            title = data.get('title', '')
            name = data.get('name', '')
            summary = data.get('summary', '')
            body = data.get('body', '')

            # Get body preview (first 500 chars)
            body_preview = body[:500] if body else ''

            # Get child names and resolve includes
            children = data.get('children', [])
            child_names = []
            included_files = []

            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        # Check for include directive
                        include_path = child.get('include')
                        if include_path and follow_includes:
                            # Resolve relative path
                            included_file = self._resolve_include_path(path, include_path)
                            if included_file:
                                included_files.append(str(included_file))
                                # Recursively index the included file
                                included_index = self._index_codex_yaml(
                                    included_file,
                                    follow_includes=True,
                                    visited=visited
                                )
                                if included_index:
                                    # Add the included file's name/title to our children
                                    inc_name = included_index.name or included_index.title
                                    if inc_name:
                                        child_names.append(inc_name)
                                    # Also inherit its children names for deeper hierarchy
                                    child_names.extend(included_index.child_names)
                                    # Track nested includes
                                    included_files.extend(included_index.included_files)
                        else:
                            # Inline child
                            child_name = child.get('name') or child.get('title', '')
                            if child_name:
                                child_names.append(child_name)

            # Calculate word count
            word_count = len(body.split()) if body else 0

            return FileIndex(
                file_path=str(path),
                file_type='codex-yaml',
                title=title,
                name=name,
                summary=summary,
                body_preview=body_preview,
                child_names=child_names,
                word_count=word_count,
                included_files=included_files
            )

        except Exception as e:
            self.logger.warning(f"Failed to index {path}: {e}")
            return None

    def _resolve_include_path(self, parent_path: Path, include_path: str) -> Optional[Path]:
        """
        Resolve an include directive path relative to the parent file.

        Args:
            parent_path: Path to the file containing the include directive
            include_path: The include path (may be relative or absolute)

        Returns:
            Resolved Path or None if file doesn't exist
        """
        try:
            # Handle relative paths
            if include_path.startswith('./') or include_path.startswith('../'):
                resolved = (parent_path.parent / include_path).resolve()
            elif include_path.startswith('/'):
                resolved = Path(include_path)
            else:
                # Assume relative to parent
                resolved = (parent_path.parent / include_path).resolve()

            if resolved.exists():
                return resolved
            else:
                self.logger.debug(f"Include file not found: {include_path} -> {resolved}")
                return None

        except Exception as e:
            self.logger.debug(f"Failed to resolve include path {include_path}: {e}")
            return None

    def _index_codex_lite(self, path: Path) -> Optional[FileIndex]:
        """Extract index information from a Markdown file with frontmatter."""
        try:
            import yaml

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter
            frontmatter = {}
            body = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    fm_text = parts[1].strip()
                    body = parts[2].strip()

                    try:
                        frontmatter = yaml.safe_load(fm_text) or {}
                    except yaml.YAMLError:
                        pass

            # Extract fields
            title = frontmatter.get('title', '')
            name = frontmatter.get('name', '')
            summary = frontmatter.get('summary', '')

            # If no title/name, try to extract from H1
            if not title and not name:
                h1_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
                if h1_match:
                    title = h1_match.group(1).strip()

            # Get body preview (first 500 chars, excluding H1)
            body_for_preview = re.sub(r'^#\s+.+\n*', '', body, count=1).strip()
            body_preview = body_for_preview[:500]

            # No children in markdown format
            child_names = []

            # Calculate word count
            word_count = frontmatter.get('word_count', 0)
            if not word_count:
                word_count = len(body.split()) if body else 0

            return FileIndex(
                file_path=str(path),
                file_type='codex-lite',
                title=title,
                name=name,
                summary=summary,
                body_preview=body_preview,
                child_names=child_names,
                word_count=word_count
            )

        except Exception as e:
            self.logger.warning(f"Failed to index {path}: {e}")
            return None

    def deep_scan_with_includes(
        self,
        entry_point: str,
        follow_includes: bool = True
    ) -> Tuple[List[FileIndex], List[str]]:
        """
        Perform a deep scan starting from an entry point, following all include directives.

        This is useful for manuscripts that use exploded file structure with includes.
        Returns both the indices and a flat list of all file paths in the hierarchy.

        Args:
            entry_point: Path to the root codex file or directory
            follow_includes: Whether to follow include directives

        Returns:
            Tuple of (list of FileIndex objects, list of all file paths)
        """
        entry = Path(entry_point)
        indices = []
        all_files = []
        visited = set()

        if entry.is_dir():
            # Scan directory first
            files = self.scan_directory(str(entry), recursive=True)
            for f in files:
                if f not in visited:
                    visited.add(f)
                    index = self.index_file(f, follow_includes=follow_includes)
                    if index:
                        indices.append(index)
                        all_files.append(f)
                        # Add included files to our list
                        for inc_file in index.included_files:
                            if inc_file not in visited:
                                all_files.append(inc_file)
                                visited.add(inc_file)
        else:
            # Single file - index it and follow includes
            index = self.index_file(str(entry), follow_includes=follow_includes)
            if index:
                indices.append(index)
                all_files.append(str(entry))
                # Include referenced files
                for inc_file in index.included_files:
                    if inc_file not in visited:
                        all_files.append(inc_file)
                        visited.add(inc_file)
                        # Index the included file too
                        inc_index = self.index_file(inc_file, follow_includes=follow_includes)
                        if inc_index:
                            indices.append(inc_index)

        return indices, all_files

    def chunk_files(
        self,
        files: List[str],
        chunk_size: int = 10
    ) -> List[List[str]]:
        """
        Group files into chunks for parallel processing.

        Args:
            files: List of file paths
            chunk_size: Maximum files per chunk

        Returns:
            List of file path lists
        """
        chunks = []
        for i in range(0, len(files), chunk_size):
            chunks.append(files[i:i + chunk_size])
        return chunks

    def format_index_for_search(
        self,
        indices: List[FileIndex],
        include_preview: bool = True,
        include_includes: bool = True
    ) -> str:
        """
        Format file indices for Claude agent search prompts.

        Args:
            indices: List of FileIndex objects
            include_preview: Whether to include body preview
            include_includes: Whether to include list of included files

        Returns:
            Formatted string for agent prompt
        """
        lines = []

        for idx, fi in enumerate(indices, 1):
            lines.append(f"## [{idx}] {fi.title or fi.name or Path(fi.file_path).stem}")
            lines.append(f"File: {fi.file_path}")
            lines.append(f"Type: {fi.file_type}")

            if fi.summary:
                lines.append(f"Summary: {fi.summary}")

            if fi.child_names:
                lines.append(f"Children: {', '.join(fi.child_names)}")

            lines.append(f"Words: {fi.word_count}")

            if include_includes and fi.included_files:
                lines.append(f"Includes: {len(fi.included_files)} file(s)")
                for inc in fi.included_files[:5]:  # Limit to first 5
                    lines.append(f"  - {Path(inc).name}")
                if len(fi.included_files) > 5:
                    lines.append(f"  ... and {len(fi.included_files) - 5} more")

            if include_preview and fi.body_preview:
                preview = fi.body_preview.replace('\n', ' ')[:200]
                lines.append(f"Preview: {preview}...")

            lines.append("")

        return '\n'.join(lines)

    def extract_location_hints(self, instruction: str) -> LocationHints:
        """
        Parse chapter/section/position hints from an instruction.

        Args:
            instruction: Natural language instruction

        Returns:
            LocationHints object with extracted information
        """
        hints = LocationHints(raw_instruction=instruction)
        text = instruction.lower()

        # Extract chapter references
        chapter_patterns = [
            r'chapter\s*(\d+)',
            r'ch\.?\s*(\d+)',
            r'chapter\s+([a-z]+)',  # "chapter one"
        ]
        for pattern in chapter_patterns:
            match = re.search(pattern, text)
            if match:
                hints.chapter = match.group(1)
                break

        # Extract section references
        section_patterns = [
            r'section\s*(\d+)',
            r'sect\.?\s*(\d+)',
            r'part\s*(\d+)',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text)
            if match:
                hints.section = match.group(1)
                break

        # Extract scene references
        scene_patterns = [
            r'scene\s*(\d+)',
            r'scene\s+(?:where|when|with)\s+(.+?)(?:\s+in|\s+at|$)',
        ]
        for pattern in scene_patterns:
            match = re.search(pattern, text)
            if match:
                hints.scene = match.group(1)
                break

        # Extract position hints
        if re.search(r'\b(after|following)\b', text):
            hints.position = 'after'
        elif re.search(r'\b(before|preceding)\b', text):
            hints.position = 'before'
        elif re.search(r'\b(beginning|start|opening)\b', text):
            hints.position = 'beginning'
        elif re.search(r'\b(end|ending|closing|conclusion)\b', text):
            hints.position = 'end'

        # Extract keywords (significant nouns/events)
        # Look for quoted phrases first
        quoted = re.findall(r'"([^"]+)"', instruction)
        hints.keywords.extend(quoted)

        # Look for event-like phrases
        event_patterns = [
            r'the\s+(\w+\s+(?:battle|fight|war|invasion|incursion|attack))',
            r'the\s+(\w+\s+(?:meeting|encounter|conversation|discussion))',
            r'the\s+(\w+\s+(?:scene|moment|event|incident))',
            r'(?:after|before|during)\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ]
        for pattern in event_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and len(match) > 3:
                    hints.keywords.append(match.strip())

        # Extract character references (capitalized names)
        # Look for proper nouns that might be character names
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        potential_names = re.findall(name_pattern, instruction)

        # Filter out common non-name words
        common_words = {'The', 'After', 'Before', 'During', 'When', 'Where',
                       'Chapter', 'Section', 'Scene', 'Part', 'This', 'Insert'}
        for name in potential_names:
            if name not in common_words:
                hints.character_refs.append(name)

        # Deduplicate
        hints.keywords = list(dict.fromkeys(hints.keywords))
        hints.character_refs = list(dict.fromkeys(hints.character_refs))

        return hints


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Location finder for Chapterwise Insert',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scan current directory (non-recursive)
    python location_finder.py scan . --no-recursive

    # Scan recursively
    python location_finder.py scan /path/to/project

    # Index a single file
    python location_finder.py index chapter1.codex.yaml

    # Extract hints from instruction
    python location_finder.py hints "after the hyperborean incursion in chapter 5"
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan directory for codex files')
    scan_parser.add_argument('directory', help='Directory to scan')
    scan_parser.add_argument('-r', '--recursive', action='store_true',
                            default=True, help='Scan recursively (default)')
    scan_parser.add_argument('--no-recursive', action='store_true',
                            help='Only scan top-level directory')
    scan_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index a codex file')
    index_parser.add_argument('file', help='File to index')
    index_parser.add_argument('--json', action='store_true', help='Output as JSON')
    index_parser.add_argument('--no-preview', action='store_true',
                             help='Exclude body preview')
    index_parser.add_argument('--follow-includes', action='store_true', default=True,
                             help='Follow include directives (default: true)')
    index_parser.add_argument('--no-follow-includes', action='store_true',
                             help='Do not follow include directives')

    # Hints command
    hints_parser = subparsers.add_parser('hints', help='Extract location hints from instruction')
    hints_parser.add_argument('instruction', help='Instruction text to parse')
    hints_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Deep scan command
    deep_parser = subparsers.add_parser('deep', help='Deep scan following include directives')
    deep_parser.add_argument('path', help='File or directory to scan')
    deep_parser.add_argument('--json', action='store_true', help='Output as JSON')
    deep_parser.add_argument('--files-only', action='store_true',
                            help='Only output file paths, not full indices')

    # Global options
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(message)s')

    finder = LocationFinder()

    if args.command == 'scan':
        recursive = not args.no_recursive

        try:
            files = finder.scan_directory(args.directory, recursive=recursive)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps({'files': files, 'count': len(files)}, indent=2))
        else:
            print(f"Found {len(files)} codex file(s):\n")
            for f in files:
                print(f"  {f}")

    elif args.command == 'index':
        follow_includes = not getattr(args, 'no_follow_includes', False)
        index = finder.index_file(args.file, follow_includes=follow_includes)

        if index is None:
            print(f"Error: Could not index file: {args.file}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(asdict(index), indent=2))
        else:
            formatted = finder.format_index_for_search(
                [index],
                include_preview=not args.no_preview
            )
            print(formatted)
            # Also show included files if any
            if index.included_files:
                print(f"Included files ({len(index.included_files)}):")
                for inc_file in index.included_files:
                    print(f"  {inc_file}")

    elif args.command == 'hints':
        hints = finder.extract_location_hints(args.instruction)

        if args.json:
            print(json.dumps(asdict(hints), indent=2))
        else:
            print("Location Hints:")
            print(f"  Instruction: {hints.raw_instruction}")
            if hints.chapter:
                print(f"  Chapter: {hints.chapter}")
            if hints.section:
                print(f"  Section: {hints.section}")
            if hints.scene:
                print(f"  Scene: {hints.scene}")
            if hints.position:
                print(f"  Position: {hints.position}")
            if hints.keywords:
                print(f"  Keywords: {', '.join(hints.keywords)}")
            if hints.character_refs:
                print(f"  Characters: {', '.join(hints.character_refs)}")

    elif args.command == 'deep':
        try:
            indices, all_files = finder.deep_scan_with_includes(args.path)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            if args.files_only:
                print(json.dumps({'files': all_files, 'count': len(all_files)}, indent=2))
            else:
                output = {
                    'indices': [asdict(idx) for idx in indices],
                    'all_files': all_files,
                    'file_count': len(all_files),
                    'index_count': len(indices)
                }
                print(json.dumps(output, indent=2))
        else:
            if args.files_only:
                print(f"Deep scan found {len(all_files)} file(s):\n")
                for f in all_files:
                    print(f"  {f}")
            else:
                print(f"Deep scan found {len(indices)} indexed file(s), {len(all_files)} total files:\n")
                formatted = finder.format_index_for_search(indices, include_preview=True)
                print(formatted)
                print("\nAll files in hierarchy:")
                for f in all_files:
                    print(f"  {f}")


if __name__ == '__main__':
    main()
