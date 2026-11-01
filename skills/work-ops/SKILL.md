---
name: work-ops
description: >-
  Manages the cumulative To-Do list (`~/docsspace/work-ops/00_TODO.md`), displays
  unfinished tasks sorted oldest-first (D+N), delegates AI-executable tasks to
  separate sessions upon user approval, logs completed work and FDE field notes
  (`~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md`), conducts daily work
  reviews, and optionally converts daily logs into de-identified engineering
  articles. Activate when a task completes or when the user drops daily work/field
  notes, or asks to show/update To-Dos, log work, review daily work, or export
  a de-identified work log post.
---

# Work-Ops Skill (Personal SSOT To-Do, FDE Field Log & Daily Review)

Operate directly on the Markdown files in `~/docsspace/work-ops/` (the unconditional Single Source of Truth across all workspaces) using `read_file`, `edit_file`, and `write_file`:
- `00_SSOT_INDEX.md`: Folder-level SSOT index listing all files/subfolders inside `work-ops/` and summarizing their contents (part of the `~/docsspace/` 2-tier Index standard). Update whenever new daily logs or archive files are added.
- `00_TODO.md`: Cumulative tasks (`## Todo`, `## Waiting`, `## Done`). Syntax: `- [ ] Task [created:: YYYY-MM-DD] #ai`
- `01_Daily_Logs/YYYY-MM-DD.md`: Daily execution & FDE field log (`## Log`) and end-of-day review (`## Review`).
- `99_Archive/Completed_YYYY-MM.md`: Move `[x]` items from `00_TODO.md` whose `done` date is > 7 days old here.

## 1. Show & Manage To-Dos (Oldest First + Separate AI Session)
- **Show**: Read `~/docsspace/work-ops/00_TODO.md`, compute elapsed days (`D+N`) from `[created:: YYYY-MM-DD]` against today's date, and display unfinished tasks (`[ ]`, `[/]`) sorted from **oldest (`D+N` highest) to newest**.
- **Add**: Edit `00_TODO.md` to add `- [ ] <Task> [created:: YYYY-MM-DD]` under `## Todo` (or under `## Waiting` with `[waiting:: <who>]`). Append `#ai` if the AI can execute the task autonomously.
- **AI Delegation**: Highlight `#ai` / AI-executable tasks and ask the user for approval. Only after explicit user approval, mark the item `[/]` in `00_TODO.md` and launch a separate session (`invoke_subagent` with `TypeName: "self"` or `orca agent launch`).

## 2. Continuous Checkpoint & Task-Completion Logging (`01_Daily_Logs/YYYY-MM-DD.md`)
Do not wait only for final session completion or explicit user requests. Trigger logging **both during work (at meaningful mid-task checkpoints) and upon task completion**:
- **Auto-Logging Triggers**:
  1. **Task Start / Delegation**: Mark the corresponding item `[/]` in `00_TODO.md` when starting a multi-step task.
  2. **Mid-Task Checkpoints (중간 체크포인트 로깅)**: Whenever an important intermediate milestone is reached (e.g., architectural/design decision confirmed, root cause or key field constraint discovered, major skill/code/report artifact written, spike/verification passed), immediately append a checkpoint entry to `01_Daily_Logs/YYYY-MM-DD.md`.
  3. **Task Completion / Git Commit & Push**: When a task or pipeline stage finishes, append the final outcome entry and update `00_TODO.md` (`[x]`).
- **Logging Procedure**:
  1. Append to `~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md` under `## Log` (if creating a new `YYYY-MM-DD.md` file, immediately register it in `~/docsspace/work-ops/00_SSOT_INDEX.md`):
     - **For general engineering / setup / milestone checkpoints**:
       ```markdown
       - **[HH:MM] <Title>** (`[[<project-or-workspace>]]`)
         - Why: <Core rationale, decision, or checkpoint outcome>
         - Files: <Key files created/modified>
       ```
     - **For FDE client / field observations (do not inflate into a full essay yet; capture structured facts)**:
       ```markdown
       - **[HH:MM] <Title>** (`[[<project-or-workspace>]]`)
         - Observation (관찰한 현업 풍경): <How operators actually work and where time/friction is spent>
         - Hidden Convention (숨은 규약): <Why the seemingly inefficient field rule existed to prevent accidents>
         - Decision & Action (FDE 80:20 판단): <What to automate (80% Auto) vs keep in human review (20% Repair Admin)>
         - Files: <Key files created/modified, if any>
       ```
  2. If the completed task matches an item in `00_TODO.md`, move that item to `## Done` as `- [x] <Task> [created:: YYYY-MM-DD] [done:: [[YYYY-MM-DD]]]`.

## 3. Daily Work Review (`## Review`)
Read `00_TODO.md` and `01_Daily_Logs/YYYY-MM-DD.md` to review and save under `## Review` in `01_Daily_Logs/YYYY-MM-DD.md`:
1. **Planned vs. Executed**: Completed (`[x]`), in-progress (`[/]`), untouched (`[ ]` sorted by `D+N`), and ad-hoc work.
2. **Focus & Decisions**: Effort distribution and key `What`/`Why` outcomes.
3. **Takeaway (오늘 남기는 원칙)**: One reusable engineering/FDE principle learned today.
4. **Carry-Over**: Aging `[ ]` items and `#ai` candidates for the next session.

## 4. On-Demand: De-identified Insight / Article Export
Activate **only** when the user explicitly asks to convert daily work/field logs into a de-identified blog post or reusable external asset (`fde-YYYY-MM-DD-<topic>.md`):
1. **De-identification Gate (Mandatory before writing)**:
   - **Client / Service Name** ➔ Generalize to industry & archetype (e.g., `"중견 수주 설계형 설비 제조사"`, `"B2B 건자재 유통사"`).
   - **Internal System / Column Names** ➔ Role-based standard terms (e.g., `"수기 발주 원장"`, `"월말 마감 대조 시트"`).
   - **Real Names** ➔ Job roles (e.g., `"현장 배차 담당자"`, `"정산 실무자"`, `"의사결정자"`).
   - **Sensitive Numbers (Revenue / Unit Price / Contract Amount)** ➔ Express only as ratios (%), step counts, or relative structures.
2. **Article Structure**:
   - YAML Frontmatter: `title`, `description`, `date: "YYYY-MM-DD"`, `tags: [FDE, Work Log]`, `published: false`
   - Body: **1. 첫 문단 결론** (현장 문제와 핵심 판단) ➔ **2. 현업의 병목과 규약 (`Why it happens`)** ➔ **3. 해결 구조와 엔지니어링 판단 (`How to solve`, ASCII 다이어그램/표 포함)** ➔ **4. 오늘 남기는 원칙 (`Takeaway`)**.
