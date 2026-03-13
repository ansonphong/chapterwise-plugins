# Rules: Testing

Applies when creating or modifying files in `tests/`.

## Conventions

- Tests use pytest
- Test files mirror the source structure: `scripts/analysis_writer.py` → `tests/test_analysis_writer.py`
- Run tests with: `python3 -m pytest tests/ -v`
- Test scripts by piping JSON to stdin and asserting stdout JSON output
- Mock file I/O when testing scripts that read/write files
- Use TDD when implementing new scripts — write failing test first
