# fde-skills — Agent Entry & FDE Skill Authoring Pattern

이 저장소는 두 가지 환경에서 모두 동작한다:
1. **Obsidian 볼트 연동 환경**: 로컬에 `../Obsidian/wiki/`가 존재할 때는 `/Users/marin/.agents/AGENTS.md`가 연결하는 [중앙 작업 규약](../Obsidian/wiki/notes/agents/work-management-policy.md)과 프로젝트 Task 정본 [`wiki/projects/fde-skills/`](../Obsidian/wiki/projects/fde-skills/index.md)을 함께 따른다.
2. **단독 클론(Standalone) 환경**: 다른 PC에 `fde-skills`만 단독으로 클론(`git clone`)한 경우, 상위 Obsidian 볼트 없이 **이 `AGENTS.md`와 [`README.md`](README.md), 그리고 `skills/*/SKILL.md`만으로** 신규 스킬 설계·고도화·설치·배포를 완결한다.

---

## 기본 구조 및 보안 규칙

1. **스킬 디렉토리 구조**:
   - 모든 개별 스킬은 `skills/fde-<name>/SKILL.md`에 위치하며 YAML frontmatter(`name`, `description`)를 포함한다.
   - 보조 스크립트는 `skills/fde-<name>/scripts/`, 시각화/샘플 예시는 `skills/fde-<name>/examples/`에 둔다.
   - 신규 스킬 추가 또는 이름 변경 후 `./scripts/install.sh`를 실행해 `~/.agents/skills/` 및 `~/.claude/skills/` 심볼릭 링크를 갱신한다.
2. **보안 및 비식별화 (Public Repo Gate)**:
   - 이 저장소는 Public GitHub 저장소(`https://github.com/Dae-Jeong/fde-skills`)이므로 **고객사 실명, 도메인 URL, 대표자/담당자 실명, 고유 모델 코드, 실제 원본 데이터, 민감 단가, 인증 정보**를 절대 커밋하지 않는다.
   - 모든 예시와 시드는 `"수주 설계형 대형 프레스/설비 제조사(가상, ETO)"`, `"반복 양산형 부품 제조사(가상, MTS/MTO)"` 형태의 일반화된 **비식별 아키텍처 프로필**로만 작성한다.

---

## FDE Skill Authoring Pattern (4-Part Minimal Standard)

다른 PC나 세션에서 새로운 `fde-*` 스킬을 추가하거나 기존 스킬을 고도화할 때 아래 4단계 표준 패턴을 그대로 적용한다.

### 1. 분리 vs 확장 판정 규칙 (Separation vs Extension Rule)

새 스킬 디렉토리(`skills/fde-<name>/`)는 **아래 두 조건을 모두 만족할 때만** 신설한다. 하나라도 아니면 기존 스킬(`fde-client-recon`, `fde-domain-simulator`, `fde-reverse-plan`, `fde-work-log`)의 Step이나 예시를 확장한다.

- **독립된 발화 시점(Trigger Timing)과 입력 상태**: 호출되는 시점(예: 첫 미팅 전 URL만 있을 때 vs 도메인 스터디 시 vs 더티 데이터 Spike 시 vs 일일 퇴근 메모 시)과 입력 아티팩트가 기존 스킬과 명확히 구별되는가?
- **Upstream ➔ Downstream 구조화 YAML Seed**: 앞 단계에서 넘겨받거나 다음 단계 스킬로 넘겨주는 **구조화된 핸드오프 시드(`*_handoff_seed`)**가 정의되는가?

### 2. 작성 전 4대 정렬 질문 (4 Pre-Authoring Alignment Questions)

`SKILL.md` 본문을 쓰기 전에 아래 4가지를 먼저 한 줄씩 확정한다.

1. **When & Input (발화 조건 및 최소 입력)**: 사용자가 언제, 무엇만 들고 이 스킬을 부르는가? (예: URL/회사명 1개, 미팅 녹취록, 현장 사진, 거친 일일 메모 등)
2. **Slot A ➔ B ➔ C ➔ D (A-to-Z 불변 슬롯 정의)**: 산출물의 처음부터 끝까지 관통하는 4개 고정 슬롯은 무엇인가?
   - 표준 기본값: `Slot A (정체·아키텍처·맥락)` ➔ `Slot B (Stage 1~4 흐름·단일 핵심 관리 키)` ➔ `Slot C (3계층 핵심 고통·병목·반증 조건)` ➔ `Slot D (핀포인트 질문·80:20 타격점·핸드오프 시드)`
3. **L1 / L2 / L3 해상도 & 양방향 모드 (`Distill` vs `Elaborate`)**:
   - **초급 `L1`** (30초 Executive Card, 6~8줄) ↔ **중급 `L2`** (미팅/실행 운영 시트 & 교차 매트릭스) ↔ **고급 `L3`** (풀스펙 도시에 & 포렌식 근거 원장 & YAML Seed)에서 각 슬롯의 해상도 파라미터만 어떻게 바꿀 것인가?
   - 초기 증거가 충분할 때의 **`Distill` 모드(`L3 ➔ L2 ➔ L1` 핵심 증류)**와 단서가 부족할 때의 **`Elaborate` 모드(`L1 v0 ➔ 타겟 수집 ➔ L2 ➔ L3/L3-pending ➔ L1 v1 역전파`)** 진입 기준은 무엇인가?
