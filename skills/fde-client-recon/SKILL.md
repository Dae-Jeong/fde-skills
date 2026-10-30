---
name: fde-client-recon
description: >
  Pre-meeting client reconnaissance for FDE engagements — decode a client's public signals (website GNB/menu structure,
  JSON-LD, product catalog specs, job postings, industrial-complex location & company age, patents/certifications/news,
  and visual/document forensic artifacts) into an operational archetype (MTS/ATO/MTO/ETO + MRO secondary axis), primary
  management key (LOT vs Machine Serial), 3-tier Owner/Manager/Operator pain hypotheses, schema keyword seeds, and
  pinpoint first-meeting questions using the Bi-directional 3-Level A-to-Z Reconnaissance Framework (초급 L1 ↔ 중급 L2 ↔ 고급 L3).
  Emits a public-safe recon_handoff_seed for fde-domain-simulator (and onward to fde-reverse-plan) while isolating
  client-identifiable context in a vault-only recon_private_overlay.
  Use when given only a client URL or company name before a first meeting, or when asked to "고객사 사전 정찰",
  "첫 미팅 준비", "이 회사 어떤 구조로 돈 버는지 분석", or "미팅 질문 뽑아줘".
---

# FDE Client Recon (Bi-directional 3-Level A-to-Z OSINT Pre-Meeting Reconnaissance)

고객사 URL이나 회사명만 주어졌을 때 **회사 소개 요약을 만들지 않는다.**
공개 신호를 **현업 프로세스와 DB 스키마 단서**로 번역해 "이 회사는 어떤 운영 아키텍처로 돈을 벌며,
지금 어느 부서에서 피가 터지고 있는가?"에 대한 **검증 전 가설**을 **단일 근거 원장(`recon_ledger`)**으로 구축하고,
이를 **양방향 3단계 A-to-Z 프레임워크(`초급 L1 ↔ 중급 L2 ↔ 고급 L3`)**로 렌더링한다.

이 스킬은 FDE 사전 준비 3단 파이프라인의 1단계다.

```text
[1단계: fde-client-recon]        [2단계: fde-domain-simulator]      [3단계: fde-reverse-plan]
고객사 URL / 회사명 입력   ───▶  판별된 세부 업종·운영 방식에  ───▶  시뮬레이션에서 도출한 더티 시드로
(Step 0 모드 결정 + OSINT)       맞춰 Stage 1~4 × 5-Layer 해부       End-to-End Spike 후 역산 계획서 작성
```

| 단계 | 스킬 | 핵심 질문 | 다음 단계로 넘기는 산출물 |
| :--- | :--- | :--- | :--- |
| 1. 고객사 정찰 | `fde-client-recon` (이 스킬) | 어떤 운영 아키텍처(MTS/ATO/MTO/ETO + MRO)로 돈을 벌며, 어디서 피가 터지는가? | 3단계 A-to-Z 리포트(`L1/L2/L3`), 단일 원장(`recon_ledger`), 공개용 **`recon_handoff_seed`** (+ 비공개 볼트용 `recon_private_overlay`) |
| 2. 도메인 시뮬레이션 | [`fde-domain-simulator`](../fde-domain-simulator/SKILL.md) | 공식 장부와 야전 장부(Shadow IT)는 어디서 갈라지는가? | Stage 1~4 × 5-Layer 매트릭스(출처 3분류 표시), 페르소나 롤플레잉, 용어 사전, **Dirty Data Seed** |
| 3. 역산 계획서 | [`fde-reverse-plan`](../fde-reverse-plan/SKILL.md) | 80% 정상 + 20% 엣지케이스로 한 판 돌리면 어디까지 자동화되는가? | 합성 더티 데이터셋, Spike 결과, 80:20 Auto/Repair 구획, 2주 스프린트 계획서 |

---

## 핵심 원칙

1. **요약이 아니라 번역**: 메뉴·채용·스펙·시각 단서 한 줄마다 "그래서 현장의 어떤 업무/테이블/병목을 뜻하는가"로 번역한다. 번역되지 않는 정보는 버린다.
2. **모든 결론은 '검증 전 가설'**: 외부 정찰로 찾은 아픈 손가락을 첫 미팅에서 단정하거나 훈수 두지 않는다. 반드시 반증 조건(Falsifier)과 현장 언어로 된 **확인 질문**으로 변환한다.
3. **레벨은 단일 원장(`recon_ledger`)의 투영(Projection)이다**: 세 레벨(`L1`, `L2`, `L3`)을 각각 별개 글로 세 번 창작하지 않는다. 하나의 원장(`S#` 신호, `H#` 가설, `Q#` 질문, `U#` 미확인)을 세우고, 각 레벨은 **동일한 4개 고정 슬롯(`Slot A ➔ B ➔ C ➔ D`)을 해상도 파라미터만 달리해 투영**한다.
4. **해상도(Resolution) ≠ 확신도(Confidence)**: 디테일하게 적는 것(고해상도 L3)과 근거가 확실한 것(고확신도)을 혼동하지 않는다. 1차 포렌식/스펙 증거가 부족할 때 억지로 소설을 써서 L3를 채우지 않고 **`L3-pending` 게이트**로 차단한다.
5. **같은 '제조업'이라도 아키텍처가 다르면 다른 회사다**: 업종명이 아니라 운영 아키텍처(`MTS/ATO/MTO/ETO` 주축 + `MRO/Aftermarket` 보조축)와 관리 키·BOM 생애주기·A/S 구조로 분류한다.
6. **공개/비공개 분리(`recon_handoff_seed` vs `recon_private_overlay`)**: 공개 저장소·예시·시뮬레이터 공용 시드(`recon_handoff_seed`)에는 고객사 실명·도메인·대표자명·성향 별칭·고유 모델명을 절대 넣지 않고 `수주 설계형 대형 프레스/설비 제조사(가상, ETO)`처럼 **비식별 아키텍처 프로필**로만 기록한다. 실명·대표자·수주 맥락은 개인 비공개 볼트 전용 `recon_private_overlay`에만 분리 보관한다.
7. **공개 정보만**: 로그인·유료 DB·내부 자료·개인 SNS 추적을 하지 않는다. 공개 웹·공개 채용 공고·공개 뉴스/특허/인증·공개 홍보 영상/카탈로그 정보만 쓴다.

