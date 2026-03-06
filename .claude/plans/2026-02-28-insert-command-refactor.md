# /insert Command Refactor — Fix All Bugs & Follow Best Practices

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the `/insert` command work 100% of the time by fixing all identified bugs in the three backing scripts, adding comprehensive tests, and refactoring `insert.md` to follow plugin skill best practices (progressive disclosure, lean body).

**Architecture:** Three Python scripts (`note_parser.py`, `location_finder.py`, `insert_engine.py`) back the `insert.md` command. Fix bugs in each script with TDD, then refactor the command spec to extract edge cases/workflows/templates into plugin-level `references/` files (using `${CLAUDE_PLUGIN_ROOT}/references/` convention matching atlas, analysis, etc.). The agent-search steps (4-5) stay as prompt instructions since they're inherently non-deterministic — but we tighten the prompts and add validation.

**Pre-existing edits (already applied by user, do NOT redo):**
- Description shortened to "Insert notes into Codex manuscripts by location"
- "When This Skill Applies" rewritten to imperative "When to Apply" style
- `argument-hint: "[instruction or --batch notes.txt]"` added to frontmatter

**Tech Stack:** Python 3, pytest, ruamel.yaml, PyYAML (safe_load for indexing)

---

## Bug Summary

| # | Bug | File | Severity |
|---|-----|------|----------|
| B1 | `accept_inserts` / `reject_inserts` index matching is O(n²) and fragile — re-scans original content inside `re.sub` callback | `insert_engine.py:751-763, 821-828` | **Critical** |
| B2 | `detect_format` checks `ext == '.codex'` but real files are `.codex.yaml` — misses them, falls through to content check | `insert_engine.py:102` | **High** |
| B3 | YAML body-end detection in `_insert_codex_line_based` is brittle — `not line.startswith(' ') and ':' in stripped` breaks on body content containing colons | `insert_engine.py:554-558` | **High** |
| B4 | `generate_insert_marker` puts metadata with colons/quotes inside YAML body — ruamel.yaml may re-escape on roundtrip, corrupting markers | `insert_engine.py:153-194, 491-495` | **High** |
| B5 | `allowed-tools` in frontmatter lists `Task` which is not a valid tool name (should be `Agent` or removed) | `insert.md:3` | **Medium** |
| B6 | Marker regex in `find_pending_inserts` requires exact field order — any drift from `generate_insert_marker` breaks parsing | `insert_engine.py:647-658` | **Medium** |
| B7 | No test coverage for any of the three scripts | `tests/` | **High** |
| B8 | `_insert_codex_line_based` indents markers with `'  ' + line`, breaking `find_pending_inserts` regex (expects column 0) | `insert_engine.py:597-599` | **High** |

---

## Task 1: Test Infrastructure Setup

**Files:**
- Create: `tests/test_note_parser.py`
- Create: `tests/test_insert_engine.py`
- Create: `tests/test_location_finder.py`
- Create: `tests/fixtures/` (directory for test fixtures)
- Create: `tests/fixtures/sample.codex.yaml`
- Create: `tests/fixtures/sample-lite.md`
- Create: `tests/fixtures/sample-plain.md`
- Create: `tests/fixtures/batch-notes.txt`
- Modify: `pytest.ini` (add sys path for scripts)

**Step 1: Create test fixtures**

Create `tests/fixtures/sample.codex.yaml`:
```yaml
type: chapter
name: "Chapter 5: The Incursion"
title: "The Incursion"
summary: "The hyperborean forces attack the northern border."
body: |
  Dawn broke over the frozen plains.

  Elena watched from the ramparts as the first scouts appeared.

  "They're coming," Marcus said, drawing his sword.

  The hyperborean forces retreated beyond the ridge.

  Night fell and the camp grew silent.
children: []
```

Create `tests/fixtures/sample-lite.md`:
```markdown
---
title: "Chapter 5: The Incursion"
type: chapter
word_count: 42
---

# The Incursion

Dawn broke over the frozen plains.

Elena watched from the ramparts as the first scouts appeared.

"They're coming," Marcus said, drawing his sword.

The hyperborean forces retreated beyond the ridge.

Night fell and the camp grew silent.
```

Create `tests/fixtures/sample-plain.md`:
```markdown
# The Incursion

Dawn broke over the frozen plains.

Elena watched from the ramparts as the first scouts appeared.
```

Create `tests/fixtures/batch-notes.txt`:
```
after the hyperborean incursion

Elena drew her sword, the blade catching the firelight.
---
before Marcus arrives

The gates swung open with a groan of iron.
---
in chapter 5 near the fountain

Water splashed against the ancient stones.
```

