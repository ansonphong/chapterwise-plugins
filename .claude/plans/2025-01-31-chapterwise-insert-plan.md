# Chapterwise Insert Plugin - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code plugin that intelligently inserts notes into Chapterwise Codex manuscripts by finding the right location using semantic matching and hierarchical agent search.

**Architecture:** A single `/insert` command with Python backend scripts. Uses two-pass hierarchical agent search (coarse scan → deep scan) to find insertion points in large manuscripts. Supports both Codex (YAML) and Codex Lite (Markdown) formats. Confidence-based UX: auto-insert at ≥95%, show options at 50-95%, ask user below 50%.

**Tech Stack:** Python 3.8+, ruamel.yaml (preserves formatting), Claude Code Task tool for parallel agents, HTML comments for insert markers.

---

## Task 1: Create Plugin Structure

**Files:**
- Create: `plugins/chapterwise-insert/.claude-plugin/plugin.json`
- Create: `plugins/chapterwise-insert/commands/` (directory)
- Create: `plugins/chapterwise-insert/scripts/` (directory)
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Create plugin directory structure**

```bash
mkdir -p plugins/chapterwise-insert/.claude-plugin
mkdir -p plugins/chapterwise-insert/commands
mkdir -p plugins/chapterwise-insert/scripts
```

**Step 2: Create plugin.json manifest**

Create `plugins/chapterwise-insert/.claude-plugin/plugin.json`:

```json
{
  "name": "chapterwise-insert",
  "description": "Intelligently insert notes into Chapterwise Codex manuscripts with semantic location finding",
  "version": "1.0.0",
  "homepage": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

**Step 3: Update marketplace.json**

Add to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "chapterwise-insert",
  "description": "Intelligently insert notes into Chapterwise Codex manuscripts with semantic location finding",
  "version": "1.0.0",
  "source": "./plugins/chapterwise-insert",
  "tags": ["codex", "manuscript", "notes", "insertion", "storytelling"],
  "category": "productivity"
}
```

**Step 4: Commit**

```bash
git add plugins/chapterwise-insert/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat(chapterwise-insert): initialize plugin structure"
```

---

## Task 2: Create Note Parser Script

**Files:**
- Create: `plugins/chapterwise-insert/scripts/note_parser.py`
- Test: Manual testing with sample notes

**Step 1: Create note_parser.py**

Create `plugins/chapterwise-insert/scripts/note_parser.py`:

```python
#!/usr/bin/env python3
"""
Note Parser for Chapterwise Insert
Parses notes from various sources, separates instructions from content,
and splits batch files into individual notes.
"""

import re
import sys
import argparse
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Note:
    """Represents a single note to insert."""
    instruction: Optional[str]  # Location hint (e.g., "after the hyperborean incursion")
    content: str                # The actual content to insert
    raw: str                    # Original raw text
    index: int                  # Position in batch (1-indexed)


class NoteParser:
    """Parse notes from text, separating instructions from content."""

    # Patterns that indicate an instruction (location hint)
    INSTRUCTION_PATTERNS = [
        r'^(this\s+(?:should\s+)?go(?:es)?)\s+',
        r'^(insert\s+(?:this\s+)?(?:after|before|at|in|into))\s+',
        r'^((?:put|place)\s+(?:this\s+)?(?:after|before|at|in|into))\s+',
        r'^(after|before)\s+',
        r'^(in\s+(?:the\s+)?(?:chapter|section|scene|part))',
        r'^(at\s+(?:the\s+)?(?:beginning|end|start))',
        r'^(near\s+(?:the\s+)?)',
        r'^(during\s+(?:the\s+)?)',
        r'^(when\s+)',
        r'^(where\s+)',
    ]

    def __init__(self, delimiter: str = '---'):
        self.delimiter = delimiter
        self._instruction_regex = re.compile(
            '|'.join(f'({p})' for p in self.INSTRUCTION_PATTERNS),
            re.IGNORECASE
        )

    def parse_single(self, text: str) -> Note:
        """
        Parse a single note, separating instruction from content.

        Args:
            text: Raw note text

        Returns:
            Note object with instruction and content separated
        """
        text = text.strip()
        if not text:
            return Note(instruction=None, content='', raw=text, index=1)

        # Split by double newline to find potential instruction
        parts = re.split(r'\n\s*\n', text, maxsplit=1)

        if len(parts) == 1:
            # No clear separation - check if whole thing is instruction-like
            if self._looks_like_instruction(text) and len(text) < 200:
                return Note(instruction=text, content='', raw=text, index=1)
            return Note(instruction=None, content=text, raw=text, index=1)

        first_part = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ''

        # Check if first part looks like an instruction
        if self._looks_like_instruction(first_part):
            return Note(instruction=first_part, content=rest, raw=text, index=1)

        # No instruction detected
        return Note(instruction=None, content=text, raw=text, index=1)

    def _looks_like_instruction(self, text: str) -> bool:
        """Check if text looks like a location instruction."""
        text_lower = text.lower().strip()

        # Check against patterns
        if self._instruction_regex.match(text_lower):
            return True

        # Check for chapter/section references
        if re.search(r'chapter\s*\d+|section\s*\d+|scene\s*\d+|part\s*\d+', text_lower):
            return True

        # Check for positional keywords
        positional_keywords = ['after', 'before', 'following', 'preceding', 'near', 'around']
        if any(text_lower.startswith(kw) for kw in positional_keywords):
            return True

        # Short text with location-like content
        if len(text) < 150 and any(kw in text_lower for kw in ['scene', 'chapter', 'section', 'part', 'where', 'when']):
            return True

        return False

    def parse_batch(self, text: str, delimiter: str = None) -> List[Note]:
        """
        Parse a batch file containing multiple notes.

        Args:
            text: Raw batch file content
            delimiter: Override default delimiter

        Returns:
            List of Note objects
        """
        if delimiter is None:
            delimiter = self.delimiter

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Split by delimiter (must be on its own line)
        # Pattern: newline + delimiter + newline (or end)
        pattern = rf'\n{re.escape(delimiter)}\s*\n'

        # Handle start of file
        if text.startswith(delimiter):
            text = '\n' + text

        raw_notes = re.split(pattern, text)

        # Clean up and filter
        notes = []
        for i, raw in enumerate(raw_notes, 1):
            raw = raw.strip()

            # Skip empty notes
            if not raw:
                continue

            # Skip if it's just the delimiter
            if raw == delimiter:
                continue

            # Remove trailing delimiter if present
            if raw.endswith(delimiter):
                raw = raw[:-len(delimiter)].strip()

            # Parse individual note
            note = self.parse_single(raw)
            note.index = i
            note.raw = raw
            notes.append(note)

        # Re-index after filtering
        for i, note in enumerate(notes, 1):
            note.index = i

        return notes

    def parse_file(self, filepath: str, delimiter: str = None) -> List[Note]:
        """
        Parse notes from a file.

        Args:
            filepath: Path to the notes file
            delimiter: Override default delimiter

        Returns:
            List of Note objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_batch(content, delimiter)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Parse notes for Chapterwise Insert',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a single note
  echo "after the battle - Elena drew her sword" | python note_parser.py --single

  # Parse a batch file
  python note_parser.py notes.txt

  # Use custom delimiter
  python note_parser.py notes.txt --delimiter "==="

  # Output as JSON
  python note_parser.py notes.txt --json
"""
    )

    parser.add_argument('file', nargs='?', help='Path to notes file (or read from stdin)')
    parser.add_argument('--single', action='store_true', help='Parse as single note')
    parser.add_argument('--delimiter', '-d', default='---', help='Delimiter for batch notes (default: ---)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Read input
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    # Parse
    parser_obj = NoteParser(delimiter=args.delimiter)

    if args.single:
        notes = [parser_obj.parse_single(text)]
    else:
        notes = parser_obj.parse_batch(text, args.delimiter)

    # Output
    if args.json:
        import json
        output = [{
            'index': n.index,
            'instruction': n.instruction,
            'content': n.content,
            'raw': n.raw
        } for n in notes]
        print(json.dumps(output, indent=2))
    else:
        for note in notes:
            print(f"=== Note {note.index} ===")
            if note.instruction:
                print(f"Instruction: {note.instruction}")
            print(f"Content: {note.content[:100]}{'...' if len(note.content) > 100 else ''}")
            print()


if __name__ == '__main__':
    main()
```

