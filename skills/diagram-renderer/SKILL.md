---
name: diagram-renderer
description: >-
  Formats agent responses using structured ASCII box-drawing diagrams by default,
  or Mermaid diagrams when explicitly requested. Activate this skill whenever the
  user asks to visualize, draw, map out, or explain architectures, execution
  processes, data flows, state transitions, or directory structures.
---

# Diagram Renderer Skill

Render architectures, execution flows, data pipelines, state transitions, and hierarchies directly inline as text-based diagrams without invoking external image generators or scripts.

## 1. Format Selection

1. **Default — Unicode Box-Drawing (`text` code block)**:
   - Use whenever the user asks to visualize, draw, or map out a structure or flow without specifying a format.
2. **On-Demand — Mermaid (`mermaid` code block)**:
   - Use **only** when the user explicitly requests Mermaid or when embedding a rendered diagram inside a Markdown artifact (`.md`).

## 2. ASCII / Unicode Box-Drawing Specification

- **Character Set**:
  - Borders: `┌`, `─`, `┐`, `│`, `└`, `┘`
  - Junctions: `├`, `┤`, `┬`, `┴`, `┼`
  - Arrows: `▼`, `▲`, `►`, `◄`
  - Section dividers: `=== [Phase Name] ===` or `───`
- **Width & CJK Alignment Rules**:
  - **Max width**: Keep lines within **80–88 columns** to prevent terminal line-wrapping distortion.
  - **CJK / Mixed-Width Safety**: Full-width CJK characters (2 columns) mixed with ASCII (1 column) frequently misalign right-hand vertical borders (`│`). When labels contain Korean/CJK or nested lists:
    - Prefer **open-right tree layouts** (`├─`, `└─`, `│`) or **top/bottom border blocks** (`┌───...───┐` / `└───...───┘` without a closed right `│`), OR
    - Keep closed boxes narrow with single-line labels padded conservatively.
- **Information Density**:
  - Label branch arrows with explicit conditions (`[Yes]`, `[No]`, `[Error]`).
  - Inside nodes, state both the core action (`What`) and key inputs/outputs rather than bare nouns.

## 3. Mermaid Specification (When Explicitly Requested)

- **Supported Types Only**: `flowchart TD/LR` (`graph TD/LR`), `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `xychart-beta`. (Use `flowchart` or Markdown tables instead of unsupported `timeline` or `gantt`).
- **Syntax Safety**:
  - Always wrap node labels containing `()`, `[]`, `/`, `:`, or spaces in double quotes (e.g., `nodeA["Auth Check (OAuth 2.0)"]`).
  - Never use HTML tags (e.g., `<br/>`) inside labels.
