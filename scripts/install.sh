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

| 폴더 | 구분 | 폴더 설명 (무엇을 관리하는 곳인가) | 진입 목차 (Index) |
| :--- | :---: | :--- | :--- |
| **[\`work-ops/\`](./work-ops/)** | 개인 업무 원장 | 전 워크스페이스 통합 누적 할 일(\`00_TODO.md\`, \`D+N\` 정렬), 일일 작업 로그 및 회고(\`01_Daily_Logs/\`), 완료 아카이브(\`99_Archive/\`) 관리 | **[work-ops/00_SSOT_INDEX.md](./work-ops/00_SSOT_INDEX.md)** |
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

> 본 폴더(\`~/docsspace/work-ops/\`)는 전 워크스페이스 통합 누적 할 일(To-Do), 일일 완료 작업 로그 및 회고, 완료 아카이브를 관리하는 **개인 업무 원장(Single Source of Truth)**입니다.

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

# 6. Configure Session-Start TODO Briefing Hook (Zero static post-hooks; logging is delegated via LLM subagent)
python3 - <<'PYEOF'
import json
import os

briefing_py = (
    "import datetime,os,re; "
    "p=os.path.expanduser('~/docsspace/work-ops/00_TODO.md'); "
    "t=datetime.date.today(); "
    "lines=open(p).read().splitlines() if os.path.exists(p) else []; "
    "items=[((t-datetime.date.fromisoformat(m.group(1))).days if (m:=re.search(r'created::\\s*(\\d{4}-\\d{2}-\\d{2})',l)) else 0, l.strip()) for l in lines if l.strip().startswith(('- [ ]','- [/]'))]; "
    "items.sort(key=lambda x:-x[0]); "
    "body='\\n'.join(f'{i}. (D+{k}) {s[2:]}' for i,(k,s) in enumerate(items,1)) or '- None'; "
    "md=f'**TODO (원장: ~/docsspace/work-ops/00_TODO.md | {t})**\\n{body}'"
)

# 6-1. Antigravity (~/.gemini/config/hooks.json)
gemini_hooks_path = os.path.expanduser("~/.gemini/config/hooks.json")
os.makedirs(os.path.dirname(gemini_hooks_path), exist_ok=True)
try:
    with open(gemini_hooks_path, encoding="utf-8") as f:
        g_hooks = json.load(f)
except Exception:
    g_hooks = {}

g_hooks["work-ops-session-briefing"] = {
    "PreInvocation": [
        {
            "type": "command",
            "command": (
                "python3 -c \"import json,sys; d=json.loads(sys.stdin.read() or '{}'); "
                "sys.exit(print('{}') or 0) if d.get('invocationNum',1)!=1 else None; "
                f"{briefing_py}; "
                "print(json.dumps({'injectSteps':[{'systemMessage':{'systemMessage':md,'metadata':{'user_markdown':md}}}]},ensure_ascii=False))\""
            ),
            "timeout": 5,
        }
    ]
}

with open(gemini_hooks_path, "w", encoding="utf-8") as f:
    json.dump(g_hooks, f, ensure_ascii=False, indent=2)
    f.write("\n")

# 6-2. Claude Code (~/.claude/settings.json)
claude_settings_path = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(claude_settings_path), exist_ok=True)
try:
    with open(claude_settings_path, encoding="utf-8") as f:
        c_settings = json.load(f)
except Exception:
    c_settings = {}

c_settings.setdefault("hooks", {})
c_settings["hooks"]["SessionStart"] = [
    {
        "matcher": "*",
        "hooks": [
            {
                "type": "command",
                "command": f"python3 -c \"{briefing_py}; print(md)\"",
            }
        ],
    }
]

with open(claude_settings_path, "w", encoding="utf-8") as f:
    json.dump(c_settings, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Synced Session-Start TODO Briefing hook -> {gemini_hooks_path} & {claude_settings_path}")
PYEOF