**Step 2: Test the parser**

```bash
# Test with sample input
echo -e "this should go after the battle\n\nElena drew her sword." | python3 plugins/chapterwise-insert/scripts/note_parser.py --single --json
```

Expected output:
```json
[
  {
    "index": 1,
    "instruction": "this should go after the battle",
    "content": "Elena drew her sword.",
    "raw": "this should go after the battle\n\nElena drew her sword."
  }
]
```

**Step 3: Commit**

```bash
git add plugins/chapterwise-insert/scripts/note_parser.py
git commit -m "feat(chapterwise-insert): add note parser with instruction extraction"
```

---

## Task 3: Create Insert Engine Script

**Files:**
- Create: `plugins/chapterwise-insert/scripts/insert_engine.py`
- Test: Manual testing with sample codex files

**Step 1: Create insert_engine.py**

Create `plugins/chapterwise-insert/scripts/insert_engine.py`:

```python
#!/usr/bin/env python3
"""
Insert Engine for Chapterwise Insert
Handles the actual insertion of content into Codex files.
Supports both Codex (YAML) and Codex Lite (Markdown) formats.
"""

import os
import re
import sys
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class InsertResult:
    """Result of an insert operation."""
    success: bool
    file_path: str
    line_number: int
    before_context: str
    after_context: str
    error: Optional[str] = None
    backup_path: Optional[str] = None


@dataclass
class InsertLocation:
    """Describes where to insert content."""
    file_path: str
    line_number: int
    insert_after: str  # Text snippet to insert after
    confidence: float
    reason: str


class InsertEngine:
    """Engine for inserting content into Codex files."""

    MARKER_START = "<!-- INSERT"
    MARKER_END = "<!-- /INSERT -->"

    def __init__(self, backup_dir: str = None):
        self.backup_dir = backup_dir

    def detect_format(self, filepath: str) -> str:
        """Detect the format of a file."""
        lower = filepath.lower()

        if lower.endswith('.codex.yaml') or lower.endswith('.codex.yml'):
            return 'codex-yaml'
        elif lower.endswith('.codex.json'):
            return 'codex-json'
        elif lower.endswith('.md'):
            # Check for YAML frontmatter
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                if content.strip().startswith('---'):
                    return 'codex-lite'
            except:
                pass
            return 'plain-markdown'

        return 'unknown'

    def create_backup(self, filepath: str) -> str:
        """Create a backup of the file before modification."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Determine backup directory
        if self.backup_dir:
            backup_base = self.backup_dir
        else:
            backup_base = os.path.join(os.path.dirname(filepath), '.backups')

        # Create timestamped backup directory
        timestamp = datetime.now().strftime('%Y-%m-%dT%H%M%S')
        backup_dir = os.path.join(backup_base, timestamp)
        os.makedirs(backup_dir, exist_ok=True)

        # Copy file to backup
        filename = os.path.basename(filepath)
        backup_path = os.path.join(backup_dir, filename)
        shutil.copy2(filepath, backup_path)

        return backup_path

    def generate_insert_marker(
        self,
        instruction: str = None,
        confidence: float = None,
        matched_after: str = None,
        source: str = None
    ) -> Tuple[str, str]:
        """
        Generate HTML comment markers for an insert.

        Returns:
            Tuple of (start_marker, end_marker)
        """
        timestamp = datetime.now().isoformat()

        lines = [self.MARKER_START]
        lines.append(f"time: {timestamp}")

        if source:
            lines.append(f"source: {source}")
        if instruction:
            # Escape any special characters in instruction
            safe_instruction = instruction.replace('\n', ' ').replace('"', '\\"')
            lines.append(f'instruction: "{safe_instruction}"')
        if confidence is not None:
            lines.append(f"confidence: {confidence:.2f}")
        if matched_after:
            # Truncate and escape matched text
            safe_matched = matched_after[:80].replace('\n', ' ').replace('"', '\\"')
            lines.append(f'matched_after: "{safe_matched}..."')

        lines.append("-->")

        start_marker = '\n'.join(lines)
        end_marker = self.MARKER_END

        return start_marker, end_marker

    def insert(
        self,
        filepath: str,
        content: str,
        location: InsertLocation,
        instruction: str = None,
        add_markers: bool = True,
        create_backup: bool = True,
        source: str = None
    ) -> InsertResult:
        """
        Insert content into a file at the specified location.

        Args:
            filepath: Path to the file
            content: Content to insert
            location: Where to insert
            instruction: Original instruction (for marker metadata)
            add_markers: Whether to wrap with INSERT markers
            create_backup: Whether to create backup before modifying
            source: Source identifier (for marker metadata)

        Returns:
            InsertResult with details of the operation
        """
        try:
            file_format = self.detect_format(filepath)

            if file_format == 'unknown':
                return InsertResult(
                    success=False,
                    file_path=filepath,
                    line_number=0,
                    before_context='',
                    after_context='',
                    error=f"Unknown file format: {filepath}"
                )

            # Create backup
            backup_path = None
            if create_backup:
                backup_path = self.create_backup(filepath)

            # Dispatch to format-specific handler
            if file_format in ('codex-yaml', 'codex-json'):
                result = self._insert_codex(
                    filepath, content, location, instruction,
                    add_markers, source, file_format
                )
            else:  # codex-lite or plain-markdown
                result = self._insert_markdown(
                    filepath, content, location, instruction,
                    add_markers, source
                )

            result.backup_path = backup_path
            return result

        except Exception as e:
            return InsertResult(
                success=False,
                file_path=filepath,
                line_number=0,
                before_context='',
                after_context='',
                error=str(e)
            )

    def _insert_markdown(
        self,
        filepath: str,
        content: str,
        location: InsertLocation,
        instruction: str,
        add_markers: bool,
        source: str
    ) -> InsertResult:
        """Insert into Markdown/Codex Lite files."""

        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find insertion point
        insert_line = location.line_number - 1  # Convert to 0-indexed

        if insert_line < 0 or insert_line > len(lines):
            insert_line = len(lines)

        # Get context
        before_start = max(0, insert_line - 3)
        before_context = ''.join(lines[before_start:insert_line]).strip()

        after_end = min(len(lines), insert_line + 3)
        after_context = ''.join(lines[insert_line:after_end]).strip()

        # Build insert block
        if add_markers:
            start_marker, end_marker = self.generate_insert_marker(
                instruction=instruction,
                confidence=location.confidence,
                matched_after=location.insert_after,
                source=source
            )
            insert_block = f"\n{start_marker}\n{content}\n{end_marker}\n"
        else:
            insert_block = f"\n{content}\n"

        # Insert content
        lines.insert(insert_line, insert_block)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return InsertResult(
            success=True,
            file_path=filepath,
            line_number=location.line_number,
            before_context=before_context,
            after_context=after_context
        )

    def _insert_codex(
        self,
        filepath: str,
        content: str,
        location: InsertLocation,
        instruction: str,
        add_markers: bool,
        source: str,
        file_format: str
    ) -> InsertResult:
        """Insert into Codex YAML/JSON files."""

        # For YAML files, we need to be careful about the body field
        # Use ruamel.yaml if available, otherwise fall back to line-based
        try:
            from ruamel.yaml import YAML
            return self._insert_codex_yaml_ruamel(
                filepath, content, location, instruction,
                add_markers, source
            )
        except ImportError:
            # Fall back to line-based insertion
            return self._insert_codex_line_based(
                filepath, content, location, instruction,
                add_markers, source, file_format
            )

    def _insert_codex_yaml_ruamel(
        self,
        filepath: str,
        content: str,
        location: InsertLocation,
        instruction: str,
        add_markers: bool,
        source: str
    ) -> InsertResult:
        """Insert into Codex YAML using ruamel.yaml (preserves formatting)."""
        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 120

        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.load(f)

        # Find the body field and insert
        # This is simplified - assumes insertion into root body
        if 'body' not in data:
            data['body'] = ''

        body = data['body'] or ''
        lines = body.split('\n')

        insert_line = location.line_number - 1
        if insert_line < 0 or insert_line > len(lines):
            insert_line = len(lines)

        # Get context
        before_start = max(0, insert_line - 3)
        before_context = '\n'.join(lines[before_start:insert_line]).strip()

        after_end = min(len(lines), insert_line + 3)
        after_context = '\n'.join(lines[insert_line:after_end]).strip()

        # Build insert block
        if add_markers:
            start_marker, end_marker = self.generate_insert_marker(
                instruction=instruction,
                confidence=location.confidence,
                matched_after=location.insert_after,
                source=source
            )
            insert_text = f"{start_marker}\n{content}\n{end_marker}"
        else:
            insert_text = content

        # Insert into body
        lines.insert(insert_line, insert_text)
        data['body'] = '\n'.join(lines)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)

        return InsertResult(
            success=True,
            file_path=filepath,
            line_number=location.line_number,
            before_context=before_context,
            after_context=after_context
        )

    def _insert_codex_line_based(
        self,
        filepath: str,
        content: str,
        location: InsertLocation,
        instruction: str,
        add_markers: bool,
        source: str,
        file_format: str
    ) -> InsertResult:
        """Fallback line-based insertion for Codex files."""
        # This is a simplified fallback - treats as text file
        return self._insert_markdown(
            filepath, content, location, instruction,
            add_markers, source
        )

    def accept_inserts(self, filepath: str) -> Tuple[int, List[str]]:
        """
        Accept all INSERT markers in a file (remove markers, keep content).

        Returns:
            Tuple of (count_accepted, list of descriptions)
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match INSERT blocks
        pattern = re.compile(
            r'<!-- INSERT\n.*?-->\n(.*?)\n<!-- /INSERT -->',
            re.DOTALL
        )

        accepted = []
        def replace_match(match):
            inner_content = match.group(1)
            preview = inner_content[:50].replace('\n', ' ')
            accepted.append(f"Accepted: {preview}...")
            return inner_content

        new_content = pattern.sub(replace_match, content)

        if accepted:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return len(accepted), accepted

    def find_pending_inserts(self, filepath: str) -> List[Dict[str, Any]]:
        """Find all pending INSERT markers in a file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = re.compile(
            r'<!-- INSERT\n(.*?)-->\n(.*?)\n<!-- /INSERT -->',
            re.DOTALL
        )

        inserts = []
        for match in pattern.finditer(content):
            metadata_str = match.group(1)
            inner_content = match.group(2)

            # Parse metadata
            metadata = {}
            for line in metadata_str.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"')

            inserts.append({
                'metadata': metadata,
                'content_preview': inner_content[:100],
                'start': match.start(),
                'end': match.end()
            })

        return inserts


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Insert content into Codex files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert content')
    insert_parser.add_argument('file', help='Target file')
    insert_parser.add_argument('--content', '-c', required=True, help='Content to insert')
    insert_parser.add_argument('--line', '-l', type=int, required=True, help='Line number')
    insert_parser.add_argument('--instruction', '-i', help='Original instruction')
    insert_parser.add_argument('--no-markers', action='store_true', help='Skip INSERT markers')
    insert_parser.add_argument('--no-backup', action='store_true', help='Skip backup')

    # Accept command
    accept_parser = subparsers.add_parser('accept', help='Accept pending inserts')
    accept_parser.add_argument('file', help='Target file')

    # List command
    list_parser = subparsers.add_parser('list', help='List pending inserts')
    list_parser.add_argument('file', help='Target file')

    args = parser.parse_args()

    engine = InsertEngine()

    if args.command == 'insert':
        location = InsertLocation(
            file_path=args.file,
            line_number=args.line,
            insert_after='',
            confidence=1.0,
            reason='Manual insert'
        )

        result = engine.insert(
            filepath=args.file,
            content=args.content,
            location=location,
            instruction=args.instruction,
            add_markers=not args.no_markers,
            create_backup=not args.no_backup
        )

        if result.success:
            print(f"Inserted at line {result.line_number}")
            if result.backup_path:
                print(f"Backup: {result.backup_path}")
        else:
            print(f"Error: {result.error}")
            sys.exit(1)

    elif args.command == 'accept':
        count, descriptions = engine.accept_inserts(args.file)
        print(f"Accepted {count} insert(s)")
        for desc in descriptions:
            print(f"  - {desc}")

    elif args.command == 'list':
        inserts = engine.find_pending_inserts(args.file)
        print(f"Found {len(inserts)} pending insert(s)")
        for i, ins in enumerate(inserts, 1):
            print(f"\n{i}. {ins['metadata'].get('instruction', 'No instruction')}")
            print(f"   Time: {ins['metadata'].get('time', 'Unknown')}")
            print(f"   Preview: {ins['content_preview'][:60]}...")


if __name__ == '__main__':
    main()
```

