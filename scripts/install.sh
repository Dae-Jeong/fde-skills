#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/skills"

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

# 2. Ensure private Obsidian Vault SSOT directories exist for work-ops
WORK_OPS_DIR="${HOME}/docsspace/work-ops"
mkdir -p "${WORK_OPS_DIR}/01_Daily_Logs" "${WORK_OPS_DIR}/99_Archive"
if [ ! -f "${WORK_OPS_DIR}/00_TODO.md" ]; then
  cat <<'EOF' > "${WORK_OPS_DIR}/00_TODO.md"
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

# 3. Symlink all skills from fde-skills/skills/* into ~/.agents, ~/.claude, and ~/.gemini
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

# 4. Sync auxiliary skills in ~/.agents/skills (e.g., archify, orca-cli) to ~/.claude and ~/.gemini
for aux_path in "${HOME}/.agents/skills"/*; do
  [ -e "${aux_path}" ] || continue
  aux_name="$(basename "${aux_path}")"
  if [ ! -d "${SKILLS_DIR}/${aux_name}" ]; then
    for extra_base in "${HOME}/.claude/skills" "${HOME}/.gemini/config/skills"; do
      ln -sfn "${aux_path}" "${extra_base}/${aux_name}"
    done
  fi
done
