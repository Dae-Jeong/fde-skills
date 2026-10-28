# fde-skills

현장 배치 엔지니어(Forward Deployed Engineer, FDE) 실전 워크플로우를 위한 에이전트 스킬 모음입니다.

## 포함된 스킬 (`skills/`)

| 스킬 이름 | 역할 요약 |
| :--- | :--- |
| [`fde-reverse-plan`](skills/fde-reverse-plan/SKILL.md) | **역산 계획서 (Spike-First Planning)** — 미팅록·요구사항 기반으로 현업 더티 데이터(80% 정상 + 20% 엣지케이스)를 먼저 합성하고, 끝까지 한 판(Spike)을 완주한 뒤 80:20 실현 가능성 구획과 복기형 계획서를 도출합니다. |

## 설치 및 심볼릭 링크 연결

클론 후 아래 스크립트를 실행하면 `~/.agents/skills/`와 `~/.claude/skills/`에 각 스킬이 심볼릭 링크로 등록됩니다.

```bash
git clone https://github.com/Dae-Jeong/fde-skills.git
cd fde-skills
./scripts/install.sh
```
