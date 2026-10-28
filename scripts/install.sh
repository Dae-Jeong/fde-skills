#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/skills"

TARGET_DIRS=(
  "${HOME}/.agents/skills"
  "${HOME}/.claude/skills"
)

for target_base in "${TARGET_DIRS[@]}"; do
  mkdir -p "${target_base}"
  for skill_path in "${SKILLS_DIR}"/*; do
    [ -d "${skill_path}" ] || continue
    skill_name="$(basename "${skill_path}")"
    ln -sfn "${skill_path}" "${target_base}/${skill_name}"
    echo "Linked: ${target_base}/${skill_name} -> ${skill_path}"
  done
done
