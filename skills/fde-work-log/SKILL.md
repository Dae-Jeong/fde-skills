---
name: fde-work-log
description: >
  Convert raw daily FDE (Forward Deployed Engineer) field notes, meeting reflections, or diary entries
  into de-identified engineering blog posts or reusable FDE assets.
  Use when the user drops daily work notes, workshop reflections, or client problem-solving logs.
---

# FDE Work Log (일일 야전 일지 ➔ 비식별화 블로그/자산 변환)

현장 배치 엔지니어(FDE)가 하루 일과 중 일기처럼 남긴 거친 메모(Raw Notes)를 **고객사 기밀·고유명사를 완벽히 제거한 엔지니어링 인사이트 아티클(`fde-YYYY-MM-DD-<topic>.md`)**로 변환한다.

---

## 1. 비식별화 원칙 (De-identification Gate)

변환 전 반드시 아래 항목을 일반화된 도메인 용어로 치환한다.
- **고객사명·서비스명** ➔ 산업군 및 비즈니스 모델로 치환 (예: `"A물류"`, `"중견 B2B 건자재 유통사"`, `"프랜차이즈 본사 정산팀"`)
- **내부 시스템·컬럼 고유명사** ➔ 역할 중심 표준 용어로 치환 (예: `"수기 발주 원장"`, `"월말 마감 대조 시트"`)
- **실무자·이해관계자 실명** ➔ 직무·역할로 치환 (예: `"현장 배차 담당자"`, `"정산 실무자"`, `"의사결정자"`)
- **민감 수치(매출액·단가·계약금)** ➔ 비율(%)이나 처리 단계 수, 상대적 구조로만 서술하며 미검증 수치는 생성하지 않는다.

---

## 2. 2단계 기록 흐름

### Stage 1. 야전 메모 누적 (Raw Note Capture)
사용자가 업무 중 짧은 키워드나 감상을 던지면 즉시 글 초안을 부풀려 쓰지 않고, 핵심 사실만 구조화해 일자별 메모에 적재한다:
- **관찰한 현업 풍경 (Observation)**: 실무자가 실제로 어떻게 일하고 어디서 시간을 쓰는지
- **숨은 규약 (Hidden Convention)**: 비효율처럼 보이지만 사고를 막고 있던 현장의 규칙
- **FDE의 판단 (Decision & Action)**: 무엇을 자동화(80%)하고 무엇을 사람이 확인(20% 수리 어드민)하게 둘 것인지, 혹은 어떤 기술적 선택을 했는지

### Stage 2. 블로그 아티클 변환 (`Dae-Jeong/app/fe/content/blog/`)
메모가 하나의 완결된 인사이트로 모이면 아래 규격으로 초안(`published: false`)을 작성한다:
- **파일명**: `fde-YYYY-MM-DD-<topic>.md` (`<topic>`은 영문 소문자 kebab-case)
- **Frontmatter**:
  ```yaml
  ---
  title: "한글 제목 (현장의 문제와 핵심 판단이 드러나는 제목)"
  description: "목록에 표시할 한 줄 요약"
  date: "YYYY-MM-DD"
  tags: [FDE, Work Log]
  published: false
  ---
  ```
- **본문 구성**:
  1. **첫 문단 결론**: 오늘 현장에서 마주한 문제와 핵심 결론을 첫 문단에 바로 제시
  2. **현업의 병목과 규약 (Why it happens)**: 왜 기존 방식이 그렇게 굳어졌는지 구조적 맥락 설명
  3. **해결 구조와 엔지니어링 판단 (How to solve)**: 아키텍처·데이터 흐름(ASCII 다이어그램 또는 표) 및 타협점
  4. **오늘 남기는 원칙 (Takeaway)**: 다음 프로젝트에서도 재사용할 한 줄 원칙
