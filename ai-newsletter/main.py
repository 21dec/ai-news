"""
AI Newsletter Automation - Main Orchestrator (LEGACY)
=====================================================

⚠️  이 스크립트는 레거시 경로입니다.

현재 발행 파이프라인은 Anthropic API 를 사용하지 않으며,
주제 선별·본문 생성·스핀오프 등 LLM 작업은 Claude 스케줄 태스크
세션이 직접 수행합니다. 운영에서 실행되는 흐름은 스케줄 태스크
`daily-ai-newsletter` 의 프롬프트에 정의되어 있습니다.

이 파일은 레거시 reference 목적으로만 유지되며, `ai/` 모듈을
import 하는 경로(select_best_topic / generate_newsletter /
generate_spinoffs)는 anthropic 패키지가 제거된 현재 환경에서
호출 시 RuntimeError 로 실패합니다.
"""

import sys
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from config import ANTHROPIC_API_KEY, OUTPUT_DIR
from crawlers import fetch_github_trending, fetch_arxiv, fetch_reddit
from ai import select_best_topic, generate_newsletter, generate_spinoffs
from diagrams import generate_diagrams
from output import (
    save_newsletter, update_backlog, add_spinoffs_to_backlog, load_published_history,
    run_content_validation, run_file_validation, run_image_placement_validation,
)
from output.validate import validate_content, validate_files
from output.writer import _slugify
from output.index_builder import build_all as build_index_and_nav

MAX_RETRIES = 3


def _generate_with_retry(topic: dict) -> dict:
    """
    콘텐츠를 생성하고 검증합니다. 실패 시 최대 MAX_RETRIES 번 재시도합니다.
    검증 실패 사유를 프롬프트에 피드백해 재생성 품질을 높입니다.
    """
    last_errors = []

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"\n  🔄 재시도 {attempt - 1}/{MAX_RETRIES - 1} — 콘텐츠 재생성 중...")
            if last_errors:
                print(f"  이전 실패 사유: {' / '.join(last_errors)}")

        content = generate_newsletter(topic, retry_hint=last_errors if attempt > 1 else None)

        result = validate_content(content)
        result.print_report(f"Content (시도 {attempt}/{MAX_RETRIES})")

        if result.passed:
            return content

        last_errors = result.errors
        if attempt == MAX_RETRIES:
            print(f"\n❌ 콘텐츠 검증이 {MAX_RETRIES}회 모두 실패했습니다. 파이프라인을 중단합니다.")
            sys.exit(2)

    # 도달 불가 — for 루프 내에서 반환 또는 sys.exit
    raise RuntimeError("unreachable")


