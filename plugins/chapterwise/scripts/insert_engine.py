#!/usr/bin/env python3
"""
Insert Engine for Chapterwise Insert
Handles the actual file insertion with format detection, backup creation,
and INSERT markers for review workflow.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple


@dataclass
class InsertResult:
    """Result of an insert operation."""
    success: bool
    file_path: str
    line_number: int
    before_context: str = ""
    after_context: str = ""
    error: Optional[str] = None
    backup_path: Optional[str] = None


@dataclass
class InsertLocation:
    """A location where content can be inserted."""
    file_path: str
    line_number: int
    insert_after: bool = True
    confidence: float = 0.0
    reason: str = ""


@dataclass
class PendingInsert:
    """A pending insert found in a file."""
    file_path: str
    line_number: int
    time: str
    source: str
    instruction: str
    confidence: float
    matched_after: str
    content: str


class InsertEngine:
    """
    Engine for inserting content into Chapterwise files.

    Supports:
    - Codex YAML format (.codex)
    - Codex Lite / Markdown format (.md)
    - Backup creation before modification
    - INSERT markers for review workflow
    """

    # Marker patterns
    INSERT_MARKER_START = "<!-- INSERT"
    INSERT_MARKER_END = "<!-- /INSERT -->"

    # Format detection patterns
    CODEX_YAML_PATTERN = re.compile(r'^type:\s*(project|document|arc|chapter|scene)', re.MULTILINE)
    CODEX_LITE_PATTERN = re.compile(r'^---\s*\n.*?^---\s*\n', re.MULTILINE | re.DOTALL)

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize the insert engine.

        Args:
            backup_dir: Directory for backups. If None, uses .backups in file's directory.
        """
        self.backup_dir = backup_dir

    def detect_format(self, file_path: str) -> str:
        """
        Detect the format of a file.

        Args:
            file_path: Path to the file

        Returns:
            Format string: 'codex-yaml', 'codex-lite', 'markdown', or 'unknown'
        """
        path = Path(file_path)
        name_lower = path.name.lower()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # Read first 4KB for detection
        except Exception:
            return 'unknown'

        # Check for .codex.yaml / .codex.yml files (compound extension)
        if name_lower.endswith('.codex.yaml') or name_lower.endswith('.codex.yml'):
            return 'codex-yaml'

        # Check for .codex files
        if path.suffix.lower() == '.codex':
            return 'codex-yaml'

        # Check for markdown files
        if path.suffix.lower() == '.md':
            if self.CODEX_LITE_PATTERN.match(content):
                return 'codex-lite'
            return 'markdown'

        # Check content patterns for other extensions
        if self.CODEX_YAML_PATTERN.search(content):
            return 'codex-yaml'
        if self.CODEX_LITE_PATTERN.match(content):
            return 'codex-lite'

        return 'unknown'

    def create_backup(self, file_path: str) -> str:
        """
        Create a timestamped backup of a file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file
        """
        path = Path(file_path)

        # Determine backup directory
        if self.backup_dir:
            backup_parent = Path(self.backup_dir)
        else:
            backup_parent = path.parent / '.backups'

        # Create backup directory
        backup_parent.mkdir(parents=True, exist_ok=True)

        # Generate timestamped backup name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{path.stem}_{timestamp}{path.suffix}"
        backup_path = backup_parent / backup_name

        # Copy the file
        import shutil
        shutil.copy2(file_path, backup_path)

        return str(backup_path)

    def generate_insert_marker(
        self,
        content: str,
        source: str = "notepad",
        instruction: str = "",
        confidence: float = 0.0,
        matched_after: str = ""
    ) -> str:
        """
        Generate INSERT marker HTML comments wrapping content.

        Args:
            content: The content to wrap
            source: Source of the insert (e.g., 'notepad', 'api')
            instruction: Original instruction from user
            confidence: Confidence score (0.0-1.0)
            matched_after: Text that this was matched after

        Returns:
            Content wrapped in INSERT markers
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Escape instruction for YAML-like format in comment
        instruction_escaped = instruction.replace('"', '\\"')
        matched_escaped = matched_after.replace('"', '\\"')

        # Truncate matched_after if too long
        if len(matched_escaped) > 100:
            matched_escaped = matched_escaped[:97] + "..."

        marker_start = f"""{self.INSERT_MARKER_START}
