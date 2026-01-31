#!/usr/bin/env python3
"""
Location Finder for Chapterwise Insert
Scans directories for codex files, indexes them, and extracts location hints.
The actual semantic matching is done by Claude agents - this script provides helper functions.

Usage:
    python location_finder.py scan <directory> [--recursive] [--no-recursive]
    python location_finder.py index <file>
    python location_finder.py hints "instruction text"

Examples:
    python location_finder.py scan . --no-recursive
    python location_finder.py scan /path/to/project
    python location_finder.py index chapter1.codex.yaml
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

    def index_file(self, file_path: str) -> Optional[FileIndex]:
        """
        Create a FileIndex from a codex file.

        Args:
            file_path: Path to the file to index

        Returns:
            FileIndex object or None if file cannot be indexed
        """
        path = Path(file_path)

        if not path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return None

        name_lower = path.name.lower()

        if name_lower.endswith('.codex.yaml') or name_lower.endswith('.codex.yml'):
            return self._index_codex_yaml(path)
        elif name_lower.endswith('.md'):
            return self._index_codex_lite(path)
        else:
            self.logger.warning(f"Unsupported file type: {file_path}")
            return None

    def _index_codex_yaml(self, path: Path) -> Optional[FileIndex]:
        """Extract index information from a YAML codex file."""
        try:
            import yaml

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

            # Get child names
            children = data.get('children', [])
            child_names = []
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
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
                word_count=word_count
            )

        except Exception as e:
            self.logger.warning(f"Failed to index {path}: {e}")
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
        include_preview: bool = True
    ) -> str:
        """
        Format file indices for Claude agent search prompts.

        Args:
            indices: List of FileIndex objects
            include_preview: Whether to include body preview

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

    # Hints command
    hints_parser = subparsers.add_parser('hints', help='Extract location hints from instruction')
    hints_parser.add_argument('instruction', help='Instruction text to parse')
    hints_parser.add_argument('--json', action='store_true', help='Output as JSON')

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
        index = finder.index_file(args.file)

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


if __name__ == '__main__':
    main()
