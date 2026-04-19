"""
AI Newsletter Local Viewer
===========================
실행: python viewer.py
     python viewer.py --port 8080
     python viewer.py --latest      # 가장 최근 뉴스레터 바로 열기

Python 표준 라이브러리만 사용 (추가 설치 불필요)
브라우저에서 http://localhost:8000 으로 접속
"""

import os
import re
import argparse
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path
import urllib.parse

# 프로젝트 루트
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
BACKLOG_FILE = os.path.join(BASE_DIR, "..", "NEWSLETTER_TOPICS.md")


# ── 데이터 로더 ────────────────────────────────────────────────────────────────

def load_issues() -> list[dict]:
    """outputs/ 폴더에서 발행된 뉴스레터 목록을 로드합니다."""
    if not os.path.exists(OUTPUTS_DIR):
        return []

    issues = []
    for entry in sorted(os.scandir(OUTPUTS_DIR), key=lambda e: e.name, reverse=True):
        if not entry.is_dir():
            continue
        # 비ASCII 슬러그 폴더 제외 (URL 인코딩 문제 방지)
        try:
            entry.name.encode('ascii')
        except UnicodeEncodeError:
            continue
        html_path = os.path.join(entry.path, "newsletter.html")
        md_path = os.path.join(entry.path, "newsletter.md")
        if not os.path.exists(html_path):
            continue

        parts = entry.name.split("-", 3)
        date_str = "-".join(parts[:3]) if len(parts) >= 3 else ""
        title = (parts[3] if len(parts) >= 4 else entry.name).replace("-", " ").title()

        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("# "):
                    title = first_line[2:]

        diagrams = list(Path(entry.path).glob("*.svg"))
        issues.append({
            "slug": entry.name,
            "title": title,
            "date": date_str,
            "html_path": html_path,
            "md_path": md_path,
            "diagram_count": len(diagrams),
        })
    return issues


def load_backlog_summary() -> dict:
    """사이드바 통계용 — 섹션별 항목 수만 반환합니다."""
    path = os.path.abspath(BACKLOG_FILE)
    if not os.path.exists(path):
        return {"backlog": 0, "in_progress": 0, "published": 0, "spinoffs": 0}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    def count_bullets(pattern: str) -> int:
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return 0
        return len([l for l in m.group(1).split("\n")
                    if l.strip().startswith("*") and "예시:" not in l])

    return {
        "backlog":      count_bullets(r'## 📋 \[Backlog\].*?\n(.*?)(?=\n## )'),
        "in_progress":  count_bullets(r'## ✍️ \[In Progress\].*?\n(.*?)(?=\n## )'),
        "published":    count_bullets(r'## ✅ \[Published\].*?\n(.*?)(?=\n## )'),
        "spinoffs":     count_bullets(r'## 💡 \[New Ideas.*?\n(.*?)$'),
    }


def load_backlog_detail() -> dict:
    """
    NEWSLETTER_TOPICS.md를 파싱해 섹션별 구조화된 데이터를 반환합니다.
    반환값:
    {
        "raw": str,                # 파일 전체 원문
        "sections": [
            {
                "id": "backlog" | "in_progress" | "published" | "spinoffs",
                "emoji": str,
                "title": str,
                "items": [
                    {
                        "text": str,       # 항목 전체 텍스트 (마크다운)
                        "title": str,      # 굵은 글씨 제목 파싱
                        "tags": [str],     # #tag 형태의 태그
                        "date": str,       # `YYYY-MM-DD` 형태의 날짜
                        "url": str,        # 링크 URL
                        "sub": [str],      # > 들여쓰기 서브텍스트
                        "is_example": bool # 예시 항목 여부
                    }
                ]
            }
        ]
    }
    """
    path = os.path.abspath(BACKLOG_FILE)
    if not os.path.exists(path):
        return {"raw": "", "sections": []}

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    section_defs = [
        ("backlog",     "📋", r'## 📋 \[Backlog\] 작성 대기 중인 주제'),
        ("in_progress", "✍️",  r'## ✍️ \[In Progress\] 작성 중'),
        ("published",   "✅", r'## ✅ \[Published\] 발행 완료'),
        ("spinoffs",    "💡", r'## 💡 \[New Ideas / Spinoffs\].*?'),
    ]

    # 각 섹션의 시작 위치 탐색
    positions = []
    for sid, emoji, pattern in section_defs:
        m = re.search(pattern, raw)
        if m:
            positions.append((m.start(), m.end(), sid, emoji))
    positions.sort()

    sections = []
    for i, (start, end, sid, emoji) in enumerate(positions):
        # 섹션 본문: 다음 섹션 시작 전까지
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(raw)
        body = raw[end:next_start].strip()

        # 헤더 텍스트 추출
        header_line = raw[start:end].split('\n')[0]
        title = re.sub(r'^##\s+', '', header_line).strip()

        items = _parse_backlog_items(body)
        sections.append({
            "id": sid,
            "emoji": emoji,
            "title": title,
            "items": items,
        })

    return {"raw": raw, "sections": sections}


