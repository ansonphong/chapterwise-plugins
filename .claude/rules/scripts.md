# Rules: Writing Scripts

Applies when creating or modifying files in `plugins/chapterwise/scripts/`.

## Conventions

- All scripts use stdin JSON for input and stdout JSON for output
- Invocation pattern: `echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py [action]`
- Scripts must work without external dependencies beyond Python stdlib + PyYAML
- Use `sys.stdin` for input, `json.dumps()` for output
- Exit code 0 on success, non-zero on failure
- Error output goes to stderr, never stdout (stdout is for data only)
- Include a `if __name__ == "__main__":` block
- Follow existing script patterns — check `analysis_writer.py` or `module_loader.py` for reference
