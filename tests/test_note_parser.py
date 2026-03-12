#!/usr/bin/env python3
"""Tests for note_parser module."""
import pytest
from note_parser import NoteParser


class TestNoteParserSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        parser = NoteParser()
        assert parser is not None
