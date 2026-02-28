# Atlas Section Type Schemas

Full output format for each atlas section type, following the Codex node schema. Reference this file when building or updating atlas sections.

---

### Characters Section

Generated for all fiction atlas types. One node per character with full profile content.

```yaml
type: section
name: Characters
description: "{N} characters across {M} chapters"

children:
  - type: character
    name: Elena Vasquez
    source: generated
    attributes:
      role: protagonist       # protagonist | deuteragonist | antagonist | supporting | minor
      first_appearance: chapter-01
      last_appearance: chapter-28
      chapters_present: 13   # count
      key_traits:
        - determined
        - haunted
        - brilliant
    content: |
      ## Elena Vasquez

      Former marine biologist turned environmental activist. Drives the central
      conflict by pursuing the suppressed Blackwood Report against corporate
      opposition.

      ### Arc

      **Beginning (Ch 1–9):** Isolated researcher, disillusioned with academia,
      discovers evidence of corporate environmental cover-up.

      **Middle (Ch 10–19):** Reluctant activist, builds unlikely alliance with
      Marcus Chen, faces personal and professional consequences.

      **End (Ch 20–28):** Transformed leader, sacrifices career security for
      public disclosure, finds purpose beyond the institution.

      ### Key Relationships

      - **Marcus Chen** — Adversary to reluctant ally to trusted partner
      - **Dr. Yuki Tanaka** — Mentor, provides scientific credibility
      - **Director Webb** — Antagonist, represents institutional suppression

      ### Key Moments

      - Ch 1: Discovers anomalous coral data
      - Ch 5: First confrontation with Marcus
      - Ch 17: Leaks the Blackwood Report
      - Ch 28: Public hearing testimony
```

### Timeline Section

Generated for all fiction atlas types. Chronological event order, even if the narrative is non-linear.

```yaml
type: section
name: Timeline
description: "{N} key events across {M} chapters"

children:
  - type: event
    name: "Discovery of anomalous coral data"
    source: generated
    attributes:
      chapter: chapter-01
      characters: [Elena Vasquez]
      act: 1
      significance: inciting_incident   # inciting_incident | turning_point | climax | resolution | setup
    content: |
      Elena discovers unexplained coral die-off patterns in her research data,
      contradicting official environmental reports from Pacific Dynamics Corp.
```

### Themes Section

Generated for all atlas types.

```yaml
type: section
name: Themes
description: "{N} major themes across {M} chapters"

children:
  - type: theme
    name: "Institutional Corruption"
    source: generated
    attributes:
      prominence: primary     # primary | secondary | minor
      chapters_present: [1, 3, 5, 8, 11, 14, 17, 20, 24, 27, 28]
      first_appearance: chapter-01
      peak_intensity: chapter-17
    content: |
      ## Institutional Corruption

      The central theme — how institutions prioritize self-preservation over
      truth. Manifests through corporate cover-up, university reluctance to
      support Elena, and regulatory agency complicity.

      ### Evolution

      **Introduction (Ch 1–5):** Subtle hints — redacted reports, dismissive
      administrators, corporate PR language masking environmental damage.

      **Development (Ch 6–17):** Explicit confrontation — Elena uncovers the
      suppression chain, Marcus sees it from inside the corporate machine.

      **Resolution (Ch 18–28):** Systemic exposure — the Blackwood Report
      reveals the full scope, forcing institutional reckoning.
```

### Plot Structure Section

Generated for fiction atlas types (story, script).

```yaml
type: section
name: Plot Structure
description: "Three-act structure with {N} turning points"

children:
  - type: structure
    name: "Three-Act Breakdown"
    source: generated
    content: |
      ## Act I: Setup (Chapters 1–9)

      **Inciting Incident (Ch 1):** Elena discovers anomalous coral data.
      **Lock-In (Ch 5):** First confrontation with Marcus.
      **Act I Climax (Ch 9):** Elena decides to investigate despite pressure.

      ## Act II: Confrontation (Chapters 10–21)

      **Midpoint (Ch 14):** Marcus discovers the Blackwood Report exists.
      **Low Point (Ch 18):** Elena is fired, Marcus is reassigned.
      **Act II Climax (Ch 21):** Alliance formed — decision to go public.

      ## Act III: Resolution (Chapters 22–28)

      **Climax (Ch 26):** Public hearing — testimony and evidence presented.
      **Resolution (Ch 28):** Aftermath — institutional reform begins.

  - type: structure
    name: "Pacing Analysis"
    source: generated
    attributes:
      tension_peaks: [5, 9, 14, 18, 21, 26]
      quiet_chapters: [3, 7, 13, 22]
    content: |
      ## Pacing

      Classic escalation pattern with breather chapters between tension peaks.
      Chapters 17–21 are the densest section — 5 consecutive high-tension
      chapters averaging 3,800 words each.
```

