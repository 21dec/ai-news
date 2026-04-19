"""
AI Topic Selector
수집된 뉴스 후보들 중에서 CO-STAR 기준으로 가장 실용적인 주제 1개를 선별합니다.

다양성 가드레일:
- 최근 발행 이력(published_history)을 Claude에게 전달
- 최근 N편에서 자주 쓰인 카테고리는 낮은 우선순위 부여
- 같은 기술/도구의 반복 선택 방지
"""
import json
import anthropic
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


def _build_history_summary(published_history: list[dict]) -> str:
    """발행 이력을 프롬프트용 텍스트로 변환합니다."""
    if not published_history:
        return "없음 (첫 번째 발행)"

    lines = []
    for i, item in enumerate(published_history[:8], 1):  # 최근 8편까지만
        date = item.get("date", "")
        title = item.get("title", "")
        tags = ", ".join(f"#{t}" for t in item.get("tags", []))
        lines.append(f"  {i}. [{date}] {title} {tags}")

    return "\n".join(lines)


def _extract_category_frequency(published_history: list[dict], recent_n: int = 4) -> dict:
    """최근 N편의 카테고리 빈도를 계산합니다."""
    freq = {}
    for item in published_history[:recent_n]:
        for tag in item.get("tags", []):
            freq[tag] = freq.get(tag, 0) + 1
    return freq


def select_best_topic(
    candidates: list[dict],
    published_history: list[dict] = None
) -> dict:
    """
    Claude API를 사용해 후보 목록에서 가장 뉴스레터에 적합한 주제를 선별합니다.

    Args:
        candidates: 크롤러에서 수집한 아이템 리스트
        published_history: 다양성 가드레일용 발행 이력 (load_published_history() 결과)

    Returns:
        선택된 아이템 dict (원본 + selection_reason, pain_point, hook, category 키 추가)
    """
    if not candidates:
        raise ValueError("후보 목록이 비어 있습니다.")

    published_history = published_history or []
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # 후보 목록 포맷
    candidate_text = ""
    for i, item in enumerate(candidates, 1):
        candidate_text += f"""
[{i}] 출처: {item.get('source', 'Unknown')}
제목: {item.get('title', '')}
URL: {item.get('url', '')}
설명: {item.get('description', '')[:200]}
추가 정보: {item.get('extra', '')}
"""

    # 발행 이력 요약
    history_text = _build_history_summary(published_history)

    # 최근 편중 카테고리 경고
    freq = _extract_category_frequency(published_history, recent_n=4)
    overused = [cat for cat, cnt in freq.items() if cnt >= 2]
    overused_warning = ""
    if overused:
        overused_warning = (
            f"\n⚠️ **카테고리 편중 경고**: 최근 4편에서 {', '.join(f'#{c}' for c in overused)} "
            f"카테고리가 2회 이상 등장했습니다. 이 카테고리들은 **최대한 피해주세요**."
        )

    prompt = f"""당신은 AI 개발자/엔지니어를 위한 기술 뉴스레터 에디터입니다.

아래의 뉴스 후보 {len(candidates)}개 중에서 뉴스레터 주제로 가장 적합한 것 **1개**를 선택해 주세요.

---
## 최근 발행 이력 (다양성 기준으로 참고)
{history_text}
{overused_warning}

독자 경험을 위해 연속으로 비슷한 카테고리의 글이 나오지 않도록 주의하세요.
이미 다룬 기술/도구가 후보에 있다면 새로운 각도가 없는 한 선택하지 마세요.

---
## 선택 기준 (우선순위 순)
1. **Actionable** - 독자가 바로 실무에 적용할 수 있는 구체적인 기술/도구
2. **Pain Point 해결** - 기존 개발자들이 겪던 문제를 명확히 해결
3. **카테고리 다양성** - 최근 발행 이력과 다른 카테고리 우선
4. **신선함** - 새로운 오픈소스, 신규 릴리즈, 최신 기법
5. **기술 깊이** - 아키텍처/코드 레벨로 설명 가능한 것

**피할 것:**
- 거시적 트렌드 분석, 투자/비즈니스 뉴스
- 최근 이력과 카테고리가 겹치는 주제 (다양성 우선)
- 너무 학문적이거나 실무 적용이 어려운 논문

---
## 후보 목록
{candidate_text}

---
아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "selected_index": <1부터 시작하는 번호>,
  "category": "<infra|framework|agent|rag|training|evaluation|multimodal|tooling|architecture|security 중 하나>",
  "selection_reason": "<선택 이유 2-3문장. 왜 지금 이것이 가장 실용적이고, 발행 이력과도 균형이 맞는가>",
  "pain_point": "<이 기술이 해결하는 구체적인 개발자 Pain Point>",
  "hook": "<뉴스레터 독자의 주목을 끄는 한 줄 훅 문장 (한국어). 어미는 '~입니다/~합니다' 또는 명사형만 사용하고, 과장 수식어(놀랍게도·혁신적인·드디어 등)와 느낌표·이모지는 사용하지 않습니다>",
  "diversity_note": "<발행 이력과의 카테고리 균형에 대한 한 줄 코멘트>"
}}"""

    print("[AI Selector] Claude에게 최적 주제 선별 요청 중...")
    if published_history:
        print(f"  참고 이력: 최근 {len(published_history)}편 | 편중 카테고리: {overused or '없음'}")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"[AI Selector] JSON 파싱 실패: {e}\n응답: {raw}")
        return {**candidates[0], "selection_reason": "자동 선택 (파싱 실패)",
                "pain_point": "", "hook": "", "category": ""}

    idx = result.get("selected_index", 1) - 1
    idx = max(0, min(idx, len(candidates) - 1))

    selected = candidates[idx].copy()
    selected["selection_reason"] = result.get("selection_reason", "")
    selected["pain_point"] = result.get("pain_point", "")
    selected["hook"] = result.get("hook", "")
    selected["category"] = result.get("category", "")
    selected["diversity_note"] = result.get("diversity_note", "")

    print(f"[AI Selector] 선택됨: {selected['title'][:60]}")
    print(f"  카테고리: #{selected['category']}")
    print(f"  다양성 코멘트: {selected['diversity_note'][:80]}")
    return selected
