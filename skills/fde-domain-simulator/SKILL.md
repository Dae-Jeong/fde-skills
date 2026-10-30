---
name: fde-domain-simulator
description: >
  Simulate an unfamiliar industry domain end-to-end before an FDE engagement — official system flow vs field Shadow IT,
  Owner/Manager/Operator incentives and data distortion, schema terms vs field slang, orthodox theory vs field breakdown,
  and FDE 80:20 intervention points with a dirty-data seed for fde-reverse-plan.
  Accepts the 3-Level A-to-Z recon_handoff_seed (resolution_achieved, synthesis_mode, primary/secondary MRO/ATO axes,
  recon_ledger IDs S#/H#/Q#/U#, theory_baseline, meeting_questions, open_unknowns) from fde-client-recon and switches axes
  by operational archetype (MTS/MTO vs ETO + ATO/MRO).
  Use when entering a new domain (manufacturing, logistics, retail, clinics, etc.), preparing for a first client meeting,
  or when asked to "도메인 시뮬레이션", "현장 업무 흐름 파악", "현장 은어 정리", or a visual domain report (HTML/PDF).
---

# FDE Domain Simulator (5-Layer Domain Simulation)

고객사 데이터를 보기 전에 **도메인의 공식 장부와 야전 장부가 어떻게 갈라지는지**를 먼저 시뮬레이션한다.
교과서(ERP/MES 매뉴얼, 정통 이론)만 읽고 들어가면 첫 미팅에서 현장 은어를 못 알아듣고,
"시스템에는 다 있는데 왜 엑셀을 또 쓰냐"는 헛질문으로 신뢰를 잃는다.

이 스킬의 산출물은 `fde-reverse-plan`의 Step 2(더티 데이터 합성) 입력이 된다.

FDE 사전 준비 3단 파이프라인에서 이 스킬은 2단계다:
[`fde-client-recon`](../fde-client-recon/SKILL.md)(고객사 3단계 A-to-Z 정찰 → `recon_handoff_seed`) → **`fde-domain-simulator`** → [`fde-reverse-plan`](../fde-reverse-plan/SKILL.md)(더티 데이터 Spike → 역산 계획서).

---

## 핵심 원칙

1. **공식 흐름 ≠ 실제 흐름**: 모든 도메인에는 공식 시스템(ERP·MES·POS·EMR) 흐름과 그 틈을 메우는 Shadow IT(엑셀·카톡·화이트보드·수기 장부)가 공존한다. 둘 다 그린다.
2. **데이터 왜곡은 인센티브에서 나온다**: 이상한 데이터는 무능이 아니라 각 역할이 평가받는 방식의 합리적 결과다. "누가, 왜 이 숫자를 이렇게 적는가"를 먼저 묻는다.
3. **현장 언어로 질문한다**: 스키마 용어(Work Order, Yield)와 현장 은어(가라, 땡겨치기)를 1:1로 매핑해야 인터뷰가 통한다.
4. **이론은 붕괴 지점을 찾는 자다**: 정통 이론·수식은 정답이 아니라, 현장이 어디서 왜 어긋나는지를 측정하는 기준선이다.
5. **출처 3분류 명시 (`recon_evidence` / `recon_hypothesis` / `simulator_assumption`)**: `fde-client-recon`에서 넘어온 1차 증거와 정찰 가설, 그리고 시뮬레이터가 메운 업종 일반론 가정을 섞지 않고 셀마다 구분 표기한다.
6. **비식별화**: 공개 산출물에는 고객사 실명·실제 원본 데이터·내부 고유명사를 넣지 않는다. 가상 업체·가상 품번·가상 수치만 쓴다(`recon_private_overlay`는 주입받더라도 공개 리포트/예시에 절대 출력하지 않는다).

---

## 시뮬레이션 프레임: Stage × Layer 교차 매트릭스

- **가로축 (Stage 1~4)**: 도메인 E2E 밸류체인을 4단계로 자른다. 예) 제조업: ① 수주·계획 → ② 자재·구매·외주 → ③ 생산·현장 실행 → ④ 품질·출하·정산.
- **세로축 (Layer 1~5)**: 아래 5대 해부 레이어.
- 각 셀(Stage × Layer)을 채운 20칸 매트릭스가 시뮬레이션의 본체다. 빈 칸은 "아직 모르는 것"(`open_unknowns`) = 첫 미팅 질문 목록이다.