**Step 2: Test the engine**

```bash
# Create a test file
echo -e "Line 1\nLine 2\nLine 3\nLine 4\nLine 5" > /tmp/test.md

# Test insert
python3 plugins/chapterwise-insert/scripts/insert_engine.py insert /tmp/test.md -c "INSERTED CONTENT" -l 3 -i "test instruction"

# Check result
cat /tmp/test.md
```

**Step 3: Commit**

```bash
git add plugins/chapterwise-insert/scripts/insert_engine.py
git commit -m "feat(chapterwise-insert): add insert engine with backup and markers"
```

---

## Task 4: Create Location Finder Scaffold

**Files:**
- Create: `plugins/chapterwise-insert/scripts/location_finder.py`

**Step 1: Create location_finder.py**

Create `plugins/chapterwise-insert/scripts/location_finder.py`:

```python
#!/usr/bin/env python3
"""
Location Finder for Chapterwise Insert
Coordinates hierarchical agent search to find insertion points.

NOTE: This script provides helper functions for the Claude skill.
The actual agent orchestration happens in the skill definition,
using Claude Code's Task tool for parallel agent execution.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Candidate:
    """A candidate insertion location."""
    file_path: str
    line_number: int
    insert_after: str
    confidence: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileIndex:
    """Index of a codex file for searching."""
    file_path: str
    file_type: str  # codex-yaml, codex-lite, etc.
    title: Optional[str]
    name: Optional[str]
    summary: Optional[str]
    body_preview: str  # First 500 chars of body
    child_names: List[str]
    word_count: int


class LocationFinder:
    """
    Helps find insertion locations in codex files.

    The heavy lifting (semantic matching) is done by Claude agents.
    This class provides utilities for:
    - Scanning directories for codex files
    - Extracting searchable content from files
    - Formatting results
    """

    CODEX_EXTENSIONS = ['.codex.yaml', '.codex.yml', '.codex.json']
    MARKDOWN_EXTENSION = '.md'

    def __init__(self):
        pass

    def scan_directory(
        self,
        path: str,
        recursive: bool = True,
        max_depth: int = None,
        include_markdown: bool = True
    ) -> List[str]:
        """
        Scan directory for codex files.

        Args:
            path: Directory path
            recursive: Whether to scan subdirectories
            max_depth: Maximum directory depth (None = unlimited)
            include_markdown: Whether to include .md files

        Returns:
            List of file paths
        """
        path = Path(path)
        files = []

        if not path.is_dir():
            if path.is_file():
                return [str(path)]
            return []

        def should_skip(dir_name: str) -> bool:
            """Check if directory should be skipped."""
            skip_dirs = {'.git', 'node_modules', '__pycache__', '.backups', 'venv', '.venv'}
            return dir_name.startswith('.') or dir_name in skip_dirs

        def scan(current_path: Path, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            try:
                for item in current_path.iterdir():
                    if item.is_file():
                        name_lower = item.name.lower()

                        # Check codex extensions
                        if any(name_lower.endswith(ext) for ext in self.CODEX_EXTENSIONS):
                            files.append(str(item))
                        # Check markdown
                        elif include_markdown and name_lower.endswith(self.MARKDOWN_EXTENSION):
                            # Verify it has frontmatter
                            if self._has_frontmatter(item):
                                files.append(str(item))

                    elif item.is_dir() and recursive:
                        if not should_skip(item.name):
                            scan(item, depth + 1)
            except PermissionError:
                pass

        scan(path, 0)
        return sorted(files)

    def _has_frontmatter(self, filepath: Path) -> bool:
        """Check if markdown file has YAML frontmatter."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line == '---'
        except:
            return False

    def index_file(self, filepath: str) -> Optional[FileIndex]:
        """
        Create a searchable index of a codex file.

        Args:
            filepath: Path to the file

        Returns:
            FileIndex object or None if file can't be indexed
        """
        try:
            filepath_lower = filepath.lower()

            if any(filepath_lower.endswith(ext) for ext in self.CODEX_EXTENSIONS):
                return self._index_codex_yaml(filepath)
            elif filepath_lower.endswith(self.MARKDOWN_EXTENSION):
                return self._index_codex_lite(filepath)

            return None
        except Exception as e:
            return None

    def _index_codex_yaml(self, filepath: str) -> Optional[FileIndex]:
        """Index a Codex YAML file."""
        import yaml

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Extract body preview
        body = data.get('body', '') or ''
        body_preview = body[:500] if body else ''

        # Extract child names
        child_names = []
        children = data.get('children', [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    name = child.get('name') or child.get('title')
                    if name:
                        child_names.append(name)

        return FileIndex(
            file_path=filepath,
            file_type='codex-yaml',
            title=data.get('title'),
            name=data.get('name'),
            summary=data.get('summary'),
            body_preview=body_preview,
            child_names=child_names,
            word_count=len(body.split()) if body else 0
        )

    def _index_codex_lite(self, filepath: str) -> Optional[FileIndex]:
        """Index a Codex Lite (Markdown) file."""
        import yaml

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()

        return FileIndex(
            file_path=filepath,
            file_type='codex-lite',
            title=frontmatter.get('title'),
            name=frontmatter.get('name'),
            summary=frontmatter.get('summary'),
            body_preview=body[:500],
            child_names=[],  # Codex Lite is flat
            word_count=len(body.split())
        )

    def chunk_files(
        self,
        files: List[str],
        max_files_per_chunk: int = 10
    ) -> List[List[str]]:
        """
        Group files into chunks for parallel processing.

        Args:
            files: List of file paths
            max_files_per_chunk: Maximum files per chunk

        Returns:
            List of file chunks
        """
        chunks = []
        for i in range(0, len(files), max_files_per_chunk):
            chunks.append(files[i:i + max_files_per_chunk])
        return chunks

    def format_index_for_search(
        self,
        indices: List[FileIndex],
        include_body: bool = True
    ) -> str:
        """
        Format file indices for Claude agent search.

        Args:
            indices: List of FileIndex objects
            include_body: Whether to include body preview

        Returns:
            Formatted string for agent prompt
        """
        lines = []

        for idx in indices:
            lines.append(f"## {idx.file_path}")
            if idx.title:
                lines.append(f"Title: {idx.title}")
            if idx.name:
                lines.append(f"Name: {idx.name}")
            if idx.summary:
                lines.append(f"Summary: {idx.summary}")
            if idx.child_names:
                lines.append(f"Children: {', '.join(idx.child_names[:10])}")
            if include_body and idx.body_preview:
                lines.append(f"Preview: {idx.body_preview[:300]}...")
            lines.append(f"Words: {idx.word_count}")
            lines.append("")

        return '\n'.join(lines)

    def extract_location_hints(self, instruction: str) -> Dict[str, Any]:
        """
        Extract structured hints from an instruction string.

        Args:
            instruction: The user's instruction

        Returns:
            Dictionary of extracted hints
        """
        hints = {
            'chapter': None,
            'section': None,
            'character': None,
            'event': None,
            'position': None,  # 'after', 'before', 'beginning', 'end'
            'keywords': []
        }

        instruction_lower = instruction.lower()

        # Extract chapter reference
        chapter_match = re.search(r'chapter\s*(\d+|[a-z]+)', instruction_lower)
        if chapter_match:
            hints['chapter'] = chapter_match.group(1)

        # Extract section reference
        section_match = re.search(r'section\s*(\d+|[a-z]+)', instruction_lower)
        if section_match:
            hints['section'] = section_match.group(1)

        # Extract position
        if 'after' in instruction_lower:
            hints['position'] = 'after'
        elif 'before' in instruction_lower:
            hints['position'] = 'before'
        elif 'beginning' in instruction_lower or 'start' in instruction_lower:
            hints['position'] = 'beginning'
        elif 'end' in instruction_lower:
            hints['position'] = 'end'

        # Extract keywords (nouns and names)
        # Simple approach: words that are capitalized or longer than 4 chars
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{5,}\b', instruction)
        hints['keywords'] = list(set(words))[:10]  # Limit to 10

        return hints


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Location finder utilities for Chapterwise Insert'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan for codex files')
    scan_parser.add_argument('path', help='Directory to scan')
    scan_parser.add_argument('--no-recursive', action='store_true', help='Don\'t scan subdirectories')
    scan_parser.add_argument('--depth', type=int, help='Maximum depth')
    scan_parser.add_argument('--no-markdown', action='store_true', help='Exclude markdown files')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index codex files')
    index_parser.add_argument('path', help='File or directory to index')
    index_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Hints command
    hints_parser = subparsers.add_parser('hints', help='Extract hints from instruction')
    hints_parser.add_argument('instruction', help='Instruction text')

    args = parser.parse_args()
    finder = LocationFinder()

    if args.command == 'scan':
        files = finder.scan_directory(
            args.path,
            recursive=not args.no_recursive,
            max_depth=args.depth,
            include_markdown=not args.no_markdown
        )
        for f in files:
            print(f)
        print(f"\nTotal: {len(files)} files")

    elif args.command == 'index':
        path = Path(args.path)

        if path.is_file():
            files = [str(path)]
        else:
            files = finder.scan_directory(str(path))

        indices = []
        for f in files:
            idx = finder.index_file(f)
            if idx:
                indices.append(idx)

        if args.json:
            output = [asdict(idx) for idx in indices]
            print(json.dumps(output, indent=2))
        else:
            print(finder.format_index_for_search(indices))

    elif args.command == 'hints':
        hints = finder.extract_location_hints(args.instruction)
        print(json.dumps(hints, indent=2))


if __name__ == '__main__':
    main()
```