time: {timestamp}
source: {source}
instruction: "{instruction_escaped}"
confidence: {confidence:.2f}
matched_after: "{matched_escaped}"
-->"""

        marker_end = self.INSERT_MARKER_END

        return f"{marker_start}\n{content}\n{marker_end}"

    def insert(
        self,
        file_path: str,
        content: str,
        line_number: int,
        insert_after: bool = True,
        source: str = "notepad",
        instruction: str = "",
        confidence: float = 0.0,
        matched_after: str = "",
        create_backup: bool = True,
        add_markers: bool = True
    ) -> InsertResult:
        """
        Insert content into a file at the specified location.

        Args:
            file_path: Path to the file to modify
            content: Content to insert
            line_number: Line number for insertion
            insert_after: If True, insert after the line; if False, insert before
            source: Source of the insert
            instruction: Original instruction
            confidence: Confidence score
            matched_after: Text matched after
            create_backup: Whether to create a backup
            add_markers: Whether to wrap content in INSERT markers

        Returns:
            InsertResult with success status and details
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return InsertResult(
                    success=False,
                    file_path=file_path,
                    line_number=line_number,
                    error=f"File not found: {file_path}"
                )

            # Create backup
            backup_path = None
            if create_backup:
                try:
                    backup_path = self.create_backup(file_path)
                except Exception as e:
                    return InsertResult(
                        success=False,
                        file_path=file_path,
                        line_number=line_number,
                        error=f"Failed to create backup: {e}"
                    )

            # Detect format and dispatch
            file_format = self.detect_format(file_path)

            if file_format in ('markdown', 'codex-lite'):
                return self._insert_markdown(
                    file_path=file_path,
                    content=content,
                    line_number=line_number,
                    insert_after=insert_after,
                    source=source,
                    instruction=instruction,
                    confidence=confidence,
                    matched_after=matched_after,
                    backup_path=backup_path,
                    add_markers=add_markers
                )
            elif file_format == 'codex-yaml':
                return self._insert_codex(
                    file_path=file_path,
                    content=content,
                    line_number=line_number,
                    insert_after=insert_after,
                    source=source,
                    instruction=instruction,
                    confidence=confidence,
                    matched_after=matched_after,
                    backup_path=backup_path,
                    add_markers=add_markers
                )
            else:
                # Default to markdown-style insertion
                return self._insert_markdown(
                    file_path=file_path,
                    content=content,
                    line_number=line_number,
                    insert_after=insert_after,
                    source=source,
                    instruction=instruction,
                    confidence=confidence,
                    matched_after=matched_after,
                    backup_path=backup_path,
                    add_markers=add_markers
                )

        except Exception as e:
            return InsertResult(
                success=False,
                file_path=file_path,
                line_number=line_number,
                error=str(e)
            )

    def _insert_markdown(
        self,
        file_path: str,
        content: str,
        line_number: int,
        insert_after: bool,
        source: str,
        instruction: str,
        confidence: float,
        matched_after: str,
        backup_path: Optional[str],
        add_markers: bool
    ) -> InsertResult:
        """
        Insert content into a markdown file.

        Works line-by-line for simple and reliable insertion.
        """
        # Read file lines
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Validate line number
        if line_number < 1:
            line_number = 1
        if line_number > len(lines):
            line_number = len(lines)

        # Prepare content with markers
        if add_markers:
            insert_content = self.generate_insert_marker(
                content=content,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after
            )
        else:
            insert_content = content

        # Ensure content ends with newline
        if not insert_content.endswith('\n'):
            insert_content += '\n'

        # Calculate insertion point
        if insert_after:
            insert_index = line_number  # After line N means index N (0-indexed would be line_number)
        else:
            insert_index = line_number - 1  # Before line N means index N-1

        # Get context
        before_context = lines[max(0, insert_index - 1)].strip() if insert_index > 0 else ""
        after_context = lines[insert_index].strip() if insert_index < len(lines) else ""

        # Insert content
        lines.insert(insert_index, insert_content)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return InsertResult(
            success=True,
            file_path=file_path,
            line_number=line_number,
            before_context=before_context,
            after_context=after_context,
            backup_path=backup_path
        )

    def _insert_codex(
        self,
        file_path: str,
        content: str,
        line_number: int,
        insert_after: bool,
        source: str,
        instruction: str,
        confidence: float,
        matched_after: str,
        backup_path: Optional[str],
        add_markers: bool
    ) -> InsertResult:
        """
        Insert content into a Codex YAML file.

        Tries ruamel.yaml first for proper YAML handling,
        falls back to line-based insertion.
        """
        try:
            # Try ruamel.yaml first
            import ruamel.yaml
            return self._insert_codex_yaml_ruamel(
                file_path=file_path,
                content=content,
                line_number=line_number,
                insert_after=insert_after,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after,
                backup_path=backup_path,
                add_markers=add_markers
            )
        except ImportError:
            # Fall back to line-based insertion
            return self._insert_codex_line_based(
                file_path=file_path,
                content=content,
                line_number=line_number,
                insert_after=insert_after,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after,
                backup_path=backup_path,
                add_markers=add_markers
            )

    def _insert_codex_yaml_ruamel(
        self,
        file_path: str,
        content: str,
        line_number: int,
        insert_after: bool,
        source: str,
        instruction: str,
        confidence: float,
        matched_after: str,
        backup_path: Optional[str],
        add_markers: bool
    ) -> InsertResult:
        """
        Insert content into Codex YAML using ruamel.yaml.

        This preserves YAML structure and comments.
        """
        import ruamel.yaml

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096  # Prevent line wrapping

        with open(file_path, 'r', encoding='utf-8') as f:
            doc = yaml.load(f)

        if doc is None:
            doc = {}

        # Find the body field
        body = doc.get('body', '')
        if not body:
            body = ''

        # Split body into lines
        body_lines = body.split('\n')

        # Validate line number (relative to body)
        if line_number < 1:
            line_number = 1
        if line_number > len(body_lines):
            line_number = len(body_lines)

        # Prepare content with markers
        if add_markers:
            insert_content = self.generate_insert_marker(
                content=content,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after
            )
        else:
            insert_content = content

        # Calculate insertion point
        if insert_after:
            insert_index = line_number
        else:
            insert_index = line_number - 1

        # Get context
        before_context = body_lines[max(0, insert_index - 1)].strip() if insert_index > 0 else ""
        after_context = body_lines[insert_index].strip() if insert_index < len(body_lines) else ""

        # Insert content
        body_lines.insert(insert_index, insert_content)

        # Force literal block scalar to preserve markers exactly
        from ruamel.yaml.scalarstring import LiteralScalarString
        doc['body'] = LiteralScalarString('\n'.join(body_lines))

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)

        return InsertResult(
            success=True,
            file_path=file_path,
            line_number=line_number,
            before_context=before_context,
            after_context=after_context,
            backup_path=backup_path
        )

    def _insert_codex_line_based(
        self,
        file_path: str,
        content: str,
        line_number: int,
        insert_after: bool,
        source: str,
        instruction: str,
        confidence: float,
        matched_after: str,
        backup_path: Optional[str],
        add_markers: bool
    ) -> InsertResult:
        """
        Insert content into Codex YAML using line-based approach.

        Fallback when ruamel.yaml is not available.
        This is less safe but works for simple cases.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find body field
        body_start = -1
        body_end = len(lines)
        in_body = False
        body_indent = -1  # Will be set from first content line

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            current_indent = len(line) - len(line.lstrip())

            if not in_body:
                if stripped.startswith('body:'):
                    body_start = i + 1
                    in_body = True

                    # Detect block scalar indicator (| or >)
                    after_body = stripped[5:].strip()
                    if after_body and after_body[0] in ('|', '>'):
                        # Block scalar — body indent determined by first content line
                        body_indent = -1
                    elif after_body:
                        # Inline body value — single line, not a block
                        body_end = i + 1
                        in_body = False
                    else:
                        # Empty body: or next line
                        body_indent = -1

            else:
                # Inside body block scalar
                if stripped == '':
                    # Blank lines are allowed inside body
                    continue

                if body_indent == -1:
                    # First content line determines the body indent level
                    body_indent = current_indent

                # A line at column 0 (or less than body indent) with a YAML key
                # pattern means we've exited the block scalar
                if current_indent < body_indent and stripped:
                    body_end = i
                    break

        if body_start == -1:
            # No body field - fall back to markdown insertion
            return self._insert_markdown(
                file_path=file_path,
                content=content,
                line_number=line_number,
                insert_after=insert_after,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after,
                backup_path=backup_path,
                add_markers=add_markers
            )

        # Calculate actual line number in file
        body_line_count = body_end - body_start
        if line_number < 1:
            line_number = 1
        if line_number > body_line_count:
            line_number = body_line_count

        file_line_number = body_start + line_number - 1

        # Prepare content with markers
        if add_markers:
            insert_content = self.generate_insert_marker(
                content=content,
                source=source,
                instruction=instruction,
                confidence=confidence,
                matched_after=matched_after
            )
        else:
            insert_content = content

        # Add proper indentation for YAML body content.
        # Marker lines (<!-- INSERT/-->/<!-- /INSERT -->) stay at column 0
        # so find_pending_inserts can find them regardless of indent tolerance.
        # Plain content lines get 2-space indent to match YAML body block.
        indented_lines = []
        for line in insert_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('<!-- INSERT') or stripped == '-->' or stripped == '<!-- /INSERT -->':
                indented_lines.append(line)
            else:
                indented_lines.append('  ' + line)
        insert_content = '\n'.join(indented_lines)

        if not insert_content.endswith('\n'):
            insert_content += '\n'

        # Calculate insertion point
        if insert_after:
            insert_index = file_line_number + 1
        else:
            insert_index = file_line_number

        # Get context
        before_context = lines[max(0, insert_index - 1)].strip() if insert_index > 0 else ""
        after_context = lines[insert_index].strip() if insert_index < len(lines) else ""

        # Insert content
        lines.insert(insert_index, insert_content)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return InsertResult(
            success=True,
            file_path=file_path,
            line_number=line_number,
            before_context=before_context,
            after_context=after_context,
            backup_path=backup_path
        )

    # Flexible block pattern: matches INSERT markers regardless of field order
    _BLOCK_PATTERN = re.compile(
        r'[ \t]*<!-- INSERT\s*\n((?:(?!-->)[^\n]*\n)*?)[ \t]*-->\s*\n(.*?)\n[ \t]*<!-- /INSERT -->',
        re.DOTALL | re.MULTILINE
    )

    def find_pending_inserts(self, file_path: str) -> List[PendingInsert]:
        """
        Find all pending INSERT markers in a file.

        Args:
            file_path: Path to the file to scan

        Returns:
            List of PendingInsert objects
        """
        pending = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find line numbers
        lines = content.split('\n')
        char_to_line = {}
        char_count = 0
        for i, line in enumerate(lines, 1):
            char_to_line[char_count] = i
            char_count += len(line) + 1  # +1 for newline

        for match in self._BLOCK_PATTERN.finditer(content):
            header = match.group(1)
            body = match.group(2).strip()

            # Parse fields from header (order-independent)
            def extract_field(name, default=''):
                m = re.search(rf'{name}:\s*"?([^"\n]*)"?', header)
                return m.group(1).strip() if m else default

            time_val = extract_field('time')
            source_val = extract_field('source')
            instruction_val = extract_field('instruction')
            matched_val = extract_field('matched_after')

            confidence_match = re.search(r'confidence:\s*([0-9.]+)', header)
            confidence_val = float(confidence_match.group(1)) if confidence_match else 0.0

            # Find line number
            start_pos = match.start()
            line_number = 1
            for char_pos, line_num in sorted(char_to_line.items()):
                if char_pos <= start_pos:
                    line_number = line_num
                else:
                    break

            pending.append(PendingInsert(
                file_path=file_path,
                line_number=line_number,
                time=time_val,
                source=source_val,
                instruction=instruction_val,
                confidence=confidence_val,
                matched_after=matched_val,
                content=body
            ))

        return pending

    def accept_inserts(
        self,
        file_path: str,
        indices: Optional[List[int]] = None,
        create_backup: bool = True
    ) -> Tuple[int, List[str]]:
        """
        Accept pending inserts by removing markers and keeping content.

        Args:
            file_path: Path to the file
            indices: If provided, only accept these inserts (1-indexed).
                    If None, accept all.
            create_backup: Whether to create a backup first

        Returns:
            Tuple of (count of accepted inserts, list of errors)
        """
        errors = []

        # Create backup
        if create_backup:
            try:
                self.create_backup(file_path)
            except Exception as e:
                errors.append(f"Failed to create backup: {e}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use flexible block pattern (field-order-independent)
        # Capture group 1 = content between markers
        accept_pattern = re.compile(
            r'[ \t]*<!-- INSERT\s*\n(?:(?!-->)[^\n]*\n)*?[ \t]*-->\s*\n(.*?)\n[ \t]*<!-- /INSERT -->',
            re.DOTALL | re.MULTILINE
        )

        accepted_count = 0
        match_counter = 0
        indices_set = set(indices) if indices else None

        def replace_insert(match):
            nonlocal accepted_count, match_counter
            match_counter += 1
            content_only = match.group(1)

            if indices_set and match_counter not in indices_set:
                return match.group(0)  # Keep unchanged

            accepted_count += 1
            return content_only

        new_content = accept_pattern.sub(replace_insert, content)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return accepted_count, errors

    def reject_inserts(
        self,
        file_path: str,
        indices: Optional[List[int]] = None,
        create_backup: bool = True
    ) -> Tuple[int, List[str]]:
        """
        Reject pending inserts by removing markers AND content.

        Args:
            file_path: Path to the file
            indices: If provided, only reject these inserts (1-indexed).
                    If None, reject all.
            create_backup: Whether to create a backup first

        Returns:
            Tuple of (count of rejected inserts, list of errors)
        """
        errors = []

        # Create backup
        if create_backup:
            try:
                self.create_backup(file_path)
            except Exception as e:
                errors.append(f"Failed to create backup: {e}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Flexible block pattern (field-order-independent)
        reject_pattern = re.compile(
            r'[ \t]*<!-- INSERT\s*\n(?:(?!-->)[^\n]*\n)*?[ \t]*-->\s*\n.*?\n[ \t]*<!-- /INSERT -->\n?',
            re.DOTALL | re.MULTILINE
        )

        rejected_count = 0
        match_counter = 0
        indices_set = set(indices) if indices else None

        def remove_insert(match):
            nonlocal rejected_count, match_counter
            match_counter += 1

            if indices_set and match_counter not in indices_set:
                return match.group(0)

            rejected_count += 1
            return ''

        new_content = reject_pattern.sub(remove_insert, content)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return rejected_count, errors


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Insert content into Chapterwise files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Insert content at line 10
  python insert_engine.py insert myfile.md -c "New paragraph here" -l 10

  # Insert with instruction
  python insert_engine.py insert myfile.md -c "Content" -l 10 -i "after the battle"

  # List pending inserts
  python insert_engine.py list myfile.md

  # Accept all pending inserts
  python insert_engine.py accept myfile.md

  # Accept specific inserts
  python insert_engine.py accept myfile.md --indices 1 3
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert content into a file')
    insert_parser.add_argument('file', help='File to modify')
    insert_parser.add_argument('-c', '--content', required=True, help='Content to insert')
    insert_parser.add_argument('-l', '--line', type=int, required=True, help='Line number')
    insert_parser.add_argument('-a', '--after', action='store_true', default=True,
                              help='Insert after the line (default)')
    insert_parser.add_argument('-b', '--before', action='store_true',
                              help='Insert before the line')
    insert_parser.add_argument('-s', '--source', default='cli', help='Source of insert')
    insert_parser.add_argument('-i', '--instruction', default='', help='Original instruction')
    insert_parser.add_argument('--confidence', type=float, default=1.0, help='Confidence score')
    insert_parser.add_argument('--matched', default='', help='Matched text')
    insert_parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    insert_parser.add_argument('--no-markers', action='store_true', help='Skip INSERT markers')
    insert_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # List command
    list_parser = subparsers.add_parser('list', help='List pending inserts')
    list_parser.add_argument('file', help='File to scan')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Accept command
    accept_parser = subparsers.add_parser('accept', help='Accept pending inserts')
    accept_parser.add_argument('file', help='File to modify')
    accept_parser.add_argument('--indices', type=int, nargs='+', help='Indices to accept (1-indexed)')
    accept_parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    accept_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Reject command
    reject_parser = subparsers.add_parser('reject', help='Reject pending inserts')
    reject_parser.add_argument('file', help='File to modify')
    reject_parser.add_argument('--indices', type=int, nargs='+', help='Indices to reject (1-indexed)')
    reject_parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    reject_parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = InsertEngine()

    if args.command == 'insert':
        insert_after = not args.before
        result = engine.insert(
            file_path=args.file,
            content=args.content,
            line_number=args.line,
            insert_after=insert_after,
            source=args.source,
            instruction=args.instruction,
            confidence=args.confidence,
            matched_after=args.matched,
            create_backup=not args.no_backup,
            add_markers=not args.no_markers
        )

        if args.json:
            output = {
                'success': result.success,
                'file_path': result.file_path,
                'line_number': result.line_number,
                'before_context': result.before_context,
                'after_context': result.after_context,
                'error': result.error,
                'backup_path': result.backup_path
            }
            print(json.dumps(output, indent=2))
        else:
            if result.success:
                print(f"Inserted at line {result.line_number}")
                if result.backup_path:
                    print(f"Backup: {result.backup_path}")
            else:
                print(f"Error: {result.error}", file=sys.stderr)
                sys.exit(1)

    elif args.command == 'list':
        pending = engine.find_pending_inserts(args.file)

        if args.json:
            output = [{
                'index': i,
                'file_path': p.file_path,
                'line_number': p.line_number,
                'time': p.time,
                'source': p.source,
                'instruction': p.instruction,
                'confidence': p.confidence,
                'matched_after': p.matched_after,
                'content_preview': p.content[:100] + '...' if len(p.content) > 100 else p.content
            } for i, p in enumerate(pending, 1)]
            print(json.dumps(output, indent=2))
        else:
            if not pending:
                print("No pending inserts found.")
            else:
                for i, p in enumerate(pending, 1):
                    print(f"\n=== Pending Insert {i} ===")
                    print(f"Line: {p.line_number}")
                    print(f"Time: {p.time}")
                    print(f"Source: {p.source}")
                    print(f"Instruction: {p.instruction}")
                    print(f"Confidence: {p.confidence:.2f}")
                    content_preview = p.content[:100] + '...' if len(p.content) > 100 else p.content
                    print(f"Content: {content_preview}")

    elif args.command == 'accept':
        count, errors = engine.accept_inserts(
            file_path=args.file,
            indices=args.indices,
            create_backup=not args.no_backup
        )

        if args.json:
            print(json.dumps({
                'accepted': count,
                'errors': errors
            }, indent=2))
        else:
            print(f"Accepted {count} insert(s)")
            for error in errors:
                print(f"Warning: {error}", file=sys.stderr)

    elif args.command == 'reject':
        count, errors = engine.reject_inserts(
            file_path=args.file,
            indices=args.indices,
            create_backup=not args.no_backup
        )

        if args.json:
            print(json.dumps({
                'rejected': count,
                'errors': errors
            }, indent=2))
        else:
            print(f"Rejected {count} insert(s)")
            for error in errors:
                print(f"Warning: {error}", file=sys.stderr)


if __name__ == '__main__':
    main()
