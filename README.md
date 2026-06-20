# 이력서 키워드 점수 분석 API 명세서

## 1. 개요

사용자의 이력서, 자기소개서, 포트폴리오에서 추출한 키워드와 선택한 채용공고의 기준 키워드를 비교하여 키워드 기반 점수를 산출한다.

분석 결과는 다음과 같이 제공된다.

* 지원자 문서 키워드 추출
* 채용공고 기준 키워드 생성
* 스킬, 경험, 포트폴리오, 직무적합성 점수 산출
* 종합 점수 산출

---

## 2. 키워드 추출

### Step01 - step01_extract_score_keywords.py

지원자 문서에서 점수 계산에 사용할 키워드를 추출한다.

### 사용 데이터

| 데이터       | 설명        |
| --------- | --------- |
| 이력서 데이터   | 지원자 이력서   |
| 자기소개서 데이터 | 지원자 자기소개서 |
| 포트폴리오 데이터 | 지원자 포트폴리오 |

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

### 응답 필드

#### keywords

| 필드          | 설명                        |
| ----------- | ------------------------- |
| skill       | 기술스택, 프레임워크, 언어, DB, 개발도구 |
| experience  | 프로젝트, 인턴, 활동, 교육, 팀 경험    |
| portfolio   | 구현 기능, 성과, 배포, 산출물        |
| job_keyword | 직무 관련 핵심 키워드              |

---

## 3. 점수 계산

### Step02 - step02_calculate_resume_score.py

지원자 키워드와 채용공고 기준 키워드를 비교하여 영역별 점수와 종합 점수를 계산한다.

### 사용 데이터

| 데이터                           | 설명               |
| ----------------------------- | ---------------- |
| extracted_score_keywords.json | Step01 키워드 추출 결과 |
| 채용공고 데이터                      | 기준 키워드 생성용 채용공고  |
| ANTHROPIC_API_KEY             | Claude API 사용    |

---

### 기준 키워드 생성 방식

현재 설정은 다음과 같다.

```python
REFERENCE_MODE = "job"
```

채용공고 데이터로부터 기준 키워드를 생성한다.

| 영역          | 기준 데이터                                   |
| ----------- | ---------------------------------------- |
| skill       | skills                                   |
| experience  | main_tasks, requirements, talent         |
| portfolio   | skills, main_tasks, requirements         |
| job_keyword | category, position, skills, requirements |

---

### 매칭 방식

| 관계      | 점수  |
| ------- | --- |
| exact   | 100 |
| related | 70  |

#### exact

지원자 키워드와 기준 키워드가 직접 일치

#### related

실제 업무 수행에 직접 활용 가능한 관련 경험 또는 기술

---

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
  ],
  "debug": {
    "reference_mode": "job",
    "target_field": null,
    "skill": {},
    "experience": {},
    "portfolio": {},
    "job_keyword": {}
  }
}
```

---

## 4. 응답 필드

### overall_score

| 필드            | 타입     | 설명             |
| ------------- | ------ | -------------- |
| overall_score | number | 4개 영역 평균 종합 점수 |

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

### debug

디버그 확인용 상세 분석 결과

| 필드             | 설명                      |
| -------------- | ----------------------- |
| reference_mode | 기준 키워드 생성 방식            |
| target_field   | reference 모드 사용 시 대상 분야 |
| skill          | 스킬 분석 결과                |
| experience     | 경험 분석 결과                |
| portfolio      | 포트폴리오 분석 결과             |
| job_keyword    | 직무적합성 분석 결과             |

---

### 영역별 debug 객체

| 필드                         | 타입     | 설명          |
| -------------------------- | ------ | ----------- |
| score                      | number | 영역 점수       |
| candidate_count            | number | 지원자 키워드 개수  |
| reference_count            | number | 기준 키워드 개수   |
| matched_count              | number | 매칭 개수       |
| matched_keywords           | array  | 매칭된 지원자 키워드 |
| matched_reference_keywords | array  | 매칭된 기준 키워드  |
| matches                    | array  | 상세 매칭 결과    |

---

### matches

| 필드                        | 타입     | 설명              |
| ------------------------- | ------ | --------------- |
| keyword                   | string | 지원자 키워드         |
| relation                  | string | exact / related |
| matched_reference_keyword | string | 매칭된 기준 키워드      |
| reason                    | string | 매칭 사유           |

---

## 5. 생성 파일

| 파일명                           | 설명        |
| ----------------------------- | --------- |
| extracted_score_keywords.json | 키워드 추출 결과 |
| resume_score_result.json      | 점수 계산 결과  |

---

## 6. 현재 미적용 사항

| 항목                                         | 현재 상태                 |
| ------------------------------------------ | --------------------- |
| FastAPI 엔드포인트                              | 아직 구현되지 않음            |
| POST /resume/{user_id}/analyze             | 미적용                   |
| GET /resume/{user_id}/detail/{document_id} | 미적용                   |
| user_id 관리                                 | 미적용                   |
| document_id 관리                             | 미적용                   |
| 분석 이력 저장                                   | 미적용                   |
| 최신 분석 조회                                   | 미적용                   |
| total_score 필드명                            | 현재 overall_score 사용   |
| radar 객체 출력                                | 현재 chart_scores 배열 사용 |
| average_score                              | 미적용                   |
| DB 저장 구조                                   | 미적용                   |
| Spring ↔ FastAPI 연동                        | 미적용                   |
| Request Body 명세                            | 미확정                   |

---

## 7. 현재 구조 요약

현재 프로젝트는 키워드 기반 점수 산출 모듈로 구성되어 있다.

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