**Step 2: Test the location finder**

```bash
# Scan for files (assuming there are test files)
python3 plugins/chapterwise-insert/scripts/location_finder.py scan .

# Test hint extraction
python3 plugins/chapterwise-insert/scripts/location_finder.py hints "after the hyperborean incursion in chapter 5"
```

**Step 3: Commit**

```bash
git add plugins/chapterwise-insert/scripts/location_finder.py
git commit -m "feat(chapterwise-insert): add location finder with file indexing"
```

---

## Task 5: Create the Insert Skill Definition

**Files:**
- Create: `plugins/chapterwise-insert/commands/insert.md`

**Step 1: Create insert.md skill definition**

Create `plugins/chapterwise-insert/commands/insert.md`:

```markdown
---
description: Intelligently insert notes into Chapterwise Codex manuscripts with semantic location finding
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Task, AskUserQuestion
triggers:
  - insert into codex
  - insert note
  - add to manuscript
  - insert scene
  - batch insert
  - chapterwise insert
---

# Chapterwise Insert

Intelligently insert notes into Chapterwise Codex manuscripts by finding the right location using semantic matching and hierarchical agent search.

## When This Skill Applies

- User wants to insert a note, scene, or content into a manuscript
- User mentions "insert", "add to manuscript", or "batch insert"
- User has notes to distribute across a codex file or folder

## Invocation Modes

```bash
# Single note (inline)
/insert "Elena drew her sword..." into chapter-23.codex.yaml

