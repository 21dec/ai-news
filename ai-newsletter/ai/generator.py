"""
Newsletter Content Generator
CO-STAR 프레임워크를 기반으로 뉴스레터 콘텐츠를 생성합니다.
- 요약글 (Summary): 400자 내외
- 딥다이브 글 (Detailed Article): 1000~3000자
- 다이어그램 스펙 (JSON): 다이어그램 생성 모듈에 전달
"""
import json
import anthropic
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    SUMMARY_LENGTH, ARTICLE_MIN_LENGTH, ARTICLE_MAX_LENGTH
)


def generate_newsletter(topic: dict, retry_hint: list[str] | None = None) -> dict:
    """
    선별된 주제를 바탕으로 뉴스레터 콘텐츠를 생성합니다.

    Args:
        topic:       select_best_topic()의 결과 dict
        retry_hint:  이전 시도의 검증 실패 사유 목록 (재시도 시 프롬프트에 포함)

    Returns:
        {
            "title": str,
            "summary": str,          # 400자 내외 요약
            "article": str,          # 1000~3000자 딥다이브
            "diagram_specs": list,   # 다이어그램 생성 스펙 (1~3개)
            "tags": list[str],       # 관련 태그
        }
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    title = topic.get("title", "")
    url = topic.get("url", "")
    description = topic.get("description", "")
    pain_point = topic.get("pain_point", "")
    hook = topic.get("hook", "")
    source = topic.get("source", "")

    print(f"[Generator] 콘텐츠 생성 중: {title[:60]}...")

    # 재시도 시 이전 실패 사유를 프롬프트 앞에 삽입
    retry_block = ""
    if retry_hint:
        reasons = "\n".join(f"  - {r}" for r in retry_hint)
        retry_block = f"""
⚠️ 이전 생성 결과가 품질 검증에 실패했습니다. 아래 문제를 반드시 해결하세요:
{reasons}

특히:
- article은 반드시 완전한 문장으로 끝나야 합니다 (마지막 문자: . ! ? ` 등).
- article은 최소 1000자 이상이어야 합니다.
- 코드블록(```)은 반드시 쌍으로 열고 닫아야 합니다.
- ## 소제목을 2개 이상 사용해 본문을 구조화하세요.

"""

    prompt = f"""{retry_block}당신은 AI/백엔드 엔지니어 대상의 기술 뉴스레터를 쓰는 테크 저널리스트입니다.

## 주제 정보
- 제목: {title}
- 출처: {source}
- URL: {url}
- 설명: {description}
- 해결하는 Pain Point: {pain_point}
- 훅 문장: {hook}

## 작성 지침 (CO-STAR 기반)

**스타일**: 기술/IT 전문 기자 + Developer Advocate. 기술의 핵심 동작 원리를 엔지니어 관점에서 해설.
**톤 (강제)**:
  - 모든 평서문은 반드시 **"~입니다 / ~합니다"** 형태의 정형화된 서술체로 작성합니다.
    (금지 어미: ~하죠, ~해요, ~네요, ~거든요, ~답니다, ~더라고요, ~이다, ~한다, ~군요)
  - 제목·소제목·표·불릿 항목은 명사형 또는 체언 종결 허용.
  - **감정/과장 표현 금지**: 놀랍게도, 혁신적인, 엄청난, 충격적인, 획기적인, 드디어, 마침내,
    압도적인, 굉장한, 어마어마한, 정말, 진짜, 매우, 아주, 무척, 몹시, 느낌표(!), 이모지.
  - 수치·API 시그니처·벤치마크·알고리즘 동작 등 **검증 가능한 팩트** 중심으로 서술.
    주관적 평가가 필요하면 "~로 보입니다", "~로 판단됩니다" 등 절제된 표현 + 근거 병기.
  - 마케팅 카피가 아닌 기술 릴리스 노트·엔지니어링 블로그의 담백한 서술 톤.
**독자**: AI 엔지니어, 백엔드 개발자, IT 아키텍트. 기본 기술 용어(RAG, WASM, in-process 등) 설명 없이 사용 가능.

## Chain-of-Thought 접근
1. 문제 원인 파악 (왜 기존 방식이 불충분한가)
2. 기술적 해결 원리 (어떻게 작동하는가)
3. 실무 도입 시 장단점 및 파급 효과

---

아래 JSON 형식으로만 응답하세요:

{{
  "title": "<뉴스레터 제목 (한국어, 임팩트 있게)>",
  "summary": "<요약글 400자 내외. 핵심 가치와 Why Now를 담아 독자가 더 읽고 싶게 만드는 글>",
  "article": "<딥다이브 글 1000~3000자. 마크다운 형식 사용 가능. ## 소제목으로 구조화. 아키텍처 비교, 코드 스니펫 포함 권장>",
  "diagram_specs": [
    {{
      "type": "comparison",
      "title": "<다이어그램 제목 (영어)>",
      "description": "<다이어그램이 보여줄 내용 설명>",
      "left_label": "<기존 방식 레이블 (영어)>",
      "right_label": "<새로운 방식 레이블 (영어)>",
      "left_items": ["<기존 방식 특징1>", "<기존 방식 특징2>", "<기존 방식 특징3>"],
      "right_items": ["<새 방식 특징1>", "<새 방식 특징2>", "<새 방식 특징3>"]
    }}
  ],
  "tags": ["<태그1>", "<태그2>", "<태그3>", "<태그4>"]
}}

diagram_specs는 1~3개 포함하세요. type은 "comparison" (기존 vs 신규 비교) 또는 "flow" (워크플로우) 중 선택.
flow 타입이면 "steps": ["<단계1>", "<단계2>", ...] 필드를 사용하세요."""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # JSON 파싱
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        content = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"[Generator] JSON 파싱 실패: {e}")
        # 폴백 — 검증 단계에서 길이 부족으로 재시도 트리거됨
        content = {
            "title": title,
            "summary": description[:400],
            "article": description,
            "diagram_specs": [],
            "tags": []
        }

    print(f"[Generator] 생성 완료: {content.get('title', '')[:60]}")
    print(f"  요약: {len(content.get('summary', ''))}자 | 본문: {len(content.get('article', ''))}자")
    return content
