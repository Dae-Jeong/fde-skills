#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/skills"
CONFIGS_DIR="${REPO_ROOT}/configs"

TARGET_DIRS=(
  "${HOME}/.agents/skills"
  "${HOME}/.claude/skills"
  "${HOME}/.codex/skills"
  "${HOME}/.gemini/config/skills"
)

# 1. Initialize local-only credentials.json for service-explorer if missing
CRED_FILE="${SKILLS_DIR}/service-explorer/credentials.json"
if [ -d "${SKILLS_DIR}/service-explorer" ] && [ ! -f "${CRED_FILE}" ]; then
  printf '{\n  "services": {}\n}\n' > "${CRED_FILE}"
  chmod 600 "${CRED_FILE}"
  echo "Initialized local credentials file: ${CRED_FILE} (chmod 600)"
fi

# 2. Ensure private Obsidian Vault SSOT directories and 2-Tier Indexes exist
DOCSSPACE_DIR="${HOME}/docsspace"
WORK_OPS_DIR="${DOCSSPACE_DIR}/work-ops"
mkdir -p "${WORK_OPS_DIR}/01_Daily_Logs" "${WORK_OPS_DIR}/99_Archive"

if [ ! -f "${DOCSSPACE_DIR}/00_INDEX.md" ]; then
  cat <<EOF > "${DOCSSPACE_DIR}/00_INDEX.md"
---
type: vault-index
updated: $(date +%Y-%m-%d)
---
# docsspace — Master Index