# Single note with instruction
/insert "after the battle - Elena drew her sword..." into ./manuscript/

# Batch from file
/insert notes.txt into ./manuscript/

# Interactive mode
/insert

# From clipboard
/insert --clipboard into ./manuscript/

# Dry run (preview only)
/insert --dry-run notes.txt into ./manuscript/

# Accept all pending inserts
/insert --accept ./manuscript/

# Undo last insert
/insert --undo chapter-23.codex.yaml
```

## Command Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview without writing |
| `--clipboard` | Read from system clipboard |
| `--accept` | Remove INSERT markers (accept all in path) |
| `--undo` | Restore from last backup |
| `--as-child` | Force insert as child node (codex only) |
| `--as-text` | Force insert into body text |
| `--depth N` | Limit folder scan depth |
| `--delimiter STR` | Custom note delimiter for batch |
| `--no-backup` | Skip backup creation |

---

## WORKFLOW

### Step 1: Parse the Request

Determine the mode from user input:

1. **Accept mode** (`--accept`): Run accept workflow
2. **Undo mode** (`--undo`): Run undo workflow
3. **Interactive mode** (no args): Start interactive session
4. **Clipboard mode** (`--clipboard`): Read from clipboard
5. **Batch mode** (file path to .txt): Parse batch file
6. **Single mode** (quoted text): Parse single note

### Step 2: Parse Notes

Use the note parser to extract instructions and content:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/note_parser.py [file] --json
```