**Step 2: Verify pytest can find and import scripts**

Add to `pytest.ini` after `addopts`:
```ini
pythonpath = plugins/chapterwise/scripts
```

**Step 3: Create skeleton test files with one smoke test each**

Create `tests/test_note_parser.py`:
```python
#!/usr/bin/env python3
"""Tests for note_parser module."""
import pytest
from note_parser import NoteParser


class TestNoteParserSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        parser = NoteParser()
        assert parser is not None
```

Create `tests/test_insert_engine.py`:
```python
#!/usr/bin/env python3
"""Tests for insert_engine module."""
import pytest
from insert_engine import InsertEngine


class TestInsertEngineSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        engine = InsertEngine()
        assert engine is not None
```

Create `tests/test_location_finder.py`:
```python
#!/usr/bin/env python3
"""Tests for location_finder module."""
import pytest
from location_finder import LocationFinder


class TestLocationFinderSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        finder = LocationFinder()
        assert finder is not None
```

**Step 4: Run tests to verify infrastructure**

Run: `cd /Users/phong/Projects/chapterwise-plugins && python -m pytest tests/test_note_parser.py tests/test_insert_engine.py tests/test_location_finder.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add tests/test_note_parser.py tests/test_insert_engine.py tests/test_location_finder.py tests/fixtures/ pytest.ini
git commit -m "test: add test infrastructure for insert command scripts"
```

---

## Task 2: Fix B2 — `detect_format` Misses `.codex.yaml` Extension

**Files:**
- Modify: `plugins/chapterwise/scripts/insert_engine.py:82-119`
- Test: `tests/test_insert_engine.py`

**Step 1: Write the failing test**

Add to `tests/test_insert_engine.py`:
```python
import os
import tempfile
import shutil
from pathlib import Path

FIXTURES = Path(__file__).parent / 'fixtures'


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
        # Create a temp .codex.yml by copying fixture
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_insert_engine.py::TestDetectFormat::test_codex_yaml_extension -v`
Expected: FAIL — returns `'unknown'` because `.yaml` suffix doesn't match `.codex`

**Step 3: Fix `detect_format`**

In `insert_engine.py`, replace the `detect_format` method body (lines 82-119):

```python
def detect_format(self, file_path: str) -> str:
    path = Path(file_path)
    name_lower = path.name.lower()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(4096)
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
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_insert_engine.py::TestDetectFormat -v`
Expected: 4 PASS

**Step 5: Commit**

```bash
git add plugins/chapterwise/scripts/insert_engine.py tests/test_insert_engine.py
git commit -m "fix: detect_format now handles .codex.yaml/.codex.yml extensions"
```

---

## Task 3: Fix B3 — Brittle YAML Body-End Detection in `_insert_codex_line_based`

**Files:**
- Modify: `plugins/chapterwise/scripts/insert_engine.py:506-573`
- Test: `tests/test_insert_engine.py`

**Step 1: Write the failing test**

Add to `tests/test_insert_engine.py`:
```python
class TestInsertCodexLineBased:
    """Test line-based YAML insertion (fallback path)."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_codex(self, body_text):
        """Create a codex file with given body content."""
        content = f"""type: chapter
name: "Test Chapter"
body: |
{self._indent(body_text, 2)}
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)
        return path

    def _indent(self, text, spaces):
        return '\n'.join(' ' * spaces + line for line in text.split('\n'))

    def test_body_with_colons_not_treated_as_yaml_key(self):
        """B3: Body text containing colons must not be mistaken for YAML keys."""
        body = 'She said: "hello"\n\nnote: this is body text\n\nEnd of chapter.'
        path = self._make_codex(body)

        engine = InsertEngine()
        result = engine.insert(
            file_path=path,
            content="INSERTED TEXT",
            line_number=3,  # After "note: this is body text"
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexLineBased::test_body_with_colons_not_treated_as_yaml_key -v`
Expected: FAIL — body detection ends prematurely at "note: this is body text"

**Step 3: Fix body-end detection**

In `insert_engine.py`, replace the body detection loop (lines 534-558) with indent-aware logic:

```python
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
                        # Block scalar — body indent is determined by first
                        # content line
                        body_indent = -1  # Will be set from first content line
                    elif after_body:
                        # Inline body value — not a block, single line
                        body_end = i + 1
                        in_body = False
            else:
                # Inside body block scalar
                if stripped == '':
                    # Blank lines are allowed inside body
                    continue

                if body_indent == -1:
                    # First content line determines the body indent level
                    body_indent = current_indent

                # A line at or below the original key indent level means
                # we've left the body block scalar
                if current_indent <= body_indent - 1 and stripped and ':' in stripped:
                    # Heuristic: top-level key has 0 indent, body content has 2+
                    # A line with 0 indent containing "key:" is a new YAML key
                    if current_indent == 0 or (body_indent > 0 and current_indent < body_indent):
                        body_end = i
                        break
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexLineBased -v`
Expected: 2 PASS

