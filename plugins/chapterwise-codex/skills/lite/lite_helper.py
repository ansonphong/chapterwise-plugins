"""
Codex Lite Helper - Validate and fix Markdown frontmatter
Ensures Codex Lite files have proper YAML frontmatter.

Usage:
    python lite_helper.py <file_or_directory> [--recursive] [--dry-run] [--init]

Examples:
    python lite_helper.py document.md
    python lite_helper.py /path/to/docs --recursive
    python lite_helper.py document.md --init  # Add frontmatter to bare markdown
"""

import os
import sys
import re
import uuid
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class CodexLiteHelper:
    """
    Helper for Codex Lite (Markdown with YAML frontmatter) files.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.fixes_applied = []

    def process_file(
        self,
        file_path: str,
        dry_run: bool = False,
        init_frontmatter: bool = False
    ) -> Tuple[str, List[str]]:
        """
        Process a Codex Lite file, fixing frontmatter issues.

        Args:
            file_path: Path to markdown file
            dry_run: If True, don't write changes
            init_frontmatter: If True, add frontmatter to bare markdown

        Returns:
            Tuple of (fixed_text, list_of_fixes)
        """
        self.fixes_applied = []

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.suffix.lower() == '.md':
            raise ValueError(f"Not a markdown file: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Extract or create frontmatter
        frontmatter, body = self._extract_frontmatter(text)

        # Handle bare markdown (no frontmatter)
        if not frontmatter:
            if init_frontmatter:
                frontmatter = {}
                self.fixes_applied.append("Initialized empty frontmatter")
            else:
                # No frontmatter and not initializing - just return as-is
                return text, []

        # Fix missing/invalid fields
        frontmatter = self._fix_frontmatter(frontmatter, body, path)

        # Calculate word count
        word_count = self._count_words(body)
        if frontmatter.get('word_count') != word_count:
            old_count = frontmatter.get('word_count')
            frontmatter['word_count'] = word_count
            if old_count is None:
                self.fixes_applied.append(f"Added word_count: {word_count}")
            else:
                self.fixes_applied.append(f"Updated word_count: {old_count} -> {word_count}")

        # Serialize back
        fixed_text = self._serialize(frontmatter, body)

        # Write if not dry run
        if not dry_run and self.fixes_applied:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(fixed_text)

        return fixed_text, self.fixes_applied

    def _extract_frontmatter(self, text: str) -> Tuple[Optional[Dict], str]:
        """Extract YAML frontmatter from markdown text."""
        import yaml

        trimmed = text.lstrip()

        if not trimmed.startswith('---'):
            return None, text

        # Find closing delimiter
        after_first = trimmed[3:]
        end_idx = after_first.find('\n---')

        if end_idx == -1:
            return None, text

        fm_text = after_first[:end_idx]
        body_start = 3 + end_idx + 4
        body = trimmed[body_start:].strip()

        try:
            frontmatter = yaml.safe_load(fm_text) or {}
            return frontmatter, body
        except yaml.YAMLError:
            return None, text

    def _fix_frontmatter(self, fm: Dict, body: str, path: Path) -> Dict:
        """Fix common frontmatter issues."""

        # Fix missing id
        if 'id' not in fm:
            fm['id'] = str(uuid.uuid4())
            self.fixes_applied.append(f"Added id: {fm['id']}")
        elif not self._is_valid_uuid(str(fm['id'])):
            old_id = fm['id']
            fm['id'] = str(uuid.uuid4())
            self.fixes_applied.append(f"Fixed invalid id: {old_id} -> {fm['id']}")

        # Fix missing name
        if 'name' not in fm and 'title' not in fm:
            # Try to extract from H1
            h1 = self._extract_h1(body)
            if h1:
                fm['name'] = h1
                self.fixes_applied.append(f"Added name from H1: {h1}")
            else:
                # Fall back to filename
                name = path.stem
                fm['name'] = name
                self.fixes_applied.append(f"Added name from filename: {name}")

        # Fix missing type
        if 'type' not in fm:
            fm['type'] = 'document'
            self.fixes_applied.append("Added type: document")

        return fm

    def _extract_h1(self, text: str) -> Optional[str]:
        """Extract first H1 heading from markdown."""
        match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len([w for w in text.split() if w])

    def _is_valid_uuid(self, s: str) -> bool:
        """Check if string is valid UUID v4."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(pattern, s.lower()))

    def _serialize(self, frontmatter: Dict, body: str) -> str:
        """Serialize frontmatter and body back to markdown."""
        import yaml

        if not frontmatter:
            return body

        # Order frontmatter fields nicely
        ordered = {}
        field_order = ['type', 'name', 'title', 'id', 'summary', 'tags', 'status',
                       'featured', 'author', 'last_updated', 'image', 'images',
                       'attributes', 'word_count']

        for field in field_order:
            if field in frontmatter:
                ordered[field] = frontmatter[field]

        # Add any remaining fields
        for key, value in frontmatter.items():
            if key not in ordered:
                ordered[key] = value

        fm_yaml = yaml.dump(ordered, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{fm_yaml}\n---\n\n{body}"


# ============================================================================
# Command-Line Interface
# ============================================================================

def process_single_file(file_path: str, dry_run: bool, init: bool, verbose: bool) -> bool:
    """Process a single file."""
    print(f"{'[DRY RUN] ' if dry_run else ''}Processing: {file_path}")

    helper = CodexLiteHelper()

    try:
        fixed_text, fixes = helper.process_file(file_path, dry_run, init)

        if not fixes:
            print("  No fixes needed")
            return True

        print(f"  Fixes applied ({len(fixes)}):")
        for fix in fixes:
            print(f"     - {fix}")

        if not dry_run:
            print(f"  File updated")

        return True

    except Exception as e:
        print(f"  Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate and fix Codex Lite (Markdown) files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python lite_helper.py document.md
    python lite_helper.py /path/to/docs -r
    python lite_helper.py document.md --init  # Add frontmatter
    python lite_helper.py document.md --dry-run
        """
    )

    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--init', action='store_true', help='Add frontmatter to bare markdown files')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)

    if path.is_file():
        success = process_single_file(str(path), args.dry_run, args.init, args.verbose)
        sys.exit(0 if success else 1)

    elif path.is_dir():
        # Process directory
        pattern = '**/*.md' if args.recursive else '*.md'
        files = list(path.glob(pattern))

        if not files:
            print(f"No markdown files found in: {path}")
            sys.exit(0)

        print(f"Found {len(files)} markdown files\n")

        success = 0
        failed = 0

        for f in files:
            if process_single_file(str(f), args.dry_run, args.init, args.verbose):
                success += 1
            else:
                failed += 1
            print()

        print(f"\n{'='*50}")
        print(f"Summary: {success} succeeded, {failed} failed")
        sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