For single notes:
```bash
echo "[note text]" | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/note_parser.py --single --json
```

**Key parsing rules:**
- First paragraph before blank line = instruction (if it looks like a location hint)
- Remaining content = the actual insert
- Instruction is used for finding, not inserted into manuscript

### Step 3: Scan Target

Scan the target directory for codex files:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/location_finder.py scan [path] --json
```

### Step 4: Hierarchical Agent Search

**For manuscripts with many files (>10), use two-pass search:**

**Pass 1: Coarse Scan**
- Launch 5-10 parallel Task agents (type: Explore)
- Each agent handles a chunk of files
- Agent reads only: titles, names, summaries, first 500 chars of body
- Agent returns: list of promising files

**Pass 2: Deep Scan**
- Launch 2-3 parallel Task agents on promising files only
- Agent reads full content
- Agent returns: exact candidates with line numbers and confidence

**Agent prompt template for coarse scan:**

```
Search these codex files for content related to this instruction:

INSTRUCTION: "[instruction]"
CONTENT PREVIEW: "[first 100 chars of content]"

FILES TO SEARCH:
[list of files with index data]

Return JSON with promising files:
{
  "promising_files": ["path1", "path2"],
  "reason": "why these files match"
}

If no files seem relevant, return empty array.
```

**Agent prompt template for deep scan:**

```
Search this codex file for the best location to insert content.

