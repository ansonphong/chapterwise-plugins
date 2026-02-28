# ChapterWise Language Rules

These rules apply to ALL recipe and cross-cutting commands. Read and follow them exactly.

## Core Rules

1. **Never say "recipe" to the user.** Internally it's the recipe system. Externally, describe what's happening without using the word.
2. **No theatrical cooking language.** Never use: "order up", "bon appetit", "chef's kiss", "ready to serve", "plating", "garnish".
3. **Use cooking verbs naturally** in progress messages — scan, slice, season, simmer, fold, reduce. These are the action verbs, not metaphors.
4. **Report real data.** Every progress message includes actual numbers: chapter counts, word counts, file counts, module names.
5. **Phase names match the command.** Each command has its own phase vocabulary — see command-specific rules below.

## Progress Message Formula

`[cooking verb] [technical noun]... [real data]`

Examples:
- "Scanning structure... PDF, 342 pages, three-act novel."
- "Slicing chapters... 28 found across 3 parts."
- "Extracting entities... 14 characters, 8 locations across 28 chapters."
- "Quick taste... summary, characters, tags on 28 chapters."

## Tool Usage Rules

- Use the **Glob** tool for file discovery (never `find`)
- Use the **Read** tool for file reading (never `cat` or `head`)
- Use the **Grep** tool for content search (never `grep` or `rg` in Bash)
- Call scripts via stdin JSON: `echo '{"key":"value"}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/script.py`

## Validation Rules

- Run `recipe_validator.py` after saving any recipe
- Run `codex_validator.py` after generating codex output
- Silent on success. Report only auto-fixes and unfixable issues.

## Common Rules

- Pair a cooking verb with a specific technical description — never a bare verb alone
- Include real data: counts, names, word counts
- Keep progress messages brief: 5-15 words
- Say "Done." at the end — plain, no flare
- No emojis
- Never replace real information with flare: the data is always the point
