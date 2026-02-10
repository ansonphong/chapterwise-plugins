# Schema Definitions Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden schema definitions by fixing pattern mismatches, creating a shared validation utility, and adding schema validation tests.

**Architecture:** Create a central `schema_validator.py` module that loads JSON schemas and provides validation functions. Update schemas to fix pattern mismatches with actual code. Add pytest-based tests to verify schema validity.

**Tech Stack:** Python 3.11+, jsonschema library, pytest

---

## Prerequisites

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
pip install jsonschema pytest
```

---

## Task 1: Fix ID Pattern Mismatch in Codex Schema

**Files:**
- Modify: `schemas/codex-v1.2.schema.json:13-15`

**Problem:** Schema ID pattern `^[a-zA-Z0-9_-]+$` doesn't allow UUID format that auto-fixer generates.

**Step 1: Update the id pattern to allow both simple IDs and UUIDs**

In `schemas/codex-v1.2.schema.json`, change:

```json
"id": {
  "type": "string",
  "description": "Unique identifier (UUID v4 recommended)",
  "pattern": "^[a-zA-Z0-9_-]+$"
}
```

To:

```json
"id": {
  "type": "string",
  "description": "Unique identifier (UUID v4 or simple slug)",
  "pattern": "^[a-zA-Z0-9_-]+$|^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
}
```

**Step 2: Verify the change**

```bash
python3 -c "import json; d=json.load(open('schemas/codex-v1.2.schema.json')); print('ID pattern:', d['properties']['id']['pattern'])"
```

Expected output: Pattern shows both alternatives with `|`

**Step 3: Commit**

```bash
git add schemas/codex-v1.2.schema.json
git commit -m "fix(schema): allow UUID format in id pattern"
```

---

## Task 2: Fix Analysis Entry ID Pattern

**Files:**
- Modify: `schemas/analysis-v1.2.schema.json:115-117`

**Problem:** Pattern `^entry-\\d{8}T\\d{6}Z$` is too strict - doesn't allow optional suffixes.

**Step 1: Relax the entry ID pattern**

In `schemas/analysis-v1.2.schema.json`, change:

```json
"id": {
  "type": "string",
  "description": "Entry ID (format: entry-YYYYMMDDTHHMMSSz)",
  "pattern": "^entry-\\d{8}T\\d{6}Z$"
}
```

To:

```json
"id": {
  "type": "string",
  "description": "Entry ID (format: entry-YYYYMMDDTHHMMSSZ with optional suffix)",
  "pattern": "^entry-\\d{8}T\\d{6}Z(-[a-z0-9]+)?$"
}
```

**Step 2: Verify the change**

```bash
python3 -c "import json; d=json.load(open('schemas/analysis-v1.2.schema.json')); print('Entry ID pattern:', d['\$defs']['analysisEntry']['properties']['id']['pattern'])"
```

**Step 3: Commit**

```bash
git add schemas/analysis-v1.2.schema.json
git commit -m "fix(schema): relax analysis entry ID pattern to allow suffix"
```

---

## Task 3: Fix Attribute Key Pattern Inconsistency

**Files:**
- Modify: `schemas/codex-v1.2.schema.json:177-179`

**Problem:** Schema says `^[a-zA-Z_][a-zA-Z0-9_]*$` (no hyphens), but auto-fixer allows `^[a-z][a-z0-9_-]*$` (lowercase with hyphens).

**Step 1: Update attribute key pattern to match auto-fixer**

In `schemas/codex-v1.2.schema.json`, in the `attribute` definition under `$defs`, change:

```json
"key": {
  "type": "string",
  "description": "Attribute identifier (snake_case recommended)",
  "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"
}
```

To:

```json
"key": {
  "type": "string",
  "description": "Attribute identifier (snake_case or kebab-case, lowercase)",
  "pattern": "^[a-z][a-z0-9_-]*$"
}
```

**Step 2: Verify the change**

```bash
python3 -c "import json; d=json.load(open('schemas/codex-v1.2.schema.json')); print('Attr key pattern:', d['\$defs']['attribute']['properties']['key']['pattern'])"
```

**Step 3: Commit**

```bash
git add schemas/codex-v1.2.schema.json
git commit -m "fix(schema): align attribute key pattern with auto-fixer"
```

---

## Task 4: Remove 'lite' from formatVersion Enum

**Files:**
- Modify: `schemas/codex-v1.2.schema.json:132-134`

**Problem:** "lite" is not a valid formatVersion - Codex Lite files are markdown, not YAML.

**Step 1: Remove 'lite' from the enum**

In `schemas/codex-v1.2.schema.json`, in the `metadata` definition, change:

```json
"formatVersion": {
  "type": "string",
  "enum": ["1.0", "1.1", "1.2", "lite"],
  "description": "Codex format version"
}
```

To:

```json
"formatVersion": {
  "type": "string",
  "enum": ["1.0", "1.1", "1.2"],
  "description": "Codex format version"
}
```

**Step 2: Verify the change**

```bash
python3 -c "import json; d=json.load(open('schemas/codex-v1.2.schema.json')); print('formatVersion enum:', d['\$defs']['metadata']['properties']['formatVersion']['enum'])"
```

Expected: `['1.0', '1.1', '1.2']`

**Step 3: Commit**

```bash
git add schemas/codex-v1.2.schema.json
git commit -m "fix(schema): remove invalid 'lite' from formatVersion enum"
```

---

## Task 5: Create Schema Validator Utility

**Files:**
- Create: `plugins/chapterwise-codex/scripts/schema_validator.py`

**Step 1: Write the test file first**

Create `tests/test_schema_validator.py`:

```python
#!/usr/bin/env python3
"""Tests for schema_validator module."""
import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise-codex' / 'scripts'))
from schema_validator import SchemaValidator, validate_codex, validate_analysis


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_load_codex_schema(self):
        """Should load codex schema successfully."""
        validator = SchemaValidator()
        schema = validator.load_schema('codex')
        assert schema is not None
        assert schema.get('title') == 'Codex V1.2'

    def test_load_analysis_schema(self):
        """Should load analysis schema successfully."""
        validator = SchemaValidator()
        schema = validator.load_schema('analysis')
        assert schema is not None
        assert schema.get('title') == 'Codex Analysis File V1.2'

    def test_load_invalid_schema_type(self):
        """Should return None for unknown schema type."""
        validator = SchemaValidator()
        schema = validator.load_schema('nonexistent')
        assert schema is None


