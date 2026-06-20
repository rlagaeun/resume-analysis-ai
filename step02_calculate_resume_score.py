from pathlib import Path
import json
import os
from anthropic import Anthropic


BASE_DIR = Path(__file__).resolve().parent

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

REFERENCE_MODE = "job"

JOB_FILE = BASE_DIR / "job" / "dummy_jobs_backend_20260419_154750.json"
REFERENCE_FILE = BASE_DIR / "reference" / "field_keywords.json"
TARGET_FIELD = "backend"

EXTRACTED_KEYWORDS_FILE = BASE_DIR / "output" / "extracted_score_keywords.json"
OUTPUT_FILE = BASE_DIR / "output" / "resume_score_result.json"

INCLUDE_DEBUG = True

RELATION_SCORE_MAP = {
    "exact": 100,
    "related": 70
}


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def unique_clean_list(items):
    result = []

    for item in items:
        if not isinstance(item, str):
            continue

        item = item.strip()

        if item and item not in result:
            result.append(item)

    return result


def parse_json_response(content):
    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "", 1).strip()

    if content.startswith("```"):
        content = content.replace("```", "", 1).strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1 and start < end:
        content = content[start:end + 1]

    return json.loads(content)


def call_claude(prompt):
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            temperature=0,
            system=(
                "너는 이력서 키워드와 기준 키워드의 관련성을 보수적으로 판단하는 평가 보조 AI다. "
                "반드시 JSON만 출력하고, 설명문이나 마크다운은 출력하지 마라."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.content[0].text.strip()
        return parse_json_response(content)

    except Exception as e:
        print(f"Claude 오류 또는 JSON 파싱 실패: {e}")
        return {"matches": []}


def build_skill_reference_from_job(job):
    keywords = []

    for item in job.get("jobs", []):
        keywords.extend(item.get("skills", []))

    return unique_clean_list(keywords)


def build_experience_reference_from_job(job):
    keywords = []

    for item in job.get("jobs", []):
        detail = item.get("detail", {})

        keywords.extend(detail.get("main_tasks", []))
        keywords.extend(detail.get("requirements", []))
        keywords.extend(detail.get("talent", []))

    return unique_clean_list(keywords)


def build_portfolio_reference_from_job(job):
    keywords = []

    for item in job.get("jobs", []):
        detail = item.get("detail", {})

        keywords.extend(item.get("skills", []))
        keywords.extend(detail.get("main_tasks", []))
        keywords.extend(detail.get("requirements", []))

    return unique_clean_list(keywords)


def build_job_keyword_reference_from_job(job):
    keywords = []

    keywords.append(job.get("category", ""))

    for item in job.get("jobs", []):
        position = item.get("position", {})
        job_category = position.get("job_category", {})
        detail = item.get("detail", {})

        keywords.append(position.get("title", ""))
        keywords.append(job_category.get("large", ""))
        keywords.append(job_category.get("mid", ""))
        keywords.append(job_category.get("small", ""))

        keywords.extend(item.get("skills", []))
        keywords.extend(detail.get("main_tasks", []))
        keywords.extend(detail.get("requirements", []))

    return unique_clean_list(keywords)


def load_reference_keywords_from_job():
    job = load_json(JOB_FILE)

    return {
        "skill": build_skill_reference_from_job(job),
        "experience": build_experience_reference_from_job(job),
        "portfolio": build_portfolio_reference_from_job(job),
        "job_keyword": build_job_keyword_reference_from_job(job)
    }


def load_reference_keywords_from_file():
    reference_data = load_json(REFERENCE_FILE)

    if TARGET_FIELD not in reference_data:
        raise ValueError(f"{TARGET_FIELD} 분야 기준 키워드가 없습니다.")

    field_data = reference_data[TARGET_FIELD]

    return {
        "skill": unique_clean_list(field_data.get("skill", [])),
        "experience": unique_clean_list(field_data.get("experience", [])),
        "portfolio": unique_clean_list(field_data.get("portfolio", [])),
        "job_keyword": unique_clean_list(field_data.get("job_keyword", []))
    }


def load_reference_keywords():
    if REFERENCE_MODE == "job":
        return load_reference_keywords_from_job()

    if REFERENCE_MODE == "reference":
        return load_reference_keywords_from_file()

    raise ValueError("REFERENCE_MODE는 'job' 또는 'reference'만 사용할 수 있습니다.")


def load_extracted_keywords():
    data = load_json(EXTRACTED_KEYWORDS_FILE)

    if "keywords" in data:
        return data["keywords"]

    return data


def exact_match_by_code(candidate_keywords, reference_keywords):
    matches = []

    reference_lower_map = {
        ref.lower(): ref
        for ref in reference_keywords
    }

    for keyword in candidate_keywords:
        key = keyword.lower()

        if key in reference_lower_map:
            matches.append({
                "keyword": keyword,
                "relation": "exact",
                "matched_reference_keyword": reference_lower_map[key],
                "reason": "지원자 키워드와 기준 키워드가 직접 일치합니다."
            })

    return matches


def get_unmatched_candidates(candidate_keywords, exact_matches):
    exact_keywords = {
        item["keyword"]
        for item in exact_matches
    }

    return [
        keyword for keyword in candidate_keywords
        if keyword not in exact_keywords
    ]


def analyze_related_matches(area_name, reference_keywords, candidate_keywords):
    if not reference_keywords or not candidate_keywords:
        return []

    prompt = f"""
아래 지원자 키워드 중 기준 키워드와 related 관계인 것만 찾아라.

[기준 키워드]
{json.dumps(reference_keywords, ensure_ascii=False)}

[지원자 키워드]
{json.dumps(candidate_keywords, ensure_ascii=False)}

[분석 영역]
{area_name}

[판단 기준]

exact:
- 동일 기술, 동일 도구, 동일 프레임워크, 동일 직무 키워드인 경우
- exact는 코드에서 이미 처리했으므로 출력하지 마라.

related:
- 기준 키워드의 실제 업무 수행에 직접 활용 가능한 경우만 인정한다.
- 같은 목적을 수행하는 기술, 방법론, 경험인 경우만 인정한다.
- 기준 키워드를 대체하거나 보완할 수 있는 구체적 실무 경험인 경우만 인정한다.
- 단순히 같은 IT/개발 분야라는 이유만으로 related 처리하지 마라.
- 단순히 간접적으로 도움이 된다는 이유만으로 related 처리하지 마라.
- 도구 사용 경험과 아키텍처 설계 역량을 동일하게 보지 마라.
- 협업 도구, 운영체제, 일반 개발 경험은 특정 기술 키워드와 related 처리하지 마라.
- 기술 이름이 달라도 실제 수행 목적이 명확히 같을 때만 related 처리해라.
- 데이터베이스는 데이터 모델이 다르면 같은 DB라는 이유만으로 related 처리하지 마라.
- 외부 API 호출 경험은 API 서버 설계·개발 경험과 동일하게 보지 마라.
- 검색, 추천, 분석 로직 구현은 서비스 분리, API 설계, 배포, 통신 구조가 명시되지 않으면 마이크로서비스 구현으로 보지 마라.

unrelated:
- 기준 키워드와 직접적인 업무 수행 연결성이 낮은 경우
- 일반적인 개발 경험일 뿐 특정 기준 키워드와 연결하기 어려운 경우
- 설명 가능한 직접 근거가 부족한 경우
- unrelated는 출력하지 마라.

[related 인정 예시]
- 동일 목적의 웹/API 프레임워크 경험 → 다른 웹/API 프레임워크 기준
- ETL 파이프라인 경험 → 데이터 처리 파이프라인 구축 기준
- 실시간 스트리밍 처리 경험 → 메시지 기반 실시간 처리 기술 기준
- SQL 경험 → 관계형 데이터베이스 활용 기준
- RDBMS 설계 경험 → 관계형 데이터베이스 설계·이해 기준

[related 금지 예시]
- 버전관리 도구 사용 → 마이크로서비스 아키텍처
- 운영체제 사용 경험 → 컨테이너 기술 경험
- 대규모 배치 처리 기술 → 메시지 큐 기술
- 그래프 DB 경험 → 관계형 DB 경험
- 외부 API 사용 → API 서버 설계·개발
- 추천/검색 로직 구현 → 마이크로서비스 구현

[중요 규칙]
- related인 항목만 출력해라.
- 없는 내용을 추측하지 마라.
- keyword는 반드시 지원자 키워드 중 하나를 그대로 사용해라.
- matched_reference_keyword는 반드시 기준 키워드 중 하나를 그대로 사용해라.
- reason은 왜 related인지 1문장으로 작성해라.
- reason은 구체적인 업무 연결성을 설명해야 한다.
- 판단이 애매하면 출력하지 마라.
- JSON만 출력해라.

[출력 형식]
{{
  "matches": [
    {{
      "keyword": "",
      "relation": "related",
      "matched_reference_keyword": "",
      "reason": ""
    }}
  ]
}}
"""

    result = call_claude(prompt)
    matches = result.get("matches", [])

    if not isinstance(matches, list):
        return []

    return matches


def normalize_matches(raw_matches, candidate_keywords, reference_keywords):
    normalized = []

    candidate_set = set(candidate_keywords)
    reference_set = set(reference_keywords)

    for item in raw_matches:
        if not isinstance(item, dict):
            continue

        keyword = item.get("keyword", "")
        relation = item.get("relation", "")
        matched_reference_keyword = item.get("matched_reference_keyword", "")
        reason = item.get("reason", "")

        if not isinstance(keyword, str):
            continue

        keyword = keyword.strip()

        if keyword not in candidate_set:
            continue

        if relation not in ["exact", "related"]:
            continue

        if not isinstance(matched_reference_keyword, str):
            continue

        matched_reference_keyword = matched_reference_keyword.strip()

        if matched_reference_keyword not in reference_set:
            continue

        if not isinstance(reason, str):
            reason = ""

        reason = reason.strip()

        if any(x["keyword"] == keyword for x in normalized):
            continue

        normalized.append({
            "keyword": keyword,
            "relation": relation,
            "matched_reference_keyword": matched_reference_keyword,
            "reason": reason
        })

    return normalized


def calculate_relation_score(matches):
    if not matches:
        return 0

    scores = [
        RELATION_SCORE_MAP.get(item["relation"], 0)
        for item in matches
    ]

    return round(sum(scores) / len(scores))


def get_matched_reference_keywords(matches):
    return unique_clean_list([
        item["matched_reference_keyword"]
        for item in matches
        if item.get("matched_reference_keyword")
    ])


def analyze_area(area_name, candidate_keywords, reference_keywords):
    candidate_keywords = unique_clean_list(candidate_keywords)
    reference_keywords = unique_clean_list(reference_keywords)

    exact_matches = exact_match_by_code(
        candidate_keywords,
        reference_keywords
    )

    unmatched_candidates = get_unmatched_candidates(
        candidate_keywords,
        exact_matches
    )

    related_matches = analyze_related_matches(
        area_name,
        reference_keywords,
        unmatched_candidates
    )

    related_matches = normalize_matches(
        related_matches,
        unmatched_candidates,
        reference_keywords
    )

    matches = exact_matches + related_matches

    score = calculate_relation_score(matches)

    return {
        "score": score,
        "candidate_count": len(candidate_keywords),
        "reference_count": len(reference_keywords),
        "matched_count": len(matches),
        "matched_keywords": unique_clean_list([
            item["keyword"]
            for item in matches
        ]),
        "matched_reference_keywords": get_matched_reference_keywords(matches),
        "matches": matches
    }


def main():
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    extracted_keywords = load_extracted_keywords()
    reference_keywords = load_reference_keywords()

    skill_result = analyze_area(
        "skill",
        extracted_keywords.get("skill", []),
        reference_keywords["skill"]
    )

    experience_result = analyze_area(
        "experience",
        extracted_keywords.get("experience", []),
        reference_keywords["experience"]
    )

    portfolio_result = analyze_area(
        "portfolio",
        extracted_keywords.get("portfolio", []),
        reference_keywords["portfolio"]
    )

    job_keyword_result = analyze_area(
        "job_keyword",
        extracted_keywords.get("job_keyword", []),
        reference_keywords["job_keyword"]
    )

    overall_score = round(
        (
            skill_result["score"] +
            experience_result["score"] +
            portfolio_result["score"] +
            job_keyword_result["score"]
        ) / 4
    )

    result = {
        "overall_score": overall_score,
        "chart_scores": [
            {"category": "스킬", "score": skill_result["score"]},
            {"category": "경험", "score": experience_result["score"]},
            {"category": "포트폴리오", "score": portfolio_result["score"]},
            {"category": "직무적합성", "score": job_keyword_result["score"]}
        ]
    }

    if INCLUDE_DEBUG:
        result["debug"] = {
            "reference_mode": REFERENCE_MODE,
            "target_field": TARGET_FIELD if REFERENCE_MODE == "reference" else None,
            "skill": skill_result,
            "experience": experience_result,
            "portfolio": portfolio_result,
            "job_keyword": job_keyword_result
        }

    save_json(result, OUTPUT_FILE)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n이력서 점수 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()