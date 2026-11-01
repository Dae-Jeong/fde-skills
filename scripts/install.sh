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
# docsspace — Master SSOT Index (전체 원장 목차)

> 본 볼트(\`~/docsspace/\`)는 모든 개인 업무(\`work-ops\`) 및 FDE 프로젝트 문서(\`<project-slug>\`)의 **유일한 단일 진실 공급원(SSOT)**입니다.

## 1. 개인 업무 운영 원장 (\`work-ops/\`)
- **[work-ops/00_TODO.md](./work-ops/00_TODO.md)**: 누적 할 일 원장 (\`D+N\` 오래된 순)
- **[work-ops/01_Daily_Logs/](./work-ops/01_Daily_Logs/)**: 일일 작업 로그 및 회고
- **[work-ops/99_Archive/](./work-ops/99_Archive/)**: 완료 아카이브

## 2. FDE 고객사 / 프로젝트별 원장 (\`<project-slug>/\`)
| 프로젝트 폴더 | 대표 목차 (Index) | 핵심 산출물 현황 |
| :--- | :--- | :--- |
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