---

## 실행 프로토콜 (Step 0 ~ Step 5)

### Step 0. 증거 인벤토리 점검 및 합성 모드 결정 (Evidence Inventory & Mode Selection)

정찰 시작 시 아래 **6대 신호 클래스**의 확보 여부와 가용 시간 예산을 먼저 점검한다.

1. **사이트/메뉴 구조** (`site`): GNB 메뉴 비중, JSON-LD, 사업장/공장 구성, A/S 접수 구조
2. **카탈로그/사양 스펙 표** (`catalog`): 제품 라인업, 물리 사양 컬럼, 표준 옵션 모듈
3. **채용 공고** (`job`): 현재 채용 직무, 자격요건/우대사항(ERP·엑셀·PLC·시운전 등), 상시 채용 여부
4. **제3자 기록** (`third_party`): 특허, 인증서(CE/UL/IATF 등 DOC/COC), 수출/납품 레퍼런스, 뉴스/공시, 연혁/M&A
5. **1차 시각·문서 포렌식** (`artifact`): 공개 홍보 영상/배너 속 모니터 화면 캡처(CAD/엑셀/카톡 작업표시줄, 도면 수기 수정 흔적), 다운로드 가능한 도면/매뉴얼/체크시트
6. **참여 맥락** (`context`): 누가(Economic Buyer), 왜 지금(Why-Now 트리거), 어떤 채널로 FDE를 불렀는가

**양방향 합성 모드 판정 규칙**:

| 합성 모드 | 진입 조건 | 전개 방향 및 실행 방식 |
| :--- | :--- | :--- |
| **`Distill` 모드**<br>*(고급 L3 ➔ 중급 L2 ➔ 초급 L1 핵심 증류)* | 확보 신호 클래스 **≥ 4개** 이고, **1차 산출물(`catalog` 또는 `artifact`) ≥ 1개** 확보 시 | 모든 증거와 포렌식 단서를 먼저 `recon_ledger`와 **고급(L3) 도시에**로 완결 구축한 뒤 ➔ 구조·스키마 매트릭스인 **중급(L2)**을 추리고 ➔ 의사결정자/FDE가 30초 만에 본질을 꿰뚫는 **초급(L1)** 카드로 증류한다. |
| **`Elaborate` 모드**<br>*(초급 L1 v0 ➔ 타겟 수집 ➔ 중급 L2 ➔ 고급 L3 또는 L3-pending ➔ 초급 L1 v1)* | 회사명·URL만 있거나 초기 확보 신호 클래스 **< 4개** (또는 미팅 임박 시) | 업종·메뉴 단서로 **초급(L1 v0)** 가설 뼈대와 최우선 미확인(`U#`)을 먼저 세운 뒤 ➔ 그 가설을 깨거나 입증할 표적 OSINT를 수집해 **중급(L2)** 구조표를 채운다 ➔ L3 진입 게이트 통과 시 **고급(L3)**을 완성하고, 기각/수정된 가설을 반영해 **초급(L1 v1)으로 역전파(Back-propagation) 갱신**한다. |

- 산출물 최상단에 `선택 모드(Distill | Elaborate)`, `확보 신호 클래스(N/6)`, `달성 해상도(L1 | L2 | L3 | L2 (L3-pending))`를 1줄로 명시한다.

---

### Step 1. 웹사이트 해부 및 시각/문서 포렌식 (Site, Catalog & Artifact Decoding)

웹사이트 GNB 메뉴 구조, JSON-LD, 제품 카탈로그·사양서 표, 공개 이미지/홍보 영상 프레임을 해독해 `recon_ledger.signals`(`S#`)에 적재한다.

| 관찰 신호 (`S#`) | 번역 (현업 프로세스 / 스키마 단서) |
| :--- | :--- |
| `기술연구소` / `R&D 실적(전용기 개발)` 메뉴 비중이 크다 | 수주 후 기구설계(CAD)·전장설계(PLC)가 고객 부품 맞춤형으로 도면을 새로 치고 BOM을 내리는 구간이 리드타임의 첫 번째 거대 병목 → **ETO 신호** |
| `A/S 프로세스(직통번호·오버홀·개조)`, `글로벌 네트워크` 전면 배치 | 납품 후 시운전(FAT/SAT), 하자보수(Warranty) 출동, 노후 호기 오버홀·베어링/슬라이드 개조 및 스페어파츠 유상 정산이 핵심 수익축 → **ETO + MRO 신호** |
| `제품 목록`이 품번·규격 그리드, `대량 주문`·`납품 실적` 강조 | 품번 + LOT 중심 반복 생산, 고객 PO/납기 대응이 핵심 → **MTS/MTO 신호** |
| 카탈로그에 `기본 모델 시리즈 + N대 표준 옵션 선택` 구조 | 본체는 ETO/MTO이나 주변 장치는 표준 모듈 조합 → **ATO 보조축 신호** |
| 홍보 영상/배너 속 PC 화면에 `3D CAD + 2D AutoCAD + 엑셀 + 메신저` 동시 실행, 2D 도면 치수 취소선 수기 수정(`~~400~~ ➔ 375`, `여유 +10`) | 전사 PLM/PDM 자동 연동 부재. 3D 모델과 2D 가공 도면 간 파라메트릭 연결이 끊긴 채 수기 오버라이드 → **`E-BOM ≠ M-BOM ≠ As-Built` 단절의 1차 포렌식 증거(`Direct`)** |