**Step 5: Commit**

```bash
git add plugins/chapterwise/scripts/insert_engine.py tests/test_insert_engine.py
git commit -m "fix: YAML body-end detection uses indent level instead of colon heuristic"
```

---

## Task 4: Fix B1 + B6 — Broken Index Matching AND Brittle Marker Regex (Combined)

These two bugs are fixed together because Task 6's flexible regex replaces the same pattern
used in accept/reject. Fixing them separately would cause intermediate test breakage.

**Files:**
- Modify: `plugins/chapterwise/scripts/insert_engine.py:646-838` (find_pending_inserts, accept_inserts, reject_inserts)
- Test: `tests/test_insert_engine.py`

**Step 1: Write failing tests for BOTH bugs**

Add to `tests/test_insert_engine.py`:
```python
class TestFindPendingInserts:
    """Test marker parsing resilience (B6)."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = InsertEngine()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_standard_marker(self):
        """Standard markers generated by engine are found."""
        marker = self.engine.generate_insert_marker(
            content="Test content",
            source="test",
            instruction="after battle",
            confidence=0.85,
            matched_after="the battle ended"
        )
        path = os.path.join(self.tmpdir, 'test.md')
        with open(path, 'w') as f:
            f.write(f"Before.\n\n{marker}\n\nAfter.\n")

        pending = self.engine.find_pending_inserts(path)
        assert len(pending) == 1
        assert pending[0].content == "Test content"
        assert pending[0].confidence == 0.85

    def test_marker_with_extra_whitespace(self):
        """B6: Markers with extra whitespace between fields still parse."""
        marker_text = """<!-- INSERT
time: 2024-01-15T10:30:00Z
source: notepad

instruction: "after battle"
confidence: 0.85
matched_after: "the battle ended"
-->
Test content
<!-- /INSERT -->"""
        path = os.path.join(self.tmpdir, 'test.md')
        with open(path, 'w') as f:
            f.write(marker_text)

        pending = self.engine.find_pending_inserts(path)
        assert len(pending) == 1

    def test_marker_with_reordered_fields(self):
        """B6: Markers with different field order still parse."""
        marker_text = """<!-- INSERT
source: notepad
time: 2024-01-15T10:30:00Z
confidence: 0.85
instruction: "after battle"
matched_after: "ended"
-->
Content here
<!-- /INSERT -->"""
        path = os.path.join(self.tmpdir, 'test.md')
        with open(path, 'w') as f:
            f.write(marker_text)

        pending = self.engine.find_pending_inserts(path)
        assert len(pending) == 1
        assert pending[0].content == "Content here"


class TestAcceptRejectInserts:
    """Test accept/reject workflows (B1)."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = InsertEngine()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _make_file_with_inserts(self, num_inserts=3):
        """Create a markdown file with N pending INSERT markers."""
        lines = ["# Test Document\n\n"]
        for i in range(1, num_inserts + 1):
            marker = self.engine.generate_insert_marker(
                content=f"Insert content {i}",
                source="test",
                instruction=f"instruction {i}",
                confidence=0.8 + i * 0.05,
                matched_after=f"matched text {i}"
            )
            lines.append(f"Paragraph {i}.\n\n")
            lines.append(marker + "\n\n")

        lines.append("Final paragraph.\n")
        path = os.path.join(self.tmpdir, 'test.md')
        with open(path, 'w') as f:
            f.write(''.join(lines))
        return path

    def test_accept_all(self):
        """Accept all inserts removes all markers, keeps content."""
        path = self._make_file_with_inserts(3)
        count, errors = self.engine.accept_inserts(path, create_backup=False)
        assert count == 3
        assert errors == []
        with open(path) as f:
            content = f.read()
        assert '<!-- INSERT' not in content
        assert 'Insert content 1' in content
        assert 'Insert content 2' in content
        assert 'Insert content 3' in content

    def test_accept_specific_indices(self):
        """B1: Accept only indices [1, 3] keeps insert 2 as pending."""
        path = self._make_file_with_inserts(3)
        count, errors = self.engine.accept_inserts(path, indices=[1, 3], create_backup=False)
        assert count == 2
        with open(path) as f:
            content = f.read()
        assert 'Insert content 1' in content
        assert 'Insert content 3' in content
        # Insert 2 still has markers
        assert 'instruction 2' in content
        assert '<!-- INSERT' in content

    def test_reject_all(self):
        """Reject all inserts removes markers AND content."""
        path = self._make_file_with_inserts(2)
        count, errors = self.engine.reject_inserts(path, create_backup=False)
        assert count == 2
        with open(path) as f:
            content = f.read()
        assert '<!-- INSERT' not in content
        assert 'Insert content 1' not in content
        assert 'Insert content 2' not in content
        assert 'Final paragraph' in content

    def test_reject_specific_indices(self):
        """B1: Reject only index [2] keeps inserts 1 and 3."""
        path = self._make_file_with_inserts(3)
        count, errors = self.engine.reject_inserts(path, indices=[2], create_backup=False)
        assert count == 1
        with open(path) as f:
            content = f.read()
        assert 'Insert content 1' in content
        assert 'Insert content 2' not in content
        assert 'Insert content 3' in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_insert_engine.py::TestAcceptRejectInserts::test_accept_specific_indices tests/test_insert_engine.py::TestFindPendingInserts::test_marker_with_reordered_fields -v`
