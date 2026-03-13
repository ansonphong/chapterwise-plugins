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