def _save_with_retry(content: dict, selected_topic: dict, diagram_paths: list,
                     date_str: str, issue_dir: str) -> dict:
    """
    파일을 저장하고 검증합니다. 실패 시 최대 MAX_RETRIES 번 재시도합니다.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            print(f"\n  🔄 재시도 {attempt - 1}/{MAX_RETRIES - 1} — 파일 재저장 중...")

        saved = save_newsletter(content, selected_topic, diagram_paths, date_str,
                                output_dir=issue_dir)

        result = validate_files(saved, content)
        result.print_report(f"File (시도 {attempt}/{MAX_RETRIES})")

        if result.passed:
            return saved

        if attempt == MAX_RETRIES:
            print(f"\n❌ 파일 검증이 {MAX_RETRIES}회 모두 실패했습니다.")
            print(f"   출력 폴더: {issue_dir}")
            print("   백로그 등록을 건너뜁니다. 파일을 직접 확인하세요.")
            sys.exit(3)

    raise RuntimeError("unreachable")


def run():
    print("=" * 60)
    print("🤖 AI Newsletter Automation")
    print(f"   실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print("\n⚠️  main.py 는 레거시 경로입니다.")
    print("   운영 파이프라인은 Claude 스케줄 태스크 `daily-ai-newsletter` 프롬프트에서 수행됩니다.")
    print("   이 스크립트는 `ai/` 모듈 호출 시점에 RuntimeError 로 실패합니다.\n")

    # ── STEP 1: 발행 이력 로드 (다양성 가드레일) ──────────────────────────
    print("\n📚 STEP 1: 발행 이력 로드 중 (다양성 가드레일)...")
    published_history = load_published_history(limit=10)
    if published_history:
        print(f"✅ 최근 발행 {len(published_history)}편 로드 완료")
        for item in published_history[:3]:
            tags = " ".join(f"#{t}" for t in item.get("tags", []))
            print(f"   - [{item.get('date', '')}] {item.get('title', '')[:45]} {tags}")
    else:
        print("ℹ️  발행 이력 없음 — 첫 번째 발행")

    # ── STEP 2: 크롤링 ────────────────────────────────────────────────────
    print("\n📡 STEP 2: 뉴스 수집 중...")
    candidates = []

    github_items = fetch_github_trending()
    arxiv_items = fetch_arxiv()
    reddit_items = fetch_reddit()

    candidates.extend(github_items)
    candidates.extend(arxiv_items)
    candidates.extend(reddit_items)

    print(f"\n✅ 총 {len(candidates)}개 후보 수집 완료")
    print(f"   - GitHub Trending: {len(github_items)}개")
    print(f"   - ArXiv: {len(arxiv_items)}개")
    print(f"   - Reddit: {len(reddit_items)}개")

    if not candidates:
        print("❌ 수집된 후보가 없습니다. 네트워크 연결을 확인하세요.")
        sys.exit(1)

    # ── STEP 3: AI 선별 (발행 이력 참고) ─────────────────────────────────
    print("\n🧠 STEP 3: 최적 주제 선별 중 (Claude API + 다양성 가드레일)...")
    selected_topic = select_best_topic(candidates, published_history=published_history)
    print(f"\n✅ 선택된 주제: {selected_topic['title'][:70]}")
    print(f"   카테고리: #{selected_topic.get('category', '?')}")
    print(f"   출처: {selected_topic['source']}")
    print(f"   훅: {selected_topic.get('hook', '')[:80]}")

    # ── STEP 4: 콘텐츠 생성 + 검증 (최대 3회) ────────────────────────────
    print("\n✍️  STEP 4: 뉴스레터 콘텐츠 생성 중 (Claude API)...")
    content = _generate_with_retry(selected_topic)
    print(f"\n✅ 콘텐츠 확정: '{content['title']}'")

    # ── STEP 5: 다이어그램 생성 ───────────────────────────────────────────
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = f"{date_str}-{_slugify(content['title'])}"
    issue_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(issue_dir, exist_ok=True)

    print(f"\n🎨 STEP 5: 다이어그램 생성 중...")
    diagram_specs = content.get("diagram_specs", [])
    diagram_paths = []
    if diagram_specs:
        diagram_paths = generate_diagrams(diagram_specs, issue_dir, slug)
        print(f"✅ 다이어그램 {len(diagram_paths)}개 생성 완료")
    else:
        print("ℹ️  다이어그램 스펙 없음 — 건너뜀")

    # ── STEP 6: 파일 저장 + 검증 (최대 3회) ──────────────────────────────
    print(f"\n💾 STEP 6: 파일 저장 중...")
    saved = _save_with_retry(content, selected_topic, diagram_paths, date_str, issue_dir)
    print(f"✅ 저장 확정")
    print(f"   📄 MD   → {saved['md_path']}")
    print(f"   🌐 HTML → {saved['html_path']}")

    # ── STEP 6.6: 이미지 위치 검증 ───────────────────────────────────────
    print(f"\n🖼️  STEP 6.6: 이미지 배치 위치 검증 중...")
    run_image_placement_validation(saved, content, diagram_paths)
    # 이미지 배치는 경고만 출력 (파이프라인 중단 없음)

    # ── STEP 6.8: 인덱스 + prev/next 네비게이션 갱신 ─────────────────────
    print(f"\n🧭 STEP 6.8: outputs/index.html + post-nav 갱신 중...")
    build_index_and_nav(OUTPUT_DIR)

    # ── STEP 7: 백로그 Published 업데이트 ────────────────────────────────
    print(f"\n📋 STEP 7: 백로그 Published 등록 중...")
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
    print(f"\n💡 STEP 8: 파생 주제(스핀오프) 자동 생성 중...")
    spinoffs = generate_spinoffs(content, selected_topic, count=3)

    if spinoffs:
        add_spinoffs_to_backlog(spinoffs, date_str=date_str)
        print(f"✅ 스핀오프 {len(spinoffs)}개 → 백로그에 추가 완료")
        print("   다음 발행 후보:")
        for s in spinoffs:
            print(f"   → [{s.get('category', '?')}] {s['title']}")
    else:
        print("ℹ️  스핀오프 생성 실패 — 건너뜀")

    # ── 완료 요약 ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🎉 뉴스레터 생성 완료!")
    print(f"   제목: {content['title']}")
    print(f"   카테고리: #{selected_topic.get('category', '?')}")
    print(f"   태그: {', '.join(article_tags)}")
    print(f"   다음 후보: {len(spinoffs)}개 백로그 추가됨")
    print(f"   출력 폴더: {saved['output_dir']}")
    print("=" * 60)

    return saved


if __name__ == "__main__":
    run()