Expected: FAIL on both

**Step 3: Fix all three methods together**

First, replace `find_pending_inserts` with field-order-independent parsing:

```python
    def find_pending_inserts(self, file_path: str) -> List[PendingInsert]:
        pending = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Two-part pattern: find marker blocks, then parse fields inside
        # Use [^<]* for header to avoid matching across INSERT blocks
        block_pattern = re.compile(
            r'<!-- INSERT\s*\n((?:(?!-->)[^\n]*\n)*?)-->\s*\n(.*?)\n<!-- /INSERT -->',
            re.DOTALL
        )

        lines = content.split('\n')
        char_to_line = {}
        char_count = 0
        for i, line in enumerate(lines, 1):
            char_to_line[char_count] = i
            char_count += len(line) + 1

        for match in block_pattern.finditer(content):
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
```

Then update accept_inserts and reject_inserts to use:
1. The same flexible block pattern (not the old strict field-order one)
2. A simple counter instead of O(n²) re-scan

In `accept_inserts`, replace the pattern and callback:

```python
        # Flexible block pattern matching (same as find_pending_inserts)
        pattern = re.compile(
            r'<!-- INSERT\s*\n(?:(?!-->)[^\n]*\n)*?-->\s*\n(.*?)\n<!-- /INSERT -->',
            re.DOTALL
        )

        accepted_count = 0
        match_counter = 0

        def replace_insert(match):
            nonlocal accepted_count, match_counter
            match_counter += 1
            content_only = match.group(1)

            if indices:
                if match_counter not in indices_set:
                    return match.group(0)  # Keep unchanged

            accepted_count += 1
            return content_only

        new_content = pattern.sub(replace_insert, content)
```

In `reject_inserts`, same pattern and counter fix:

```python
        pattern = re.compile(
            r'<!-- INSERT\s*\n(?:(?!-->)[^\n]*\n)*?-->\s*\n.*?\n<!-- /INSERT -->\n?',
            re.DOTALL
        )

        rejected_count = 0
        match_counter = 0
        indices_set = set(indices) if indices else None

        def remove_insert(match):
            nonlocal rejected_count, match_counter
            match_counter += 1

            if indices_set:
                if match_counter not in indices_set:
                    return match.group(0)

            rejected_count += 1
            return ''

        new_content = pattern.sub(remove_insert, content)
```

**Step 4: Run ALL tests to verify they pass**

Run: `python -m pytest tests/test_insert_engine.py::TestFindPendingInserts tests/test_insert_engine.py::TestAcceptRejectInserts -v`
Expected: 7 PASS (3 find + 4 accept/reject)

**Step 5: Commit**

```bash
git add plugins/chapterwise/scripts/insert_engine.py tests/test_insert_engine.py
git commit -m "fix: accept/reject uses counter not rescan (B1), marker regex is field-order-independent (B6)"
```

---

## Task 5: Fix B4 — Protect INSERT Markers from ruamel.yaml Re-Escaping

**Files:**
- Modify: `plugins/chapterwise/scripts/insert_engine.py:421-504`
- Test: `tests/test_insert_engine.py`

**Step 1: Write the failing test**