**카탈로그 스펙 표 = 스키마 시드(`schema_keywords`)**: 사양 표의 물리 항목과 연혁 상의 코드 체계가 곧 핵심 테이블 컬럼명이다.
- 예(수주형 프레스/설비 제조): `project_no`, `machine_serial_no`, `legacy_lineage`(합병 전 구 법인 코드 계보), `model_series`, `capacity_ton`, `stroke_mm`, `spm`, `die_height_mm`, `slide_adjust_mm`, `slide_area_lr_fb`, `bed_area_lr_fb`, `main_motor_kw`, `option_flags`, `dwg_no`, `eco_rev_no`, `as_built_diff_note`.
- 예(반복 양산 부품 제조): `item_code`, `lot_no`, `work_order_no`, `cavity_no`, `cycle_time_sec`, `yield_rate`, `snp_qty`, `backflush_flag`.

---

### Step 2. 외부 공개 시그널 수집 (External OSINT & Context)

1. **채용 공고 역추적 (Job Posting = Live Pain Point)**:
   - `생산관리(구매/자재) — ERP 및 엑셀 활용 능숙자` → 전산 재고와 실물/외주 재고 불일치로 수기 엑셀 대사에 인력이 묶여 있음.
   - `PLC 제어 / 해외 시운전 가능자` → 기계 조립 후 전장 시운전·셋업 단계에서 납기 지연 발생 중 (ETO).
   - `기구설계(CAD) 경력자 상시 채용` → 수주 대비 설계 캐파 부족, 설계변경(ECO) 누적 (ETO).
   - `생산직(주야 2교대)·품질검사원 다수` → 라인 가동률·불량률 관리가 핵심 (MTS/MTO).
2. **소재지 공단 특성·공장 분리·업력·M&A 연혁 (Organizational & Identifier Friction)**:
   - 업력 30~40년 이상, 수도권 산단 소재 → 고숙련 고령 장인(현장 반장)의 현장 맞춤 가공 관행과 경영진의 전산화 의지 간 **입력 저항 및 디지털 격차**.
   - 제1·2공장 물리적 이원화 및 주물·열처리·대형가공 외주 생태계 → 공장 간/외주 간 반제품 이동 및 진도 추적 블랙박스.
   - 과거 동종 업체 인수·합병(M&A) 이력 → 구 법인 모델 코드와 현 법인 모델 코드가 고객사 납품 원장 및 A/S 이력에 혼재(`legacy_lineage` 분열).
3. **특허/인증/수출 레퍼런스 및 참여 맥락**:
   - CE/UL 인증서 상의 실제 수출 모델·고객사 분포 및 수출 비중 → 장기 리드타임·해외 시운전 체류비·개별 호기 문서(DOC/COC) 정합성 요구.
   - 경제적 구매자(Economic Buyer)와 Why-Now 트리거(대형 턴키 수출 급증, 2세 경영 체제 전환, 공정 혁신 추진 등)를 식별한다.

---

### Step 3. 생산/운영 아키텍처 판별 (Operational Archetype: Primary + Secondary MRO/ATO)

업종명이 아니라 아래 **4대 판별 기준**으로 주 아키텍처(`primary: MTS | ATO | MTO | ETO`)와 수익/고통 비중이 큰 보조축(`secondary: ATO | MRO | MTS`)을 함께 판별한다. 특히 대형 설비 제조사에서 노후 호기 오버홀·개조·예비부품 사업이 핵심인 경우 반드시 **`MRO` 보조축**을 명시해야 A/S 단계의 `As-Built` 도면 단절 고통이 누락되지 않는다.

| 판별 기준 | ① 반복 양산형 (MTS / 반복 MTO) | ② 수주 설계형 장비/설비 제조 (ETO + ATO/MRO) |
| :--- | :--- | :--- |
| **핵심 관리 키 (Primary Key)** | **품번(Item Code) + LOT 번호** (일 수천~수만 개 생산) | **프로젝트 번호 + 모델 시리즈 + 호기 번호(Machine Serial No.)** (대당 수개월 제작) |
| **BOM 생애주기** | 표준 BOM 고정, 변경은 드물고 버전 관리. MRP/Backflush로 자재 소요 계산 | 수주마다 **E-BOM(설계) → M-BOM(구매/외주) → As-Built BOM(현장 조립)** 진화. 제작 중 수기 치수 수정·ECO 상시 발생 |
| **A/S 및 MRO 프로세스** | 클레임·반품·LOT 추적(8D, 불량 원인 분석) 중심. 개별 제품 A/S는 미미 | 시운전(FAT/SAT), 하자보수 출동, **노후 호기 오버홀·개조(MRO)**, 스페어파츠 유상 정산, **호기별 평생 이력**이 수익 핵심 |
| **채용 공고 시그널** | 생산직 다수·교대 근무, 품질검사원, 생산관리(MPS/MRP), 금형 정비 | 기구/전장 설계, PLC 제어, 해외 시운전, 프로젝트 관리(PM), A/S 엔지니어 |
| **Stage 1~4 흐름** | 수주/MPS → 자재/MRP → 라인 생산(POP) → 품질/출하 | 수주/사양확정(ATO 옵션) → **설계(3D/2D E-BOM)** → 대형 외주가공/조립 → **시운전(FAT/SAT)·수출인증·오버홀 A/S(MRO)** |
| **작동 이론 (`theory_baseline`)** | OEE, Little's Law, MRP/Backflush, SPC($C_{pk}$) | PERT/CPM(공정관리), EVM(진척도), 호기별 개별원가계산(Job-Order Costing), Configuration Management(형상관리) |
| **대표 붕괴 지점** | 1공정 땡겨치기로 WIP 적체, 양품만 골라 적어 $C_{pk}$ 착시 | 3D↔2D 수기 오버라이드 및 `E-BOM → M-BOM → As-Built` 단절로 호기별 실시간 마진 및 오버홀 A/S 이력 붕괴 |