def _parse_backlog_items(body: str) -> list[dict]:
    """백로그 섹션 본문을 항목 리스트로 파싱합니다."""
    items = []
    current = None

    for line in body.split("\n"):
        stripped = line.strip()

        if stripped.startswith("* ") or stripped.startswith("- "):
            if current:
                items.append(current)
            text = stripped[2:]
            is_example = "예시:" in text or text.startswith("*예시")

            # 굵은 글씨 제목 파싱 (**제목**)
            title_m = re.search(r'\*\*(.+?)\*\*', text)
            title = title_m.group(1) if title_m else re.sub(r'\[.*?\]\(.*?\)', '', text).strip()

            # 태그 (#tag)
            tags = re.findall(r'#(\w+)', text)

            # 날짜 (`YYYY-MM-DD`)
            date_m = re.search(r'`(\d{4}-\d{2}-\d{2})`', text)
            date = date_m.group(1) if date_m else ""

            # URL
            url_m = re.search(r'\[(?:[^\]]+)\]\((https?://[^)]+)\)', text)
            url = url_m.group(1) if url_m else ""

            # 카테고리 `[category]`
            cat_m = re.search(r'`\[(\w+)\]`', text)
            category = cat_m.group(1) if cat_m else ""

            current = {
                "text": text,
                "title": title[:80],
                "tags": tags,
                "date": date,
                "url": url,
                "category": category,
                "sub": [],
                "is_example": is_example,
            }

        elif stripped.startswith("> ") and current:
            current["sub"].append(stripped[2:])

        elif stripped.startswith("*(") and current:
            current["sub"].append(stripped.strip("*"))

    if current:
        items.append(current)

    return items


# ── HTML 공통 스타일 ──────────────────────────────────────────────────────────