FILE: [filepath]
INSTRUCTION: "[instruction]"
CONTENT PREVIEW: "[first 100 chars]"

Read the full file content and find where this content should go.

Return JSON:
{
  "candidates": [
    {
      "line": 247,
      "insert_after": "text snippet before insertion point...",
      "confidence": 87,
      "reason": "Matches 'hyperborean incursion' at line 245"
    }
  ]
}

Confidence scoring:
- 95-100: Exact phrase match or explicit chapter reference
- 80-94: Strong semantic match
- 50-79: Partial match, related content
- Below 50: Weak match, best guess
```

### Step 5: Confidence-Based UX

After collecting candidates from all agents:

**If top candidate ≥ 95% confidence:**
- Auto-insert
- Report: "Inserted after [context] in [file]"
- Show before/after snippet

**If candidates between 50-95%:**
- Show top 3 options with context snippets
- Ask user: "Pick location: A/B/C"
- Use AskUserQuestion tool with options

**If all candidates < 50%:**
- Show best guess
- Ask: "Couldn't find a strong match. Best guess is [location]. Insert here? Or clarify where it belongs?"
- Options: Insert here / Specify location / Skip

### Step 6: Execute Insert

Use the insert engine:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/insert_engine.py insert [file] \
  --content "[content]" \
  --line [line_number] \
  --instruction "[instruction]"
```

**Insert marker format:**

```html
<!-- INSERT
time: 2024-01-27T10:30:00Z
source: notepad
instruction: "this should go after the hyperborean incursion"
confidence: 0.93
matched_after: "The hyperborean horde breached the northern wall..."
-->
Elena drew her sword, the blade catching moonlight...
<!-- /INSERT -->
```

### Step 7: Summary Report

After batch processing, display summary:

```
╔══════════════════════════════════════════════════════════════════╗
║                    INSERT SUMMARY REPORT                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Batch: notes-to-insert.txt                                     ║
║  Target: ./manuscript/                                          ║
║  Total notes: 12                                                ║
╠══════════════════════════════════════════════════════════════════╣

  #  │ STATUS   │ CONF │ FILE                    │ LINE │ MATCHED
 ────┼──────────┼──────┼─────────────────────────┼──────┼──────────────────
  1  │ ✓ AUTO   │  97% │ chapter-23.codex.yaml   │  847 │ "hyperborean horde"
  2  │ ✓ PICKED │  89% │ chapter-03.codex.yaml   │  156 │ "council meeting"
  ...

╠══════════════════════════════════════════════════════════════════╣
║  SUMMARY: ✓ Inserted: 9  ✗ Skipped: 2  ⚠ Duplicates: 1         ║
║  Backups: ./manuscript/.backups/2024-01-27T103000/              ║
╚══════════════════════════════════════════════════════════════════╝
```

**Status codes:**

| Status | Meaning |
|--------|---------|
| `✓ AUTO` | Confidence ≥95%, auto-inserted |
| `✓ PICKED` | User picked from options (50-95%) |
| `✓ MANUAL` | User specified location manually (<50%) |
| `✗ SKIP` | User chose to skip |
| `⚠ DUP` | Duplicate detected, skipped |
| `⚠ ERROR` | File write failed |

---

## ACCEPT WORKFLOW

