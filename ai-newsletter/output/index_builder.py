"""
Index & Navigation Builder
──────────────────────────
`outputs/` 폴더를 스캔해 두 가지를 생성/갱신한다.

1. `outputs/index.html` — 전체 이슈 목록 (Render 랜딩 페이지)
2. 각 `outputs/YYYY-MM-DD-slug/newsletter.html` 하단에
   "← 이전 글 / 다음 글 →" 네비게이션 삽입

의존성: 표준 라이브러리만 사용.
호출 시점: `main.py` STEP 6 (save_newsletter) 직후.
"""
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR


# ── 이슈 폴더 스캔 ────────────────────────────────────────────────────────────

_ISSUE_DIR_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)$')


def _scan_issues(outputs_root: str) -> list[dict]:
    """
    outputs/ 바로 아래의 이슈 폴더를 수집한다.
    각 이슈에서 newsletter.md 의 첫 H1 을 제목으로, 폴더명 앞 10자를 날짜로 사용.

    반환값 (최신순 정렬):
        [{"date": "2026-04-19", "slug": "...", "title": "...",
          "dir_name": "...", "html_rel": "..."}]
    """
    issues: list[dict] = []
    if not os.path.isdir(outputs_root):
        return issues

    for name in os.listdir(outputs_root):
        full = os.path.join(outputs_root, name)
        if not os.path.isdir(full):
            continue
        m = _ISSUE_DIR_RE.match(name)
        if not m:
            continue

        md_path = os.path.join(full, "newsletter.md")
        html_path = os.path.join(full, "newsletter.html")
        if not os.path.isfile(html_path):
            continue  # HTML 없는 이슈는 네비 대상에서 제외

        date_str = m.group(1)
        slug = m.group(2)

        # 제목 추출 — MD 첫 H1 우선, 없으면 slug
        title = slug
        if os.path.isfile(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
            except Exception:
                pass

        issues.append({
            "date": date_str,
            "slug": slug,
            "title": title,
            "dir_name": name,
            "html_rel": f"{name}/newsletter.html",
        })

    # 날짜 내림차순 → 같은 날짜면 폴더명 내림차순
    issues.sort(key=lambda x: (x["date"], x["dir_name"]), reverse=True)
    return issues


# ── index.html 생성 ──────────────────────────────────────────────────────────

_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Newsletter — 발행 목록</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
</head>
<body>
  <header class="index-header">
    <div class="brand">AI Newsletter</div>
    <h1 class="title">AI 엔지니어를 위한 기술 뉴스레터</h1>
    <p class="date">총 {count}개 이슈 · 마지막 업데이트 {updated}</p>
  </header>

  <ul class="index-list">
{items}
  </ul>
</body>
</html>
"""


def _render_item(issue: dict) -> str:
    return (
        '    <li>\n'
        f'      <span class="date">{issue["date"]}</span>\n'
        f'      <a href="{issue["html_rel"]}">{issue["title"]}</a>\n'
        '    </li>'
    )


def build_index(outputs_root: str = None) -> str:
    """
    outputs/index.html 을 생성한다.
    반환값: 생성된 index.html 의 절대경로
    """
    outputs_root = outputs_root or OUTPUT_DIR
    os.makedirs(outputs_root, exist_ok=True)

    issues = _scan_issues(outputs_root)
    items_html = "\n".join(_render_item(i) for i in issues) if issues else \
                 '    <li><span class="date">—</span>아직 발행된 이슈가 없습니다.</li>'

    html = _INDEX_TEMPLATE.format(
        count=len(issues),
        updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        items=items_html,
    )

    index_path = os.path.join(outputs_root, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[IndexBuilder] {len(issues)}개 이슈 → {index_path}")
    return index_path


# ── 개별 포스트에 prev/next 네비게이션 삽입 ─────────────────────────────────

_NAV_MARKER_START = "<!-- POST-NAV:START -->"
_NAV_MARKER_END = "<!-- POST-NAV:END -->"
_NAV_BLOCK_RE = re.compile(
    re.escape(_NAV_MARKER_START) + r".*?" + re.escape(_NAV_MARKER_END),
    re.DOTALL,
)


def _render_nav(prev: dict | None, next_: dict | None) -> str:
    """이전/다음 링크 HTML 블록 (style.css 의 .post-nav 클래스와 매칭)."""
    prev_html = (
        f'<a class="post-nav__link post-nav__prev" href="../{prev["html_rel"]}">'
        f'<span class="post-nav__label">← 이전 글</span>'
        f'<span class="post-nav__title">{prev["title"]}</span></a>'
        if prev else '<span class="post-nav__placeholder"></span>'
    )
    next_html = (
        f'<a class="post-nav__link post-nav__next" href="../{next_["html_rel"]}">'
        f'<span class="post-nav__label">다음 글 →</span>'
        f'<span class="post-nav__title">{next_["title"]}</span></a>'
        if next_ else '<span class="post-nav__placeholder"></span>'
    )
    home_html = '<a class="post-nav__home" href="../index.html">전체 목록</a>'

    return (
        f"{_NAV_MARKER_START}\n"
        '<nav class="post-nav">\n'
        f'  {prev_html}\n'
        f'  {home_html}\n'
        f'  {next_html}\n'
        '</nav>\n'
        f"{_NAV_MARKER_END}"
    )


def _inject_nav(html: str, nav_block: str) -> str:
    """기존 POST-NAV 블록을 대체하거나, </body> 직전에 삽입."""
    if _NAV_BLOCK_RE.search(html):
        return _NAV_BLOCK_RE.sub(nav_block, html)
    if "</body>" in html:
        return html.replace("</body>", f"{nav_block}\n</body>")
    return html + "\n" + nav_block


def update_post_navigation(outputs_root: str = None) -> int:
    """
    모든 이슈 HTML 에 prev/next 네비를 주입/갱신한다.
    반환값: 업데이트된 파일 수
    """
    outputs_root = outputs_root or OUTPUT_DIR
    issues = _scan_issues(outputs_root)
    if not issues:
        return 0

    # 날짜 내림차순이 "최신 → 과거" 이므로
    # 같은 인덱스의 "다음 글(더 최신)" = issues[i-1], "이전 글(더 과거)" = issues[i+1]
    updated = 0
    for i, issue in enumerate(issues):
        next_issue = issues[i - 1] if i > 0 else None
        prev_issue = issues[i + 1] if i + 1 < len(issues) else None

        html_path = os.path.join(outputs_root, issue["html_rel"])
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
        except FileNotFoundError:
            continue

        nav_block = _render_nav(prev_issue, next_issue)
        new_html = _inject_nav(html, nav_block)
        if new_html != html:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(new_html)
            updated += 1

    print(f"[IndexBuilder] prev/next 네비 업데이트: {updated}개")
    return updated


def build_all(outputs_root: str = None) -> None:
    """index.html 생성 + 모든 포스트의 네비 갱신 (한 번에)."""
    outputs_root = outputs_root or OUTPUT_DIR
    build_index(outputs_root)
    update_post_navigation(outputs_root)


if __name__ == "__main__":
    build_all()