STYLE = """
<style>
  :root {
    --red: #D75656;
    --gray: #EEEEEE;
    --dark: #1a1a2e;
    --sidebar-w: 300px;
    --text: #222;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', 'Noto Sans KR', Arial, sans-serif; background: #f5f5f7; color: var(--text); }

  /* ── 레이아웃 ── */
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: var(--sidebar-w);
    background: var(--dark);
    color: #ccc;
    position: fixed; top: 0; left: 0; height: 100vh;
    overflow-y: auto;
    display: flex; flex-direction: column;
  }
  .main { margin-left: var(--sidebar-w); flex: 1; }

  /* ── 사이드바 ── */
  .sidebar-header {
    padding: 24px 20px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .sidebar-header h1 { font-size: 15px; font-weight: 700; color: #fff; line-height: 1.4; }
  .sidebar-header .subtitle { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 4px; }

  .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 16px 20px; }
  .stat {
    background: rgba(255,255,255,0.06);
    border-radius: 8px; padding: 10px 12px; text-align: center;
  }
  .stat .num { font-size: 22px; font-weight: 800; color: var(--red); }
  .stat .label { font-size: 10px; color: rgba(255,255,255,0.45); margin-top: 2px; }

  .sidebar-section {
    padding: 10px 20px 4px;
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: rgba(255,255,255,0.3);
  }
  .sidebar-divider {
    margin: 8px 20px;
    border: none; border-top: 1px solid rgba(255,255,255,0.07);
  }

  /* 사이드바 네비 링크 */
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 20px;
    font-size: 13px; font-weight: 500;
    color: #aaa; text-decoration: none;
    border-left: 3px solid transparent;
    transition: all 0.15s;
  }
  .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
  .nav-item.active { background: rgba(215,86,86,0.12); color: #fff; border-left-color: var(--red); }
  .nav-item .nav-icon { font-size: 15px; width: 20px; text-align: center; }

  /* 뉴스레터 목록 아이템 */
  .issue-item {
    display: block; padding: 11px 20px;
    border-left: 3px solid transparent;
    text-decoration: none; color: #aaa;
    transition: all 0.15s;
  }
  .issue-item:hover { background: rgba(255,255,255,0.05); color: #fff; border-left-color: rgba(215,86,86,0.4); }
  .issue-item.active { background: rgba(215,86,86,0.12); color: #fff; border-left-color: var(--red); }
  .issue-item .issue-title { font-size: 12px; font-weight: 500; line-height: 1.4; margin-bottom: 3px; }
  .issue-item .issue-meta { font-size: 11px; color: rgba(255,255,255,0.3); display: flex; gap: 8px; }
  .issue-item .diag-badge {
    background: rgba(215,86,86,0.2); color: var(--red);
    font-size: 10px; padding: 1px 5px; border-radius: 3px;
  }
  .empty-sidebar { padding: 16px 20px; font-size: 12px; color: rgba(255,255,255,0.25); line-height: 1.6; }

  /* ── 메인 헤더 ── */
  .main-header {
    background: #fff;
    border-bottom: 1px solid #e8e8e8;
    padding: 14px 32px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 10;
  }
  .main-header .breadcrumb { font-size: 13px; color: #888; }
  .main-header .breadcrumb span { color: var(--text); font-weight: 600; }
  .toolbar { display: flex; gap: 8px; align-items: center; }
  .btn {
    padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600;
    border: none; cursor: pointer; text-decoration: none; display: inline-block;
    transition: all 0.15s;
  }
  .btn-primary { background: var(--red); color: #fff; }
  .btn-primary:hover { background: #c04040; }
  .btn-secondary { background: var(--gray); color: var(--text); }
  .btn-secondary:hover { background: #ddd; }
  .btn.active { background: var(--red); color: #fff; }

  /* ── iframe 뷰어 ── */
  .viewer-frame { width: 100%; height: calc(100vh - 53px); border: none; background: #fff; }
  #md-view {
    display: none; padding: 40px 48px; background: #fff;
    height: calc(100vh - 53px); overflow-y: auto;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px; line-height: 1.8; white-space: pre-wrap; color: #333;
  }

  /* ── 홈 화면 ── */
  .home { padding: 40px 48px; }
  .home h2 { font-size: 26px; font-weight: 800; margin-bottom: 6px; }
  .home .desc { font-size: 14px; color: #666; margin-bottom: 32px; line-height: 1.6; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px; }
  .card {
    background: #fff; border-radius: 10px; padding: 20px;
    border: 1px solid #e8e8e8; cursor: pointer; transition: all 0.15s;
    text-decoration: none; color: inherit;
  }
  .card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-color: var(--red); }
  .card .card-date { font-size: 11px; color: var(--red); font-weight: 700; margin-bottom: 6px; }
  .card .card-title { font-size: 15px; font-weight: 700; line-height: 1.4; margin-bottom: 10px; }
  .card .card-meta { font-size: 12px; color: #999; display: flex; gap: 10px; }
  .empty-home { text-align: center; padding: 80px 40px; color: #999; }
  .empty-home .icon { font-size: 48px; margin-bottom: 16px; }
  .empty-home h3 { font-size: 20px; font-weight: 700; color: #555; margin-bottom: 8px; }
  .empty-home p { font-size: 14px; line-height: 1.6; }
  .empty-home code { background: var(--gray); padding: 2px 8px; border-radius: 4px; font-size: 13px; color: #444; }

  /* ── 백로그 페이지 ── */
  .backlog-page { padding: 40px 48px; }
  .backlog-page h2 { font-size: 26px; font-weight: 800; margin-bottom: 6px; }
  .backlog-page .desc { font-size: 14px; color: #666; margin-bottom: 36px; }

  .bl-section { margin-bottom: 40px; }
  .bl-section-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--gray);
  }
  .bl-section-header h3 { font-size: 17px; font-weight: 700; }
  .bl-badge {
    font-size: 11px; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; color: #fff;
  }
  .bl-badge.backlog     { background: #6b7280; }
  .bl-badge.in_progress { background: #f59e0b; }
  .bl-badge.published   { background: #10b981; }
  .bl-badge.spinoffs    { background: var(--red); }

  .bl-empty { font-size: 13px; color: #aaa; padding: 12px 0; font-style: italic; }

  /* 백로그 아이템 카드 */
  .bl-item {
    background: #fff; border: 1px solid #e8e8e8;
    border-radius: 8px; padding: 16px 20px;
    margin-bottom: 10px; transition: border-color 0.15s;
  }
  .bl-item:hover { border-color: #ccc; }
  .bl-item.published  { border-left: 3px solid #10b981; }
  .bl-item.in_progress { border-left: 3px solid #f59e0b; }
  .bl-item.backlog    { border-left: 3px solid #6b7280; }
  .bl-item.spinoffs   { border-left: 3px solid var(--red); }
  .bl-item.is-example { opacity: 0.45; }

  .bl-item-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 6px; }
  .bl-item-title { font-size: 14px; font-weight: 600; line-height: 1.4; flex: 1; }
  .bl-item-title a { color: inherit; text-decoration: none; }
  .bl-item-title a:hover { color: var(--red); text-decoration: underline; }

  .bl-item-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 6px; }
  .bl-tag {
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 3px; background: var(--gray); color: #555;
  }
  .bl-cat {
    font-size: 11px; font-weight: 700; padding: 2px 8px;
    border-radius: 3px; background: rgba(215,86,86,0.1); color: var(--red);
  }
  .bl-date { font-size: 11px; color: #999; }
  .bl-sub { font-size: 12px; color: #666; margin-top: 6px; line-height: 1.5; border-left: 2px solid var(--gray); padding-left: 10px; }

  /* Raw 뷰 */
  .raw-view {
    background: #fff; margin: 0 48px 40px;
    border: 1px solid #e8e8e8; border-radius: 8px;
    padding: 28px 32px;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px; line-height: 1.8;
    white-space: pre-wrap; color: #333;
    overflow-x: auto; display: none;
  }
  .view-toggle { display: flex; gap: 4px; }
  .view-toggle .btn { padding: 5px 12px; font-size: 12px; }
</style>
"""