To accept (remove markers from) pending inserts:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/insert_engine.py accept [file_or_folder]
```

This removes `<!-- INSERT -->` markers while preserving the content.

---

## UNDO WORKFLOW

To restore from backup:

1. Find most recent backup in `.backups/` directory
2. Copy backup file over current file
3. Report: "Restored [file] from backup [timestamp]"

---

## EDGE CASES & POLICIES

### Content Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Same phrase, multiple locations** | All become candidates; ask user to pick |
| **Very long note (10k+ words)** | Warn user; still insert; recommend `--as-child` |
| **Whitespace-only note** | Reject: "Note is empty. Skipping." |
| **Instruction-only, no content** | Warn: "No content found, only instruction." |
| **Note contains `---` delimiter** | Only split on `---` at start of line preceded by blank line |
| **Note contains `<!-- -->`** | Use unique marker: `<!-- INSERT` to avoid collision |

### Matching Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Non-English content** | Text-based matching still works; fuzzy match handles accents |
| **Ambiguous pronouns** ("after she betrayed him") | Low confidence; ask user to clarify |
| **Contradictory hints** ("chapter 3" but content references ch.5) | Flag conflict; ask user |
| **Multiple target hints** ("chapter 3 or maybe 4") | Find matches in both; present as options |
| **Case sensitivity** | Case-insensitive matching |
| **Typos in instruction** | Fuzzy matching with tolerance |

### File System Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **No codex files found** | Error: "No codex files found in [path]" |
| **File is read-only** | Error: "Cannot write to [file] - read-only" |
| **Circular includes** | Detect cycle; warn; don't infinite loop |
| **Empty file (metadata only)** | Create `body:` field; confidence 100% |

### Batch Processing Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **Large batch (500+ notes)** | Process in chunks of 20; show progress |
| **Duplicate notes** | Detect via content hash; warn and skip |
| **All notes fail to match** | Summary shows failures; suggest more specific instructions |
| **Multiple notes same location** | Ask for ordering; or insert in batch-file order |

### Insert Marker Edge Cases

| Edge Case | Policy |
|-----------|--------|
| **File has existing INSERT markers** | Warn: "File has N unaccepted inserts" |
| **Nested INSERT blocks** | Prevent; error if attempting |

---

## SUPPORTED FORMATS

| Format | Extension | Insert Method |
|--------|-----------|---------------|
| **Codex** | `.codex.yaml` | YAML manipulation (ruamel.yaml) |
| **Codex JSON** | `.codex.json` | JSON manipulation |
| **Codex Lite** | `.md` | Text insertion after frontmatter |

---

## QUICK REFERENCE

```bash
# Single insert
/insert "content here" into file.codex.yaml

# With instruction
/insert "after the battle - content here" into ./manuscript/

# Batch
/insert notes.txt into ./manuscript/

# Preview only
/insert --dry-run notes.txt into ./manuscript/

# Accept markers
/insert --accept ./manuscript/

# Undo
/insert --undo file.codex.yaml
```
```

**Step 2: Verify syntax**

```bash
# Check YAML frontmatter is valid
head -20 plugins/chapterwise-insert/commands/insert.md
```

**Step 3: Commit**

```bash
git add plugins/chapterwise-insert/commands/insert.md
git commit -m "feat(chapterwise-insert): add insert skill definition with edge cases"
```

---

## Task 6: Add Requirements File

**Files:**
- Create: `plugins/chapterwise-insert/requirements.txt`

**Step 1: Create requirements.txt**

Create `plugins/chapterwise-insert/requirements.txt`:

```
ruamel.yaml>=0.17.0
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-insert/requirements.txt
git commit -m "feat(chapterwise-insert): add Python requirements"
```

---

## Task 7: Integration Testing

**Files:**
- Test all scripts together

**Step 1: Create test manuscript**

```bash
mkdir -p /tmp/test-manuscript

# Create a test codex file
cat > /tmp/test-manuscript/chapter-1.codex.yaml << 'EOF'
metadata:
  formatVersion: "1.2"

id: "test-chapter-1"
type: chapter
name: "The Beginning"

body: |
  The sun rose over the mountains.

  Elena walked through the village square.

  The hyperborean forces gathered in the north.

  By nightfall, everything had changed.

children: []
EOF
```

**Step 2: Test note parsing**

```bash
echo -e "after the hyperborean forces gathered\n\nElena drew her sword, ready for battle." | \
  python3 plugins/chapterwise-insert/scripts/note_parser.py --single --json
```

Expected: instruction and content separated correctly.

**Step 3: Test file scanning**

```bash
python3 plugins/chapterwise-insert/scripts/location_finder.py scan /tmp/test-manuscript
```

Expected: Lists chapter-1.codex.yaml

**Step 4: Test file indexing**

```bash
python3 plugins/chapterwise-insert/scripts/location_finder.py index /tmp/test-manuscript --json
```

Expected: JSON with title, body preview, etc.

**Step 5: Test manual insert**

```bash
python3 plugins/chapterwise-insert/scripts/insert_engine.py insert \
  /tmp/test-manuscript/chapter-1.codex.yaml \
  --content "Elena drew her sword, ready for battle." \
  --line 8 \
  --instruction "after the hyperborean forces gathered"
```

**Step 6: Verify insert**

```bash
cat /tmp/test-manuscript/chapter-1.codex.yaml
```

Expected: Content inserted with `<!-- INSERT -->` markers.

**Step 7: Test accept**

```bash
python3 plugins/chapterwise-insert/scripts/insert_engine.py accept \
  /tmp/test-manuscript/chapter-1.codex.yaml
```

Expected: Markers removed, content preserved.

**Step 8: Commit**

```bash
git add -A
git commit -m "test(chapterwise-insert): verify integration works"
```

---

## Task 8: Documentation

**Files:**
- Update: `README.md` (root)

**Step 1: Add plugin to README**

Add section to root README.md about chapterwise-insert plugin.

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add chapterwise-insert to README"
```

---

## Summary

This plan creates the complete chapterwise-insert plugin:

1. **Plugin structure** - Standard Claude plugin layout
2. **note_parser.py** - Parses notes, separates instructions from content
3. **insert_engine.py** - Handles file insertion with markers and backups
4. **location_finder.py** - Utilities for scanning and indexing files
5. **insert.md** - Full skill definition with workflow and edge cases
6. **Integration tests** - Verify all components work together

The skill uses hierarchical agent search (two-pass) to handle large manuscripts without overwhelming context, and provides confidence-based UX to balance automation with user control.