Add to `tests/test_insert_engine.py`:
```python
class TestInsertCodexYamlRuamel:
    """Test ruamel.yaml insertion path."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_markers_survive_ruamel_roundtrip(self):
        """B4: INSERT markers must not be corrupted by ruamel.yaml dump."""
        content = """type: chapter
name: "Test Chapter"
body: |
  Dawn broke over the frozen plains.

  Elena watched from the ramparts.

  Night fell and the camp grew silent.
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)

        engine = InsertEngine()
        result = engine.insert(
            file_path=path,
            content="The scouts returned.",
            line_number=3,
            insert_after=True,
            source="test",
            instruction='after "the ramparts"',
            confidence=0.87,
            matched_after="Elena watched from the ramparts.",
            create_backup=False,
            add_markers=True
        )

        assert result.success

        with open(path) as f:
            output = f.read()

        # Markers must be parseable
        pending = engine.find_pending_inserts(path)
        assert len(pending) == 1
        assert pending[0].content == "The scouts returned."
        assert pending[0].confidence == 0.87

    def test_accept_after_ruamel_insert(self):
        """Markers inserted via ruamel must be acceptable."""
        content = """type: chapter
name: "Test"
body: |
  Line one.
  Line two.
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)

        engine = InsertEngine()
        engine.insert(
            file_path=path,
            content="New line.",
            line_number=1,
            insert_after=True,
            create_backup=False,
            add_markers=True
        )

        count, errors = engine.accept_inserts(path, create_backup=False)
        assert count == 1
        assert errors == []
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexYamlRuamel::test_markers_survive_ruamel_roundtrip -v`
Expected: Likely FAIL — ruamel may re-escape the marker content within the YAML block scalar

**Step 3: Fix ruamel insertion to use LiteralScalarString**

In `_insert_codex_yaml_ruamel`, ensure the body stays as a literal block scalar:

```python
    def _insert_codex_yaml_ruamel(self, ...):
        import ruamel.yaml
        from ruamel.yaml.scalarstring import LiteralScalarString

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096

        with open(file_path, 'r', encoding='utf-8') as f:
            doc = yaml.load(f)

        if doc is None:
            doc = {}

        body = doc.get('body', '')
        if not body:
            body = ''

        # Convert to plain string for manipulation
        body_str = str(body)
        body_lines = body_str.split('\n')

        if line_number < 1:
            line_number = 1
        if line_number > len(body_lines):
            line_number = len(body_lines)

        if add_markers:
            insert_content = self.generate_insert_marker(
                content=content, source=source, instruction=instruction,
                confidence=confidence, matched_after=matched_after
            )
        else:
            insert_content = content

        if insert_after:
            insert_index = line_number
        else:
            insert_index = line_number - 1

        before_context = body_lines[max(0, insert_index - 1)].strip() if insert_index > 0 else ""
        after_context = body_lines[insert_index].strip() if insert_index < len(body_lines) else ""

        body_lines.insert(insert_index, insert_content)

        # Force literal block scalar to preserve markers exactly
        doc['body'] = LiteralScalarString('\n'.join(body_lines))

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)

        return InsertResult(
            success=True, file_path=file_path, line_number=line_number,
            before_context=before_context, after_context=after_context,
            backup_path=backup_path
        )
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexYamlRuamel -v`
Expected: 2 PASS

**Step 5: Commit**

```bash
git add plugins/chapterwise/scripts/insert_engine.py tests/test_insert_engine.py
git commit -m "fix: use LiteralScalarString to prevent ruamel from re-escaping INSERT markers"
```

---

---

## Task 6: Fix B8 — Line-Based Fallback Indents Markers, Breaking Parsing

**Files:**
- Modify: `plugins/chapterwise/scripts/insert_engine.py:506-629` (`_insert_codex_line_based`)
- Test: `tests/test_insert_engine.py`

**Step 1: Write the failing test**

Add to `tests/test_insert_engine.py`:
```python
class TestInsertCodexLineBasedMarkers:
    """Test that line-based YAML insertion preserves findable markers (B8)."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_markers_findable_after_line_based_insert(self):
        """B8: Markers inserted via line-based fallback must be parseable by find_pending_inserts."""
        content = """type: chapter
name: "Test Chapter"
body: |
  Dawn broke over the frozen plains.
  Elena watched from the ramparts.
  Night fell and the camp grew silent.
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)

        engine = InsertEngine()

        # Force the line-based path by monkeypatching ruamel import
        import importlib
        original_insert_codex = engine._insert_codex
        engine._insert_codex = engine._insert_codex_line_based

        result = engine.insert(
            file_path=path,
            content="Scouts returned at dusk.",
            line_number=2,
            insert_after=True,
            source="test",
            instruction="after ramparts",
            confidence=0.88,
            matched_after="Elena watched from the ramparts.",
            create_backup=False,
            add_markers=True
        )
        assert result.success

        # Markers must be findable even though they're inside indented YAML body
        pending = engine.find_pending_inserts(path)
        assert len(pending) == 1, f"Expected 1 pending insert, found {len(pending)}"
        assert pending[0].content == "Scouts returned at dusk."

        # Restore
        engine._insert_codex = original_insert_codex

    def test_accept_after_line_based_insert(self):
        """Markers inserted via line-based path must be acceptable."""
        content = """type: chapter
name: "Test"
body: |
  Line one.
  Line two.
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)

        engine = InsertEngine()
        engine._insert_codex = engine._insert_codex_line_based

        engine.insert(
            file_path=path,
            content="New line.",
            line_number=1,
            insert_after=True,
            create_backup=False,
            add_markers=True
        )

        count, errors = engine.accept_inserts(path, create_backup=False)
        assert count == 1
        assert errors == []
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexLineBasedMarkers::test_markers_findable_after_line_based_insert -v`
Expected: FAIL — markers are indented with 2 spaces, `find_pending_inserts` regex can't find them

