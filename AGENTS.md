# fde-skills — Agent Entry, Vault Architecture & Skill Authoring Pattern

이 저장소는 FDE(Forward Deployed Engineer) 파이프라인 스킬과 일일 업무/시각화 표준 스킬의 **단일 원장(Single Source of Truth)**이며, 로컬 비공개 Obsidian 볼트(`~/docsspace/`)와 결합해 동작한다:

1. **Public 스킬 저장소 (`~/personalspace/fde-skills`)**:
   - 모든 에이전트(`~/.agents/skills/`, `~/.claude/skills/`, `~/.gemini/config/skills/`)가 공유하는 7종 스킬(`fde-client-recon`, `service-explorer`, `fde-domain-simulator`, `fde-reverse-plan`, `fde-work-log`, `work-ops`, `diagram-renderer`)을 관리한다.
2. **비공개 Obsidian 볼트 (`~/docsspace/`)**:
   - **개인 업무 원장 (`~/docsspace/work-ops/`)**: 어느 작업 공간에서 세션을 열든 모든 할 일(`00_TODO.md`, `D+N` 오래된 순 정렬)과 일일 작업 로그(`01_Daily_Logs/YYYY-MM-DD.md`), 완료 아카이브(`99_Archive/`)는 무조건 이곳을 유일한 원장(SSOT)으로 참조·갱신한다.
   - **프로젝트별 비공개 영역 (`~/docsspace/<project-slug>/`)**: 고객사 실명 문서, 웹 시스템 탐색 원본, 그리고 `fde-client-recon`의 **`recon_private_overlay`**(실명·도메인·대표자·수주 맥락)는 로컬 볼트에만 격리 보관한다.

---

## 기본 구조 및 보안 규칙

1. **스킬 디렉토리 구조**:
   - 모든 개별 스킬은 `skills/<skill-name>/SKILL.md`에 위치하며 YAML frontmatter(`name`, `description`)를 포함한다.
   - 불필요한 Python 래퍼 스크립트 대신 에이전트 네이티브 도구(`read_file`, `edit_file`, `write_file`)와 `orca` CLI를 직접 호출하는 순수 지침(Instruction-First) 구조를 기본으로 한다.
   - 신규 스킬 추가 또는 수정 후 `./scripts/install.sh`를 실행해 `~/.agents/skills/`, `~/.claude/skills/`, `~/.gemini/config/skills/` 심볼릭 링크를 일괄 갱신한다.
2. **보안 및 비식별화 (Public Repo Gate)**:
   - 이 저장소는 Public GitHub 저장소(`https://github.com/Dae-Jeong/fde-skills`)이므로 **고객사 실명, 도메인 URL, 대표자/담당자 실명, 고유 모델 코드, 실제 원본 데이터, 민감 단가, 로그인 자격증명(`credentials.json`)**을 절대 커밋하지 않는다.
   - `skills/service-explorer/credentials.json`은 `.gitignore`(`**/credentials.json`)로 원천 차단하며, 저장소에는 `credentials.example.json`만 유지한다.
   - 모든 예시와 시드는 `"수주 설계형 대형 프레스/설비 제조사(가상, ETO)"`, `"반복 양산형 부품 제조사(가상, MTS/MTO)"` 형태의 일반화된 **비식별 아키텍처 프로필**로만 작성한다.

---

## FDE Skill Authoring Pattern (4-Part Minimal Standard)

새로운 FDE 파이프라인 스킬을 추가하거나 기존 스킬을 고도화할 때 아래 4단계 표준 패턴을 적용한다.

### 1. 분리 vs 확장 판정 규칙 (Separation vs Extension Rule)

새 스킬 디렉토리(`skills/<name>/`)는 **아래 두 조건을 모두 만족할 때만** 신설한다. 하나라도 아니면 기존 스킬의 Step이나 예시를 확장한다.

- **독립된 발화 시점(Trigger Timing)과 입력 상태**: 호출되는 시점(예: 첫 미팅 전 외부 URL만 있을 때 vs 데모/ERP 계정으로 실제 화면을 전수 탐색할 때 vs 도메인 스터디 시 vs 더티 데이터 Spike 시 vs 일일 업무 원장/회고 시)과 입력 아티팩트가 기존 스킬과 명확히 구별되는가?
- **Upstream ➔ Downstream 구조화 핸드오프**: 앞 단계에서 넘겨받거나 다음 단계 스킬로 넘겨주는 **구조화된 핸드오프 시드(`*_handoff_seed` 또는 `99-cross-page-relations.md`)**가 정의되는가?