### Layer 1. 이중 장부 구조 (Official vs Shadow IT E2E Flow)
- 각 Stage의 **공식 시스템 흐름**(입력 화면, 테이블, 승인 단계)을 적는다.
- 같은 Stage에서 실제로 돌아가는 **Shadow IT**(엑셀 시트명, 카톡방, 화이트보드, 수기 일보, 로컬 DWG 폴더)를 적는다.
- 두 장부가 **언제 동기화되는지**(월말 일괄 입력, 사후 backflush, 출하 후 사후 정산 등)와 그 시차를 기록한다. 시차 = 데이터 신뢰도 붕괴 구간.

### Layer 2. 3대 페르소나 시뮬레이션 (Owner / Manager / Operator)
대표 시나리오 1개(예: "금요일 오후 긴급 PO 변경" 또는 "조립 중 3D/2D 도면 치수 간섭 발각")를 골라 세 역할로 롤플레잉한다.

| 역할 | 기록할 항목 |
| :--- | :--- |
| **Owner (사장님·경영진)** | 평가 지표(매출·납기·현금흐름), 보고 싶은 숫자, 구조적 불안/의사결정 요구, 그가 유발하는 왜곡 |
| **Manager (중간관리자·팀장)** | 위아래 압박, 방어용 버퍼, 보고용 숫자 가공 방식 |
| **Operator (현장/A/S 실무자)** | 실제 손으로 하는 일, 입력 부담, 숨기는 것(불량·대기·현장 맞춤 가공), 퇴근 전/출동 시 불안 |

- 각 역할마다 **"이 사람 때문에 데이터가 어떻게 휘는가"**(Data Distortion)를 1줄로 명시한다.
- FDE 솔루션이 각 역할에게 주는 **WIIFM(내게 이득)**을 1줄로 적는다. 이득이 없는 역할은 입력을 거부한다.

### Layer 3. 2계층 용어 사전 (Schema Terms vs Field Slang)
- **Tier 1 스키마 용어**: 시스템·표준 문서·카탈로그 스펙(`schema_keywords`)에 나오는 정식 개념(정의, 대표 테이블/필드, 흔한 오해).
- **Tier 2 현장 은어**: 현장에서 실제로 쓰는 말(어원, 실제 의미, 데이터에 남는 흔적, 인터뷰 질문 예).
- 은어마다 **"데이터에 어떤 흔적을 남기는가"**를 반드시 적는다. 이것이 더티 데이터 시드의 원천이다.