**Step 3: Fix — update `find_pending_inserts` to handle indented markers AND fix line-based indentation**

Two-part fix:

**Part A:** In `_insert_codex_line_based`, do NOT indent the marker lines themselves — only indent the actual content within the markers. Or simpler: don't indent markers at all; write them at column 0 as a YAML comment (HTML comments are valid in YAML block scalars regardless of indent).

Replace the indentation logic in `_insert_codex_line_based` (around lines 596-600):

```python
        # For YAML body, the content needs proper indentation but markers
        # should remain at column 0 so find_pending_inserts can find them.
        # HTML comments are valid inside YAML block scalars at any indent level.
        if not insert_content.endswith('\n'):
            insert_content += '\n'
```

**Part B:** Also update `find_pending_inserts` block pattern to optionally match leading whitespace on marker lines (defense in depth):

```python
        block_pattern = re.compile(
            r'^[ \t]*<!-- INSERT\s*\n((?:(?!-->)[^\n]*\n)*?)[ \t]*-->\s*\n(.*?)\n[ \t]*<!-- /INSERT -->',
            re.DOTALL | re.MULTILINE
        )
```

And update the same pattern in `accept_inserts` and `reject_inserts`.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_insert_engine.py::TestInsertCodexLineBasedMarkers -v`
Expected: 2 PASS

Also verify no regressions:
Run: `python -m pytest tests/test_insert_engine.py::TestFindPendingInserts tests/test_insert_engine.py::TestAcceptRejectInserts -v`
Expected: 7 PASS (still passing)

**Step 5: Commit**

```bash
git add plugins/chapterwise/scripts/insert_engine.py tests/test_insert_engine.py
git commit -m "fix: line-based YAML insert no longer breaks marker parsing (B8)"
```

---

## Task 7: Add Tests for `note_parser.py`

**Files:**
- Modify: `tests/test_note_parser.py`

**Step 1: Write comprehensive tests**

Replace `tests/test_note_parser.py`:
```python
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
```

**Step 2: Run tests**

Run: `python -m pytest tests/test_note_parser.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_note_parser.py
git commit -m "test: add comprehensive tests for note_parser"
```

---

## Task 8: Add Tests for `location_finder.py`

**Files:**
- Modify: `tests/test_location_finder.py`
- Create: `tests/fixtures/include-parent.codex.yaml`
- Create: `tests/fixtures/include-child.codex.yaml`

**Step 1: Create include fixtures**

Create `tests/fixtures/include-parent.codex.yaml`:
```yaml
type: project
name: "Test Project"
title: "Test Project"
summary: "A test project with includes."
body: ""
children:
  - include: "./include-child.codex.yaml"
```

Create `tests/fixtures/include-child.codex.yaml`:
```yaml
type: chapter
name: "Included Chapter"
title: "The Included Chapter"
summary: "This chapter is included via directive."
body: |
  Content of the included chapter.
children: []
```

**Step 2: Write tests**

Replace `tests/test_location_finder.py`:
```python
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
```

**Step 3: Run tests**

Run: `python -m pytest tests/test_location_finder.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/test_location_finder.py tests/fixtures/include-parent.codex.yaml tests/fixtures/include-child.codex.yaml
git commit -m "test: add comprehensive tests for location_finder"
```

---

## Task 9: Fix B5 — Fix Frontmatter and Refactor `insert.md` for Progressive Disclosure

**Note:** The user has already shortened the description and rewritten "When to Apply" to
imperative style. Do NOT redo those edits. Also preserve the existing `argument-hint` field.

**Files:**
- Modify: `plugins/chapterwise/commands/insert.md` (fix `allowed-tools`, extract sections)
- Create: `plugins/chapterwise/references/insert-edge-cases.md` (plugin-level, matches existing convention)
- Create: `plugins/chapterwise/references/insert-workflows.md`
- Create: `plugins/chapterwise/references/insert-marker-format.md`

**Step 1: Create `references/insert-edge-cases.md`**

Create in `plugins/chapterwise/references/` (same directory as `language-rules.md` and `atlas-section-schemas.md`):

```markdown
# Insert Command — Edge Cases & Policies