### 2. 작성 전 4대 정렬 질문 (4 Pre-Authoring Alignment Questions)

`SKILL.md` 본문을 쓰기 전에 아래 4가지를 먼저 한 줄씩 확정한다.

1. **When & Input (발화 조건 및 최소 입력)**: 사용자가 언제, 무엇만 들고 이 스킬을 부르는가?
2. **Slot A ➔ B ➔ C ➔ D (A-to-Z 불변 슬롯 정의)**: 산출물의 처음부터 끝까지 관통하는 4개 고정 슬롯은 무엇인가?
   - 표준 기본값: `Slot A (정체·아키텍처·맥락)` ➔ `Slot B (Stage 1~4 흐름·단일 핵심 관리 키)` ➔ `Slot C (3계층 핵심 고통·병목·반증 조건)` ➔ `Slot D (핀포인트 질문·80:20 타격점·핸드오프 시드)`
3. **L1 / L2 / L3 해상도 & 양방향 모드 (`Distill` vs `Elaborate`)**:
   - **초급 `L1`** (30초 Executive Card, 6~8줄) ↔ **중급 `L2`** (미팅/실행 운영 시트 & 교차 매트릭스) ↔ **고급 `L3`** (풀스펙 도시에 & 포렌식 근거 원장 & YAML Seed)에서 각 슬롯의 해상도 파라미터만 어떻게 바꿀 것인가?
   - 초기 증거가 충분할 때의 **`Distill` 모드(`L3 ➔ L2 ➔ L1` 핵심 증류)**와 단서가 부족할 때의 **`Elaborate` 모드(`L1 v0 ➔ 타겟 수집 ➔ L2 ➔ L3/L3-pending ➔ L1 v1 역전파`)** 진입 기준은 무엇인가?
4. **Upstream ➔ Downstream Handoff Seed**: 앞 스킬의 어느 필드를 받아서, 다음 스킬의 어느 Step/Layer로 어떤 키를 넘기는가?

### 3. 6-Section 표준 `SKILL.md` 골격 (FDE 도메인 스킬 기준)

FDE 분석/정찰 스킬(`skills/fde-*/SKILL.md`)은 아래 6개 섹션 순서로 작성한다(레퍼런스 구현: [`skills/fde-client-recon/SKILL.md`](skills/fde-client-recon/SKILL.md), [`skills/fde-domain-simulator/SKILL.md`](skills/fde-domain-simulator/SKILL.md)).

1. **YAML Frontmatter & 파이프라인 위치 (Overview & I/O Seed)**
2. **Step 0. 증거 점검·합성 모드 선택 및 `L3-pending` 게이트 (Mode Selection & Hallucination Gate)**
3. **Core Protocol — FDE 3대 해부 렌즈 (Step 1~N 실행 절차)**:
   - 렌즈 ① 공식 전산 vs 야전 장부(Shadow IT)
   - 렌즈 ② 3대 계층(Owner / Manager / Operator) 인센티브 왜곡 & WIIFM
   - 렌즈 ③ 80:20 Auto / Repair 구획
4. **양방향 3단계 A-to-Z 출력 규격 (`Slot A~D × L1/L2/L3` & No-Repetition Delta Rule)**
5. **공개 `*_handoff_seed` vs 비공개 `*_private_overlay` 분리 스키마**
6. **산출물 표준 목차 및 완료 체크리스트 (Anti-Patterns & Verification Checklist)**

### 4. 4단계 릴리즈 체크리스트 (4-Step Release Checklist)

신규 스킬 작성이나 기존 스킬 수정 후 커밋·푸시 전에 반드시 아래 4단계를 순서대로 실행한다.

```bash
# Step 1. 스킬 작성/수정 후 로컬 에이전트 심볼릭 링크 갱신 및 확인
./scripts/install.sh
ls -la ~/.agents/skills/ ~/.claude/skills/ ~/.gemini/config/skills/

# Step 2. README.md 파이프라인 Mermaid 다이어그램, 프로젝트 구조 트리, 스킬 가이드 표 동기화 확인

# Step 3. 비식별화(De-identification) 및 자격증명 보안 게이트 검증
git status --ignored -s
grep -riE "<고객사실명>|<도메인키워드>|<대표자명>|<고유모델코드>" skills/ README.md AGENTS.md

# Step 4. Git 상태 확인, 커밋 및 origin/main 푸시
git status -sb
git add .gitignore AGENTS.md README.md scripts/ skills/
git commit -m "feat: <변경 요약>"
git push origin main
```
