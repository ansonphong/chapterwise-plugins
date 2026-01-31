# Codex V1.2 Analysis Output Format

All analysis modules MUST output results in this exact format.

## Required JSON Structure

```json
{
  "body": "## Module Name\n\nMain analysis content in markdown...",
  "summary": "One-line summary of findings",
  "children": [
    {
      "name": "Section Name",
      "summary": "Section summary",
      "content": "## Section\n\nDetailed content...",
      "attributes": [
        {
          "key": "score",
          "name": "Score",
          "value": 8,
          "dataType": "int"
        }
      ]
    }
  ],
  "tags": ["analysis", "module-name"],
  "attributes": [
    {
      "key": "overall_score",
      "name": "Overall Score",
      "value": 7,
      "dataType": "int"
    }
  ]
}
```

## Rules

1. **body** - Main analysis in markdown with ## headers
2. **summary** - 1-2 sentence overview
3. **children** - Structured sub-sections (2-5 recommended)
4. **attributes** - Scored metrics with dataType
5. **tags** - Relevant keywords for searchability

## Markdown in body/content

- Use `##` for section headers
- Use `**bold**` for emphasis
- Use `- ` for bullet lists
- Use `> ` for quotes from source text
- Keep paragraphs concise
