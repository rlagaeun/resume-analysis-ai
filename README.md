# 이력서 키워드 점수 분석 API 명세서

## 1. 개요

사용자의 이력서, 자기소개서, 포트폴리오에서 추출한 키워드와 선택한 채용공고의 기준 키워드를 비교하여 키워드 기반 점수를 산출한다.

분석 결과는 다음과 같이 제공된다.

* 지원자 문서 키워드 추출
* 채용공고 기준 키워드 생성
* 스킬, 경험, 포트폴리오, 직무적합성 점수 산출
* 종합 점수 산출

---

## 2. 키워드 점수 분석

### `POST /resume/analyze/score`

이력서·자기소개서·포트폴리오와 선택 채용공고 정보를 기반으로 키워드 매칭 점수를 계산한다.

> 현재는 FastAPI 엔드포인트가 구현되지 않은 상태이며, Step01·Step02 스크립트 기준으로 동작한다.
> Request Body는 Spring ↔ FastAPI 연동 방식 확정 후 작성 예정이다.

### 사용 데이터

| 데이터                           | 설명                          |
| ----------------------------- | --------------------------- |
| 통합 이력서 데이터                    | 이력서·자기소개서·포트폴리오를 통합한 지원자 정보 |
| 선택 채용공고 데이터                   | 점수 산출 기준이 되는 회사 공고 정보       |
| extracted_score_keywords.json | 지원자 문서에서 추출한 키워드            |
| resume_score_result.json      | 키워드 매칭 점수 계산 결과             |

### Response

```json
{
  "overall_score": 73,
  "chart_scores": [
    {
      "category": "스킬",
      "score": 81
    },
    {
      "category": "경험",
      "score": 70
    },
    {
      "category": "포트폴리오",
      "score": 70
    },
    {
      "category": "직무적합성",
      "score": 70
    }
  ]
}
```

---

## 3. Step01 키워드 추출

### Step01 - step01_extract_score_keywords.py

지원자 문서에서 점수 계산에 사용할 키워드를 추출한다.

### 사용 데이터

| 데이터                   | 설명                            |
| --------------------- | ----------------------------- |
| test.extracted_y.json | 이력서·자기소개서·포트폴리오 기반 지원자 문서 데이터 |

### 출력 파일

```json
{
  "model": "claude-sonnet-4-6",
  "source_file": "test.extracted_y.json",
  "keywords": {
    "skill": [],
    "experience": [],
    "portfolio": [],
    "job_keyword": []
  }
}
```

### keywords 필드

| 필드          | 설명                        |
| ----------- | ------------------------- |
| skill       | 기술스택, 프레임워크, 언어, DB, 개발도구 |
| experience  | 프로젝트, 인턴, 활동, 교육, 팀 경험    |
| portfolio   | 구현 기능, 성과, 배포, 산출물        |
| job_keyword | 직무 관련 핵심 키워드              |

### 생성 파일

| 파일명                           | 설명               |
| ----------------------------- | ---------------- |
| extracted_score_keywords.json | 지원자 문서 기반 추출 키워드 |

---

## 4. Step02 점수 계산

### Step02 - step02_calculate_resume_score.py

지원자 키워드와 채용공고 기준 키워드를 비교하여 영역별 점수와 종합 점수를 계산한다.

### 사용 데이터

| 데이터                                     | 설명                       |
| --------------------------------------- | ------------------------ |
| extracted_score_keywords.json           | Step01에서 추출한 지원자 키워드     |
| dummy_jobs_backend_20260419_154750.json | 기준 키워드 추출에 사용하는 채용공고 데이터 |
| ANTHROPIC_API_KEY                       | Claude API 호출을 위한 환경변수   |

---

### 기준 키워드 생성 방식

현재 기준 키워드는 `REFERENCE_MODE = "job"` 설정에 따라 채용공고 데이터에서 생성된다.

| 영역          | 기준 키워드 생성 기준                                                             |
| ----------- | ------------------------------------------------------------------------ |
| skill       | 채용공고의 skills                                                             |
| experience  | 채용공고의 main_tasks, requirements, talent                                   |
| portfolio   | 채용공고의 skills, main_tasks, requirements                                   |
| job_keyword | 채용공고의 category, position, job_category, skills, main_tasks, requirements |

---

### 매칭 방식

| relation | 점수  | 설명                         |
| -------- | --- | -------------------------- |
| exact    | 100 | 지원자 키워드와 기준 키워드가 직접 일치     |
| related  | 70  | 기준 키워드의 실제 업무 수행과 직접 관련 있음 |

