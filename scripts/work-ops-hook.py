#!/usr/bin/env python3
"""
Work-Ops Lifecycle Hook for Antigravity (agy) & Claude Code.
1. SessionStart / First PreInvocation: Injects oldest-first (D+N) TODO briefing from ~/docsspace/work-ops/00_TODO.md.
2. PostInvocation Checkpoint Trigger: Monitors conversation activity (decisions via ask_question,
   document/code analysis & synthesis across multiple steps, file modifications, or git commits).
   When a meaningful milestone or decision occurs without a recent update to today's Daily Log
   (~/docsspace/work-ops/01_Daily_Logs/YYYY-MM-DD.md), injects a concise ephemeral reminder so the
   agent logs the checkpoint (What + Why + Files) naturally.
"""
import datetime
import json
import os
import re
import sys


def get_todo_briefing() -> str:
    todo_path = os.path.expanduser("~/docsspace/work-ops/00_TODO.md")
    today = datetime.date.today()
    lines = open(todo_path, encoding="utf-8").read().splitlines() if os.path.exists(todo_path) else []
    items = []
    for line in lines:
        s = line.strip()
        if s.startswith(("- [ ]", "- [/]")):
            m = re.search(r"created::\s*(\d{4}-\d{2}-\d{2})", s)
            days = (today - datetime.date.fromisoformat(m.group(1))).days if m else 0
            items.append((days, s))
    items.sort(key=lambda x: -x[0])
    body = "\n".join(f"{i}. (D+{k}) {s[2:]}" for i, (k, s) in enumerate(items, 1)) or "- None"
    return f"**TODO (원장: ~/docsspace/work-ops/00_TODO.md | {today})**\n{body}"


def check_checkpoint_needed(payload: dict) -> str:
    transcript_path = payload.get("transcriptPath", "")
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    today_str = datetime.date.today().isoformat()
    log_rel_marker = f"01_Daily_Logs/{today_str}.md"

    try:
        with open(transcript_path, encoding="utf-8") as f:
            steps = [json.loads(line) for line in f if line.strip()]
    except Exception:
        return ""

    # Locate the last user turn or last daily-log write
    last_log_step = -1
    last_user_step = -1
    for idx, step in enumerate(steps):
        if step.get("type") == "USER_INPUT":
            last_user_step = idx
        for tc in step.get("tool_calls") or []:
            args_str = json.dumps(tc.get("args") or {}, ensure_ascii=False)
            if log_rel_marker in args_str and tc.get("name") in ("edit_file", "write_file"):
                last_log_step = idx

    # Examine steps since the later of (last_log_step, last_user_step)
    start_idx = max(last_log_step + 1, last_user_step)
    recent_steps = steps[start_idx:]

    has_decision = False
    has_file_change = False
    has_git_commit = False
    analysis_tool_count = 0

    for step in recent_steps:
        for tc in step.get("tool_calls") or []:
            name = tc.get("name", "")
            args_str = json.dumps(tc.get("args") or {}, ensure_ascii=False)
            if name in ("ask_question", "AskUserQuestion"):
                has_decision = True
            elif name in ("edit_file", "write_file") and "work-ops/" not in args_str:
                has_file_change = True
            elif name == "run_command" and ("git commit" in args_str or "orca " in args_str):
                has_git_commit = True
            elif name in ("read_file", "search_web", "run_command", "invoke_subagent"):
                analysis_tool_count += 1

    reasons = []
    if has_decision:
        reasons.append("의사결정 확정(ask_question)")
    if has_file_change:
        reasons.append("주요 문서/파일 생성·수정")
    if has_git_commit:
        reasons.append("Git 커밋/시스템 상태 변경")
    if analysis_tool_count >= 5:
        reasons.append(f"심층 문서/데이터 분석({analysis_tool_count}회 도구 탐색)")

    if not reasons:
        return ""

    reason_text = ", ".join(reasons)
    return (
        f"[Work-Ops Checkpoint Trigger] 이번 작업 구간에서 [{reason_text}] 마일스톤이 감지되었으나 "
        f"아직 `~/docsspace/work-ops/01_Daily_Logs/{today_str}.md`에 기록되지 않았습니다. "
        f"의미 있는 의사결정·분석 결론·산출물 마일스톤에 도달했다면 답변 전(또는 완료 시) "
        f"`01_Daily_Logs/{today_str}.md`(및 신규 파일 시 `work-ops/00_SSOT_INDEX.md`, 할 일 변경 시 `00_TODO.md`)에 "
        f"체크포인트 로그(`- **[HH:MM] <제목>**` + `Why` + `Files`)를 남기세요."
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {}

    if mode == "claude-session":
        print(get_todo_briefing())
        return

    if mode == "pre":
        if payload.get("invocationNum", 1) != 1:
            print("{}")
            return
        md = get_todo_briefing()
        print(
            json.dumps(
                {
                    "injectSteps": [
                        {
                            "systemMessage": {
                                "systemMessage": md,
                                "metadata": {"user_markdown": md},
                            }
                        }
                    ]
                },
                ensure_ascii=False,
            )
        )
        return

    if mode == "post":
        reminder = check_checkpoint_needed(payload)
        if not reminder:
            print("{}")
            return
        print(
            json.dumps(
                {"injectSteps": [{"ephemeralMessage": reminder}]},
                ensure_ascii=False,
            )
        )
        return

    print("{}")


if __name__ == "__main__":
    main()
