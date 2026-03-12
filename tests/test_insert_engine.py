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


class TestInsertCodexLineBased:
    """Test line-based YAML insertion (fallback path)."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_codex(self, body_text):
        """Create a codex file with given body content."""
        indented = '\n'.join('  ' + line for line in body_text.split('\n'))
        content = f"type: chapter\nname: \"Test Chapter\"\nbody: |\n{indented}\nchildren: []\n"
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_body_with_colons_not_treated_as_yaml_key(self):
        """B3: Body text containing colons must not be mistaken for YAML keys."""
        body = 'She said: "hello"\n\nnote: this is body text\n\nEnd of chapter.'
        path = self._make_codex(body)

        engine = InsertEngine()
        # Force line-based path
        engine._insert_codex = engine._insert_codex_line_based

        result = engine.insert(
            file_path=path,
            content="INSERTED TEXT",
            line_number=3,
            insert_after=True,
            create_backup=False,
            add_markers=False
        )

        assert result.success
        with open(path) as f:
            content = f.read()
        assert 'INSERTED TEXT' in content
        assert 'children: []' in content  # Structure preserved

    def test_body_end_detected_by_dedent(self):
        """Body ends when indentation returns to top-level YAML key."""
        body = 'Line 1\nLine 2\nLine 3'
        path = self._make_codex(body)

        engine = InsertEngine()
        engine._insert_codex = engine._insert_codex_line_based

        result = engine.insert(
            file_path=path,
            content="INSERTED",
            line_number=2,
            insert_after=True,
            create_backup=False,
            add_markers=False
        )

        assert result.success
        with open(path) as f:
            content = f.read()
        assert 'INSERTED' in content
        assert 'children: []' in content
