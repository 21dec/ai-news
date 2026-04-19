"""
Backlog Manager
NEWSLETTER_TOPICS.md를 읽고 쓰는 모든 기능을 담당합니다.

주요 기능:
- update_backlog(): 발행 완료 항목을 Published 섹션에 기록
- add_spinoffs_to_backlog(): 스핀오프 아이디어를 Backlog + Spinoffs 섹션에 추가
- load_published_history(): 다양성 가드레일용 발행 이력 로드
"""
import os
import re
from datetime import datetime
from typing import Optional
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import BACKLOG_FILE


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _read_backlog() -> str:
    path = os.path.abspath(BACKLOG_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"백로그 파일을 찾을 수 없음: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_backlog(content: str) -> None:
    path = os.path.abspath(BACKLOG_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ── Public API ────────────────────────────────────────────────────────────────

def update_backlog(title: str, source_url: str, tags: list[str] = None, date_str: str = None) -> bool:
    """
    발행 완료 항목을 ✅ [Published] 섹션에 추가합니다.

    Args:
        title: 뉴스레터 제목
        source_url: 원문 URL
        tags: 카테고리 태그 리스트 (다양성 가드레일에서 활용)
        date_str: 발행일 (기본: 오늘)
    """
    if date_str is None:
        date_str = _today()

    tags_str = " ".join(f"#{t}" for t in (tags or []))
    entry = f"* **{title}** — `{date_str}` [{source_url}]({source_url})"
    if tags_str:
        entry += f" {tags_str}"

    try:
        content = _read_backlog()
    except FileNotFoundError as e:
        print(f"[Backlog] {e}")
        return False

    # ✅ Published 섹션 찾아 맨 위에 삽입 (최신이 위에 오도록)
    pattern = r'(## ✅ \[Published\] 발행 완료\n)'
    match = re.search(pattern, content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + entry + "\n" + content[insert_pos:]
    else:
        content += f"\n{entry}\n"

    _write_backlog(content)
    print(f"[Backlog] Published 등록: '{title}' ({date_str})")
    return True


def add_spinoffs_to_backlog(spinoffs: list[dict], date_str: str = None) -> bool:
    """
    생성된 스핀오프 주제를 두 곳에 동시 추가합니다:
      1. 📋 [Backlog] 섹션 - 다음 글감으로 대기
      2. 💡 [New Ideas / Spinoffs] 섹션 - 파생 이력 추적

    Args:
        spinoffs: generate_spinoffs()의 결과 리스트
        date_str: 추가일 (기본: 오늘)
    """
    if not spinoffs:
        return True

    if date_str is None:
        date_str = _today()

    try:
        content = _read_backlog()
    except FileNotFoundError as e:
        print(f"[Backlog] {e}")
        return False

    # ── 1. 📋 Backlog 섹션에 추가 ─────────────────────────────────────────
    backlog_entries = []
    for s in spinoffs:
        tags_str = " ".join(f"#{t}" for t in s.get("tags", []))
        cat = s.get("category", "")
        title = s.get("title", "")
        desc = s.get("description", "")
        entry = f"* **{title}** `[{cat}]` {tags_str}"
        if desc:
            entry += f"\n  > {desc}"
        entry += f"\n  > *(스핀오프 from: {s.get('source_article', '')} | 추가: {date_str})*"
        backlog_entries.append(entry)

    backlog_block = "\n".join(backlog_entries) + "\n"

    backlog_pattern = r'(## 📋 \[Backlog\] 작성 대기 중인 주제\n)'
    match = re.search(backlog_pattern, content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + backlog_block + content[insert_pos:]
    else:
        content += f"\n{backlog_block}"

    # ── 2. 💡 Spinoffs 섹션에 이력 추가 ──────────────────────────────────
    spinoff_entries = []
    for s in spinoffs:
        cat = s.get("category", "")
        title = s.get("title", "")
        rationale = s.get("rationale", "")
        source = s.get("source_article", "")
        spinoff_entries.append(
            f"* `[{cat}]` **{title}** ← {source} 작성 중 포착\n"
            f"  > {rationale}"
        )

    spinoff_block = "\n".join(spinoff_entries) + "\n"

    spinoff_pattern = r'(## 💡 \[New Ideas / Spinoffs\].*?\n)'
    match = re.search(spinoff_pattern, content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + spinoff_block + content[insert_pos:]
    else:
        content += f"\n{spinoff_block}"

    _write_backlog(content)
    print(f"[Backlog] 스핀오프 {len(spinoffs)}개 추가 완료")
    return True


def load_published_history(limit: int = 10) -> list[dict]:
    """
    다양성 가드레일용: 최근 발행된 뉴스레터 이력을 로드합니다.

    Returns:
        List of dicts:
        [
            {
                "title": "뉴스레터 제목",
                "date": "2025-01-01",
                "tags": ["infra", "serving"],
                "url": "https://..."
            },
            ...
        ]
        (최신순, limit개까지)
    """
    try:
        content = _read_backlog()
    except FileNotFoundError:
        return []

    # Published 섹션 추출
    pub_pattern = r'## ✅ \[Published\] 발행 완료\n(.*?)(?=\n## |\Z)'
    match = re.search(pub_pattern, content, re.DOTALL)
    if not match:
        return []

    pub_section = match.group(1).strip()
    if not pub_section:
        return []

    history = []
    for line in pub_section.split("\n"):
        line = line.strip()
        if not line.startswith("*"):
            continue

        # 제목 파싱: * **제목** — `날짜` [url](url) #tag1 #tag2
        title_match = re.search(r'\*\*(.+?)\*\*', line)
        date_match = re.search(r'`(\d{4}-\d{2}-\d{2})`', line)
        url_match = re.search(r'\[https?://[^\]]+\]\((https?://[^)]+)\)', line)
        tags = re.findall(r'#(\w+)', line)

        if title_match:
            history.append({
                "title": title_match.group(1),
                "date": date_match.group(1) if date_match else "",
                "url": url_match.group(1) if url_match else "",
                "tags": tags
            })

    return history[:limit]


def mark_in_progress(title_keyword: str) -> bool:
    """
    백로그에서 특정 주제를 ✍️ [In Progress] 섹션으로 이동합니다.

    Args:
        title_keyword: 이동할 항목의 제목 키워드 (부분 매칭)
    """
    try:
        content = _read_backlog()
    except FileNotFoundError as e:
        print(f"[Backlog] {e}")
        return False

    # Backlog에서 해당 항목 찾기
    backlog_pattern = r'(## 📋 \[Backlog\] 작성 대기 중인 주제\n)(.*?)(## ✍️)'
    match = re.search(backlog_pattern, content, re.DOTALL)
    if not match:
        return False

    backlog_content = match.group(2)
    lines = backlog_content.split("\n")

    found_line = None
    remaining_lines = []
    for line in lines:
        if title_keyword.lower() in line.lower() and found_line is None:
            found_line = line
        else:
            remaining_lines.append(line)

    if not found_line:
        print(f"[Backlog] '{title_keyword}' 항목을 찾을 수 없습니다.")
        return False

    # In Progress 섹션에 추가
    new_backlog = match.group(1) + "\n".join(remaining_lines) + match.group(3)
    content = content.replace(match.group(0), new_backlog)

    in_progress_pattern = r'(## ✍️ \[In Progress\] 작성 중\n)'
    ip_match = re.search(in_progress_pattern, content)
    if ip_match:
        content = content[:ip_match.end()] + f"* {found_line.lstrip('* ')}\n" + content[ip_match.end():]

    _write_backlog(content)
    print(f"[Backlog] In Progress로 이동: {found_line[:60]}")
    return True
