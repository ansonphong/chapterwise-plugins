#!/usr/bin/env python3
"""Tests for location_finder module."""
import pytest
from pathlib import Path
from location_finder import LocationFinder

FIXTURES = Path(__file__).parent / 'fixtures'


class TestScanDirectory:
    """Test directory scanning."""

    def test_finds_codex_yaml(self):
        finder = LocationFinder()
        files = finder.scan_directory(str(FIXTURES), recursive=False)
        names = [Path(f).name for f in files]
        assert 'sample.codex.yaml' in names

    def test_finds_markdown_with_frontmatter(self):
        finder = LocationFinder()
        files = finder.scan_directory(str(FIXTURES), recursive=False)
        names = [Path(f).name for f in files]
        assert 'sample-lite.md' in names

    def test_skips_plain_markdown(self):
        """Plain markdown without frontmatter is excluded."""
        finder = LocationFinder()
        files = finder.scan_directory(str(FIXTURES), recursive=False)
        names = [Path(f).name for f in files]
        assert 'sample-plain.md' not in names

    def test_nonexistent_directory_raises(self):
        finder = LocationFinder()
        with pytest.raises(ValueError):
            finder.scan_directory('/nonexistent/path')


class TestIndexFile:
    """Test file indexing."""

    def test_index_codex_yaml(self):
        finder = LocationFinder()
        index = finder.index_file(str(FIXTURES / 'sample.codex.yaml'))
        assert index is not None
        assert index.file_type == 'codex-yaml'
        assert 'Incursion' in index.title

    def test_index_codex_lite(self):
        finder = LocationFinder()
        index = finder.index_file(str(FIXTURES / 'sample-lite.md'))
        assert index is not None
        assert index.file_type == 'codex-lite'
        assert 'Incursion' in index.title

    def test_index_follows_includes(self):
        finder = LocationFinder()
        index = finder.index_file(str(FIXTURES / 'include-parent.codex.yaml'))
        assert index is not None
        assert 'Included Chapter' in index.child_names
        assert len(index.included_files) > 0


class TestExtractLocationHints:
    """Test instruction parsing."""

    def test_chapter_reference(self):
        finder = LocationFinder()
        hints = finder.extract_location_hints("after the battle in chapter 5")
        assert hints.chapter == '5'
        assert hints.position == 'after'

    def test_character_names(self):
        finder = LocationFinder()
        hints = finder.extract_location_hints("when Elena meets Marcus")
        assert 'Elena' in hints.character_refs
        assert 'Marcus' in hints.character_refs

    def test_position_before(self):
        finder = LocationFinder()
        hints = finder.extract_location_hints("before the ending")
        assert hints.position == 'before'

    def test_keywords_extracted(self):
        finder = LocationFinder()
        hints = finder.extract_location_hints("after the hyperborean incursion")
        assert len(hints.keywords) > 0