class TestValidateCodex:
    """Test codex validation."""

    def test_valid_minimal_codex(self):
        """Should validate minimal valid codex."""
        data = {
            'metadata': {'formatVersion': '1.2'}
        }
        is_valid, errors = validate_codex(data)
        assert is_valid is True
        assert errors == []

    def test_valid_full_codex(self):
        """Should validate full codex with all fields."""
        data = {
            'metadata': {
                'formatVersion': '1.2',
                'documentVersion': '1.0.0'
            },
            'id': 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
            'type': 'chapter',
            'name': 'Test Chapter',
            'body': 'Some content here',
            'attributes': [
                {'key': 'word_count', 'value': 100}
            ]
        }
        is_valid, errors = validate_codex(data)
        assert is_valid is True
        assert errors == []

    def test_invalid_missing_metadata(self):
        """Should fail when metadata is missing."""
        data = {'id': 'test', 'name': 'Test'}
        is_valid, errors = validate_codex(data)
        assert is_valid is False
        assert len(errors) > 0

    def test_invalid_format_version(self):
        """Should fail with invalid formatVersion."""
        data = {
            'metadata': {'formatVersion': '2.0'}
        }
        is_valid, errors = validate_codex(data)
        assert is_valid is False

    def test_uuid_id_accepted(self):
        """Should accept UUID format for id."""
        data = {
            'metadata': {'formatVersion': '1.2'},
            'id': 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d'
        }
        is_valid, errors = validate_codex(data)
        assert is_valid is True

    def test_simple_id_accepted(self):
        """Should accept simple slug format for id."""
        data = {
            'metadata': {'formatVersion': '1.2'},
            'id': 'my-chapter-1'
        }
        is_valid, errors = validate_codex(data)
        assert is_valid is True


