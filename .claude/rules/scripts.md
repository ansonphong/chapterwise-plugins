# Rules: Writing Scripts

Applies when creating or modifying files in `plugins/chapterwise/scripts/`.

## Conventions

- All scripts output JSON to stdout
- Error output goes to stderr, never stdout (stdout is for data only)
- Scripts must work without external dependencies beyond Python stdlib + PyYAML
- Include a `if __name__ == "__main__":` block
- Exit code 0 on success, non-zero on failure
- Follow existing script patterns — check `analysis_writer.py` or `module_loader.py` for reference

## Input Conventions

Scripts use one of two input patterns:

### Pattern A: stdin JSON (preferred for new scripts)

```bash
echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py [action]
```

Used by: `recipe_manager.py`, `module_loader.py`, `codex_validator.py`, `format_detector.py`

### Pattern B: Positional arguments + optional stdin

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py SOURCE_FILE MODULE_NAME
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py SOURCE_FILE MODULE_NAME - < data.json
```

Used by: `staleness_checker.py`, `analysis_writer.py`, `explode_codex.py`, `implode_codex.py`

**New scripts should use Pattern A.** Existing Pattern B scripts are stable and should not be refactored unless there's a functional reason.
