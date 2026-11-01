#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/skills"
CONFIGS_DIR="${REPO_ROOT}/configs"

TARGET_DIRS=(
  "${HOME}/.agents/skills"
  "${HOME}/.claude/skills"
  "${HOME}/.gemini/config/skills"
)

# 1. Initialize local-only credentials.json for service-explorer if missing
CRED_FILE="${SKILLS_DIR}/service-explorer/credentials.json"
if [ -d "${SKILLS_DIR}/service-explorer" ] && [ ! -f "${CRED_FILE}" ]; then
  printf '{\n  "services": {}\n}\n' > "${CRED_FILE}"
  chmod 600 "${CRED_FILE}"
  echo "Initialized local credentials file: ${CRED_FILE} (chmod 600)"
fi

# 2. Ensure private Obsidian Vault SSOT directories and Master Index (00_INDEX.md) exist
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

> \`~/docsspace/\` 내 전체 폴더 목록과 역할 요약입니다. 각 폴더 내부의 상세 파일 목록은 해당 폴더의 Index 문서를 참조합니다.

| 폴더 | 구분 | 폴더 설명 (무엇을 관리하는 곳인가) | 진입 목차 (Index) |
| :--- | :---: | :--- | :--- |
| **[\`work-ops/\`](./work-ops/)** | 개인 업무 원장 | 전 워크스페이스 통합 누적 할 일(\`00_TODO.md\`, \`D+N\` 정렬), 일일 작업 로그 및 회고(\`01_Daily_Logs/\`), 완료 아카이브(\`99_Archive/\`) 관리 | **[work-ops/00_TODO.md](./work-ops/00_TODO.md)** |
EOF
  echo "Initialized Vault Master Index: ${DOCSSPACE_DIR}/00_INDEX.md"
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

# 3. Sync global root rules (~/.gemini/GEMINI.md)
if [ -f "${CONFIGS_DIR}/GEMINI.md" ]; then
  mkdir -p "${HOME}/.gemini"
  cp "${CONFIGS_DIR}/GEMINI.md" "${HOME}/.gemini/GEMINI.md"
  echo "Synced global rules: ${HOME}/.gemini/GEMINI.md"
fi

# 4. Symlink all skills from fde-skills/skills/* into ~/.agents, ~/.claude, and ~/.gemini
for target_base in "${TARGET_DIRS[@]}"; do
  mkdir -p "${target_base}"
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

# 5. Sync auxiliary skills in ~/.agents/skills (e.g., archify, orca-cli) to ~/.claude and ~/.gemini
for aux_path in "${HOME}/.agents/skills"/*; do
  [ -e "${aux_path}" ] || continue
  aux_name="$(basename "${aux_path}")"
  if [ ! -d "${SKILLS_DIR}/${aux_name}" ]; then
    for extra_base in "${HOME}/.claude/skills" "${HOME}/.gemini/config/skills"; do
      ln -sfn "${aux_path}" "${extra_base}/${aux_name}"
    done
  fi
done
