#!/usr/bin/env python3
"""Tests for insert_engine module."""
import os
import tempfile
import shutil
import pytest
from pathlib import Path
from insert_engine import InsertEngine

FIXTURES = Path(__file__).parent / 'fixtures'


class TestInsertEngineSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        engine = InsertEngine()
        assert engine is not None


class TestDetectFormat:
    """Test format detection for various file types."""

    def test_codex_yaml_extension(self):
        """B2: .codex.yaml files must be detected as codex-yaml."""
        engine = InsertEngine()
        result = engine.detect_format(str(FIXTURES / 'sample.codex.yaml'))
        assert result == 'codex-yaml'

    def test_codex_yml_extension(self):
        """B2: .codex.yml files must be detected as codex-yaml."""
        engine = InsertEngine()
        with tempfile.NamedTemporaryFile(suffix='.codex.yml', mode='w', delete=False) as f:
            f.write(open(FIXTURES / 'sample.codex.yaml').read())
            tmp_path = f.name
        try:
            result = engine.detect_format(tmp_path)
            assert result == 'codex-yaml'
        finally:
            os.unlink(tmp_path)

    def test_codex_lite_extension(self):
        """Markdown with frontmatter detected as codex-lite."""
        engine = InsertEngine()
        result = engine.detect_format(str(FIXTURES / 'sample-lite.md'))
        assert result == 'codex-lite'

    def test_plain_markdown(self):
        """Plain markdown without frontmatter detected as markdown."""
        engine = InsertEngine()
        result = engine.detect_format(str(FIXTURES / 'sample-plain.md'))
        assert result == 'markdown'