---

### Step 4. 단일 근거 원장(`recon_ledger`) 및 3대 계층 병목 가설 구축

Step 1~3에서 수집한 신호를 아래 **단일 근거 원장(`recon_ledger`)** 구조로 정규화한다. 모든 가설(`H#`)은 반드시 **출처 3분류(`Direct` 1차 포렌식/스펙 증거 | `Inferred` 다중 신호 추론 | `Archetype Prior` 업종 아키텍처 일반론)** 중 하나를 표기하고, **반증 조건(`falsifier`)**과 **대안 해석(`alternatives`)**을 포함해야 한다.

```yaml
recon_ledger:
  signals:      # S1..Sn: {id, source_type: site|catalog|job|third_party|artifact|context, evidence_class: Direct|Inferred, observed_at, summary, translation}
  hypotheses:   # H1..Hn: {id, slot: A|B|C|D, tier: owner|manager|operator|structural, stage: 1..4, claim, signal_refs: [S#], source_tag: Direct|Inferred|Archetype Prior, confidence: high|medium|low, shadow_it, distortion, wiifm, falsifier, alternatives: [...], status: open|supported|refuted}
  questions:    # Q1..Qn: {id, target_hypothesis: H#, question, branch_if_yes, branch_if_no}
  unknowns:     # U1..Un: {id, unknown, why_unobservable, verify_in_meeting}
```

- **3대 계층(Owner / Manager / Operator) 병목 맞물림**:
  - **👑 사장님 (`owner`, 대표 가설 `H1`)**: 장기 제작 호기의 납기·사후 원가 블랙박스(ETO) 또는 품목별 실마진·가동률 착시(MTS). *구조가 만드는 의사결정 요구*(예: 수개월 제작 블랙박스와 현장 미정착 우려로 인해 추상적 계획서보다 실물 조기경보 신호등을 선호)를 도출한다.
  - **📋 중간관리자 (`manager`, 대표 가설 `H2`)**: 3D↔2D 수기 치수 수정(`~~400~~➔375`) 및 카톡 ECO 통보로 인한 외주 오발주·납기 지연(ETO) 또는 금형 단도리 리스케줄링·재고 대사(MTS).
  - **🔧 현장/A/S 실무자 (`operator`, 대표 가설 `H3`)**: 조립 시 현장 공차 맞춤(`여유 +10` 그라인더/보링 가공) 미반영으로 인한 수년 뒤 오버홀/A/S 출동 시 도면(`As-Designed`) ≠ 실물(`As-Built`) 불일치(ETO+MRO) 또는 작업일보 몰아치기 가라 입력(MTS).
- **파이프라인 경계 준수**: `fde-client-recon`은 관찰 근거가 있는 **`dirty_data_hints`**와 **`automation_candidate_hints`**까지만 도출한다. 구체적인 80:20 Auto/Repair 확정 구획과 합성 더티 데이터 레코드 생성은 후속 스킬(`fde-domain-simulator` Layer 5 및 `fde-reverse-plan` Step 2)의 고유 역할로 남겨둔다.

---

### Step 5. 양방향 3단계 A-to-Z 렌더링 (`초급 L1 ↔ 중급 L2 ↔ 고급 L3`) 및 Seed 출력

단일 원장(`recon_ledger`)으로부터 아래 **고정 슬롯(A~D) × 3단계 해상도 매트릭스**에 따라 산출물을 렌더링한다.

#### 5.1 고정 슬롯(A~D) × 3단계 해상도 매트릭스 (불변식)

모든 레벨(`L1`, `L2`, `L3`)은 **반드시 동일한 4개 슬롯(`Slot A ➔ Slot B ➔ Slot C ➔ Slot D`) 전체를 완결되게 포함**해야 한다. 어느 레벨에서 읽기를 멈춰도 미팅에 즉시 들어갈 수 있어야 한다.