# ── 사이드바 공통 컴포넌트 ─────────────────────────────────────────────────────

def _render_sidebar(issues: list[dict], stats: dict,
                    active_nav: str = "", active_slug: str = "") -> str:
    """
    사이드바 전체 HTML을 렌더링합니다.
    active_nav: "home" | "backlog"
    active_slug: 현재 뷰어에서 열린 뉴스레터 슬러그
    """
    home_active  = " active" if active_nav == "home"    else ""
    bl_active    = " active" if active_nav == "backlog" else ""

    # 뉴스레터 목록
    issues_html = ""
    if issues:
        for issue in issues:
            a_class = " active" if issue["slug"] == active_slug else ""
            diag = (f'<span class="diag-badge">🎨 {issue["diagram_count"]}</span>'
                    if issue["diagram_count"] else "")
            issues_html += f"""
      <a class="issue-item{a_class}" href="/view/{issue['slug']}">
        <div class="issue-title">{issue['title'][:44]}{'…' if len(issue['title'])>44 else ''}</div>
        <div class="issue-meta"><span>{issue['date']}</span>{diag}</div>
      </a>"""
    else:
        issues_html = '<div class="empty-sidebar">아직 발행된 뉴스레터가 없습니다.</div>'

    return f"""
      <div class="sidebar-header">
        <h1>🤖 AI Newsletter<br>Local Viewer</h1>
        <div class="subtitle">발행 전 미리보기</div>
      </div>

      <div class="stats">
        <div class="stat"><div class="num">{stats['published']}</div><div class="label">Published</div></div>
        <div class="stat"><div class="num">{stats['backlog']}</div><div class="label">Backlog</div></div>
        <div class="stat"><div class="num">{stats['in_progress']}</div><div class="label">In Progress</div></div>
        <div class="stat"><div class="num">{stats['spinoffs']}</div><div class="label">Spinoffs</div></div>
      </div>

      <hr class="sidebar-divider">

      <a class="nav-item{home_active}" href="/">
        <span class="nav-icon">🏠</span> 홈
      </a>
      <a class="nav-item{bl_active}" href="/backlog">
        <span class="nav-icon">📋</span> 백로그 관리
      </a>

      <hr class="sidebar-divider">
      <div class="sidebar-section">뉴스레터</div>
      {issues_html}
    """