> \`~/docsspace/\` 내 전체 폴더 목록과 역할 요약입니다. 각 폴더 내부의 상세 파일 목록과 내용은 해당 폴더의 \`00_SSOT_INDEX.md\` 문서를 참조합니다.

| 프로젝트명 (폴더) | 구분 | 연결된 코드 저장소 (\`workspace\`) | 폴더 설명 (무엇을 관리하는 곳인가) | 진입 목차 (Index) |
| :--- | :---: | :--- | :--- | :--- |
| **[\`work-ops/\`](./work-ops/)** | 개인 업무 원장 | *(해당 없음 — 볼트 전용)* | 전 워크스페이스 통합 누적 할 일(\`00_TODO.md\`, \`D+N\` 정렬), 일일 작업 로그 및 회고(\`01_Daily_Logs/\`), 완료 아카이브(\`99_Archive/\`) 관리 | **[work-ops/00_SSOT_INDEX.md](./work-ops/00_SSOT_INDEX.md)** |
EOF
  echo "Initialized Vault Master Index: ${DOCSSPACE_DIR}/00_INDEX.md"
fi

if [ ! -f "${WORK_OPS_DIR}/00_SSOT_INDEX.md" ]; then
  cat <<EOF > "${WORK_OPS_DIR}/00_SSOT_INDEX.md"
---
type: folder-index
updated: $(date +%Y-%m-%d)
---
# work-ops — 개인 업무 원장 SSOT Index

## 🧠 Live Memory Header (세션 0턴 핵심 요약)
- **프로젝트 정체성**: 전 워크스페이스 통합 할 일(\`00_TODO.md\`), 일일 작업/현장 로그(\`01_Daily_Logs/YYYY-MM-DD.md\`), 장기 완료 아카이브(\`99_Archive/\`)를 관리하는 개인 운영 원장 (\`~/docsspace/work-ops\`)
- **핵심 운영 규칙**: \`00_TODO.md\`는 \`[created:: YYYY-MM-DD]\` 기준 \`D+N\` 오래된 순으로 브리핑하며, 완료(\`done\`) 후 7일 경과 항목만 \`99_Archive/Completed_YYYY-MM.md\`로 이관

---

## 📚 폴더 내 파일 및 하위 디렉토리 요약

| 구분 | 파일명 / 경로 | 역할 및 담고 있는 핵심 내용 |
| :---: | :--- | :--- |
| **누적 할 일** | **[00_TODO.md](./00_TODO.md)** | **[전 워크스페이스 통합 To-Do 원장]** 미완료 할 일(\`## Todo\`, \`[created:: YYYY-MM-DD]\` 기준 \`D+N\` 오래된 순 정렬 및 \`#ai\` 위임 대상 표시), 대기 항목(\`## Waiting\`), 최근 완료 항목(\`## Done\`) 관리 |
| **완료 보관소** | **[\`99_Archive/\`](./99_Archive/)** | **[장기 완료 아카이브]** \`00_TODO.md\`의 \`## Done\` 항목 중 완료일(\`done\`)로부터 7일이 경과한 항목을 월별(\`Completed_YYYY-MM.md\`)로 이관·보관하는 폴더 |
EOF
  echo "Initialized Folder SSOT Index: ${WORK_OPS_DIR}/00_SSOT_INDEX.md"
fi

if [ ! -f "${WORK_OPS_DIR}/00_TODO.md" ]; then
  cat <<EOF > "${WORK_OPS_DIR}/00_TODO.md"
---
type: todo
updated: $(date +%Y-%m-%d)
---
# TODO

## Todo

## Waiting

## Done
EOF
  echo "Initialized SSOT ledger: ${WORK_OPS_DIR}/00_TODO.md"
fi

# 3. Sync global root rules across Gemini (~/.gemini/GEMINI.md), Claude (~/.claude/CLAUDE.md), and Codex (~/.codex/AGENTS.md & ~/.agents/AGENTS.md)
RULE_SRC="${CONFIGS_DIR}/GLOBAL_RULES.md"
if [ -f "${RULE_SRC}" ]; then
  mkdir -p "${HOME}/.gemini" "${HOME}/.claude" "${HOME}/.codex" "${HOME}/.agents"
  ln -sfn "${RULE_SRC}" "${HOME}/.gemini/GEMINI.md"
  ln -sfn "${RULE_SRC}" "${HOME}/.claude/CLAUDE.md"
  ln -sfn "${RULE_SRC}" "${HOME}/.codex/AGENTS.md"
  ln -sfn "${RULE_SRC}" "${HOME}/.agents/AGENTS.md"
  echo "Linked global rules (GEMINI.md / CLAUDE.md / AGENTS.md) -> ${RULE_SRC}"
fi

# 4. Prune broken symlinks and link all skills from fde-skills/skills/* into ~/.agents, ~/.claude, ~/.codex, and ~/.gemini
for target_base in "${TARGET_DIRS[@]}"; do
  mkdir -p "${target_base}"
  for existing in "${target_base}"/*; do
    if [ -L "${existing}" ] && [ ! -e "${existing}" ]; then
      rm -f "${existing}"
      echo "Pruned broken symlink: ${existing}"
    fi
  done
  for skill_path in "${SKILLS_DIR}"/*; do
    [ -d "${skill_path}" ] || continue
    skill_name="$(basename "${skill_path}")"
    target_link="${target_base}/${skill_name}"
    if [ -d "${target_link}" ] && [ ! -L "${target_link}" ]; then
      rm -rf "${target_link}"
    fi
    ln -sfn "${skill_path}" "${target_link}"
    echo "Linked: ${target_link} -> ${skill_path}"
  done
done

# 5. Sync auxiliary skills in ~/.agents/skills (e.g., archify, orca-cli) to ~/.claude, ~/.codex, and ~/.gemini
for aux_path in "${HOME}/.agents/skills"/*; do
  [ -e "${aux_path}" ] || continue
  aux_name="$(basename "${aux_path}")"
  if [ ! -d "${SKILLS_DIR}/${aux_name}" ]; then
    for extra_base in "${HOME}/.claude/skills" "${HOME}/.codex/skills" "${HOME}/.gemini/config/skills"; do
      ln -sfn "${aux_path}" "${extra_base}/${aux_name}"
    done
  fi
done

# 6. Configure Session-Start & Post-Compact Briefing Hook (TODO + CWD Project Live Memory)
BRIEFING_SCRIPT="${HOME}/.agents/session-briefing.py"
cat <<'PYEOF' > "${BRIEFING_SCRIPT}"
#!/usr/bin/env python3
import datetime
import glob
import json
import os
import re
import sys


def build_briefing() -> str:
    today = datetime.date.today()
    todo_path = os.path.expanduser("~/docsspace/work-ops/00_TODO.md")
    lines = open(todo_path, encoding="utf-8").read().splitlines() if os.path.exists(todo_path) else []
    items = []
    for line in lines:
        s = line.strip()
        if s.startswith(("- [ ]", "- [/]")):
            m = re.search(r"created::\s*(\d{4}-\d{2}-\d{2})", s)
            days = (today - datetime.date.fromisoformat(m.group(1))).days if m else 0
            items.append((days, s))
    items.sort(key=lambda x: -x[0])
    todo_body = "\n".join(f"{i}. (D+{k}) {s[2:]}" for i, (k, s) in enumerate(items, 1)) or "- None"
    sections = [f"**TODO (원장: ~/docsspace/work-ops/00_TODO.md | {today})**\n{todo_body}"]

    cwd = os.path.realpath(os.getcwd())
    docsspace = os.path.realpath(os.path.expanduser("~/docsspace"))

    for ssot_path in sorted(glob.glob(os.path.join(docsspace, "*", "00_SSOT_INDEX.md"))):
        proj_dir = os.path.realpath(os.path.dirname(ssot_path))
        slug = os.path.basename(proj_dir)
        try:
            text = open(ssot_path, encoding="utf-8").read()
        except Exception:
            continue
        code_repo = None
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if fm:
            cm = re.search(r"^code_repo:\s*(.+)$", fm.group(1), re.MULTILINE)
            if cm:
                code_repo = os.path.realpath(os.path.expanduser(cm.group(1).strip()))
        matched = (cwd == proj_dir or cwd.startswith(proj_dir + os.sep)) or (
            code_repo and (cwd == code_repo or cwd.startswith(code_repo + os.sep))
        )
        if matched:
            hm = re.search(
                r"^##\s+🧠\s+Live Memory Header[^\n]*\n(.*?)(?=\n---|\n##\s+|\Z)",
                text,
                re.MULTILINE | re.DOTALL,
            )
            if hm and hm.group(1).strip():
                sections.append(
                    f"**[Project Live Memory: {slug} ({ssot_path})]**\n{hm.group(1).strip()}"
                )
            break

    return "\n\n".join(sections)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "claude"
    if mode == "antigravity":
        raw = sys.stdin.read() or "{}"
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {}
        if payload.get("invocationNum", 1) != 1:
            print("{}")
            return
        md = build_briefing()
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
    else:
        print(build_briefing())


if __name__ == "__main__":
    main()
PYEOF
chmod 755 "${BRIEFING_SCRIPT}"

python3 - <<'PYEOF'
import json
import os

briefing_script = os.path.expanduser("~/.agents/session-briefing.py")


def load_json_safe(path: str) -> dict:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


# 6-1. Antigravity (~/.gemini/config/hooks.json)
gemini_hooks_path = os.path.expanduser("~/.gemini/config/hooks.json")
os.makedirs(os.path.dirname(gemini_hooks_path), exist_ok=True)
g_hooks = load_json_safe(gemini_hooks_path)
g_hooks["work-ops-session-briefing"] = {
    "PreInvocation": [
        {
            "type": "command",
            "command": f"python3 {briefing_script} antigravity",
            "timeout": 5,
        }
    ]
}
with open(gemini_hooks_path, "w", encoding="utf-8") as f:
    json.dump(g_hooks, f, ensure_ascii=False, indent=2)
    f.write("\n")

# 6-2. Claude Code (~/.claude/settings.json) — preserve Orca hooks at inner hook level
claude_settings_path = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(claude_settings_path), exist_ok=True)
c_settings = load_json_safe(claude_settings_path)
c_hooks = c_settings.setdefault("hooks", {})
briefing_entry = {
    "matcher": "*",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {briefing_script} claude",
            "timeout": 5,
        }
    ],
}

for event_name in ("SessionStart", "PostCompact"):
    existing = c_hooks.get(event_name, [])
    filtered = []
    for item in existing:
        if not isinstance(item, dict):
            continue
        kept_inner = [
            h
            for h in item.get("hooks", [])
            if not (
                isinstance(h, dict)
                and (
                    "00_TODO.md" in h.get("command", "")
                    or "session-briefing.py" in h.get("command", "")
                )
            )
        ]
        if kept_inner:
            new_item = dict(item)
            new_item["hooks"] = kept_inner
            filtered.append(new_item)
    c_hooks[event_name] = [briefing_entry] + filtered

with open(claude_settings_path, "w", encoding="utf-8") as f:
    json.dump(c_settings, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Synced Session-Start & Post-Compact Briefing hook -> {gemini_hooks_path} & {claude_settings_path}")
PYEOF