| 고정 슬롯 | 초급 (`L1` — 30초 Executive Card)<br>*미팅 입장 직전 FDE·리드용 1장 카드* | 중급 (`L2` — 미팅 운영 시트 & 구조 매트릭스)<br>*첫 미팅 진행용 구조표·질문 트리* | 고급 (`L3` — FDE 풀스펙 도시에 & 시드)<br>*내부 심층 분석 & 시뮬레이터 직결 명세* |
| :--- | :--- | :--- | :--- |
| **Slot A.<br>정체·아키텍처·맥락** | • 주 아키텍처 **단 1개** + 핵심 보조축 **≤ 1개** (`ETO + MRO` 등), 신뢰도<br>• 경제적 구매자 1명 + Why-Now 트리거 1줄 | • 4대 판별 기준별 증거 매핑표 (`[S#]` 참조)<br>• 복합 아키텍처(본체 ETO + 옵션 ATO + A/S MRO) 수익/고통 분해<br>• 구매 동기 및 기존 전산(ERP/PLM) 가설 | • 판별 근거 전체 + 반대 증거 검토<br>• 조직 연혁/M&A가 만든 레거시 식별자 분열(`legacy_lineage`)<br>• 글로벌 인증/납품 레퍼런스 원장 |
| **Slot B.<br>4단계 흐름·관리 키** | • Stage 1~4 밸류체인 1줄 요약<br>• 비즈니스를 관통하는 **단일 핵심 관리 키** (`LOT` vs `호기번호`) | • `Stage 1~4 × 공식 전산 vs Shadow IT(엑셀/카톡) × 관리 키 변환/단절 지점 × 카탈로그 스키마 컬럼` 교차 매트릭스 | • 엔티티·식별자 수준 데이터 흐름 및 키 단절 메커니즘<br>• 1차 시각/문서 포렌식 증거 해독(예: CAD 치수 오버라이드, 작업표시줄 분석) |
| **Slot C.<br>핵심 고통·병목 가설** | • 구매자의 가장 큰 R1 고통 가설 **단 1개(`[H1]`)**<br>• `[H1]`의 **반증 조건(Falsifier)** 1줄 | • 사장님(`[H1]`)·중간관리자(`[H2]`)·현장/A/S(`[H3]`) 3계층 맞물림 가설표 (`Stage`, `Shadow IT`, `데이터 왜곡`, `반증 조건`, `WIIFM`) | • 가설별 전체 증거 사슬(`[S#]`, 출처 3분류 태그)<br>• 가설별 **대안 해석(Alternative Interpretation)** 및 구별 질문<br>• 정통 운영이론(`theory_baseline`) 붕괴 메커니즘 및 구조적 의사결정 요구 |
| **Slot D.<br>미팅 질문·타격점** | • 첫 5분 원샷 킬러 질문 **단 1개(`[Q1]`)**<br>• 답변 Yes/No 양갈래 다음 행동(타격점) | • 확인 질문 5선 분기 트리(`[Q1~Q5]`, 검증 가설 ID·Yes/No 분기)<br>• 80:20 Auto/Repair 후보 힌트(`automation_candidate_hints`) | • 질문 전체 + 미확보 증거 수집 계획<br>• 관찰 기반 `dirty_data_hints`<br>• 공개용 **`recon_handoff_seed` YAML** (+ 볼트 전용 `recon_private_overlay` 분리) |
| **공통 필수 (`U#`)** | • 최우선 미확인 사항 Top 2 (`[U1, U2]`) | • 미확인 목록 전체 + 확인 방법 | • `open_unknowns` 전체 + 신호 관찰 시점(`observed_at`) 및 신선도 |
| **포맷·분량 예산** | • 6~8줄 불릿 카드, 주장마다 `[H#]`/`[Q#]` 태그 | • 매트릭스 표 2개 + 질문 트리 (1~2페이지) | • 섹션형 도시에 + `recon_ledger` + YAML Seed |

#### 5.2 레벨 간 무반복 델타 규칙 (No-Repetition Delta Rule)

1. **문장 복붙 금지**: 상위 레벨은 하위 레벨에 쓴 문장을 그대로 복사해 분량을 늘리지 않는다. 하위 레벨 주장은 `[H1]`, `[Q1]` ID로만 참조하고, 상위 레벨에서는 **새 차원(Stage/엔티티 분해), 새 근거(`[S#]` 원문/포렌식), 대안 해석, Yes/No 분기** 중 최소 1개 이상을 반드시 추가한다.
2. **형태(Shape) 차별화**: `L1`은 6~8줄 요약 카드, `L2`는 교차 표와 분기 트리, `L3`는 포렌식 증거 원장과 YAML 시드로 형태 자체를 다르게 렌더링한다.
3. **양방향 동기화**:
   - `Distill` 추적성: `L1` 카드의 모든 문장은 반드시 `L3` 원장의 특정 `H#`, `Q#`, `U#` ID로 역추적되어야 한다.
   - `Elaborate` 역전파: 타겟 수집 과정에서 초기 `L1 v0` 가설이 기각(`refuted`)되거나 보조축(예: `MRO`)이 핵심으로 부상하면 즉시 `L1 v1` 카드를 갱신하고 변경 사유를 1줄 기록한다.

#### 5.3 환각 차단 `L3-pending` 진입 게이트

- **L3 진입 조건**: (1) 확보 신호 클래스 ≥ 4개, (2) 1차 산출물 근거(`catalog` 스펙 표 또는 `artifact` 시각/문서 포렌식) ≥ 1개, (3) Slot C 가설의 과반수가 단순 `Archetype Prior`(업종 일반론)가 아닌 해당 고객사 고유 신호(`Direct` 또는 `Inferred`)에 기반할 것.
- **미충족 시 처리 (`L3-pending`)**: 위 조건을 충족하지 못하면 가짜 도면 번호·가짜 화면 캡처·창작된 납품 원장으로 L3를 꾸며내는 것을 **엄격히 금지**한다. 대신 달성 해상도를 `resolution_achieved: L2 (L3-pending)`으로 선언하고, L3 섹션 자리에 **"L3 승격을 위해 첫 미팅/추가 조사에서 확보할 1차 증거 체크리스트"**만 출력한다.

---

## Recon Handoff Seed 및 비공개 오버레이 형식 (→ `fde-domain-simulator` → `fde-reverse-plan`)

공개 저장소(`fde-skills`) 및 시뮬레이터 표준 입력에는 **`recon_handoff_seed`**만 포함하며, 실제 고객사 식별 정보는 개인 볼트(Obsidian 등) 전용 **`recon_private_overlay`** 블록으로 엄격히 분리한다.