exact 매칭은 코드에서 직접 처리하고, related 매칭은 Claude API를 통해 보수적으로 판단한다.

---

## 5. 응답 필드

### overall_score

| 필드            | 타입     | 설명                 |
| ------------- | ------ | ------------------ |
| overall_score | number | 4개 영역 점수의 평균 종합 점수 |

---

### chart_scores

| 필드       | 타입     | 설명     |
| -------- | ------ | ------ |
| category | string | 평가 영역  |
| score    | number | 영역별 점수 |

### category 값

| 값     |
| ----- |
| 스킬    |
| 경험    |
| 포트폴리오 |
| 직무적합성 |

---

## 6. debug 출력

현재 코드에서는 `INCLUDE_DEBUG = True` 설정 시 디버그 정보가 함께 출력된다.

### debug 예시

```json
{
  "debug": {
    "reference_mode": "job",
    "target_field": null,
    "skill": {
      "score": 81,
      "candidate_count": 35,
      "reference_count": 14,
      "matched_count": 8,
      "matched_keywords": [],
      "matched_reference_keywords": [],
      "matches": []
    },
    "experience": {},
    "portfolio": {},
    "job_keyword": {}
  }
}
```

### debug 필드

| 필드             | 타입             | 설명                         |
| -------------- | -------------- | -------------------------- |
| reference_mode | string         | 기준 키워드 생성 방식               |
| target_field   | string 또는 null | reference 모드 사용 시 대상 직무 분야 |
| skill          | object         | 스킬 영역 상세 결과                |
| experience     | object         | 경험 영역 상세 결과                |
| portfolio      | object         | 포트폴리오 영역 상세 결과             |
| job_keyword    | object         | 직무 키워드 영역 상세 결과            |

---

### 영역별 debug 객체

| 필드                         | 타입     | 설명                     |
| -------------------------- | ------ | ---------------------- |
| score                      | number | 해당 영역 점수               |
| candidate_count            | number | 지원자 키워드 개수             |
| reference_count            | number | 기준 키워드 개수              |
| matched_count              | number | 매칭된 키워드 개수             |
| matched_keywords           | array  | 매칭된 지원자 키워드            |
| matched_reference_keywords | array  | 매칭된 기준 키워드             |
| matches                    | array  | exact/related 매칭 상세 결과 |

---

### matches 객체

| 필드                        | 타입     | 설명         |
| ------------------------- | ------ | ---------- |
| keyword                   | string | 지원자 키워드    |
| relation                  | string | 매칭 관계      |
| matched_reference_keyword | string | 매칭된 기준 키워드 |
| reason                    | string | 매칭 판단 이유   |

### relation 값

| 값       |
| ------- |
| exact   |
| related |

---

## 7. 생성 파일

| 파일명                           | 설명               |
| ----------------------------- | ---------------- |
| extracted_score_keywords.json | 지원자 문서 기반 추출 키워드 |
| resume_score_result.json      | 키워드 매칭 점수 계산 결과  |

---

## 8. 현재 미적용 사항

| 항목                           | 현재 상태                          |
| ---------------------------- | ------------------------------ |
| FastAPI 엔드포인트                | 아직 구현되지 않음                     |
| POST /resume/analyze/score   | 예정 엔드포인트                       |
| Request Body                 | Spring ↔ FastAPI 연동 방식 확정 후 작성 |
| user_id / resume_id / job_id | 현재 코드에서 직접 사용하지 않음             |
| DB 저장 구조                     | 미적용                            |
| 분석 이력 저장                     | 미적용                            |
| 최신 분석 조회                     | 미적용                            |
| total_score 필드명              | 현재 overall_score 사용            |
| radar 객체 출력                  | 현재 chart_scores 배열 사용          |
| average_score                | 미적용                            |
| Spring ↔ FastAPI 연동          | 미적용                            |

---

## 9. 현재 구조 요약

현재 프로젝트는 FastAPI 서버가 아니라 키워드 기반 점수 산출 스크립트로 구성되어 있다.

### 구현 완료

* 지원자 문서 키워드 추출
* 채용공고 기준 키워드 생성
* exact / related 매칭
* 스킬 점수 계산
* 경험 점수 계산
* 포트폴리오 점수 계산
* 직무적합성 점수 계산
* 종합 점수 계산
* 디버그 정보 출력

### 미구현

* API 서버
* 사용자별 결과 관리
* 분석 이력 관리
* DB 저장
* 프론트 연동용 API 응답 구조
