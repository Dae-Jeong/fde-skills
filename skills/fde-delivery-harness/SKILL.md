---
name: fde-delivery-harness
description: >
  Post-contract FDE delivery and end-to-end requirement-to-product traceability (RTM) harness.
  Manages the full project lifecycle across Step 0 (Handover & Kickoff) through Step 5 (4-Week Internalization & Handover)
  with a Required Document Check briefing protocol, composite track modeling (PORT / IA / BOT), composite (IA-###, FN-###)
  traceability keys, ASIS-to-PORT-to-IA coverage mapping, upstream/downstream data linkage, test-first 5-condition TCs,
  variance-aware source reconciliation, and an 11-item operational handover package. Use when kicking off a delivery project,
  checking current stage and required documents, writing requirement/IA/screen specs, tracking RTM, preparing UAT sign-off,
  or assembling handover deliverables.
---

# FDE Delivery & End-to-End Traceability Harness (`fde-delivery-harness`)

계약 체결 이후 **Step 0(인계·킥오프) ➔ Step 1(Discovery·요구사항) ➔ Step 2(실행계획·IA·DB 설계) ➔ Step 3(Build·10칸 명세·선 TC) ➔ Step 4(통합 검증 UAT·원천 대사) ➔ Step 5(내재화 2~4주[기본 4주]·운영 인계 11종)** 전 과정을 **단일 추적 원장(`00_RTM_TRACKER.md`)**과 **8종 대외 제출 표준 템플릿**으로 통제하는 구축·전환 딜리버리 스킬이다.

---

## 1. 파이프라인 위치, 저장소 경계 및 반출 필터 게이트 (`Architecture & Export Gate`)

### 1-1. 프로젝트 저장소 vs 비공개 볼트 물리적 격리 원칙 (`Zero-Leakage Isolation`)
납품 종료 시 프로젝트 Git 저장소(`OWN-02`)의 소유권과 커밋 이력 전체가 고객사로 이전된다. 따라서 **내부 전용 메모·포렌식 원문·기술 검토서는 고객에게 이전되는 프로젝트 저장소 안에 절대 두지 않고 비공개 볼트(`~/docsspace/<project-slug>/internal/`)에 격리**한다.

```
[1] 고객사 소유권 이전 대상: <project-repo>/docs/ (대외 반출·검수 정본만 배치)
 ├── _harness/00_RTM_TRACKER.md          # 단계 진단 · 복합 트랙(PORT/IA/BOT) · (IA-###, FN-###) 마스터 추적 원장
 └── deliverables/                       # 고객사 제출 · 검수 · 서명용 7종 공식 산출물 (10_ ~ 50_*.md)

[2] 수행사 전용 비공개 볼트: ~/docsspace/<project-slug>/internal/ (고객 저장소 커밋 절대 금지)
 ├── handover-notes/                     # 내부 인수인계 메모, 레거시 결함 분석 원문
 └── spike-and-reviews/                  # 사전 데이터 실험 로그, 내부 기술·일정 검토 메모
```

> 저장소 소유권 이전(`OWN-02`) 전에는 파일 삭제만으로 끝내지 않고 **Git 커밋 히스토리 정화(`50_HANDOVER_PACKAGE.md` `SEC-06`)** 를 선행해 과거 커밋에 남은 내부 문서·타 고객사 경로를 말소한다.

### 1-2. 대외 제출 산출물 반출 필터 게이트 (`Export Sanitization Gate`)
`<project-repo>/docs/` 내 모든 문서는 작성·반출 전 아래 3대 필터를 통과해야 한다:
1. **내부 은어 제거**: 비공식 현업 수기 문서는 `현업 보조 관리 대장(비표준 수기 양식)`으로, 비정형 오류 입력은 `예외 데이터 보정 및 승인 구간`으로, 범위 기준 관리는 `과업 범위 기준선(Baseline)`으로, 차기 과제는 `차기 단계(Next Phase) 고도화 과제`로 표기한다.
2. **보안·자격증명·식별자 차단(2층 분리)**: 평문 DB 비밀번호·API Secret Key·접속 문자열은 어디에도 기재하지 않고 환경변수 키(`DATABASE_URL`)와 역할명으로만 표기한다. 식별자 금지 범위는 두 층으로 나눈다 — **(a) Public 스킬 저장소(`fde-skills`)의 `SKILL.md`·`templates/` 예시**: 고객 식별자·실제 테이블명·실제 화면 ID 절대 금지(가상 예시만 사용). **(b) 고객 이전 대상 `<project-repo>/docs/`**: 해당 고객 소유 저장소이므로 그 고객의 실제 테이블명(`TBL-###` PK/FK)·실제 화면 ID(ASIS 계보) 기재 허용. 단 평문 자격증명·API 키·로컬 절대 경로(`/Users/...`)·**수행사 내부 작업자 핸들(`@...`)**·**타 고객사 프로젝트명·경로(Cross-Client Leakage)**는 (a)·(b) 공통 금지이며, 반출 전 정규식 스캔으로 `0건`을 확인한다.
3. **성과 산식 및 범위 한계 명시**: 작업시간 절감(`횟수 × 인원 × 단축시간`)의 인건비 환산치는 참고용 추정치이며 현금 절감·매출 증가를 법적으로 보증하지 않음을 명시한다.

---

## 2. Step-by-Step 진행 시점 트래킹 및 현재 필요 문서 체크 프로토콜 (`Stage Tracker & Briefing`)

### 2-1. Step 0 ~ Step 5 단계별 필수 문서 · 핵심 내용 · 전환 게이트 매트릭스

> **진단 규칙**: 현재 단계의 필수 문서와 Exit Gate가 모두 충족되어야 다음 단계로 전환한다. **역순 진입(Out-of-Order / Port-First) 판정 규칙**: 코드 구현(Step 3)이 Step 0~2 문서 확정보다 먼저 진행된 브라운필드·인수인계 프로젝트는 단일 `Step N`으로 표기하지 않고, **트랙별로 `물리 구현 단계`(예: `PORT` Step 3 완료)와 `공식 게이트 계류 단계`(예: Step 2 ➔ 3 진입 게이트 계류 — 역순 진입)를 병기**하며, 소급(Retroactive) 작성할 Step 0~2 문서를 필수 보완 문서로 명시한다(`00_RTM_TRACKER.md` §1 트랙별 현재 Step 열).

| 단계 (`Step`) | Flowpass 단계 | 표준 기간 (16주 예시) | 현 단계 필수 작성·갱신 문서 (`templates/`) | 필수 포함 핵심 내용 (`Mandatory Contents`) | 다음 단계 진입 게이트 (`Exit Gate`) |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **Step 0**<br>인계 및 킥오프 | `08 ~ 09` | 시작 후 1주<br>(D+3 / D+5) | • `10_SOW_AND_WBS.md`<br>• `00_RTM_TRACKER.md` | • 이해한 범위 한 장(5칸), 역산 WBS, **킥오프 6대 수령 항목**<br>• 복합 트랙(`PORT`/`IA`/`BOT`) 선언, 초기 미결(`D-###`)·차단(`B-###`) 등록 | • 3영업일 내 범위 5칸 역제출(D+3)<br>• 5영업일 내 킥오프(D+5): **읽기전용 권한 1개 필수 수령**, 나머지 5가지는 당일 수령 또는 서면 기한 확약 허용 |
| **Step 1**<br>Discovery·요구확정 | `10` | 킥오프 후<br>1 ~ 2주 | • `20_REQ_AND_FLOW.md`<br>• `00_RTM_TRACKER.md` | • **고객사 유형 A/B/C(PI 유무 기준)** 판정, `REQ-###`(`[사실: 출처]`)<br>• 단계별 `[입력·판단·결과·원천대조]` 흐름도(`FLOW-##`) 및 3박자 개선안 | • 고객사 유형(A/B/C) 판정<br>• 모든 `REQ-###` 채번·`FLOW-##` 원천 대조 완료<br>• 미결(`D`)·차단(`B`) 분리 합의 |
| **Step 2**<br>실행계획·설계확정 | `11` | 그다음 1주 | • `22_IA_AND_LINKAGE.md`<br>• `30_INFRA_AND_MIGRATION.md`<br>• `00_RTM_TRACKER.md` | • 전체 IA 트리·3계층 권한, 내장 단위기능(`FN-###`) 요약 통합<br>• `ASIS ➔ PORT ➔ IA` (**주/보조/보관/폐기**) 매핑, `[선행 IA ➔ 현재 IA(FN) ➔ 후속 IA + R/W TBL]` 연계표<br>• `dev`/`main` 환경 분리, 물리 테이블(`TBL-###`), 이관 설계(`MIG-###`) | • **"이후 모든 일이 IA 번호에서 시작"**<br>• `(IA-###, FN-###)` 복합 키 RTM 등록 100% |
| **Step 3**<br>Build·선(先) TC 구현 | `12` | 남은 기간 전부<br>(예: 7주) | • `23_SCREEN_SPEC_TEMPLATE.md`(`IA`/`BOT` 개별; `PORT` 대량 이식은 면제 — 3절 4항)<br>• `00_RTM_TRACKER.md` | • 화면/자동화별 **공통 10칸(종류·상태 포함)** 상세 명세 + Use Case<br>• 구현 전 **선(先) 작성 5대 조건 TC(`TC-01~05`)** + 결함/변경(`CR-###`) 분리 검수의견표<br>• `PORT`: 이식 계약 원장 + 자동 동등성 테스트 + 핵심 쓰기 화면 Top-N TC | • `IA`/`BOT`: 개별 `23_` 공통 10칸 + 선작성 `TC-01~05`, `IA 1개 = 브랜치 1개` 배포(대규모 IA는 Wave 묶음 — 각 Wave는 Wave 내 화면 전부 치명 0건·중간보고 통과 시 다음 Wave 착수, Step 3 ➔ 4 전환은 전 Wave 완료 시)<br>• `PORT`: 이식 계약 원장 + 자동 동등성 테스트 + Top-N TC로 갈음<br>• 내부 검수회의 **치명 결함 0건** 및 중간보고 통과 |
| **Step 4**<br>통합 검증(UAT)·대사 | `13` | 종료일 - (내재화+UAT)<br>(예: 4주+1주 = 5주 전) | • `40_UAT_AND_DATA_RECON.md`<br>• `30_INFRA_AND_MIGRATION.md` | • 3층(인수기준·Use Case·TC) UAT 총괄표 + 실행 증적 연결표(`RUN-##`) + 되돌리기(`RB-##`) 실연 기록<br>• 원천 대사표(**`원천 - 신규 = 승인된 변경 차이(VAR-###)`**)<br>• 이관 결과 대사 및 **전환 전략(일괄/병행/단계)·역이행 런북** 확정 | • 미승인 원천 오차 `0건/0원` 및 치명 결함 `0건`<br>• 고객 UAT 서명 및 `main v1.0` 승격 |
| **Step 5**<br>내재화·클로징 | `14 ~ 15` | 종료 전 승인 내재화 길이<br>(2~4주, 기본 4주 — 3절 3항) | • `50_HANDOVER_PACKAGE.md`<br>• `00_RTM_TRACKER.md` | • 내재화 기본 4주(`1주 쓴다 ➔ 2주 고친다[소유권이전·8/10] ➔ 3주 버틴다[장애·백업복원·운영점검회의] ➔ 4주 넘긴다[월마감·서명]`; 2~3주면 활동 합침)+**원본 종료조건 6가지 조건별 판정**<br>• **운영 인계 11종(유지보수·하자보수 설명서, Penpot/IA 설계 원본 포함)** + 최종 인수인계확인서 | • 6조건 조건별 판정 + **종료 처분 확정(완전 충족 종료 / 승인된 조건부 인계[미충족 항목·담당·기한·잔여지원 명시])**<br>• 인계 11종 전달 및 최종 인수인계확인서 서명 |

### 2-2. 현재 시점 진단 및 필요 문서 체크 브리핑 포맷 (`Required Document Check Protocol`)
사용자가 **"현재 시점 체크해줘"**, **"지금 어떤 문서가 필요해?"**, **"다음 단계 가려면 뭐 해야 해?"**라고 요청하면, 에이전트는 대상 저장소의 `docs/_harness/00_RTM_TRACKER.md` 및 `docs/deliverables/` 파일 상태를 1차 스캔한 뒤 반드시 아래 **표준 4줄 브리핑 포맷**으로 먼저 응답한다. **폴백(Fallback)**: 해당 경로가 아직 없는 초기·중도투입 프로젝트라면 ① `~/docsspace/<project-slug>/00_SSOT_INDEX.md`(Live Memory Header 포함)와 ② 코드 저장소 `docs/` 하위 인덱스·설계·인계 문서를 전수 스캔하여 8종 템플릿(`DOC-000~501`)과의 1:1 대응 매핑 및 충족도(`충족·부분·공백`)를 먼저 도출한 뒤 브리핑한다.

```markdown
① 📍 현재 시점: Step N (<단계명> — Flowpass <번호>) [역순 진입 시: 트랙별 물리 구현 단계 + 공식 게이트 계류 단계 병기]
② ✅ 완료 문서: <생성 및 확정 완료된 문서 목록과 핵심 달성 지표 요약>
③ 🔥 현 단계 필수 작성·보완 문서: <지금 즉시 생성해야 할 템플릿 또는 채워야 할 미결(D-###)·차단(B-###)·미실행 TC 항목 — 역순 진입 시 소급 작성할 Step 0~2 문서 포함>
④ ⏭️ 다음 단계(Step N+1) 진입 게이트: <다음 단계로 넘어가기 위해 완료해야 할 필수 검증 조건 및 고객 합의/서명 항목>
```

---

## 3. 핵심 추적 및 품질 통제 규칙 (`Core Traceability & Quality Rules`)

1. **복합 트랙(`PORT` / `IA` / `BOT`) 및 `(IA-###, FN-###)` 복합 추적 키**:
   - 단일 프로젝트 안에서도 **레거시 그대로 이식(`PORT`)**, **화면·흐름 재설계(`IA`)**, **단일 자동화·알림 봇(`BOT`)** 트랙의 명세·검수 기준을 분리 선언한다(`00_RTM_TRACKER.md` 제1절).
   - 한 화면에 여러 기능이 들어가거나 공통 기능이 여러 화면에 배치되는 N:M 충돌을 막기 위해 RTM 행은 **`(IA-###, FN-###)` 복합 단위**로 구성하고, 단위 기능 요약은 `22_IA_AND_LINKAGE.md`에 통합하며 공통 10칸 상세와 5대 TC는 `23_SCREEN_SPEC_TEMPLATE.md`에만 단일 정본으로 둔다(`PORT` 트랙은 이식 계약 원장이 대체 정본 — 3절 4항).
   - **ID 표기 허용 범위**: 숫자형 `(IA-###, FN-###)` 외에 고객사·Penpot·코드베이스에 이미 공유된 **프로젝트 도메인 코드 `(IA-<코드>, FN-###)`** 와 레거시 코드 **`PORT:<레거시코드>` / `ASIS:<레거시코드>`** 를 정식 허용한다(템플릿 예시는 숫자형, 프로젝트별로 한 체계만 선택해 전 문서에 동일 적용).
2. **선(先) 5대 조건 TC 커버리지 및 원천 대조(`원천 - 신규 = 승인된 변경 차이`)**:
   - 모든 `IA-###`는 구현 전 **`TC-01(정상)` · `TC-02(예외/보정)` · `TC-03(3계층 권한)` · `TC-04(복구/멱등)` · `TC-05(원천대조)`**를 먼저 정의한다(해당 없는 조건은 승인된 `N/A 사유` 기재; `PORT`는 핵심 쓰기 화면 Top-N 표본 TC로 갈음).
   - 레거시 계산 오류를 바로잡은 개선 트랙(`IA`)에서는 구시스템 숫자와 신규 숫자가 다른 것이 정상이므로, 대사 판정식을 **`원천 수치 - 신규 수치 = 사전 승인된 변경 차이(VAR-###)`**로 적용한다(미승인 차이만 치명 결함).
3. **일정 역산 철칙 및 양식 경량화**:
   - 내재화 길이는 제안·견적 단계(Flowpass `06`)에서 **과업 유형(①~⑥)과 계약 주수·월 단위 업무 유무**로 결정한다: **월 단위 업무가 있으면 4주, 없으면 8주 미만 계약 2주 · 8~11주 3주 · 12주 이상 4주** `[사실: 덱 p.24]`. 본 하네스의 기본 상정은 **④ 재구축형(20주 이상) = 내재화 4주**이다 `[사실: 덱 p.29]`.

     | 과업 유형 (`[사실: 덱 p.29]`) | 기간 구간 | 내재화 길이 |
     | :--- | :---: | :--- |
     | ① 진단형 | 해당 없음 (PI 2주·4주) | 없음 |
     | ② 단일 자동화형 (`BOT`) | 7~11주 | 2주 (월 업무 있으면 4주) |
     | ③ 디지털 전환형 | 12~14주 | 3~4주 |
     | **④ 재구축형 (본 하네스 기본)** | **20주 이상** | **4주** |
     | ⑤ 이관·인프라형 (`PORT`) | 11주 이하 | 2주 (`고친다`·`버틴다` 중심) |
     | ⑥ 운영·유지보수형 | 해당 없음 | 운영 구독 |

   - **우선순위 선언**: 과업 유형 표(`[사실: 덱 p.29]`)가 1차 기준이고, 같은 유형 안에서는 계약 주수·월 단위 업무 유무 규칙(`[사실: 덱 p.24]`)으로 2/3/4주를 확정한다. 확정값은 `10_SOW_AND_WBS.md` §4 역산 WBS에 **"승인 내재화 길이"로 1회만 기재**하고, 다른 모든 문서(`00_`·`40_`·`50_`)는 그 값을 참조한다(`00_RTM_TRACKER.md` §1 트랙별 내재화 칸은 기본값 표시용).
   - 전체 계약 기간에서 **`[승인 내재화 길이(2~4주) + UAT 1~2주]`를 종료일로부터 먼저 차감**한다 — **UAT 착수 시점 = 종료일 - (승인 내재화 길이 + UAT 길이)** (예: 4주+2주 = 종료 6주 전, 2주+1주 = 종료 3주 전). 이어서 앞단 `[인계·킥오프 1주 + Discovery 1~2주 + 실행계획 1주]`를 뺀 남은 기간만 Build에 배정한다. 내재화를 줄일 때는 `쓴다·고친다·버틴다·넘긴다` 네 활동을 **합칠 뿐 빠뜨리지 않는다**(3주: `쓴다` / `고친다·버틴다` 합침 / `넘긴다` · 2주: `쓴다·고친다` 합침 / `버틴다·넘긴다` 합침) `[사실: 덱 p.24]`. **Build ≤ 0이면 내재화를 깎지 않고 범위 축소 또는 기한 연장을 재합의**한다.
   - 3자 서명란은 계약·검수·인계 구속력이 있는 **`10_SOW_AND_WBS.md`, `40_UAT_AND_DATA_RECON.md`, `50_HANDOVER_PACKAGE.md` 3개 문서에만** 두고, 나머지 5개 템플릿(`00_`, `20_`, `22_`, `23_`, `30_`)은 상단 4줄 메타데이터 표만 유지한다. 모든 템플릿의 판정 기본값은 **`[미실행]` / `[대기]`**로 고정하여 허위 증적 오염을 차단한다.
4. **트랙별 명세·브랜치 차등 적용**:
   - **`IA`·`BOT` 트랙**: 화면/봇 단위로 `23_SCREEN_SPEC_TEMPLATE.md`(공통 10칸 + `TC-01~05`)를 개별 작성하고 `1화면(또는 1에픽 그룹) = 1브랜치`를 적용한다. 대규모 IA는 **Wave/우선순위 묶음(Wave 1 핵심 Top-N ➔ Wave 2~N)** 단위로 순차 작성·게이트 통과를 허용한다. **Wave 게이트와 Step 3 게이트의 관계**: 각 Wave는 Wave 내 화면 전부가 치명 결함 0건·중간보고 통과일 때 다음 Wave 착수가 가능하고, Step 3 ➔ 4 전환(UAT 착수)은 전 Wave 완료 시에만 성립한다.
   - **`PORT` 트랙(대량 1:1 이식)**: 개별 `23_` 작성을 면제하고 **① 이식 계약 원장, ② 자동 조회·저장 동등성 테스트 스위트, ③ 핵심 쓰기 화면 상위 표본(Top-N) TC**로 갈음한다(`00_RTM_TRACKER.md` §1 `PORT` 행 검수 방식과 동일).

---

## 4. 표준 템플릿 8종 카탈로그 (`skills/fde-delivery-harness/templates/`)

| 순서 | 템플릿 파일 경로 | 문서번호 | 서명란 | 담당 단계 (`Step`) 및 핵심 포함 구조 |
| :---: | :--- | :---: | :---: | :--- |
| **1** | [`templates/00_RTM_TRACKER.md`](templates/00_RTM_TRACKER.md) | `DOC-000` | 4줄 헤더 | **[전 단계 공통]** Step 0~5 진행 진단표 + 복합 트랙(`PORT/IA/BOT`) 선언 + `(IA-###, FN-###)` RTM 추적표 + `D/B/CR` 대장 |
| **2** | [`templates/10_SOW_AND_WBS.md`](templates/10_SOW_AND_WBS.md) | `DOC-101` | **3자 서명** | **[Step 0]** 이해한 범위 한 장(5칸) + 과업 범위 기준 관리 원칙 + **킥오프 6대 수령 체크리스트** + 역산 WBS(내재화 주차 반영) |
| **3** | [`templates/20_REQ_AND_FLOW.md`](templates/20_REQ_AND_FLOW.md) | `DOC-201` | 4줄 헤더 | **[Step 1]** **고객사 유형 A/B/C(PI 유무 기준)** + 요구사항(`REQ-###`, 기능/비기능) + `[입력·판단·결과·원천대조]` 흐름도(`FLOW-##`) |
| **4** | [`templates/22_IA_AND_LINKAGE.md`](templates/22_IA_AND_LINKAGE.md) | `DOC-202` | 4줄 헤더 | **[Step 2]** IA 메뉴 트리·3계층 권한·내장 `FN-###` 요약 통합 + `ASIS➔PORT➔IA`(주/보조/보관/폐기) 매핑 + 전후 `LINK`·`TBL` 연계표 |
| **5** | [`templates/23_SCREEN_SPEC_TEMPLATE.md`](templates/23_SCREEN_SPEC_TEMPLATE.md) | `DOC-203` | 4줄 헤더 | **[Step 3]** 개별 `IA-###` 상세 설계서 — **공통 10칸(종류·상태 포함)** + Use Case + 선작성 `TC-01~05` + 결함/변경(`CR`) 검수의견표 |
| **6** | [`templates/30_INFRA_AND_MIGRATION.md`](templates/30_INFRA_AND_MIGRATION.md) | `DOC-301` | 4줄 헤더 | **[Step 2 & 4]** `dev`/`main` 환경 명세 + 물리 DB(`TBL-###`) PK/FK 정의 + 이관 검증(`MIG-###`) + **일괄/병행 전환 및 역이행 런북** |
| **7** | [`templates/40_UAT_AND_DATA_RECON.md`](templates/40_UAT_AND_DATA_RECON.md) | `DOC-401` | **3자 서명** | **[Step 4]** 3층 통합 검수 집계표 + 원천 대사표(**`원천 - 신규 = 승인된 변경 차이 VAR-###`**, 키 집합·고아 FK 비교) + 실행 증적 연결표(`RUN-##`) + 되돌리기(`RB-##`) 시연 + UAT 승인서 |
| **8** | [`templates/50_HANDOVER_PACKAGE.md`](templates/50_HANDOVER_PACKAGE.md) | `DOC-501` | **3자 서명** | **[Step 5]** **운영 인계 11종(하자보수 설명서·Penpot/IA 원본 포함)** + 자가유지보수 8/10 + 소유권·알람 + **원본 종료 6조건(조건별 판정·종료 처분 분리)** + 확인서 |