```yaml
# [1] 비공개 볼트 전용 오버레이 (Vault-Only — 공개 저장소 fde-skills 커밋 절대 금지)
# recon_private_overlay:
#   private_client_name: "<실제 법인명 (비공개 볼트에만 기록)>"
#   domain: "<https://client-domain.example>"
#   key_decision_makers: "<대표이사/담당 임원 실명 및 연혁 맥락>"
#   decision_style_note: "<장기 리드타임 블랙박스 및 현장 저항 우려로 인한 실물 조기경보 선호 등>"
#   engagement_context:
#     channel: "<유입 경로>"
#     economic_buyer: "<예산 의사결정자>"
#     why_now: "<현재 프로젝트 추진 트리거>"

# [2] 공개 안전 핸드오프 시드 (Public-Safe Schema — fde-domain-simulator 직결 입력)
recon_handoff_seed:
  resolution_achieved: L3          # L1 | L2 | L3 | L2 (L3-pending)
  synthesis_mode: Distill          # Distill (L3->L2->L1) | Elaborate (L1 v0->L2->L3->L1 v1)
  generated_at: "2026-10-31"
  profile:                         # 비식별 아키텍처 프로필 (실명·도메인·고유 브랜드명 금지)
    label: "수주 설계형 대형 프레스/설비 제조사(가상, ETO)"
    industry: "열간·냉간·온간 단조 프레스, 너클/스탬핑 프레스, 빌렛 절단기 및 턴키 자동화 라인 제조"
    scale: "업력 40년+, 최대 8000톤급, 특허 20건+, 글로벌 인증 20건+, 20개국+ 수출(수출비중 70%)"
    location_trait: "수도권 국가산단 제1·2공장 이원화, 주물·열처리·대형가공 외주 생태계"
  archetype:
    primary: ETO                   # MTS | ATO | MTO | ETO
    secondary:                     # 혼합형 보조축 (ATO | MRO | MTS)
      - ATO                        # 표준 옵션 모듈(다이셋트, QDC, 하중계, 오토트랜스퍼 등) 조합
      - MRO                        # 노후 호기 오버홀·구동부/슬라이드 개조·스페어파츠 A/S
    confidence: high               # high | medium | low
    primary_key: "수주 프로젝트 번호 + 모델 시리즈 + 호기 번호(Machine Serial No.)"
    bom_lifecycle: "3D CAD 어셈블리 ➔ 2D AutoCAD DWG(수기 치수 수정 ~~400~~➔375) ➔ 엑셀 구매/외주 BOM ➔ 현장 맞춤 조립(As-Built)"
    evidence:
      - "[S1 | Direct] R&D 홍보 영상 모니터 캡처: 좌측 3D CAD + 작업표시줄(로컬 탐색기·엑셀·메신저) / 우측 AutoCAD 2D 도면 치수 취소선 수기 수정(~~400~~➔375, 여유 +10)"
      - "[S2 | Direct] 기술연구소 실적: 고객사 타겟 부품(등속조인트, 트랙링크 등) 맞춤형 전용 프레스·서보 스토퍼 ETO 개발"
      - "[S3 | Direct] 글로벌 인증 목록: 해외 단조·자동차 부품사 대상 1000~5000T 대형 수출 호기 개별 인증(DOC/COC)"
      - "[S4 | Direct] A/S 프로세스: 직통 접수 ➔ 실시간 전달 ➔ 현장 출동 3단계 및 노후 설비 전체 오버홀·클러치/슬라이드 개조(MRO)"
  stages:                          # simulator 가로축 Stage 1~4 제안
    - "Stage 1. 수주·사양확정 (표준 옵션 조합·타겟 단조품 사양 협의 및 견적원가 산정)"
    - "Stage 2. 기구/전장 설계 & BOM (3D CAD ➔ 2D DWG ➔ 엑셀 발주 BOM & ECO 변경)"
    - "Stage 3. 대형 외주가공·제1/2공장 조립 (주물/가공 외주 진도 & 현장 공차 맞춤 가공)"
    - "Stage 4. 동조 시운전(FAT/SAT)·해외수출 인증·오버홀 A/S (개별 인증 & 호기별 사후원가·MRO 이력)"
  schema_keywords:                 # 카탈로그·메뉴에서 뽑은 컬럼 후보 (simulator Layer 3 Tier 1 입력)
    - project_no
    - machine_serial_no
    - legacy_lineage               # 합병 전 구 법인 계열 코드 혼재 구분
    - model_series
    - capacity_ton
    - stroke_mm
    - spm
    - die_height_mm
    - slide_adjust_mm
    - slide_area_lr_fb
    - bed_area_lr_fb
    - main_motor_kw
    - option_flags
    - dwg_no
    - eco_rev_no
    - as_built_diff_note
  theory_baseline:                 # simulator Layer 4 후보
    - "Project WBS & Critical Path (PERT/CPM): 6~10개월 장기 제작 호기의 외주 대형 주물·가공 리드타임 병목 관리"
    - "EVM (Earned Value Management) & Job-Order Costing: 호기별 계획 대비 실적 진도율 및 설계변경(ECO)/재가공 원가 집계"
    - "Configuration Management (E-BOM ➔ M-BOM ➔ As-Built BOM): 설계 치수 변경과 현장 맞춤 가공 이력의 호기별 형상 정합성 유지"
  pain_hypotheses:                 # simulator Layer 2 입력 (모두 검증 전 가설)
    owner:
      - id: H1
        hypothesis: "6~10개월 장기 제작·해외 수출 호기의 진행 상황 및 사후 원가 블랙박스"
        signal_refs: ["S2", "S3"]
        source_tag: Inferred       # Direct | Inferred | Archetype Prior
        confidence: high
        stage: 4
        shadow_it: "부서별 주간보고 엑셀, 사후 경리 정산 시트"
        distortion: "설계변경·외주 재가공·해외 시운전 체류비가 호기별로 안 잡히고 사후에 뭉뚱그려져 마진 누수 원인 불명"
        wiifm: "출하 전 호기별 납기 지연 Top 5 부품 및 실시간 마진 Burn-rate 조기경보 신호등"
        falsifier: "이미 ERP/PMS에서 호기별(Project No.) 실시간 원가·외주 진도율과 ECO 손실액이 일 마감으로 집계되고 있다면 기각"
        alternatives:
          - "원가 미집계가 아니라 과거 ERP 도입 실패 트라우마로 인한 현장 미정착 자체가 대표의 진짜 제1 불안일 가능성"
    manager:
      - id: H2
        hypothesis: "3D CAD ↔ 2D DWG 수기 치수 수정(~~400~~➔375) 및 메신저 ECO 통보로 인한 외주 오발주·납기 지연"
        signal_refs: ["S1"]
        source_tag: Direct
        confidence: high
        stage: 2
        shadow_it: "로컬 폴더 DWG, 설계-구매 메신저방, 구매팀 외주 독촉 엑셀"
        distortion: "2D 도면만 고치고 엑셀 BOM은 구버전 유지 ➔ 외주 가공품 입고 후 조립 시점에 치수 불일치 발각"
        wiifm: "도면 DWG 저장 시 구버전 BOM과의 치수·수량 차이 자동 하이라이트 및 외주 발주 잠금"
        falsifier: "PDM/PLM이 구축되어 3D/2D 도면 수정 시 구매 발주 BOM이 자동 잠금·갱신된다면 기각"
        alternatives:
          - "화면 속 ~~400~~➔375 취소선은 설계-구매 단절이 아니라 정상적인 사내 설계 검토 마크업 절차일 가능성"
    operator:
      - id: H3
        hypothesis: "조립 시 현장 공차 맞춤('여유 +10' 그라인더/보링 가공) 미반영으로 인한 수년 뒤 오버홀·A/S 시 도면≠실물 불일치"
        signal_refs: ["S1", "S4"]
        source_tag: Inferred
        confidence: medium
        stage: 3
        shadow_it: "종이 도면 위 볼펜 메모, 고참 반장 개인 수첩"
        distortion: "As-Built 도면 부재로 수년 뒤 오버홀/베어링 교체 출동 시 옛날 도면 믿고 깎아간 부품이 안 맞음"
        wiifm: "복잡한 전산 입력 없이 종이 도면 메모 사진만 찍어 올리면 호기 번호로 1초 만에 검색되는 As-Built 이력 카드"
        falsifier: "시운전(FAT) 완료 시 현장 수정 치수를 도면 Rev에 의무 반영하는 검수 게이트가 작동 중이라면 기각"
        alternatives:
          - "오버홀 시 옛날 도면을 보지 않고 현장에서 매번 실측 후 가공하는 것이 표준 프로세스일 가능성"
  dirty_data_hints:                # 관찰 근거가 있는 오염 패턴 (simulator Layer 5 입력)
    - "[S1] 2D DWG 치수 텍스트 오버라이드: 실제 폴리라인 길이는 400인데 텍스트만 '<s>400</s> 375'로 덮어쓴 도면"
    - "[S3] 과거 합병 전 구 법인 모델 코드와 현 법인 모델 코드가 한 고객사 이력 시트에 혼재"
    - "[S1] BOM 엑셀 수량/단가 란에 '외주 가공집 협의 중', '여유 +10 현장가공 요망' 수기 메모 삽입"
    - "[S2] 동일 턴키 라인인데 프레스 본체와 자동화 이송 장치의 프로젝트 번호가 따로 발번되어 원가 분리"
  automation_candidate_hints:      # 80:20 구획 후보 힌트 (최종 경계 확정은 fde-domain-simulator Layer 5 소유)
    - "DWG/엑셀 BOM 파싱을 통한 정상 80% 자동 매핑 vs 치수 오버라이드(400≠375)·수기 메모 건 20% 수리 어드민(Repair Queue) 분리"
  meeting_questions:               # 핀포인트 확인 질문 (가설 ID 및 Yes/No 분기 포함)
    - id: Q1
      target_hypothesis: H1
      question: "수출 비중이 높고 대형 라인은 제작부터 해외 시운전까지 반년 이상 걸릴 텐데, 현재 진행 중인 호기들 중 '설계 변경이나 외주 지연 때문에 마진이 깎이고 있는 호기'를 출하 전에 미리 보실 수 있습니까, 아니면 다 끝나고 결산이 나와야 아십니까?"
      branch_if_yes: "기존 정산 시트/ERP 화면의 입력 주체와 지연 시간(Lag) 확인 ➔ 실시간 조기경보 대시보드로 좁히기"
      branch_if_no: "구매자 핵심 불안(원가·납기 블랙박스) 적중 ➔ 호기별 신호등 트래커를 1주차 Quick Win으로 제안"
    - id: Q2
      target_hypothesis: H2
      question: "기구 설계에서 급하게 치수를 고치실 때(예: 400을 375로 수정), 도면만 먼저 고치고 구매팀이나 외주 가공집에는 메신저/구두로 연락하다가 옛날 도면대로 가공돼서 들어온 적이 일 년에 몇 번쯤 있으십니까?"
      branch_if_yes: "ECO 도면-구매 BOM 변경 차이 자동 감지(80% Auto + 20% Repair) 파이프라인을 MVP 핵심 기능으로 확정"
      branch_if_no: "설계-구매 간 실제 소통 채널과 외주 납기 지연의 진짜 병목(주물 수급 vs 전장 판넬) 재탐색"
    - id: Q3
      target_hypothesis: H3
      question: "도면에 '여유 +10'처럼 조립 현장에서 반장님들이 직접 맞춰 깎은 치수들이 몇 년 뒤 오버홀이나 베어링 교체 A/S 나갈 때 기록으로 남아 있습니까, 아니면 당시 조립했던 분 기억에 의존하십니까?"
      branch_if_yes: "현장 기록 매체(종이 체크시트 vs 태블릿) 확인 후 호기별 As-Built 이력 통합"
      branch_if_no: "출하 시운전(FAT) 체크시트 사진/메모만 찍으면 호기 번호에 자동 귀속되는 As-Built 아카이브 제안"
  open_unknowns:                   # 정찰로 확인 불가 → simulator 매트릭스 빈 칸
    - id: U1
      unknown: "현재 사내에 도입된 공식 전산(ERP/그룹웨어/PDM) 유무와 실제 사용 범위"
      verify_in_meeting: "구매 발주서와 작업지시서를 현재 엑셀로 뽑는지 특정 ERP 패키지에서 뽑는지 첫 10분 내 확인"
    - id: U2
      unknown: "이번 투입 프로젝트의 공식 발주 범위(설계/BOM 관리 vs 생산/외주 공정 진도 vs A/S 이력 관리)"
      verify_in_meeting: "의사결정자가 가장 먼저 눈으로 보고 싶어 하는 '첫 화면 1장'이 무엇인지 질문하여 스코프 고정"
```