class TestValidateAnalysis:
    """Test analysis validation."""

    def test_valid_analysis(self):
        """Should validate valid analysis file."""
        data = {
            'metadata': {'formatVersion': '1.2'},
            'id': 'test-analysis',
            'type': 'analysis',
            'name': 'Analysis Results',
            'attributes': [
                {'key': 'sourceFile', 'value': 'test.codex.yaml'}
            ],
            'children': []
        }
        is_valid, errors = validate_analysis(data)
        assert is_valid is True

    def test_invalid_analysis_missing_type(self):
        """Should fail when type is not 'analysis'."""
        data = {
            'metadata': {'formatVersion': '1.2'},
            'id': 'test-analysis',
            'type': 'wrong-type',
            'attributes': [{'key': 'sourceFile', 'value': 'test.yaml'}],
            'children': []
        }
        is_valid, errors = validate_analysis(data)
        assert is_valid is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_schema_validator.py -v
```

Expected: ModuleNotFoundError (schema_validator doesn't exist yet)

**Step 3: Create the schema_validator.py module**

Create `plugins/chapterwise-codex/scripts/schema_validator.py`:

```python
#!/usr/bin/env python3
"""
Schema Validator for Codex V1.2 and Analysis files.
Provides centralized JSON Schema validation for all scripts.

Usage:
    from schema_validator import validate_codex, validate_analysis

    is_valid, errors = validate_codex(data)
    if not is_valid:
        print(f"Validation errors: {errors}")
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import jsonschema
    from jsonschema import Draft202012Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    Draft202012Validator = None

logger = logging.getLogger(__name__)

# Schema directory relative to this file
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / 'schemas'

# Schema file mapping
SCHEMA_FILES = {
    'codex': 'codex-v1.2.schema.json',
    'analysis': 'analysis-v1.2.schema.json',
}


class SchemaValidator:
    """
    Centralized schema validator for Codex V1.2 format.

    Caches loaded schemas for performance.
    """

    def __init__(self, schema_dir: Path = None):
        """
        Initialize validator with optional custom schema directory.

        Args:
            schema_dir: Path to directory containing schema files.
                       Defaults to ../../../schemas relative to this file.
        """
        self.schema_dir = schema_dir or SCHEMA_DIR
        self._schema_cache: Dict[str, dict] = {}
        self._validator_cache: Dict[str, Any] = {}

    def load_schema(self, schema_type: str) -> Optional[dict]:
        """
        Load a schema by type name.

        Args:
            schema_type: One of 'codex' or 'analysis'

        Returns:
            Schema dict or None if not found
        """
        if schema_type in self._schema_cache:
            return self._schema_cache[schema_type]

        filename = SCHEMA_FILES.get(schema_type)
        if not filename:
            logger.warning(f"Unknown schema type: {schema_type}")
            return None

        schema_path = self.schema_dir / filename
        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return None

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            self._schema_cache[schema_type] = schema
            return schema
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema {schema_path}: {e}")
            return None

    def get_validator(self, schema_type: str) -> Optional[Any]:
        """
        Get a jsonschema validator for the given schema type.

        Args:
            schema_type: One of 'codex' or 'analysis'

        Returns:
            Draft202012Validator instance or None
        """
        if not HAS_JSONSCHEMA:
            logger.warning("jsonschema not installed, validation disabled")
            return None

        if schema_type in self._validator_cache:
            return self._validator_cache[schema_type]

        schema = self.load_schema(schema_type)
        if schema is None:
            return None

        validator = Draft202012Validator(schema)
        self._validator_cache[schema_type] = validator
        return validator

    def validate(self, data: dict, schema_type: str) -> Tuple[bool, List[str]]:
        """
        Validate data against a schema.

        Args:
            data: Data to validate
            schema_type: One of 'codex' or 'analysis'

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        if not HAS_JSONSCHEMA:
            # No validation library, assume valid
            return True, []

        validator = self.get_validator(schema_type)
        if validator is None:
            # Schema not found, skip validation
            return True, []

        errors = list(validator.iter_errors(data))

        if not errors:
            return True, []

        # Format error messages with path
        error_msgs = []
        for err in errors[:10]:  # Limit to 10 errors
            path = '.'.join(str(p) for p in err.absolute_path) or 'root'
            error_msgs.append(f"{path}: {err.message}")

        return False, error_msgs