### Locations Section

Generated for fiction atlas types with significant settings.

```yaml
type: section
name: Locations
description: "{N} locations across {M} chapters"

children:
  - type: location
    name: "Coral Bay Research Station"
    source: generated
    attributes:
      chapters_present: [1, 3, 7, 15, 27]
      characters_associated: [Elena Vasquez, Dr. Yuki Tanaka, Sam Reyes]
      significance: primary_setting    # primary_setting | secondary_setting | mentioned_only
    content: |
      ## Coral Bay Research Station

      Isolated marine research facility on the Pacific coast. Elena's workplace
      and the site of the original data discovery. The station's isolation
      mirrors Elena's professional isolation — surrounded by ocean, cut off
      from institutional support.

      **Narrative function:** Safe harbor that becomes contested ground.

      **Key scenes:**
      - Ch 1: Data discovery
      - Ch 7: Late-night break-in attempt
      - Ch 15: Marcus visits — first alliance discussion
      - Ch 27: Return for final evidence collection
```

### Relationships Section

Generated for fiction with 5 or more named characters.

```yaml
type: section
name: Relationships
description: "{N} key relationships between {M} characters"

children:
  - type: relationship
    name: "Elena & Marcus"
    source: generated
    attributes:
      characters: [Elena Vasquez, Marcus Chen]
      type: adversary_to_ally    # ally | adversary | mentor | romantic | familial | adversary_to_ally | rival
      turning_point: chapter-15
    content: |
      ## Elena Vasquez & Marcus Chen

      **Phase 1: Adversaries (Ch 1–9)**
      Elena sees Marcus as a corporate fixer. Marcus sees Elena as a liability.

      **Phase 2: Reluctant Respect (Ch 10–14)**
      Marcus discovers the Blackwood Report and begins questioning his role.

      **Turning Point (Ch 15):**
      Marcus visits Coral Bay to warn Elena about surveillance. First honest
      conversation. Trust begins.

      **Phase 3: Alliance (Ch 16–28)**
      Full partnership — Marcus provides legal strategy, Elena provides evidence.
```

### World Section (Fantasy / Sci-Fi Only)

Generated for fantasy, sci-fi, and speculative fiction. Contains magic system or technology rules, factions, artifacts, and world history.

```yaml
type: section
name: World
description: "World reference — {N} factions, {M} locations, {K} significant artifacts"

children:
  - type: world-element
    name: "The Resonance System"
    source: generated
    attributes:
      category: magic_system    # magic_system | technology | faction | artifact | lore
    content: |
      ## The Resonance System

      Description of rules, limitations, and narrative significance...
```

### Topic Map Section (Non-Fiction Only)

Generated for non-fiction, academic, and research atlas types.

```yaml
type: section
name: Topic Map
description: "Key arguments and source references across {N} chapters"

children:
  - type: topic
    name: "Central Argument"
    source: generated
    attributes:
      chapters_present: [1, 3, 5, 8, 12]
      prominence: primary
    content: |
      Main thesis and how it develops across chapters. Supporting evidence
      by chapter. Key counterarguments addressed.
```

### Imagery and Devices Section (Poetry Only)

Generated for poetry collection atlas types.

```yaml
type: section
name: Imagery and Devices
description: "Recurring imagery, formal devices, and emotional arc across {N} poems"

children:
  - type: imagery-element
    name: "Water and Dissolution"
    source: generated
    attributes:
      category: imagery     # imagery | device | formal_element | emotional_arc
      poems_present: [2, 5, 7, 11, 14]
    content: |
      Water imagery threads through the collection as a symbol of both
      cleansing and loss. Appears most intensely at the collection's midpoint.
```
