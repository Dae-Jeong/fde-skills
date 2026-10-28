# fde-skills — Agent Entry

공통 작업 탐색·기록·인수는 `/Users/marin/.agents/AGENTS.md`가 연결하는 [중앙 작업 규약](../Obsidian/wiki/notes/agents/work-management-policy.md)을 따른다. 프로젝트 Task 정본은 Obsidian의 [`wiki/projects/fde-skills/`](../Obsidian/wiki/projects/fde-skills/index.md)에 둔다.

이 파일은 `fde-skills` 저장소 고유 구조와 스킬 작성 경계만 소유한다.

## 구조 및 규칙

1. **작업 규약 및 현재 Task**: 작업 시작 전 [중앙 작업 규약](../Obsidian/wiki/notes/agents/work-management-policy.md)과 프로젝트 진입점 [`wiki/projects/fde-skills/index.md`](../Obsidian/wiki/projects/fde-skills/index.md)에서 현재 활성화된 Task(`tasks/`)의 목표·범위·인수 기준을 확인한다.
2. **스킬 디렉토리 구조**:
   - 모든 개별 스킬은 `skills/<skill-name>/SKILL.md`에 위치하며 YAML frontmatter(`name`, `description`)를 포함한다.
   - 보조 스크립트는 `skills/<skill-name>/scripts/`에 둔다.
   - 신규 스킬 추가 또는 이름 변경 후 `./scripts/install.sh`를 실행해 `~/.agents/skills/` 및 `~/.claude/skills/` 심볼릭 링크를 갱신한다.
3. **보안 및 비식별화**:
   - 이 저장소는 Public GitHub 저장소(`https://github.com/Dae-Jeong/fde-skills`)이므로 고객사 실명, 내부 도메인 고유명사, 실제 원본 데이터, 인증 정보를 절대 커밋하지 않는다.
