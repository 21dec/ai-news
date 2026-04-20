"""
AI Newsletter Automation - Main Orchestrator
=============================================

`uv run python main.py` 로 실행하면 크롤링 → 주제 선별 → 본문 생성 →
파일 저장 → 백로그 관리까지 1편의 뉴스레터를 완전 자동으로 발행합니다.

LLM: OpenAI GPT-5.4  |  환경변수: OPENAI_API_KEY
"""

import sys
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from config import OPENAI_API_KEY, OUTPUT_DIR
from crawlers import fetch_github_trending, fetch_arxiv, fetch_reddit, fetch_rss_feeds
from ai import select_best_topic, generate_newsletter, generate_spinoffs
from diagrams import generate_diagrams
from output import (
    save_newsletter, update_backlog, add_spinoffs_to_backlog, load_published_history,
    run_content_validation, run_file_validation, run_image_placement_validation,
)
from output.validate import validate_content, validate_files
from output.writer import _slugify
from output.index_builder import build_all as build_index_and_nav
from output.backlog import recommended_spinoff_count

MAX_RETRIES = 3


def _generate_with_retry(topic: dict) -> dict:
    """콘텐츠를 생성하고 검증합니다. 실패 시 최대 MAX_RETRIES 번 재시도합니다."""
    last_errors = []

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"\n  재시도 {attempt - 1}/{MAX_RETRIES - 1}")
            if last_errors:
                print(f"  이전 실패 사유: {' / '.join(last_errors)}")

        content = generate_newsletter(topic, retry_hint=last_errors if attempt > 1 else None)

        result = validate_content(content)
        result.print_report(f"Content (시도 {attempt}/{MAX_RETRIES})")

        if result.passed:
            return content

        last_errors = result.errors
        if attempt == MAX_RETRIES:
            print(f"\n콘텐츠 검증이 {MAX_RETRIES}회 모두 실패했습니다. 중단합니다.")
            sys.exit(2)

    raise RuntimeError("unreachable")


def _save_with_retry(content: dict, selected_topic: dict, diagram_paths: list,
                     date_str: str, issue_dir: str) -> dict:
    """파일을 저장하고 검증합니다. 실패 시 최대 MAX_RETRIES 번 재시도합니다."""
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"\n  재시도 {attempt - 1}/{MAX_RETRIES - 1} — 파일 재저장 중...")

        saved = save_newsletter(content, selected_topic, diagram_paths, date_str,
                                output_dir=issue_dir)

        result = validate_files(saved, content)
        result.print_report(f"File (시도 {attempt}/{MAX_RETRIES})")

        if result.passed:
            return saved

        if attempt == MAX_RETRIES:
            print(f"\n파일 검증이 {MAX_RETRIES}회 모두 실패했습니다.")
            sys.exit(3)

    raise RuntimeError("unreachable")


def run():
    print("=" * 60)
    print("AI Newsletter Automation (GPT-5.4)")
    print(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print(".env 파일에 OPENAI_API_KEY=sk-... 를 추가하세요.")
        sys.exit(1)

    # ── STEP 1: 발행 이력 로드 ────────────────────────────────────────────
    print("\nSTEP 1: 발행 이력 로드 중...")
    published_history = load_published_history(limit=10)
    if published_history:
        print(f"  최근 발행 {len(published_history)}편 로드 완료")
        for item in published_history[:3]:
            tags = " ".join(f"#{t}" for t in item.get("tags", []))
            print(f"  - [{item.get('date', '')}] {item.get('title', '')[:45]} {tags}")
    else:
        print("  발행 이력 없음 (첫 번째 발행)")

    # ── STEP 2: 크롤링 ────────────────────────────────────────────────────
    print("\nSTEP 2: 뉴스 수집 중...")
    candidates = []

    github_items = fetch_github_trending()
    arxiv_items = fetch_arxiv()
    reddit_items = fetch_reddit()
    rss_items = fetch_rss_feeds()

    candidates.extend(github_items)
    candidates.extend(arxiv_items)
    candidates.extend(reddit_items)
    candidates.extend(rss_items)

    print(f"\n  총 {len(candidates)}개 후보 수집 완료")

    if not candidates:
        print("수집된 후보가 없습니다. 네트워크 연결을 확인하세요.")
        sys.exit(1)

    # ── STEP 3: AI 선별 ──────────────────────────────────────────────────
    print("\nSTEP 3: GPT-5.4-mini 주제 선별 중...")
    selected_topic = select_best_topic(candidates, published_history=published_history)
    print(f"\n  선택됨: {selected_topic['title'][:70]}")
    print(f"  카테고리: #{selected_topic.get('category', '?')}")

    # ── STEP 4: 콘텐츠 생성 + 검증 ───────────────────────────────────────
    print("\nSTEP 4: 뉴스레터 콘텐츠 생성 중...")
    content = _generate_with_retry(selected_topic)
    print(f"\n  확정: '{content['title']}'")

    # ── STEP 5: 다이어그램 생성 (선택적) ──────────────────────────────────
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = f"{date_str}-{_slugify(content['title'])}"
    issue_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(issue_dir, exist_ok=True)

    diagram_specs = content.get("diagram_specs", [])
    diagram_paths = []
    if diagram_specs:
        print(f"\nSTEP 5: 다이어그램 {len(diagram_specs)}개 생성 중...")
        diagram_paths = generate_diagrams(diagram_specs, issue_dir, slug)
    else:
        print("\nSTEP 5: 다이어그램 없음 (건너뜀)")

    # ── STEP 6: 파일 저장 + 검증 ─────────────────────────────────────────
    print(f"\nSTEP 6: 파일 저장 중...")
    saved = _save_with_retry(content, selected_topic, diagram_paths, date_str, issue_dir)
    print(f"  MD   → {saved['md_path']}")
    print(f"  HTML → {saved['html_path']}")

    # ── STEP 6.6: 이미지 위치 검증 ───────────────────────────────────────
    if diagram_paths:
        run_image_placement_validation(saved, content, diagram_paths)

    # ── STEP 6.8: 인덱스 + 네비게이션 갱신 ───────────────────────────────
    print(f"\nSTEP 6.8: index.html + post-nav 갱신 중...")
    build_index_and_nav(OUTPUT_DIR)

    # ── STEP 7: 백로그 Published 업데이트 ────────────────────────────────
    print(f"\nSTEP 7: 백로그 Published 등록 중...")
    article_tags = content.get("tags", [])
    category = selected_topic.get("category", "")
    all_tags = list(set([category] + article_tags)) if category else article_tags

    update_backlog(
        title=content["title"],
        source_url=selected_topic.get("url", ""),
        tags=all_tags,
        date_str=date_str
    )

    # ── STEP 8: 스핀오프 자동 생성 ───────────────────────────────────────
    spinoff_cap = recommended_spinoff_count()
    spinoffs = []
    if spinoff_cap > 0:
        print(f"\nSTEP 8: 파생 주제 {spinoff_cap}개 생성 중...")
        spinoffs = generate_spinoffs(content, selected_topic, count=spinoff_cap)
        if spinoffs:
            add_spinoffs_to_backlog(spinoffs, date_str=date_str)
    else:
        print("\nSTEP 8: 백로그 포화 — 스핀오프 생략")

    # ── 완료 요약 ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"발행 완료: {content['title']}")
    print(f"카테고리: #{selected_topic.get('category', '?')}")
    print(f"출력: {saved['output_dir']}")
    print(f"스핀오프: {len(spinoffs)}개 백로그 추가")
    print("=" * 60)

    return saved


if __name__ == "__main__":
    run()
