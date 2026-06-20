from pathlib import Path
import json
import os
from anthropic import Anthropic


BASE_DIR = Path(__file__).resolve().parent

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-6"

INPUT_FILE = BASE_DIR / "test.extracted_y.json"
OUTPUT_FILE = BASE_DIR / "output" / "extracted_score_keywords.json"

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def normalize_keywords(result):
    normalized = {}

    for area in ["skill", "experience", "portfolio", "job_keyword"]:
        values = result.get(area, [])
        clean_values = []

        if isinstance(values, list):
            for item in values:
                if not isinstance(item, str):
                    continue

                item = item.strip()

                if item and item not in clean_values:
                    clean_values.append(item)

        normalized[area] = clean_values

    return normalized


def call_claude(prompt):
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=3000,
            temperature=0,
            system=(
                "너는 이력서 점수 평가용 키워드 추출기다. "
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

        return {
            "skill": [],
            "experience": [],
            "portfolio": [],
            "job_keyword": []
        }


def extract_score_keywords(user_document):
    prompt = f"""
아래는 이력서/자소서/포트폴리오에서 추출된 사용자 문서 JSON이다.

이 문서를 의미 기반으로 읽고, 이력서 점수 산출에 사용할 키워드를 4개 영역으로 분리해라.

[사용자 문서 JSON]
{json.dumps(user_document, ensure_ascii=False)}

[추출 영역]

1. skill
- 기술스택, 언어, 프레임워크, 데이터베이스, 인프라, 도구, 라이브러리, 분석 기법, 개발 도구를 추출한다.
- skill은 기술명, 도구명, 프레임워크명, 방법론명 중심으로 분류한다.
- 수행 행위나 구현 결과는 skill이 아니라 experience 또는 portfolio로 분류한다.
- 예: Python, SQL, Java, Spring Boot, Docker, PostgreSQL, TensorFlow

2. experience
- 경험 유형, 역할, 수행 방식, 협업, 문제 해결, 데이터 처리 경험, 프로젝트 수행 경험을 추출한다.
- 예: 프로젝트 기획, 데이터 전처리, API 개발, 협업, 트러블슈팅, 성능 개선

3. portfolio
- 프로젝트 산출물, 구현 기능, 시스템 구축 내용, 기술 적용 결과, 트러블슈팅 결과를 추출한다.
- 예: ETL 파이프라인 구축, 추천 시스템 개발, 실시간 데이터 처리 시스템, 모델 최적화, 데이터 분석 대시보드 구축

4. job_keyword
- 지원자의 직무 방향성을 보여주는 핵심 키워드를 추출한다.
- 예: 데이터 엔지니어링, 백엔드 개발, 데이터 분석, 머신러닝, 클라우드 인프라

[중요 규칙]
- 문장 전체를 그대로 넣지 마라.
- 짧은 키워드 또는 짧은 구 형태로 추출해라.
- 문장 안에 숨어 있는 핵심 기술, 구현 내용, 문제 해결 방식을 놓치지 마라.
- 없는 내용을 새로 만들지 마라.
- 중복 키워드는 제거해라.
- 각 영역 최대 개수 제한을 두지 마라.
- 점수 평가에 의미 있는 키워드는 모두 추출해라.
- 너무 일반적인 단어만 단독으로 출력하지 마라.
  나쁜 예: 데이터, 개발, 프로젝트, 시스템, 분석, 처리, 구현, 추천
- 구체적인 표현은 허용한다.
  좋은 예: 데이터 엔지니어링, 데이터 파이프라인, 실시간 데이터 처리, API 개발, 추천 시스템 개발
- 인원 수 정보는 키워드로 추출하지 마라.
  나쁜 예: 1인 프로젝트 수행, 2인 팀 프로젝트 수행
- 단순 수상명은 portfolio 키워드로 추출하지 마라.
  나쁜 예: 공모전 수상, 경진대회 입선, 논문상 수상
- 단, 수상 자체가 아니라 구현 성과와 연결된 표현은 portfolio에 포함할 수 있다.
  좋은 예: 모델 정확도 개선, 사용자 지표 개선, 처리 속도 개선, 오류율 감소
- JSON만 출력해라.

[출력 형식]
{{
  "skill": [],
  "experience": [],
  "portfolio": [],
  "job_keyword": []
}}
"""

    result = call_claude(prompt)
    return normalize_keywords(result)


def main():
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    user_document = load_json(INPUT_FILE)

    extracted_keywords = extract_score_keywords(user_document)

    output = {
        "model": MODEL_NAME,
        "source_file": INPUT_FILE.name,
        "keywords": extracted_keywords
    }

    save_json(output, OUTPUT_FILE)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n점수용 키워드 추출 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()