## Content Edge Cases
[copy table from insert.md lines 366-373]

## Matching Edge Cases
[copy table from insert.md lines 376-383]

## File System Edge Cases
[copy table from insert.md lines 386-395]

## Batch Edge Cases
[copy table from insert.md lines 398-404]

## Marker Edge Cases
[copy table from insert.md lines 407-414]
```

**Step 2: Create `references/insert-workflows.md`**

```markdown
# Insert Command — Secondary Workflows

## Accept Workflow
[copy from insert.md Accept Workflow section]

## Undo Workflow
[copy from insert.md Undo Workflow section]

## Summary Report Template
[copy from insert.md Summary Report section]

## Supported Formats
[copy from insert.md Supported Formats table]
```

**Step 3: Create `references/insert-marker-format.md`**

```markdown
# INSERT Marker Format

## Marker Structure
[copy INSERT marker HTML comment spec from insert.md]

## Field Descriptions
- time: ISO 8601 UTC timestamp
- source: Origin of the insert (e.g., "notepad", "cli", "clipboard")
- instruction: Original location instruction from user
- confidence: 0.00-1.00 confidence score
- matched_after: Context text the insert was matched after

Note: Fields are parsed order-independently. The marker regex tolerates
reordered fields and extra whitespace between them.
```

**Step 4: Refactor `insert.md`**

Only change that needs to be made to frontmatter — fix `allowed-tools` (`Task` is not a valid tool):
```yaml
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent, AskUserQuestion
```

Remove the extracted sections (edge cases, accept/undo workflows, marker format, supported formats, summary report template) and add references using the plugin convention:
```markdown
## ADDITIONAL RESOURCES

For edge cases, secondary workflows, and format specs, consult:
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-edge-cases.md`** — All edge case tables and policies
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-workflows.md`** — Accept, Undo, Summary Report workflows
- **`${CLAUDE_PLUGIN_ROOT}/references/insert-marker-format.md`** — INSERT marker HTML comment spec