# ── 페이지 렌더러 ─────────────────────────────────────────────────────────────

def render_home(issues: list[dict], stats: dict) -> str:
    cards_html = ""
    if issues:
        for issue in issues:
            diag = f'<span>🎨 다이어그램 {issue["diagram_count"]}개</span>' if issue["diagram_count"] else ""
            cards_html += f"""
        <a class="card" href="/view/{issue['slug']}">
          <div class="card-date">{issue['date']}</div>
          <div class="card-title">{issue['title']}</div>
          <div class="card-meta"><span>📄 MD + HTML</span>{diag}</div>
        </a>"""
    else:
        cards_html = """
        <div class="empty-home">
          <div class="icon">📭</div>
          <h3>아직 발행된 뉴스레터가 없습니다</h3>
          <p>먼저 뉴스레터를 생성해 주세요:<br><code>uv run python main.py</code></p>
        </div>"""

    sidebar = _render_sidebar(issues, stats, active_nav="home")
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Newsletter Viewer</title>{STYLE}
</head>
<body>
  <div class="layout">
    <nav class="sidebar">{sidebar}</nav>
    <main class="main">
      <div class="main-header">
        <div class="breadcrumb"><span>홈</span></div>
        <div class="toolbar">
          <span style="font-size:12px;color:#999;">총 {len(issues)}편 발행</span>
        </div>
      </div>
      <div class="home">
        <h2>발행된 뉴스레터</h2>
        <p class="desc">클릭하면 미리보기 화면으로 이동합니다. 블로그에 포스팅하기 전 렌더링을 확인하세요.</p>
        <div class="cards">{cards_html}</div>
      </div>
    </main>
  </div>
</body>
</html>"""


def render_viewer(issue: dict, issues: list[dict], stats: dict) -> str:
    sidebar = _render_sidebar(issues, stats, active_nav="", active_slug=issue["slug"])
    html_url = f"/file/{issue['slug']}/newsletter.html"
    md_url   = f"/file/{issue['slug']}/newsletter.md"
    short_title = issue['title'][:42] + ('…' if len(issue['title']) > 42 else '')

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{issue['title']} — Viewer</title>{STYLE}
</head>
<body>
  <div class="layout">
    <nav class="sidebar">{sidebar}</nav>
    <main class="main">
      <div class="main-header">
        <div class="breadcrumb">
          <a href="/" style="color:#888;text-decoration:none;">홈</a>
          &nbsp;/&nbsp;<span>{short_title}</span>
        </div>
        <div class="toolbar">
          <div class="view-toggle">
            <button class="btn btn-secondary active" id="btn-html" onclick="showHtml()">HTML 미리보기</button>
            <button class="btn btn-secondary" id="btn-md" onclick="showMd()">Markdown</button>
          </div>
        </div>
      </div>
      <iframe id="html-view" class="viewer-frame" src="{html_url}"></iframe>
      <div id="md-view">로딩 중...</div>
    </main>
  </div>
  <script>
    function showHtml() {{
      document.getElementById('html-view').style.display = 'block';
      document.getElementById('md-view').style.display = 'none';
      document.getElementById('btn-html').classList.add('active');
      document.getElementById('btn-md').classList.remove('active');
    }}
    function showMd() {{
      document.getElementById('html-view').style.display = 'none';
      document.getElementById('md-view').style.display = 'block';
      document.getElementById('btn-html').classList.remove('active');
      document.getElementById('btn-md').classList.add('active');
      const el = document.getElementById('md-view');
      if (el.dataset.loaded) return;
      el.dataset.loaded = '1';
      fetch('{md_url}').then(r => r.text()).then(t => {{ el.textContent = t; }});
    }}
  </script>
</body>
</html>"""


