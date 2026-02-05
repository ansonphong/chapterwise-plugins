# Port All Analysis Modules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Port all 26 remaining analysis modules from chapterwise-app to chapterwise-claude-plugins, creating a complete feature-parity analysis toolkit.

**Architecture:** Each module is a self-contained markdown file with YAML frontmatter defining metadata and prompt content. Modules are auto-discovered by `module_loader.py` and invoked via the `/analysis` command. Output follows the Codex V1.2 JSON format processed by `analysis_writer.py`.

**Tech Stack:** Markdown with YAML frontmatter, JSON Schema validation, Python scripts (module_loader.py, analysis_writer.py)

---

## Repository Paths

- **Source (app):** `/Users/phong/Projects/chapterwise-app/app/analysis/modules/`
- **Target (plugins):** `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/`

---

## Module Template

Every module follows this exact structure:

```markdown
---
name: module_name
displayName: Human Readable Name
description: One-line description of what this module analyzes
category: Category Name
icon: ph ph-icon-name
applicableTypes: [novel, short_story, screenplay, theatrical_play]
---

# Module Name Analysis

You are an expert literary analyst specializing in [Specialty Area].

## Your Task

Analyze the provided content for [specific analysis goals]:

1. **Aspect One** - Description
2. **Aspect Two** - Description
3. **Aspect Three** - Description

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Main Analysis\n\n[Detailed analysis in markdown]",
  "summary": "[1-2 sentence overview]",
  "children": [
    {
      "name": "Section Name",
      "summary": "Brief description",
      "content": "## Section\n\n[Detailed content]",
      "attributes": [
        {"key": "score", "name": "Score", "value": 8, "dataType": "int"}
      ]
    }
  ],
  "tags": ["relevant", "tags"],
  "attributes": [
    {"key": "overall_score", "name": "Overall Score", "value": 7, "dataType": "int"}
  ]
}
```

## Guidelines

- Analyze the ACTUAL text provided - do NOT use placeholder values
- Write detailed, specific analysis referencing the source content
- Rate scores 1-10 based on your analysis
- Use markdown formatting: ## Headers, **bold**, *italic*, - lists
- Include specific examples and quotes from the text
```

---

## Modules to Port (26 total)

### Currently Implemented (5)
- summary
- characters
- plot_holes
- story_beats
- critical_review

### To Be Ported (26)

| Module | Display Name | Category | Priority |
|--------|--------------|----------|----------|
| status | Manuscript Status | Quality Assessment | Phase 1 |
| tags | Content Tags & Keywords | Writing Craft | Phase 1 |
| writing_style | Writing Style Analysis | Writing Craft | Phase 1 |
| reader_emotions | Reader Emotions | Narrative Structure | Phase 2 |
| story_pacing | Story Pacing | Narrative Structure | Phase 2 |
| three_act_structure | Three-Act Structure | Narrative Structure | Phase 2 |
| heros_journey | Hero's Journey | Narrative Structure | Phase 2 |
| eight_stage | Eight-Point Story Arc | Narrative Structure | Phase 2 |
| plot_twists | Plot Twists | Quality Assessment | Phase 3 |
| clarity_accessibility | Clarity & Accessibility | Quality Assessment | Phase 3 |
| story_strength | Story Strength | Quality Assessment | Phase 3 |
| thematic_depth | Thematic Depth | Quality Assessment | Phase 3 |
| language_style | Language & Style | Writing Craft | Phase 3 |
| rhythmic_cadence | Rhythmic Cadence | Writing Craft | Phase 4 |
| psychogeography | Psychogeography | Writing Craft | Phase 4 |
| four_weapons | Four Weapons Balance | Writing Craft | Phase 4 |
| misdirection_surprise | Misdirection & Surprise | Narrative Structure | Phase 4 |
| character_relationships | Character Relationships | Characters | Phase 5 |
| jungian_analysis | Jungian Analysis | Characters | Phase 5 |
| alchemical_symbolism | Alchemical Symbolism | Characters | Phase 5 |
| dream_symbolism | Dream Symbolism | Characters | Phase 5 |
| ai_detector | AI Detection | Quality Assessment | Phase 6 |
| cultural_authenticity | Cultural Authenticity | Quality Assessment | Phase 6 |
| immersion | Immersion | Quality Assessment | Phase 6 |
| self_awareness | Meta-Narrative & Reflexivity | Quality Assessment | Phase 6 |
| gag_analysis | Gag Analysis | Writing Craft | Phase 6 |

---

## Phase 1: Foundation Modules (3 modules)

Essential utility modules that support other analyses.

### Task 1.1: Port status module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/status.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/status.md`