## QUICK REFERENCE
[keep the quick reference section — it's useful at ~35 lines]
```

The resulting `insert.md` should be ~200-250 lines (down from ~480), containing only:
1. Frontmatter (with existing description, argument-hint, triggers — unchanged)
2. When to Apply (already rewritten by user — unchanged)
3. Invocation Modes table
4. Command Flags table
5. Steps 1-7 (core workflow)
6. Additional Resources section (new — points to references/)
7. Quick Reference
8. Remember list

**Step 5: Verify the command still has all content accessible**

Run: `wc -l plugins/chapterwise/commands/insert.md` — should be ~200-250 lines
Run: `ls plugins/chapterwise/references/insert-*` — should show 3 files

**Step 6: Commit**

```bash
git add plugins/chapterwise/commands/insert.md plugins/chapterwise/references/insert-*.md
git commit -m "refactor: extract insert.md edge cases and workflows into references/ for progressive disclosure"
```

---

## Task 10: Full Integration Test & Final Verification

**Files:**
- Modify: `tests/test_insert_engine.py` (add integration test)

**Step 1: Write end-to-end integration test**

Add to `tests/test_insert_engine.py`:
```python
class TestInsertIntegration:
    """End-to-end integration tests."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = InsertEngine()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_full_lifecycle_markdown(self):
        """Insert → find → accept lifecycle on markdown file."""
        src = str(FIXTURES / 'sample-lite.md')
        path = os.path.join(self.tmpdir, 'chapter.md')
        shutil.copy(src, path)

        # Insert with markers
        result = self.engine.insert(
            file_path=path, content="New scene content.",
            line_number=5, insert_after=True,
            source="test", instruction="after ramparts",
            confidence=0.9, matched_after="Elena watched from the ramparts.",
            create_backup=False, add_markers=True
        )
        assert result.success

        # Find pending
        pending = self.engine.find_pending_inserts(path)
        assert len(pending) == 1
        assert pending[0].content == "New scene content."

        # Accept
        count, errors = self.engine.accept_inserts(path, create_backup=False)
        assert count == 1
        assert errors == []

        # Verify clean
        pending_after = self.engine.find_pending_inserts(path)
        assert len(pending_after) == 0

        with open(path) as f:
            final = f.read()
        assert "New scene content." in final
        assert "<!-- INSERT" not in final

    def test_full_lifecycle_codex_yaml(self):
        """Insert → find → accept lifecycle on codex YAML file."""
        src = str(FIXTURES / 'sample.codex.yaml')
        path = os.path.join(self.tmpdir, 'chapter.codex.yaml')
        shutil.copy(src, path)

        result = self.engine.insert(
            file_path=path, content="Scouts returned at dusk.",
            line_number=3, insert_after=True,
            source="test", instruction="after scouts appeared",
            confidence=0.92, matched_after="the first scouts appeared",
            create_backup=False, add_markers=True
        )
        assert result.success

        pending = self.engine.find_pending_inserts(path)
        assert len(pending) == 1

        count, errors = self.engine.accept_inserts(path, create_backup=False)
        assert count == 1

        with open(path) as f:
            final = f.read()
        assert "Scouts returned at dusk." in final
        assert "<!-- INSERT" not in final

    def test_backup_creation(self):
        """Backups are created in .backups/ directory."""
        src = str(FIXTURES / 'sample-lite.md')
        path = os.path.join(self.tmpdir, 'chapter.md')
        shutil.copy(src, path)

        engine = InsertEngine(backup_dir=os.path.join(self.tmpdir, '.backups'))
        result = engine.insert(
            file_path=path, content="Test.",
            line_number=1, insert_after=True,
            create_backup=True, add_markers=False
        )

        assert result.success
        assert result.backup_path is not None
        assert os.path.exists(result.backup_path)
```

**Step 2: Run all tests**

Run: `python -m pytest tests/test_note_parser.py tests/test_insert_engine.py tests/test_location_finder.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/test_insert_engine.py
git commit -m "test: add end-to-end integration tests for insert lifecycle"
```

---

## Task 11: Hardening — Fallback Path, Env Var Guard, Defensive Patterns

**Files:**
- Modify: `tests/test_insert_engine.py`
- Modify: `plugins/chapterwise/commands/insert.md` (add env var check to Step 1)

**Step 1: Test ruamel.yaml fallback selection**

Add to `tests/test_insert_engine.py`:
```python
import unittest.mock

class TestFallbackBehavior:
    """Test that line-based fallback is used when ruamel is unavailable."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_falls_back_to_line_based_without_ruamel(self):
        """When ruamel.yaml is not installed, line-based insertion is used."""
        content = """type: chapter
name: "Test"
body: |
  Line one.
  Line two.
children: []
"""
        path = os.path.join(self.tmpdir, 'test.codex.yaml')
        with open(path, 'w') as f:
            f.write(content)

        engine = InsertEngine()

        # Monkeypatch: make ruamel import fail inside _insert_codex
        with unittest.mock.patch.dict('sys.modules', {'ruamel': None, 'ruamel.yaml': None}):
            result = engine.insert(
                file_path=path,
                content="Fallback content.",
                line_number=1,
                insert_after=True,
                create_backup=False,
                add_markers=False
            )

        assert result.success
        with open(path) as f:
            output = f.read()
        assert "Fallback content." in output
```

**Step 2: Add env var guard to insert.md Step 1**

In `insert.md`, add to the beginning of Step 1 (Parse the Request):

```markdown
**Pre-flight check:** Before proceeding, verify that `${CLAUDE_PLUGIN_ROOT}` resolves to a
valid path containing the `scripts/` directory. If not, report an error:
"Cannot find ChapterWise plugin scripts. Is the plugin installed correctly?"
```

**Step 3: Run all tests**

Run: `python -m pytest tests/test_insert_engine.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/test_insert_engine.py plugins/chapterwise/commands/insert.md
git commit -m "test: add fallback path and hardening tests"
```

---

## Summary

| Task | What | Bug Fixed |
|------|------|-----------|
| 1 | Test infrastructure + fixtures | — |
| 2 | Fix `detect_format` for `.codex.yaml` | B2 |
| 3 | Fix YAML body-end detection | B3 |
| 4 | Fix accept/reject index matching + flexible marker regex | B1 + B6 |
| 5 | Protect markers from ruamel re-escaping | B4 |
| 6 | Fix line-based fallback marker indentation | B8 |
| 7 | Tests for `note_parser.py` | B7 |
| 8 | Tests for `location_finder.py` | B7 |
| 9 | Fix frontmatter + progressive disclosure refactor | B5 |
| 10 | Full integration tests | — |
| 11 | Hardening — fallback path, env var guard | — |

After all 11 tasks: **7 bugs fixed, 35+ tests, command spec reduced from ~480 to ~230 lines**.