4. **Upstream ➔ Downstream Handoff Seed**: 앞 스킬의 어느 필드를 받아서, 다음 스킬의 어느 Step/Layer로 어떤 YAML 키(`*_handoff_seed`)를 넘기는가?

### 3. 6-Section 표준 `SKILL.md` 골격 (6-Section Standard Skeleton)

모든 `skills/fde-<name>/SKILL.md`는 아래 6개 섹션 순서로 작성한다(레퍼런스 구현: [`skills/fde-client-recon/SKILL.md`](skills/fde-client-recon/SKILL.md), [`skills/fde-domain-simulator/SKILL.md`](skills/fde-domain-simulator/SKILL.md)).

1. **YAML Frontmatter & 파이프라인 위치 (Overview & I/O Seed)**:
   - `name`, `description`(영어 요약 + 한국어 트리거 키워드 명시).
   - 전체 FDE 파이프라인(`fde-client-recon ➔ fde-domain-simulator ➔ fde-reverse-plan ➔ fde-work-log` 등) 내에서의 위치 다이어그램과 입출력 표.
2. **Step 0. 증거 점검·합성 모드 선택 및 `L3-pending` 게이트 (Mode Selection & Hallucination Gate)**:
   - 보유 신호/데이터 인벤토리를 점검해 **`Distill`(`L3➔L2➔L1`)** 또는 **`Elaborate`(`L1 v0➔L2➔L3➔L1 v1`)** 모드를 선언한다.
   - **해상도(Resolution) ≠ 확신도(Confidence)**: 1차 포렌식/실물 증거가 부족할 때 소설을 써서 `L3`를 채우지 않고, `resolution_achieved: L2 (L3-pending)`으로 차단한 뒤 추가 확보 체크리스트만 출력한다.
3. **Core Protocol — FDE 3대 해부 렌즈 (Step 1~N 실행 절차)**:
   - **렌즈 ① 공식 전산 vs 야전 장부(Shadow IT)**: ERP/MES/PLM 공식 흐름과 실제 현장을 굴리는 엑셀·메신저·수기 도면·화이트보드의 사후 동기화 시차(데이터 붕괴 지점) 포착.
   - **렌즈 ② 3대 계층(Owner 사장님 / Manager 중간관리자 / Operator 현장·A/S 실무자) 인센티브 왜곡 & WIIFM**: 각 계층의 평가 지표가 만드는 데이터 왜곡(`distortion`), 기각 조건(`falsifier`), 대안 해석(`alternatives`), 자발적 입력을 유도할 내게 이득(`wiifm`).
   - **렌즈 ③ 80:20 Auto / Repair 구획**: 100% 무인화 환상을 버리고 **80% 정형 자동화(Auto Zone)**와 **20% 예외 인간 수리 어드민(Human-in-the-Loop Repair Queue)** 경계를 구획.
4. **양방향 3단계 A-to-Z 출력 규격 (`Slot A~D × L1/L2/L3` & No-Repetition Delta Rule)**:
   - 단일 근거 원장(`*_ledger`: 신호 `S#`, 가설 `H#`, 질문 `Q#`, 미확인 `U#` 및 출처 3분류 `Direct | Inferred | Archetype Prior`)을 정의한다.
   - `L1`, `L2`, `L3` 모두 `Slot A ➔ B ➔ C ➔ D` 전체를 완결되게 포함하되, 상위 레벨은 하위 레벨 문장을 복붙하지 않고 `[H#]`/`[S#]` 참조 후 새 차원·포렌식 근거·대안 해석·Yes/No 분기만 추가한다(**No-Repetition Delta Rule**).
5. **공개 `*_handoff_seed` vs 비공개 `*_private_overlay` 분리 스키마**:
   - 시뮬레이터·하위 스킬 및 공개 저장소에 남기는 **`*_handoff_seed` (Public-Safe YAML)**와 로컬 개인 볼트에만 분리 보관하는 **`*_private_overlay` (Vault-Only: 실명·도메인·대표자·수주 맥락)**를 명확히 나눈다.
6. **산출물 표준 목차 및 완료 체크리스트 (Anti-Patterns & Verification Checklist)**:
   - 산출물 목차와 완료 전 자기점검 체크리스트(모드 선언, Slot A~D 완결성, 무반복 델타, `L3-pending` 준수, 반증 조건 포함 여부, 비식별화 `grep` 0건).

### 4. 4단계 릴리즈 체크리스트 (4-Step Release Checklist)

신규 스킬 작성이나 기존 스킬 수정 후 커밋·푸시 전에 반드시 아래 4단계를 순서대로 실행한다.

```bash
# Step 1. 스킬 작성/수정 후 로컬 에이전트 심볼릭 링크 갱신 및 확인
./scripts/install.sh
ls -la ~/.agents/skills/fde-* ~/.claude/skills/fde-*

# Step 2. README.md 파이프라인 Mermaid 다이어그램, 프로젝트 구조 트리, 스킬 가이드 표 동기화 확인

# Step 3. 비식별화(De-identification) 보안 게이트 — 고객사 고유명사·도메인·모델코드 0건 검증 (매치 없어야 정상)
grep -riE "<고객사실명>|<도메인키워드>|<대표자명>|<고유모델코드>" skills/ README.md AGENTS.md

# Step 4. Git 상태 확인, 커밋 및 origin/main 푸시
git status -sb
git add AGENTS.md README.md skills/
git commit -m "feat: <변경 요약>"
git push origin main
```