**Step 1: Read the app module**
```bash
cat /Users/phong/Projects/chapterwise-app/app/analysis/modules/status.py
```

**Step 2: Create the plugin module**

Extract from the app module:
- `get_module_display_name()` → displayName
- `get_module_description()` → description
- `get_module_icon()` → icon
- `get_module_category()` → category
- `get_applicable_types()` → applicableTypes
- `build_node_analysis_prompt()` system content → prompt body

Create `/plugins/chapterwise-analysis/modules/status.md` with proper frontmatter and prompt.

**Step 3: Test the module**
```bash
python3 plugins/chapterwise-analysis/scripts/module_loader.py get status
```

**Step 4: Commit**
```bash
git add plugins/chapterwise-analysis/modules/status.md
git commit -m "feat(analysis): port status module from app

Manuscript Status analysis - assesses completion, quality, and readiness.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.2: Port tags module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/tags.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/tags.md`

Follow same pattern as Task 1.1.

---

### Task 1.3: Port writing_style module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/writing_style.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/writing_style.md`

Follow same pattern as Task 1.1.

---

## Phase 2: Narrative Structure Modules (5 modules)

Core story structure analysis tools.

### Task 2.1: Port reader_emotions module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/reader_emotions.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/reader_emotions.md`

---

### Task 2.2: Port story_pacing module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/story_pacing.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/story_pacing.md`

---

### Task 2.3: Port three_act_structure module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/three_act_structure.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/three_act_structure.md`

---

### Task 2.4: Port heros_journey module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/heros_journey.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/heros_journey.md`

---

### Task 2.5: Port eight_stage module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/eight_stage.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/eight_stage.md`

---

## Phase 3: Quality Assessment Modules (5 modules)

Tools for evaluating writing quality and effectiveness.

### Task 3.1: Port plot_twists module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/plot_twists.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/plot_twists.md`

---

### Task 3.2: Port clarity_accessibility module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/clarity_accessibility.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/clarity_accessibility.md`

---

### Task 3.3: Port story_strength module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/story_strength.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/story_strength.md`

---

### Task 3.4: Port thematic_depth module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/thematic_depth.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/thematic_depth.md`

---

### Task 3.5: Port language_style module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/language_style.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/language_style.md`

---

## Phase 4: Advanced Writing Craft Modules (4 modules)

Specialized writing analysis tools.

### Task 4.1: Port rhythmic_cadence module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/rhythmic_cadence.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/rhythmic_cadence.md`

---

### Task 4.2: Port psychogeography module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/psychogeography.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/psychogeography.md`

---

### Task 4.3: Port four_weapons module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/four_weapons.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/four_weapons.md`

---

### Task 4.4: Port misdirection_surprise module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/misdirection_surprise.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/misdirection_surprise.md`

---

## Phase 5: Character Analysis Modules (4 modules)

Deep character and psychological analysis.

### Task 5.1: Port character_relationships module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/character_relationships.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/character_relationships.md`

---

### Task 5.2: Port jungian_analysis module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/jungian_analysis.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/jungian_analysis.md`

---

### Task 5.3: Port alchemical_symbolism module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/alchemical_symbolism.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/alchemical_symbolism.md`

---

### Task 5.4: Port dream_symbolism module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/dream_symbolism.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/dream_symbolism.md`

---

## Phase 6: Specialized Modules (5 modules)

Niche and specialized analysis tools.

### Task 6.1: Port ai_detector module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/ai_detector.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/ai_detector.md`

---

### Task 6.2: Port cultural_authenticity module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/cultural_authenticity.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/cultural_authenticity.md`

---

### Task 6.3: Port immersion module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/immersion.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/immersion.md`

---

### Task 6.4: Port self_awareness module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/self_awareness.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/self_awareness.md`

---

### Task 6.5: Port gag_analysis module

**Files:**
- Read: `/Users/phong/Projects/chapterwise-app/app/analysis/modules/gag_analysis.py`
- Create: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/gag_analysis.md`

---

## Phase 7: Final Integration

### Task 7.1: Update analysis.md command with all modules

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/commands/analysis.md`

Add all new module triggers to the command file.

---

### Task 7.2: Test all modules load correctly

**Step 1: List all modules**
```bash
python3 plugins/chapterwise-analysis/scripts/module_loader.py list
```