def render_backlog_page(issues: list[dict], stats: dict) -> str:
    """NEWSLETTER_TOPICS.md를 파싱해 백로그 관리 페이지를 렌더링합니다."""
    detail = load_backlog_detail()
    sidebar = _render_sidebar(issues, stats, active_nav="backlog")

    # 섹션별 렌더링
    sections_html = ""
    for section in detail["sections"]:
        sid     = section["id"]
        title   = section["title"]
        items   = [i for i in section["items"] if not i["is_example"]]
        count   = len(items)

        badge_html = f'<span class="bl-badge {sid}">{count}</span>'
        items_html = ""

        if not items:
            items_html = '<p class="bl-empty">항목 없음</p>'
        else:
            for item in items:
                # 제목 (URL 있으면 링크)
                if item["url"]:
                    title_inner = f'<a href="{item["url"]}" target="_blank">{item["title"]}</a>'
                else:
                    title_inner = item["title"]

                # 태그
                tags_html = "".join(f'<span class="bl-tag">#{t}</span>' for t in item["tags"])

                # 카테고리
                cat_html = f'<span class="bl-cat">{item["category"]}</span>' if item["category"] else ""

                # 날짜
                date_html = f'<span class="bl-date">📅 {item["date"]}</span>' if item["date"] else ""

                # 서브텍스트
                sub_html = ""
                if item["sub"]:
                    sub_text = " · ".join(s for s in item["sub"] if s.strip())
                    if sub_text:
                        sub_html = f'<div class="bl-sub">{sub_text}</div>'

                example_class = " is-example" if item["is_example"] else ""

                items_html += f"""
          <div class="bl-item {sid}{example_class}">
            <div class="bl-item-header">
              <div class="bl-item-title">{title_inner}</div>
            </div>
            <div class="bl-item-meta">
              {cat_html}{tags_html}{date_html}
            </div>
            {sub_html}
          </div>"""

        sections_html += f"""
      <div class="bl-section">
        <div class="bl-section-header">
          <h3>{title}</h3>
          {badge_html}
        </div>
        {items_html}
      </div>"""

    # Raw 뷰 (원문 Markdown)
    raw_escaped = detail["raw"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>백로그 관리 — AI Newsletter Viewer</title>{STYLE}
</head>
<body>
  <div class="layout">
    <nav class="sidebar">{sidebar}</nav>
    <main class="main">
      <div class="main-header">
        <div class="breadcrumb">
          <a href="/" style="color:#888;text-decoration:none;">홈</a>
          &nbsp;/&nbsp;<span>백로그 관리</span>
        </div>
        <div class="toolbar">
          <div class="view-toggle">
            <button class="btn btn-secondary active" id="btn-cards" onclick="showCards()">카드 보기</button>
            <button class="btn btn-secondary"         id="btn-raw"   onclick="showRaw()">원문 MD</button>
          </div>
        </div>
      </div>

      <div id="cards-view">
        <div class="backlog-page">
          <h2>백로그 관리</h2>
          <p class="desc">NEWSLETTER_TOPICS.md 현황입니다. 파일을 직접 수정하면 새로고침 시 반영됩니다.</p>
          {sections_html}
        </div>
      </div>

      <pre id="raw-view" class="raw-view">{raw_escaped}</pre>
    </main>
  </div>
  <script>
    function showCards() {{
      document.getElementById('cards-view').style.display = 'block';
      document.getElementById('raw-view').style.display = 'none';
      document.getElementById('btn-cards').classList.add('active');
      document.getElementById('btn-raw').classList.remove('active');
    }}
    function showRaw() {{
      document.getElementById('cards-view').style.display = 'none';
      document.getElementById('raw-view').style.display = 'block';
      document.getElementById('btn-cards').classList.remove('active');
      document.getElementById('btn-raw').classList.add('active');
    }}
  </script>
</body>
</html>"""


# ── HTTP 핸들러 ────────────────────────────────────────────────────────────────

class ViewerHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]}")

    def send_html(self, html: str, status: int = 200):
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def send_file(self, filepath: str):
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        mime_map = {
            ".html": "text/html; charset=utf-8",
            ".md":   "text/plain; charset=utf-8",
            ".svg":  "image/svg+xml",
            ".png":  "image/png",
            ".jpg":  "image/jpeg",
        }
        ext = os.path.splitext(filepath)[1].lower()
        mime = mime_map.get(ext, "application/octet-stream")
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = urllib.parse.unquote(parsed.path).rstrip("/") or "/"

        issues = load_issues()
        stats  = load_backlog_summary()

        # ── 홈 ──
        if path == "/":
            self.send_html(render_home(issues, stats))
            return

        # ── 백로그 페이지 ──
        if path == "/backlog":
            self.send_html(render_backlog_page(issues, stats))
            return

        # ── 뉴스레터 뷰어 ──
        if path.startswith("/view/"):
            slug  = path[6:]
            issue = next((i for i in issues if i["slug"] == slug), None)
            if not issue:
                self.send_html(
                    f'<h2 style="font-family:sans-serif;padding:40px">404 — 뉴스레터를 찾을 수 없습니다<br>'
                    f'<small style="color:#999">{slug}</small></h2>', 404)
                return
            self.send_html(render_viewer(issue, issues, stats))
            return

        # ── 정적 파일 ──
        if path.startswith("/file/"):
            parts = path[6:].split("/", 1)
            if len(parts) == 2:
                slug, filename = parts
                self.send_file(os.path.join(OUTPUTS_DIR, slug, filename))
                return

        self.send_error(404, "Not found")


# ── 실행 ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Newsletter Local Viewer")
    parser.add_argument("--port",       type=int, default=8000)
    parser.add_argument("--latest",     action="store_true", help="최신 뉴스레터 바로 열기")
    parser.add_argument("--no-browser", action="store_true", help="브라우저 자동 실행 안 함")
    args = parser.parse_args()

    server = HTTPServer(("localhost", args.port), ViewerHandler)

    if args.latest:
        issues   = load_issues()
        slug     = issues[0]["slug"] if issues else None
        open_url = f"http://localhost:{args.port}/view/{slug}" if slug else f"http://localhost:{args.port}"
    else:
        open_url = f"http://localhost:{args.port}"

    stats = load_backlog_summary()
    print()
    print("=" * 52)
    print("🌐 AI Newsletter Local Viewer")
    print(f"   URL    : {open_url}")
    print(f"   Backlog: http://localhost:{args.port}/backlog")
    print(f"   종료   : Ctrl+C")
    print("=" * 52)
    print(f"\n   📊 Published {stats['published']} | Backlog {stats['backlog']} | Spinoffs {stats['spinoffs']}")
    issues = load_issues()
    if issues:
        print(f"   📄 최신: {issues[0]['title'][:48]} ({issues[0]['date']})")
    print()

    if not args.no_browser:
        def _open():
            import time; time.sleep(0.8)
            webbrowser.open(open_url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 뷰어를 종료합니다.")
        server.shutdown()


if __name__ == "__main__":
    main()
