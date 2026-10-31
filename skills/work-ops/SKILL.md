---
name: work-ops
description: >-
  Manages the cumulative To-Do list (`~/docsspace/work-ops/00_TODO.md`), displays
  unfinished tasks sorted oldest-first (D+N), delegates AI-executable tasks to
  separate sessions upon user approval, logs completed work (`~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md`),
  and conducts daily work reviews. Activate when a task completes or when the
  user asks to show/update To-Dos, log work, or review daily work.
---

# Work-Ops Skill (Personal SSOT To-Do & Daily Log Ledger)

Operate directly on the Markdown files in `~/docsspace/work-ops/` (the unconditional Single Source of Truth across all workspaces) using `read_file`, `edit_file`, and `write_file`:
- `00_TODO.md`: Cumulative tasks (`## Todo`, `## Waiting`, `## Done`). Syntax: `- [ ] Task [created:: YYYY-MM-DD] #ai`
- `01_Daily_Logs/YYYY-MM-DD.md`: Completed work log (`## Log`) and review (`## Review`).
- `99_Archive/Completed_YYYY-MM.md`: Move `[x]` items from `00_TODO.md` whose `done` date is > 7 days old here.

> **Relationship with `fde-work-log`**: `work-ops` maintains internal, real-name daily execution logs in the private vault (`~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md`). When converting daily field observations into external/reusable engineering blog posts, pass the raw log entries through [`fde-work-log`](../fde-work-log/SKILL.md)'s De-identification Gate.

## 1. Show & Manage To-Dos (Oldest First + Separate AI Session)
- **Show**: Read `~/docsspace/work-ops/00_TODO.md`, compute elapsed days (`D+N`) from `[created:: YYYY-MM-DD]` against today's date, and display unfinished tasks (`[ ]`, `[/]`) sorted from **oldest (`D+N` highest) to newest**.
- **Add**: Edit `00_TODO.md` to add `- [ ] <Task> [created:: YYYY-MM-DD]` under `## Todo` (or under `## Waiting` with `[waiting:: <who>]`). Append `#ai` if the AI can execute the task autonomously.
- **AI Delegation**: Highlight `#ai` / AI-executable tasks and ask the user for approval. Only after explicit user approval, mark the item `[/]` in `00_TODO.md` and launch a separate session (`invoke_subagent` with `TypeName: "self"` or `orca agent launch`).

## 2. Log Completed Work
When a meaningful task completes (or when asked to log work):
1. Append to `~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md` under `## Log`:
   ```markdown
   - **[HH:MM] <Title>** (`[[<project-or-workspace>]]`)
     - Why: <Core rationale and outcome>
     - Files: <Key files created/modified>
   ```
2. If the task matches an item in `00_TODO.md`, move that item to `## Done` as `- [x] <Task> [created:: YYYY-MM-DD] [done:: [[YYYY-MM-DD]]]`.

## 3. Daily Work Review
Read `00_TODO.md` and `01_Daily_Logs/YYYY-MM-DD.md` to review:
1. **Planned vs. Executed**: Completed (`[x]`), in-progress (`[/]`), untouched (`[ ]` sorted by `D+N`), and ad-hoc work.
2. **Focus & Decisions**: Effort distribution and key `What`/`Why` outcomes.
3. **Carry-Over**: Aging `[ ]` items and `#ai` candidates for the next session. Save the summary under `## Review` in `01_Daily_Logs/YYYY-MM-DD.md`.