반복 양산형 프로필 예시는 `label: "반복 양산형 부품 제조사(가상, MTS/MTO)"`, `primary: MTS`, `secondary: [MTO]`, `primary_key: "품번 + LOT 번호"`, `bom_lifecycle: "표준 BOM(버전 관리), MRP/Backflush"`, `stages: [수주/MPS, 자재/MRP, 라인 생산(POP), 품질/출하]`, `theory_baseline: [OEE, Little's Law, MRP/Backflush, SPC]` 형태로 채운다.

### 핸드오프 매핑 규칙

| Recon Seed 필드 | `fde-domain-simulator` 입력 위치 | `fde-reverse-plan` 최종 도착 지점 |
| :--- | :--- | :--- |
| `resolution_achieved`, `synthesis_mode` | 실행 절차 0(Seed 해상도 확인 및 일반론 보완 비중 결정) | Step 1 계획서 가정 신뢰도 수준 |
| `profile`, `archetype` (`primary` + `secondary: ATO/MRO`) | 실행 절차 1(도메인·범위 고정), 가상 업체 프로필 | Step 1 문제 정의의 도메인 맥락 |
| `stages` | 실행 절차 2(Stage 1~4 절단) | 퍼널/세그먼트 분해 축 |
| `pain_hypotheses` (`id`, `source_tag`, `falsifier`, `alternatives`) | Layer 1(Shadow IT), Layer 2(페르소나 왜곡·WIIFM), 셀별 출처 3분류 표시 | Step 1 R1(As-Is 병목) 및 R2 후보 |
| `schema_keywords` | Layer 3 Tier 1 스키마 용어 | Step 2 더티 데이터 엔티티/컬럼 |
| `theory_baseline` | Layer 4 이론 대조 | 계획서 핵심 성과 지표(Y) 정의 |
| `dirty_data_hints`, `automation_candidate_hints` | Layer 5 80:20 타격점 및 Dirty Data Seed 확정 | Step 2 엣지케이스 20% 유형 & Step 3 Auto/Repair 구획 |
| `meeting_questions`, `open_unknowns` | 실행 절차 7(첫 미팅 질문) 및 매트릭스 빈 칸 | 미팅 후 R1/R2 확정 및 기각 근거 |