Expected: 31 modules listed (5 existing + 26 new)

**Step 2: Verify each module loads**
```bash
for module in status tags writing_style reader_emotions story_pacing three_act_structure heros_journey eight_stage plot_twists clarity_accessibility story_strength thematic_depth language_style rhythmic_cadence psychogeography four_weapons misdirection_surprise character_relationships jungian_analysis alchemical_symbolism dream_symbolism ai_detector cultural_authenticity immersion self_awareness gag_analysis; do
  echo "Testing: $module"
  python3 plugins/chapterwise-analysis/scripts/module_loader.py get $module > /dev/null && echo "  OK" || echo "  FAILED"
done
```

---

### Task 7.3: Run integration test

**Step 1: Create test codex file**
```bash
cat > /tmp/test-all-modules.codex.yaml << 'EOF'
metadata:
  formatVersion: "1.2"
id: test-modules
type: chapter
name: "Test Chapter"
body: |
  The old wizard Merlin stood at the edge of the Whispering Woods, his staff
  glowing with ethereal light. Elena approached cautiously, her heart pounding.

  "You've come seeking answers," Merlin said, not turning around. "But answers
  have a price, young one."

  Elena clutched the ancient map tighter. "I know. I'm willing to pay it."

  The forest seemed to hold its breath. In the distance, a wolf howled.
EOF
```

**Step 2: Test one module from each phase**
```bash
# Phase 1
python3 plugins/chapterwise-analysis/scripts/analysis_writer.py /tmp/test-all-modules.codex.yaml status '{"body":"Test","summary":"Test","children":[],"tags":[],"attributes":[]}'

# Phase 2
python3 plugins/chapterwise-analysis/scripts/analysis_writer.py /tmp/test-all-modules.codex.yaml heros_journey '{"body":"Test","summary":"Test","children":[],"tags":[],"attributes":[]}'
```

---

### Task 7.4: Commit and push all changes

```bash
git add plugins/chapterwise-analysis/modules/*.md
git add plugins/chapterwise-analysis/commands/analysis.md
git commit -m "feat(analysis): port all 26 remaining modules from chapterwise-app

Complete feature parity with web app analysis capabilities:

Phase 1 - Foundation:
- status, tags, writing_style

Phase 2 - Narrative Structure:
- reader_emotions, story_pacing, three_act_structure, heros_journey, eight_stage

Phase 3 - Quality Assessment:
- plot_twists, clarity_accessibility, story_strength, thematic_depth, language_style

Phase 4 - Writing Craft:
- rhythmic_cadence, psychogeography, four_weapons, misdirection_surprise

Phase 5 - Character Analysis:
- character_relationships, jungian_analysis, alchemical_symbolism, dream_symbolism

Phase 6 - Specialized:
- ai_detector, cultural_authenticity, immersion, self_awareness, gag_analysis

Total: 31 analysis modules now available.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push origin master
```

---

## Verification Checklist

After all tasks complete:

- [ ] All 26 new modules created in `/plugins/chapterwise-analysis/modules/`
- [ ] All modules have correct frontmatter (name, displayName, description, category, icon, applicableTypes)
- [ ] All modules use snake_case for name field
- [ ] All modules follow Codex V1.2 output format
- [ ] `module_loader.py list` shows 31 modules
- [ ] Each module loads without error
- [ ] `analysis.md` command updated with all triggers
- [ ] Integration test passes
- [ ] Changes committed and pushed

---

## Module Metadata Reference

For each module, extract these fields from the app Python file:

| App Method | Plugin Field |
|------------|--------------|
| `get_module_name()` | `name` |
| `get_module_display_name()` | `displayName` |
| `get_module_description()` | `description` |
| `get_module_category()` | `category` |
| `get_module_icon()` | `icon` |
| `get_applicable_types()` | `applicableTypes` |
| `build_node_analysis_prompt()` system content | Prompt body after frontmatter |

---

## Porting Checklist Per Module

For each module:

1. [ ] Read app module Python file
2. [ ] Extract metadata (name, displayName, description, category, icon, applicableTypes)
3. [ ] Extract prompt content from `build_node_analysis_prompt()` system message
4. [ ] Adapt prompt to plugin format (remove Python string formatting, use markdown)
5. [ ] Create .md file with YAML frontmatter + prompt content
6. [ ] Test module loads: `module_loader.py get <name>`
7. [ ] Commit module