# Module-level singleton for convenience
_default_validator = None


def _get_validator() -> SchemaValidator:
    """Get or create default validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = SchemaValidator()
    return _default_validator


def validate_codex(data: dict) -> Tuple[bool, List[str]]:
    """
    Validate codex data against the Codex V1.2 schema.

    Args:
        data: Parsed codex content (dict)

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        is_valid, errors = validate_codex(yaml.safe_load(content))
        if not is_valid:
            for error in errors:
                print(f"  - {error}")
    """
    return _get_validator().validate(data, 'codex')


def validate_analysis(data: dict) -> Tuple[bool, List[str]]:
    """
    Validate analysis data against the Analysis V1.2 schema.

    Args:
        data: Parsed analysis content (dict)

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    return _get_validator().validate(data, 'analysis')


def validate_codex_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Load and validate a codex file.

    Args:
        file_path: Path to .codex.yaml or .codex.json file

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    import yaml

    file_path = Path(file_path)

    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Parse error: {e}"]

    return validate_codex(data)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: schema_validator.py <file.codex.yaml>")
        print("       schema_validator.py --test")
        sys.exit(1)

    if sys.argv[1] == '--test':
        # Quick self-test
        print("Testing schema validator...")

        # Test codex validation
        valid_codex = {'metadata': {'formatVersion': '1.2'}}
        is_valid, errors = validate_codex(valid_codex)
        print(f"Valid codex: {is_valid} (expected: True)")

        invalid_codex = {'id': 'test'}  # Missing metadata
        is_valid, errors = validate_codex(invalid_codex)
        print(f"Invalid codex: {is_valid} (expected: False)")
        print(f"  Errors: {errors}")

        print("Self-test complete!")
    else:
        # Validate a file
        file_path = Path(sys.argv[1])
        is_valid, errors = validate_codex_file(file_path)

        if is_valid:
            print(f"✅ {file_path} is valid")
        else:
            print(f"❌ {file_path} has validation errors:")
            for error in errors:
                print(f"  - {error}")

        sys.exit(0 if is_valid else 1)
```

**Step 4: Create tests directory and run tests**

```bash
mkdir -p /Users/phong/Projects/chapterwise-claude-plugins/tests
pytest tests/test_schema_validator.py -v
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add plugins/chapterwise-codex/scripts/schema_validator.py tests/test_schema_validator.py
git commit -m "feat(schema): add centralized schema validator utility"
```

---

## Task 6: Add --validate Flag to Auto-Fixer

**Files:**
- Modify: `plugins/chapterwise-codex/scripts/auto_fixer.py`

**Step 1: Write failing test**

Add to `tests/test_schema_validator.py`:

```python
class TestAutoFixerValidation:
    """Test auto-fixer produces schema-valid output."""

    def test_auto_fixer_output_is_valid(self):
        """Auto-fixer should produce schema-valid codex."""
        from auto_fixer import CodexAutoFixer

        # Minimal input that needs fixing
        input_data = {
            'name': 'Test',
            'type': 'chapter'
        }

        fixer = CodexAutoFixer()
        fixed, fixes = fixer.auto_fix_codex(None, input_data)

        is_valid, errors = validate_codex(fixed)
        assert is_valid, f"Auto-fixer output invalid: {errors}"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_schema_validator.py::TestAutoFixerValidation -v
```

Expected: ImportError (auto_fixer not in path) or assertion failure

**Step 3: Update auto_fixer.py imports and add validation**

At the top of `auto_fixer.py`, after existing imports, add:

```python
# Schema validation (optional, for --validate flag)
try:
    from schema_validator import validate_codex
    HAS_SCHEMA_VALIDATOR = True
except ImportError:
    HAS_SCHEMA_VALIDATOR = False
    validate_codex = None