### Layer 4. 정통 이론/수식 vs 현장 붕괴 지점 (Theory-Reality Gap)
- Stage마다 대표 이론·공식(`theory_baseline`) 1개를 고른다(예: MTS는 OEE, Little's Law, MRP, SPC / ETO는 PERT/CPM, EVM, 호기별 개별원가계산, Configuration Management).
- **공식** → **필요한 입력 데이터** → **현장에서 그 입력이 오염되는 방식** → **결과적으로 숫자가 어떻게 거짓말하는가**를 순서대로 적는다.
- 이론을 버리지 말고 "어떤 최소 데이터(Minimum Honest Data)만 정직하게 모이면 이론이 다시 작동하는가"를 함께 적는다.

### Layer 5. FDE 80:20 개입 지점 & Dirty Data Seed
- 각 Stage에서 **20% 노력으로 80% 고통을 줄이는 타격점** 1개를 고른다(입력 1회 줄이기, 동기화 시차 없애기, 예외 큐 만들기).
- 100% 자동화를 약속하지 않는다. `fde-client-recon`의 `automation_candidate_hints`를 받아 **Auto Zone(80%) / Repair Zone(20%)** 경계를 확정한다.
- `fde-reverse-plan` Step 2에 바로 넣을 수 있도록 **더티 시드 명세**를 작성한다:
  - 엔티티/컬럼 목록, 정상 80% 규칙, 엣지케이스 20% 유형(`dirty_data_hints` + Layer 3 은어 흔적 기반), 예시 레코드 3~5건.

---

## 입력: `fde-client-recon` 3단계 A-to-Z & `recon_handoff_seed` 연동

고객사 정찰 결과(`recon_handoff_seed` YAML 및 `L1/L2/L3` 리포트)가 있으면 업종 일반론으로 시작하지 않고 Seed를 파라미터로 주입한다. Seed가 없으면 실행 절차 1에서 업종·운영 아키텍처를 직접 가정하고 그 가정을 명시한다.

| Seed 필드 (`fde-client-recon` 출력) | `fde-domain-simulator` 주입 위치 및 처리 규칙 |
| :--- | :--- |
| `resolution_achieved` (`L1 \| L2 \| L3 \| L2 (L3-pending)`), `synthesis_mode` (`Distill \| Elaborate`) | **실행 절차 0**: 정찰 해상도에 따라 시뮬레이터의 업종 일반론(`simulator_assumption`) 보완 비중을 결정한다 (`L3`이면 포렌식 증거 중심, `L1/L2`이면 표준 아키텍처 템플릿으로 빈 칸 보완). |
| `profile`, `archetype` (`primary: MTS\|ATO\|MTO\|ETO`, `secondary: [ATO, MRO]`, `primary_key`, `bom_lifecycle`, `evidence: [S#]`) | **실행 절차 1**: 도메인·범위 고정 및 산출물 1 가상 업체 프로필. `secondary`에 `MRO`가 있으면 Stage 4에 **노후 호기 오버홀·개조·As-Built 이력 추적** 레인을 필수로 추가한다. |
| `stages` | **실행 절차 2**: Stage 1~4 절단 축으로 그대로 채택한다. |
| `pain_hypotheses.owner/manager/operator` (`id: H#`, `signal_refs: [S#]`, `source_tag`, `shadow_it`, `distortion`, `wiifm`, `falsifier`, `alternatives`) | **Layer 1 & Layer 2**: Shadow IT 레인과 3대 페르소나 왜곡·WIIFM의 시작점으로 삼는다. 가설별 반증 조건(`falsifier`)과 대안 해석(`alternatives`)을 페르소나 롤플레잉 분기에 반영한다. |
| `schema_keywords` (incl. `legacy_lineage`, `as_built_diff_note` 등) | **Layer 3 Tier 1 스키마 용어**: 카탈로그 스펙 컬럼과 레거시 식별자 계보를 테이블 스키마에 직접 매핑한다. |
| `theory_baseline` | **Layer 4**: Stage별 정통 이론 선택 및 현장 붕괴 지점 대조의 기준선으로 사용한다. |
| `dirty_data_hints`, `automation_candidate_hints` | **Layer 5**: 80:20 Auto/Repair 구획 확정 및 `fde-reverse-plan`용 Dirty Data Seed(합성 레코드) 생성의 직접 원천으로 사용한다. |
| `meeting_questions` (`Q#`, `target_hypothesis: H#`, `branch_if_yes/no`), `open_unknowns` (`U#`) | **실행 절차 7 & 매트릭스 빈 칸**: `U#`은 20칸 매트릭스의 미확인 셀로 표시하고, `Q#` 분기 트리를 시뮬레이션 질문 목록과 통합한다. |

### 매트릭스 셀 출처 3분류 규칙 (Provenance Tagging)

시뮬레이션 매트릭스의 각 항목에는 반드시 아래 3가지 출처 태그 중 하나를 표시해 정찰 사실과 시뮬레이션 가정을 구별한다:
1. **`[recon_evidence: S#]`**: `fde-client-recon`이 포착한 1차 공개 신호·포렌식 증거(`Direct`).
2. **`[recon_hypothesis: H#]`**: 공개 신호로부터 추론된 검증 전 정찰 가설(`Inferred`).
3. **`[simulator_assumption]`**: 정찰에서 관측되지 않아(`open_unknowns` 또는 `L1/L2` 해상도 한계) 시뮬레이터가 아키텍처 표준 모델(`Archetype Prior`)로 채운 가정.

- 시뮬레이션 중 Seed 가설(`H#`)과 모순되는 도메인 구조가 발견되면 임의로 덮어쓰지 않고 `Recon 가설 충돌 (H# vs 시뮬레이션)`로 기록해 첫 미팅 최우선 확인 질문으로 올린다.

---

## 운영 아키텍처별 시뮬레이션 축 (MTS/MTO vs ETO + ATO/MRO)

같은 제조업이라도 운영 아키텍처가 다르면 Stage 축·관리 키·이론·은어가 완전히 바뀐다. 실행 절차 1에서 아키텍처를 먼저 고정하고 아래 축을 고른다. 판별 기준은 [`fde-client-recon` Step 3](../fde-client-recon/SKILL.md)을 따른다.

| 비교 기준 | 반복 양산형 부품 제조사(가상, MTS/MTO) | 수주 설계형 대형 프레스/설비 제조사(가상, ETO + ATO/MRO) |
| :--- | :--- | :--- |
| **핵심 관리 키** | 품번(Item Code) + LOT 번호 | 수주 프로젝트 번호 + 모델 시리즈 + 호기 번호(Machine Serial No.) |
| **Stage 1~4** | ① 수주/MPS → ② 자재/MRP → ③ 라인 생산(POP) → ④ 품질/출하 | ① 수주/사양확정(ATO 옵션) → ② 설계(3D/2D E-BOM) → ③ 대형 외주가공/조립 → ④ 시운전(FAT/SAT)·수출인증·오버홀 A/S(MRO) |
| **BOM 생애주기** | 표준 BOM 고정·버전 관리 | 3D CAD → 2D DWG(수기 수정) → M-BOM(구매/외주) → As-Built BOM(현장 조립), 제작 중 ECO 상시 발생 |
| **Layer 1 대표 Shadow IT** | 퇴근 전 작업일보, 재고 대사 엑셀, 금형 교체 화이트보드 | 로컬 DWG 폴더, 설계-구매 메신저방, 외주 진도 엑셀, 종이 도면 위 볼펜 치수 수정 메모 |
| **Layer 2 👑 사장님 (`H1`)** | 품목별 실제 마진 깜깜이, 가동률 착시, 원자재 현금 묶임 | 6~10개월 장기 제작·수출 호기별 진행/사후 원가 블랙박스, 현장 미정착 우려(실물 조기경보 신호등 선호) |
| **Layer 2 📋 중간관리자 (`H2`)** | 금형 교체(단도리) 리스케줄링, 전산≠실물 재고 대사 | 3D↔2D 도면 수기 치수 수정(`~~400~~➔375`) 및 메신저 ECO 통보로 기발주 외주 자재 오가공·납기 지연 |
| **Layer 2 🔧 현장/A/S (`H3`)** | 작업일보 몰아치기 입력(가라), 사상/빠우 재작업 은폐 | 조립 시 현장 공차 맞춤(`여유 +10` 그라인더/보링) 후 도면 미반영 → 수년 뒤 오버홀(MRO) 시 `As-Designed ≠ As-Built` |
| **Layer 3 Tier 1 용어 예** | Work Order, LOT, Yield, Backflush, SNP | Machine Serial, Legacy Lineage, ECO/ECN, E-BOM/M-BOM/As-Built, FAT/SAT, Ton/SPM/Die Height |
| **Layer 4 이론 (`theory_baseline`)** | OEE, Little's Law, MRP/Backflush, SPC($C_{pk}$) | PERT/CPM, EVM(진척도), 호기별 개별원가계산(Job-Order Costing), Configuration Management(형상관리) |
| **Layer 4 붕괴 지점** | 땡겨치기로 WIP 적체, 양품만 골라 적어 $C_{pk}$ 착시 | 3D↔2D 수기 오버라이드 및 `E-BOM → M-BOM → As-Built` 연결 단절로 호기별 원가·MRO 오버홀 이력 붕괴 |
| **Layer 5 80:20 타격점 예** | 작업일보 입력 1회화(설비/바코드 연동), 재고 차이 예외 큐 | 호기별 납기·마진 신호등 조기경보, DWG↔BOM 치수 차이(400≠375) 20% 수리 어드민 큐, 사진 기반 As-Built 1초 이력 카드 |
| **Layer 5 더티 시드 예** | LOT 번호 누락·중복, 일괄 입력 타임스탬프 집중, 불량 수량 0 편향 | 2D DWG 치수 텍스트 오버라이드(`<s>400</s> 375`), 구 법인/현 법인 모델 코드 혼재, BOM 비고란 `여유 +10 현장가공` |

- 혼합형(예: 본체 `ETO` + 표준 옵션 `ATO` + 노후 설비 오버홀/개조 `MRO`)은 주 아키텍처(`ETO`)로 매트릭스 골격을 세우고, Stage 1에 `ATO` 옵션 조합 규칙을, Stage 4에 `MRO` 오버홀·구형 코드(`legacy_lineage`)·`As-Built` 추적 행을 명시적으로 결합한다.

---

## 실행 절차 (Workflow)

0. **Recon Seed 및 해상도 확인**: `fde-client-recon`의 `recon_handoff_seed`(`resolution_achieved`, `synthesis_mode`, `S#/H#/Q#/U#`)가 있으면 위 주입 규칙과 출처 3분류(`recon_evidence` / `recon_hypothesis` / `simulator_assumption`)대로 반영한다. 없으면 운영 아키텍처 가정을 명시한다.
1. **도메인·범위 고정**: 업종, 규모(중소/중견), 주 아키텍처 및 보조축(`MTS/ATO/MTO/ETO + MRO`), 대상 부서를 1문단으로 고정한다.
2. **Stage 1~4 절단**: E2E 밸류체인을 4단계로 자르고 Stage별 핵심 산출물(문서·도면·전표·실물)과 핵심 관리 키 전이를 적는다.
3. **Layer 1 → 5 순서로 매트릭스 채우기**: Layer 1(흐름)을 먼저 그려야 Layer 2~5가 구체적이 된다.
4. **페르소나 시나리오 롤플레잉**: Stage를 가로지르는 사건 1개로 3역할 대사·행동·왜곡·반증 조건·대안 해석을 시뮬레이션한다.
5. **이론 대조**: Stage별 이론(`theory_baseline`) 1개씩 붕괴 지점과 최소 정직 데이터(Minimum Honest Data)를 기록한다.
6. **80:20 타격점 및 더티 시드 확정**: `automation_candidate_hints`와 `dirty_data_hints`를 구체화해 `fde-reverse-plan` 입력 형식으로 넘긴다.
7. **첫 미팅 질문 목록 추출**: `meeting_questions`(`Q#` 분기 트리)와 매트릭스의 미확인 칸(`open_unknowns`, `U#`)을 결합해 현장 은어로 된 질문 10개 이내로 정리한다.

---

## 산출물 표준 목차

1. 도메인 개요 및 범위 (가상 업체 프로필 + Recon Seed 해상도/모드 메타데이터)
2. 매크로 아키텍처 Flow 다이어그램 (공식 시스템 레인 vs Shadow IT 레인, 동기화/단절 지점 표시)
3. Stage 1~4 × Layer 1~5 교차 매트릭스 (`recon_evidence` / `recon_hypothesis` / `simulator_assumption` 태그 포함)
4. 3대 페르소나 Deep Dive (대표 시나리오 롤플레잉 카드 + WIIFM + 반증/대안 해석)
5. 정통 이론 vs 현장 리얼리티 대조표 (`theory_baseline` 기반)
6. 2계층 용어 사전 (스키마 용어 `schema_keywords` / 현장 은어)
7. FDE 80:20 타격점 & Dirty Data Seed 명세 (`fde-reverse-plan` 핸드오프)
8. 첫 미팅 질문 분기 트리 (`Q#`) 및 미확인 사항 (`U#`)

---

## 시각화 리포트 규칙 (HTML → PDF)

긴 도메인 시뮬레이션은 Markdown보다 **단일 HTML → A4 PDF**가 공유·검토에 유리하다.

- **소스와 렌더 둘 다 보관**: `examples/<domain>-domain-simulation.html`과 `.pdf`를 함께 커밋한다. 외부 CDN·웹폰트·이미지에 의존하지 않는 자급식 HTML(인라인 CSS, 인라인 SVG/CSS 다이어그램)로 만든다. 폰트는 시스템 한글 폰트 스택(`Apple SD Gothic Neo`, `Noto Sans KR`, `Malgun Gothic`)을 쓴다.
- **페이지 설계**: `@page { size: A4; margin: 0 }` + 섹션마다 `.page { width: 210mm; height: 297mm; overflow: hidden; page-break-after: always }`. 한 섹션이 넘치면 내용을 줄이거나 페이지를 나눈다. 표·카드에는 `break-inside: avoid`를 건다.
- **아키텍처 다이어그램 규칙**:
  - 가로 = Stage 1~4 흐름, 세로 레인 = 공식 시스템 / Shadow IT / 실물(자재·제품) 흐름.
  - 공식 흐름은 실선·차분한 색, Shadow IT는 점선·경고색, 동기화(사후 입력) 지점은 번호 배지로 표시한다.
  - 색 의미를 리포트 전체에서 고정한다(예: 파랑=공식, 주황=Shadow, 빨강=붕괴/리스크, 초록=FDE 개입).
- **렌더링**: 헤드리스 Chrome으로 출력한다.
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
    --no-pdf-header-footer --print-to-pdf=examples/<domain>-domain-simulation.pdf \
    "file://$PWD/examples/<domain>-domain-simulation.html"
  ```
- **밀도 조정**: 페이지 하단 여백이 1/4 이상 남으면 해당 페이지에 `data-zoom style="--z:1.2"` 같은 페이지별 확대(`.page[data-zoom] > :not(.foot) { zoom: var(--z) }`)로 채운다. `overflow: hidden` 때문에 넘친 내용은 조용히 잘리므로, 확대 전후 **페이지별 추출 텍스트 글자 수**를 비교해 줄어든 페이지가 없는지 확인한다.
- **시각 검증 필수**: PDF를 페이지 이미지로 래스터화해(예: `uv run --with pymupdf python ...`) 모든 페이지의 잘림·겹침·글자 깨짐·빈 페이지를 눈으로 확인한 뒤 완료로 보고한다. 페이지 수가 의도한 섹션 수와 일치하는지도 확인한다.

---

## 예시

- [제조업(중소/중견 임가공·조립·부품 및 ETO 설비 비교) 도메인 시뮬레이션](examples/manufacturing-domain-simulation.html) — [PDF](examples/manufacturing-domain-simulation.pdf)
- 수주 설계형 대형 프레스/설비 제조사(가상, ETO + ATO/MRO): 위 [운영 아키텍처별 시뮬레이션 축](#운영-아키텍처별-시뮬레이션-축-mtsmto-vs-eto--atomro) 비교표의 ETO 열과 [`fde-client-recon`의 Recon Handoff Seed 예시](../fde-client-recon/SKILL.md#recon-handoff-seed-및-비공개-오버레이-형식--fde-domain-simulator--fde-reverse-plan)를 입력으로 Stage 1~4 × Layer 1~5 매트릭스를 채운다.
