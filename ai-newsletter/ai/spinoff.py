"""
Spinoff Idea Generator
발행된 뉴스레터에서 파생 주제를 자동으로 추출합니다.

동작 원리:
- 발행된 글의 제목/요약/본문을 GPT-5.4에게 전달
- "이 글을 읽은 AI 엔지니어가 자연스럽게 궁금해할 후속 주제"를 추출
- 카테고리 태그와 함께 백로그용 포맷으로 반환
"""
import json
import os
import sys
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OPENAI_API_KEY, OPENAI_MODEL_LIGHT

# 허용 카테고리 (다양성 가드레일과 공유)
CATEGORIES = [
    "infra",        # 인프라, 서빙, 배포
    "framework",    # 프레임워크, 라이브러리
    "agent",        # 에이전트, 워크플로우
    "rag",          # RAG, 검색, 임베딩
    "training",     # 파인튜닝, 학습, 최적화
    "evaluation",   # 평가, 벤치마크, 모니터링
    "multimodal",   # 멀티모달, Vision-Language
    "tooling",      # 개발 도구, IDE, CLI
    "architecture", # 모델 아키텍처, 설계 패턴
    "security",     # 보안, 프라이버시, 안전성
]


def generate_spinoffs(content: dict, topic: dict, count: int = 3) -> list[dict]:
    """
    발행된 뉴스레터에서 파생 주제를 자동 생성합니다.

    Args:
        content: generate_newsletter()의 결과 (title, summary, article, tags)
        topic: 원본 선택 주제 (source, url 등)
        count: 생성할 스핀오프 개수

    Returns:
        List of dicts with title, description, category, tags, source_article, rationale
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    article_title = content.get("title", topic.get("title", ""))
    article_summary = content.get("summary", "")
    article_tags = ", ".join(content.get("tags", []))
    article_excerpt = content.get("article", "")[:800]

    categories_str = ", ".join(CATEGORIES)

    prompt = f"""당신은 AI 개발자 뉴스레터의 시니어 에디터입니다.
방금 아래 뉴스레터 글이 발행되었습니다. 이 글을 읽은 AI 엔지니어라면 자연스럽게 "그 다음엔 뭘 알아야 하지?" 또는 "이거랑 비교해서 저건 어때?" 라고 궁금해할 후속 주제 {count}개를 추출해 주세요.

---
## 발행된 글 정보
**제목**: {article_title}
**태그**: {article_tags}
**요약**: {article_summary}
**본문 일부**:
{article_excerpt}
---

## 스핀오프 생성 원칙
1. **기술적 연속성**: 이 글에서 다루지 않았지만 독자가 자연스럽게 궁금해할 심화 주제
2. **대조/비교**: "이 기술 vs 유사 기술" 비교 분석
3. **실무 확장**: 이 기술을 실제 프로덕션에서 더 잘 쓰기 위한 주변 기술
4. **주제 다양성**: 서로 다른 카테고리에서 선택할 것
5. **Actionable**: 독자가 바로 시도해볼 수 있는 구체적 주제

## 허용 카테고리
{categories_str}

아래 JSON 형식으로만 응답하세요:
{{
  "spinoffs": [
    {{
      "title": "<스핀오프 주제 제목 (한국어, 구체적으로)>",
      "description": "<이 주제가 왜 AI 엔지니어에게 중요한지, 어떤 Pain Point를 다루는지 1-2문장>",
      "category": "<위 카테고리 중 하나>",
      "tags": ["<태그1>", "<태그2>", "<태그3>"],
      "rationale": "<이 글의 어떤 부분에서 이 주제가 파생됐는지 1문장>"
    }}
  ]
}}"""

    print(f"[Spinoff] 파생 주제 {count}개 생성 중...")

    response = client.chat.completions.create(
        model=OPENAI_MODEL_LIGHT,
        reasoning_effort="low",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        spinoffs = result.get("spinoffs", [])
    except json.JSONDecodeError as e:
        print(f"[Spinoff] JSON 파싱 실패: {e}")
        return []

    # source_article 필드 추가
    for s in spinoffs:
        s["source_article"] = article_title

    print(f"[Spinoff] {len(spinoffs)}개 파생 주제 생성 완료:")
    for s in spinoffs:
        print(f"  → [{s.get('category','?')}] {s['title']}")

    return spinoffs[:count]