---

## 산출물 표준 목차

1. **Step 0 헤더**: 확보 신호 인벤토리(N/6) · 합성 모드(`Distill` vs `Elaborate`) · 달성 해상도(`L1 | L2 | L3 | L2 (L3-pending)`)
2. **초급(`L1`) — 30초 Executive Card**: 고정 슬롯 `A ➔ B ➔ C ➔ D` + 최우선 미확인(`U1, U2`) (6~8줄 카드)
3. **중급(`L2`) — 미팅 운영 시트 & 구조 매트릭스**: 고정 슬롯 `A(판별표·혼합축 분해) ➔ B(Stage × Shadow IT × 키 단절 × 스키마 매트릭스) ➔ C(3계층 병목·왜곡·반증·WIIFM 표) ➔ D(질문 분기 트리 & 80:20 힌트)`
4. **고급(`L3`) — FDE 풀스펙 도시에** *(또는 증거 미달 시 `L3-pending` 수집 계획)*: 고정 슬롯 `A(레거시 코드 분열·납품 원장) ➔ B(시각/문서 포렌식 해독) ➔ C(증거 사슬·대안 해석·이론 붕괴) ➔ D(Recon Handoff Seed)`
5. **단일 근거 원장 (`recon_ledger`)**: `S#` 신호 · `H#` 가설 · `Q#` 질문 · `U#` 미확인 목록
6. **Recon Handoff Seed (YAML)**: 공개 안전 스키마 (`recon_private_overlay`는 개인 볼트에만 별도 분리)

---

## 완료 체크리스트

- [ ] **Step 0 모드 선언**: 6대 신호 클래스 점검 결과에 따라 `Distill` 또는 `Elaborate` 모드가 명시되어 있다.
- [ ] **고정 슬롯 A~D 완결성**: `L1`, `L2`, `L3` 모든 레벨이 `Slot A(정체/아키텍처) ➔ Slot B(흐름/관리키) ➔ Slot C(고통/병목) ➔ Slot D(질문/타격점)` 4개 슬롯과 미확인(`U#`)을 빠짐없이 포함한다.
- [ ] **무반복 델타 규칙(No-Repetition Delta)**: 상위 레벨이 하위 레벨 문장을 그대로 복붙하지 않고 `[H#]`/`[S#]` 참조 후 새 차원·포렌식 근거·대안 해석·분기를 추가했다.
- [ ] **L3 진입 게이트 준수**: 1차 포렌식/스펙 증거 없이 창작된 소설로 L3를 채우지 않았으며, 증거 부족 시 `L3-pending`으로 처리했다.
- [ ] **아키텍처 + 보조축 판정**: 관리 키 · BOM 생애주기 · A/S 프로세스 · 채용 공고 4대 기준으로 주 아키텍처(`MTS/ATO/MTO/ETO`)와 보조축(`ATO/MRO`)을 판별했다.
- [ ] **반증 조건 및 대안 해석**: 모든 핵심 가설(`H#`)에 출처 3분류(`Direct | Inferred | Archetype Prior`), 반증 조건(`falsifier`), 대안 해석(`alternatives`)이 붙어 있다.
- [ ] **공개/비공개 완벽 분리**: `recon_handoff_seed` 본문과 공개 산출물에 고객사 실명 · 도메인 · 대표자명 · 성향 별칭 · 고유 모델명이 전혀 없으며(`grep` 검증 0건), 실명 맥락은 볼트 전용 `recon_private_overlay`로 분리되었다.
