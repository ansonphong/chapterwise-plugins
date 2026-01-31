#!/usr/bin/env python3
"""
Word Count - Update word_count attributes in Codex files

Recursively traverses a codex file and its children, counts words in body
fields, and updates the word_count attribute on each entity.

Usage:
    python word_count.py <file_or_directory> [options]

Examples:
    python word_count.py story.codex.yaml
    python word_count.py chapter.md
    python word_count.py /path/to/codex --recursive
    python word_count.py story.codex.yaml --follow-includes
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set

logger = logging.getLogger(__name__)


def is_codex_file(file_path: str) -> bool:
    """Check if file is a codex file."""
    lower = file_path.lower()
    return any(lower.endswith(ext) for ext in ['.codex.yaml', '.codex.yml', '.codex.json', '.codex'])


def is_markdown_file(file_path: str) -> bool:
    """Check if file is a markdown file."""
    return file_path.lower().endswith('.md')


def is_codex_like_file(file_path: str) -> bool:
    """Check if file is either a codex or markdown file."""
    return is_codex_file(file_path) or is_markdown_file(file_path)


class WordCounter:
    """Update word counts in codex files."""

    def __init__(self):
        self.entities_updated = 0
        self.total_words = 0
        self.files_modified: List[str] = []
        self.errors: List[str] = []
        self.processed_files: Set[str] = set()

    def _count_words(self, text: str) -> int:
        """Count words in a text string (split on whitespace)."""
        if not text or not isinstance(text, str):
            return 0
        return len([w for w in text.split() if w])

    def _find_or_create_word_count_attribute(self, attributes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find an existing word_count attribute or create a new one."""
        # Find existing attribute
        for attr in attributes:
            if attr.get('key') == 'word_count':
                return attr

        # Create new attribute
        new_attr = {
            'key': 'word_count',
            'name': 'Word Count',
            'value': 0,
            'dataType': 'int'
        }
        attributes.append(new_attr)
        return new_attr

    def _update_word_count_in_object(
        self,
        obj: Dict[str, Any],
        parent_dir: str,
        follow_includes: bool
    ) -> bool:
        """Update word count in an object and its children recursively."""
        was_modified = False

        # Check if this object has a body field
        body = obj.get('body')
        if body and isinstance(body, str):
            word_count = self._count_words(body)
            self.total_words += word_count

            # Ensure attributes array exists
            if 'attributes' not in obj or not isinstance(obj.get('attributes'), list):
                obj['attributes'] = []
                was_modified = True

            # Find or create word_count attribute
            attr = self._find_or_create_word_count_attribute(obj['attributes'])

            # Update if different
            if attr.get('value') != word_count:
                attr['value'] = word_count
                attr['name'] = 'Word Count'
                attr['dataType'] = 'int'
                was_modified = True
                self.entities_updated += 1

        # Process children recursively
        children = obj.get('children', [])
        if children and isinstance(children, list):
            for child in children:
                if child and isinstance(child, dict):
                    # Check if this is an include directive
                    if 'include' in child and isinstance(child['include'], str) and follow_includes:
                        include_path = child['include']
                        if include_path.startswith('/'):
                            full_path = os.path.join(parent_dir, include_path)
                        else:
                            full_path = os.path.normpath(os.path.join(parent_dir, include_path))

                        # Process the included file if not already processed
                        if full_path not in self.processed_files:
                            self._process_included_file(full_path, follow_includes)
                    else:
                        # Regular child - recurse
                        child_modified = self._update_word_count_in_object(child, parent_dir, follow_includes)
                        was_modified = was_modified or child_modified

        return was_modified

    def _process_included_file(self, file_path: str, follow_includes: bool):
        """Process an included file."""
        # Mark as processed to avoid infinite loops
        self.processed_files.add(file_path)

        if not os.path.exists(file_path):
            self.errors.append(f"Include file not found: {file_path}")
            return

        if not is_codex_file(file_path):
            # Skip markdown files in includes for now
            if is_markdown_file(file_path):
                return
            self.errors.append(f"Include is not a valid codex file: {file_path}")
            return

        try:
            import yaml

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_json = file_path.lower().endswith('.json')

            if is_json:
                import json
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)

            parent_dir = os.path.dirname(file_path)
            was_modified = self._update_word_count_in_object(data, parent_dir, follow_includes)

            if was_modified:
                self._write_codex_file(file_path, data, 'json' if is_json else 'yaml')
                self.files_modified.append(file_path)
                logger.info(f"Updated included file: {file_path}")

        except Exception as e:
            self.errors.append(f"Failed to process include '{file_path}': {e}")

    def _write_codex_file(self, file_path: str, data: Dict[str, Any], fmt: str):
        """Write codex data to file with proper formatting."""
        import yaml

        if fmt == 'json':
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # Create custom Dumper to avoid modifying global yaml state
            class CodexDumper(yaml.SafeDumper):
                pass

            def str_representer(dumper, s):
                if '\n' in s or len(s) > 80:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', s, style='|')
                return dumper.represent_scalar('tag:yaml.org,2002:str', s)

            CodexDumper.add_representer(str, str_representer)

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, Dumper=CodexDumper, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    def _extract_frontmatter(self, text: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter from markdown text."""
        import yaml

        trimmed = text.lstrip()

        # Check for frontmatter delimiter
        if not trimmed.startswith('---'):
            return {}, text

        # Find the closing delimiter
        after_first = trimmed[3:]
        end_index = after_first.find('\n---')

        if end_index == -1:
            return {}, text

        frontmatter_text = after_first[:end_index]
        body_start = 3 + end_index + 4  # "---" + content + "\n---"
        body = trimmed[body_start:].strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
            return frontmatter, body
        except yaml.YAMLError:
            return {}, text

    def _serialize_markdown(self, frontmatter: Dict[str, Any], body: str) -> str:
        """Serialize frontmatter and body back to markdown format."""
        import yaml

        if not frontmatter:
            return body

        fm_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{fm_yaml}\n---\n\n{body}"

    def _update_word_count_in_markdown(self, file_path: str, dry_run: bool = False) -> bool:
        """Update word count in a markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter, body = self._extract_frontmatter(content)

            # If no frontmatter, can't update
            if not frontmatter:
                self.errors.append(f"No frontmatter found in: {file_path}")
                return False

            # Count words in body
            word_count = self._count_words(body)
            self.total_words += word_count

            # Check if word_count needs to be updated
            old_word_count = frontmatter.get('word_count')
            if old_word_count == word_count:
                return False  # No change needed

            # Update word count
            frontmatter['word_count'] = word_count
            self.entities_updated += 1

            if not dry_run:
                # Write back to file
                new_content = self._serialize_markdown(frontmatter, body)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            return True

        except Exception as e:
            self.errors.append(f"Failed to update markdown file '{file_path}': {e}")
            return False

    def update_word_counts(
        self,
        input_path: str,
        follow_includes: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update word counts in a codex or markdown file.

        Returns:
            Dict with keys: success, entities_updated, total_words, files_modified, errors
        """
        # Reset state
        self.entities_updated = 0
        self.total_words = 0
        self.files_modified = []
        self.errors = []
        self.processed_files = set()

        try:
            import yaml

            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Mark this file as processed
            self.processed_files.add(input_path)

            # Check if this is a markdown file
            if is_markdown_file(input_path):
                # Handle Codex Lite (Markdown) format
                was_modified = self._update_word_count_in_markdown(input_path, dry_run)

                if was_modified and not dry_run:
                    self.files_modified.append(input_path)

                return {
                    'success': True,
                    'entities_updated': self.entities_updated,
                    'total_words': self.total_words,
                    'files_modified': self.files_modified,
                    'errors': self.errors
                }

            # Handle full Codex format files
            with open(input_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            is_json = input_path.lower().endswith('.json')

            if is_json:
                import json
                codex_data = json.loads(file_content)
            else:
                codex_data = yaml.safe_load(file_content)

            # Validate structure
            if not codex_data or not isinstance(codex_data, dict):
                raise ValueError("Invalid codex file structure")

            parent_dir = os.path.dirname(input_path)

            # Update word counts recursively
            was_modified = self._update_word_count_in_object(codex_data, parent_dir, follow_includes)

            if was_modified and not dry_run:
                # Save the main file
                self._write_codex_file(input_path, codex_data, 'json' if is_json else 'yaml')
                self.files_modified.append(input_path)

            return {
                'success': True,
                'entities_updated': self.entities_updated,
                'total_words': self.total_words,
                'files_modified': self.files_modified,
                'errors': self.errors
            }

        except Exception as e:
            return {
                'success': False,
                'entities_updated': 0,
                'total_words': 0,
                'files_modified': [],
                'errors': [str(e)] + self.errors
            }


def process_directory(
    directory_path: str,
    recursive: bool = False,
    follow_includes: bool = False,
    dry_run: bool = False,
    include_markdown: bool = True
) -> Tuple[int, int]:
    """
    Process all codex files in a directory.

    Returns:
        Tuple of (successful_count, failed_count)
    """
    # Find all codex files
    extensions = ['.codex.yaml', '.codex.yml', '.codex.json', '.codex']
    if include_markdown:
        extensions.append('.md')

    codex_files = []

    if recursive:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    codex_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and any(file.endswith(ext) for ext in extensions):
                codex_files.append(file_path)

    if not codex_files:
        print("No codex files found")
        return 0, 0

    print(f"Found {len(codex_files)} file(s)\n")

    successful = 0
    failed = 0
    total_words = 0
    total_updated = 0

    for i, file_path in enumerate(codex_files, 1):
        print(f"[{i}/{len(codex_files)}] Processing: {file_path}")

        counter = WordCounter()
        result = counter.update_word_counts(file_path, follow_includes, dry_run)

        if result['success']:
            successful += 1
            total_words += result['total_words']
            total_updated += result['entities_updated']

            if result['entities_updated'] > 0:
                print(f"    Updated: {result['entities_updated']} entities, {result['total_words']:,} words")
            else:
                print(f"    No changes ({result['total_words']:,} words)")
        else:
            failed += 1
            print(f"    Failed: {result['errors'][0] if result['errors'] else 'Unknown error'}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files processed: {len(codex_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Entities updated: {total_updated}")
    print(f"  Total words: {total_words:,}")
    print(f"{'='*60}")

    return successful, failed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update word_count attributes in Codex files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python word_count.py story.codex.yaml
    python word_count.py chapter.md
    python word_count.py /path/to/codex --recursive
    python word_count.py story.codex.yaml --follow-includes
    python word_count.py story.codex.yaml --dry-run
        """
    )

    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
    parser.add_argument('--follow-includes', action='store_true', help='Process included files')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--no-markdown', action='store_true', help='Skip .md files when processing directories')
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

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Updating word counts")

    if path.is_file():
        print(f"File: {path}\n")

        counter = WordCounter()
        result = counter.update_word_counts(str(path), args.follow_includes, args.dry_run)

        if result['success']:
            print(f"Entities updated: {result['entities_updated']}")
            print(f"Total words: {result['total_words']:,}")

            if result['files_modified']:
                print(f"\nFiles modified:")
                for f in result['files_modified']:
                    print(f"  - {f}")

            if result['errors']:
                print(f"\nWarnings:")
                for e in result['errors']:
                    print(f"  - {e}")

            sys.exit(0)
        else:
            print(f"Failed: {result['errors'][0] if result['errors'] else 'Unknown error'}")
            sys.exit(1)

    elif path.is_dir():
        print(f"Directory: {path}")
        print(f"Recursive: {args.recursive}")
        print(f"Follow includes: {args.follow_includes}")
        print()

        successful, failed = process_directory(
            str(path),
            args.recursive,
            args.follow_includes,
            args.dry_run,
            not args.no_markdown
        )
        sys.exit(0 if failed == 0 else 1)

    else:
        print(f"Error: Invalid path: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