```

**Step 4: Add --validate argument to argparse**

In the `main()` function, add to the argument parser:

```python
parser.add_argument('--validate', action='store_true',
                    help='Validate output against JSON schema after fixing')
```

**Step 5: Add validation call in fix_single_file()**

In `fix_single_file()`, after the fixes are applied but before writing, add:

```python
# Validate against schema if requested
if hasattr(args, 'validate') and args.validate and HAS_SCHEMA_VALIDATOR:
    is_valid, errors = validate_codex(fixed_content)
    if not is_valid:
        print(f"\n⚠️ Schema validation warnings ({len(errors)}):")
        for error in errors[:5]:
            print(f"  - {error}")
```

Update the function signature to accept `validate` parameter:

```python
def fix_single_file(file_path: str, dry_run: bool = False, verbose: bool = False,
                    regenerate_all_ids: bool = False, validate: bool = False) -> bool:
```

**Step 6: Run tests**

```bash
pytest tests/test_schema_validator.py -v
```

**Step 7: Commit**

```bash
git add plugins/chapterwise-codex/scripts/auto_fixer.py tests/test_schema_validator.py
git commit -m "feat(auto-fixer): add --validate flag for schema validation"
```

---

## Task 7: Add Schema Example Validation Tests

**Files:**
- Create: `tests/test_schema_examples.py`

**Step 1: Write tests that validate schema examples**

Create `tests/test_schema_examples.py`:

```python
#!/usr/bin/env python3
"""
Tests that validate the examples embedded in schema files.
Ensures schema examples are themselves valid.
"""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins' / 'chapterwise-codex' / 'scripts'))
from schema_validator import SchemaValidator


SCHEMA_DIR = Path(__file__).parent.parent / 'schemas'


class TestCodexSchemaExamples:
    """Test examples in codex schema are valid."""

    @pytest.fixture
    def validator(self):
        return SchemaValidator()

    @pytest.fixture
    def codex_schema(self):
        with open(SCHEMA_DIR / 'codex-v1.2.schema.json') as f:
            return json.load(f)

    def test_schema_has_examples(self, codex_schema):
        """Schema should have examples section."""
        assert 'examples' in codex_schema
        assert len(codex_schema['examples']) > 0

    def test_all_examples_are_valid(self, validator, codex_schema):
        """All examples in schema should be valid."""
        for i, example in enumerate(codex_schema.get('examples', [])):
            is_valid, errors = validator.validate(example, 'codex')
            assert is_valid, f"Example {i} invalid: {errors}"


class TestAnalysisSchemaExamples:
    """Test examples in analysis schema are valid."""

    @pytest.fixture
    def validator(self):
        return SchemaValidator()

    @pytest.fixture
    def analysis_schema(self):
        with open(SCHEMA_DIR / 'analysis-v1.2.schema.json') as f:
            return json.load(f)

    def test_schema_has_examples(self, analysis_schema):
        """Schema should have examples section."""
        assert 'examples' in analysis_schema
        assert len(analysis_schema['examples']) > 0

    def test_all_examples_are_valid(self, validator, analysis_schema):
        """All examples in schema should be valid."""
        for i, example in enumerate(analysis_schema.get('examples', [])):
            is_valid, errors = validator.validate(example, 'analysis')
            assert is_valid, f"Example {i} invalid: {errors}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Step 2: Run tests**

```bash
pytest tests/test_schema_examples.py -v
```

Expected: All pass (our schema examples should be valid)

**Step 3: Commit**

```bash
git add tests/test_schema_examples.py
git commit -m "test(schema): add tests validating schema examples"
```

---

## Task 8: Update analysis_writer.py to Use Shared Validator

**Files:**
- Modify: `plugins/chapterwise-analysis/scripts/analysis_writer.py`

**Step 1: Replace inline schema loading with shared validator**

In `analysis_writer.py`, replace the schema loading code:

```python
# OLD CODE (lines 31-58):
# Load schema for validation
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / 'schemas'


def _load_analysis_schema() -> Optional[dict]:
    """Load the analysis JSON schema."""
    schema_path = SCHEMA_DIR / 'analysis-v1.2.schema.json'
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            return json.load(f)
    return None  # Schema not available, skip validation


def _validate_analysis(data: dict) -> Tuple[bool, List[str]]:
    """Validate analysis data against schema."""
    schema = _load_analysis_schema()
    if schema is None:
        return True, []  # No schema, skip validation

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return True, []

    error_msgs = [f"{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
                  for e in errors[:5]]  # Limit to 5 errors
    return False, error_msgs
```

With:

```python
# Use shared schema validator
try:
    # Add parent scripts directory to path for cross-plugin imports
    _codex_scripts = Path(__file__).parent.parent.parent / 'chapterwise-codex' / 'scripts'
    if str(_codex_scripts) not in sys.path:
        sys.path.insert(0, str(_codex_scripts))
    from schema_validator import validate_analysis as _validate_analysis
except ImportError:
    # Fallback if schema_validator not available
    def _validate_analysis(data: dict) -> Tuple[bool, List[str]]:
        return True, []  # Skip validation
```

**Step 2: Remove jsonschema import if no longer needed elsewhere**

Check if `jsonschema` is used anywhere else in the file. If not, remove:

```python
import jsonschema  # Remove this line
```

**Step 3: Verify file still works**

```bash
python3 -c "from plugins.chapterwise_analysis.scripts.analysis_writer import add_analysis_result; print('Import OK')"
```

**Step 4: Commit**

```bash
git add plugins/chapterwise-analysis/scripts/analysis_writer.py
git commit -m "refactor(analysis-writer): use shared schema validator"
```

---

## Task 9: Create pytest.ini for Test Configuration

**Files:**
- Create: `pytest.ini`

**Step 1: Create pytest configuration**

Create `pytest.ini` in repo root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

**Step 2: Run all tests**

```bash
pytest
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add pytest.ini
git commit -m "chore: add pytest configuration"
```

---

## Task 10: Update META-DEV-PROMPT Status

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/dev/META-DEV-PROMPT.md`

**Step 1: Mark Schema Definitions as complete**

Change:

```markdown
| 48 | Schema Definitions | 🔄 | 1 | | | V1.2 spec compliance |
```

To:

```markdown
| 48 | Schema Definitions | ✅ | 1 | 2026-02-04 | | V1.2 spec compliance, shared validator |
```

**Step 2: Add notes to decisions log**

Add to NOTES & DECISIONS LOG section:

```markdown
### 2026-02-04 - Schema Definitions (#48)
Decision: Created shared schema_validator.py utility, fixed pattern mismatches between schema and code
Rationale: Centralized validation prevents drift between schema and implementation
Trade-offs: Added jsonschema as a dependency
Deferred:
- Schema hosting at chapterwise.app URLs (low priority)
- Schema versioning strategy documentation (medium priority)
- Codex Lite schema definition (low priority - markdown files have simpler validation needs)
```

**Step 3: Commit**

```bash
git add /Users/phong/Projects/chapterwise-app/dev/META-DEV-PROMPT.md
git commit -m "docs: mark Schema Definitions (#48) as complete"
```

---

## Summary

| Task | Description | Files Changed |
|------|-------------|---------------|
| 1 | Fix ID pattern to allow UUIDs | codex-v1.2.schema.json |
| 2 | Relax analysis entry ID pattern | analysis-v1.2.schema.json |
| 3 | Align attribute key pattern with auto-fixer | codex-v1.2.schema.json |
| 4 | Remove 'lite' from formatVersion enum | codex-v1.2.schema.json |
| 5 | Create schema_validator.py utility | New file + tests |
| 6 | Add --validate flag to auto-fixer | auto_fixer.py |
| 7 | Add schema example validation tests | New test file |
| 8 | Refactor analysis_writer to use shared validator | analysis_writer.py |
| 9 | Add pytest configuration | pytest.ini |
| 10 | Update META-DEV-PROMPT status | META-DEV-PROMPT.md |

**Total commits:** 10
**Estimated implementation time:** 30-45 minutes
