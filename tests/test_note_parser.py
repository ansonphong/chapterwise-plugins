#!/usr/bin/env python3
"""Tests for note_parser module."""
import pytest
from pathlib import Path
from note_parser import NoteParser

FIXTURES = Path(__file__).parent / 'fixtures'


class TestParseSingle:
    """Test single note parsing."""

    def setup_method(self):
        self.parser = NoteParser()

    def test_instruction_with_content(self):
        """Instruction separated from content by double newline."""
        text = "after the battle\n\nElena drew her sword."
        note = self.parser.parse_single(text)
        assert note.instruction == "after the battle"
        assert note.content == "Elena drew her sword."

    def test_no_instruction(self):
        """Pure content with no location hint."""
        text = "Elena drew her sword, the blade catching the firelight."
        note = self.parser.parse_single(text)
        assert note.instruction is None
        assert note.content == text

    def test_before_instruction(self):
        """'before' keyword detected as instruction."""
        text = "before Marcus arrives\n\nThe gates swung open."
        note = self.parser.parse_single(text)
        assert note.instruction == "before Marcus arrives"
        assert note.content == "The gates swung open."

    def test_chapter_reference(self):
        """Chapter reference detected as instruction."""
        text = "in chapter 5 near the fountain\n\nWater splashed."
        note = self.parser.parse_single(text)
        assert note.instruction == "in chapter 5 near the fountain"

    def test_empty_text(self):
        """Empty text returns empty note."""
        note = self.parser.parse_single("")
        assert note.instruction is None
        assert note.content == ''

    def test_instruction_only_no_content(self):
        """Short instruction-like text with no content."""
        text = "after the battle"
        note = self.parser.parse_single(text)
        assert note.instruction == "after the battle"
        assert note.content == ''

    def test_when_keyword(self):
        """'when' keyword triggers instruction detection."""
        text = "when Elena first meets Marcus\n\nShe paused."
        note = self.parser.parse_single(text)
        assert note.instruction == "when Elena first meets Marcus"


class TestParseBatch:
    """Test batch file parsing."""

    def setup_method(self):
        self.parser = NoteParser()

    def test_parse_batch_file(self):
        """Parse fixture batch file with 3 notes."""
        notes = self.parser.parse_file(str(FIXTURES / 'batch-notes.txt'))
        assert len(notes) == 3
        assert notes[0].instruction == "after the hyperborean incursion"
        assert notes[1].instruction == "before Marcus arrives"
        assert notes[2].instruction is not None  # "in chapter 5..."

    def test_batch_indices_are_sequential(self):
        """Notes are indexed 1, 2, 3."""
        notes = self.parser.parse_file(str(FIXTURES / 'batch-notes.txt'))
        assert [n.index for n in notes] == [1, 2, 3]

    def test_custom_delimiter(self):
        """Custom delimiter works."""
        text = "after x\n\nContent A\n===\nafter y\n\nContent B"
        notes = self.parser.parse_batch(text, delimiter='===')
        assert len(notes) == 2

    def test_empty_batch(self):
        """Empty text returns no notes."""
        notes = self.parser.parse_batch("")
        assert notes == []
