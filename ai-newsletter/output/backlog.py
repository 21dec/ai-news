"""
Backlog Manager
NEWSLETTER_TOPICS.md를 읽고 쓰는 모든 기능을 담당합니다.

주요 기능:
- update_backlog(): 발행 완료 항목을 Published 섹션에 기록
- add_spinoffs_to_backlog(): 스핀오프 아이디어를 Backlog + Spinoffs 섹션에 추가
- load_published_history(): 다양성 가드레일용 발행 이력 로드
- load_backlog_items(): 📋 Backlog 섹션 파싱
- count_backlog_items(): 백로그 크기 — 적응형 스핀오프 개수 결정용
- filter_duplicate_spinoffs(): Published + Backlog 제목과 겹치는 스핀오프 제거
- prune_old_spinoffs(): N일 초과한 미소비 스핀오프 백로그 정리
"""
import os
import re
from datetime import datetime, date, timedelta
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


def add_spinoffs_to_backlog(spinoffs: list[dict], date_str: str = None,
                             dedup: bool = True) -> bool:
    """
    생성된 스핀오프 주제를 두 곳에 동시 추가합니다:
      1. 📋 [Backlog] 섹션 - 다음 글감으로 대기
      2. 💡 [New Ideas / Spinoffs] 섹션 - 파생 이력 추적

    Args:
        spinoffs: generate_spinoffs()의 결과 리스트
        date_str: 추가일 (기본: 오늘)
        dedup: True 이면 Published + 기존 Backlog 제목과 겹치는 항목을 자동 제거
    """
    if dedup and spinoffs:
        spinoffs, dropped = filter_duplicate_spinoffs(spinoffs)
        if dropped:
            print(f"[Backlog] 중복 감지 — 스핀오프 {len(dropped)}개 제외")
            for d in dropped:
                print(f"   - {d.get('title', '')}")

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


# ── Dedup / 크기 관리 ────────────────────────────────────────────────────────

_TITLE_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "vs", "vs.", "은", "는", "이", "가", "을", "를", "의", "에", "에서", "으로",
    "그", "이것", "저것", "위한", "통한", "기반", "활용", "사용", "대한", "및", "및",
}


def _normalize_title_tokens(title: str) -> set[str]:
    """제목을 소문자 키워드 집합으로 변환합니다. 중복 판정의 키로 사용됩니다."""
    title = title.lower()
    raw = re.findall(r"[\w가-힣]+", title, flags=re.UNICODE)
    tokens = set()
    for t in raw:
        if len(t) < 2:
            continue
        if t in _TITLE_STOPWORDS:
            continue
        if t.isdigit():
            continue
        tokens.add(t)
    return tokens


def is_duplicate_title(new_title: str, existing_titles: list[str],
                        threshold: float = 0.55) -> bool:
    """키워드 Jaccard 유사도 기반 중복 판정.

    임계값 기본 0.55 는 "FlashAttention-3 vs DeepGEMM ..." 계열의
    거의-같은-제목을 동일 주제로 잡고, 카테고리만 겹치는 별개 주제는
    통과시키는 수준으로 튜닝되어 있습니다.
    """
    new_kw = _normalize_title_tokens(new_title)
    if not new_kw:
        return False
    for existing in existing_titles:
        ex_kw = _normalize_title_tokens(existing)
        if not ex_kw:
            continue
        inter = len(new_kw & ex_kw)
        union = len(new_kw | ex_kw)
        if union and inter / union >= threshold:
            return True
    return False


def load_backlog_items() -> list[dict]:
    """📋 [Backlog] 섹션의 항목을 리스트로 반환합니다.

    Returns:
        [{"title", "category", "tags", "added_date", "raw"}, ...]

        시드로 등록된 항목(추가일 미기록)은 added_date 가 빈 문자열.
    """
    try:
        content = _read_backlog()
    except FileNotFoundError:
        return []

    m = re.search(
        r'## 📋 \[Backlog\] 작성 대기 중인 주제\n(.*?)(?=\n## |\Z)',
        content, re.DOTALL,
    )
    if not m:
        return []

    section = m.group(1)
    items: list[dict] = []
    current: Optional[dict] = None

    for line in section.split("\n"):
        stripped = line.strip()
        if stripped.startswith("* "):
            if current is not None:
                items.append(current)
            title_m = re.search(r'\*\*(.+?)\*\*', stripped)
            cat_m = re.search(r'`\[(\w+)\]`', stripped)
            tags = re.findall(r'#([\w\-]+)', stripped)
            current = {
                "title": title_m.group(1).strip() if title_m else stripped.lstrip("* "),
                "category": cat_m.group(1) if cat_m else "",
                "tags": tags,
                "added_date": "",
                "raw": stripped,
            }
        elif current is not None and "추가:" in stripped:
            date_m = re.search(r'추가:\s*(\d{4}-\d{2}-\d{2})', stripped)
            if date_m:
                current["added_date"] = date_m.group(1)

    if current is not None:
        items.append(current)
    return items


def count_backlog_items() -> int:
    """📋 Backlog 섹션의 항목 개수. 적응형 스핀오프 개수 결정에 사용됩니다."""
    return len(load_backlog_items())


def filter_duplicate_spinoffs(spinoffs: list[dict]) -> tuple[list[dict], list[dict]]:
    """스핀오프 중 Published 또는 기존 Backlog 제목과 겹치는 것을 제외합니다.

    Returns:
        (kept, dropped) — kept 는 백로그에 추가할 최종 리스트,
                           dropped 는 중복으로 판단되어 버려진 항목.
    """
    existing_titles: list[str] = [it["title"] for it in load_backlog_items()]
    existing_titles += [it["title"] for it in load_published_history(limit=100)]

    kept: list[dict] = []
    dropped: list[dict] = []
    for s in spinoffs:
        title = (s.get("title") or "").strip()
        if not title:
            dropped.append(s)
            continue
        if is_duplicate_title(title, existing_titles):
            dropped.append(s)
        else:
            kept.append(s)
            existing_titles.append(title)  # 같은 배치 내부 중복도 흡수
    return kept, dropped


def recommended_spinoff_count(backlog_size: Optional[int] = None) -> int:
    """현재 백로그 크기에 따른 권장 스핀오프 개수를 반환합니다.

    파이프라인 기하급수 증가를 막기 위한 적응형 cap:
        < 5         → 3 개
        5  ~ 9      → 2 개
        10 ~ 14     → 1 개
        >= 15       → 0 개 (백로그를 먼저 소비)
    """
    if backlog_size is None:
        backlog_size = count_backlog_items()
    if backlog_size >= 15:
        return 0
    if backlog_size >= 10:
        return 1
    if backlog_size >= 5:
        return 2
    return 3


def prune_old_spinoffs(days: int = 30) -> list[str]:
    """📋 Backlog 에 추가된 지 `days` 일이 지난 항목을 제거합니다.

    - 추가일이 기록된 항목(스핀오프 자동 등록분)만 대상.
    - 수동 시드 항목(추가일 없음)은 제거하지 않습니다.

    Returns:
        제거된 항목의 title 리스트.
    """
    try:
        content = _read_backlog()
    except FileNotFoundError:
        return []

    m = re.search(
        r'(## 📋 \[Backlog\] 작성 대기 중인 주제\n)(.*?)(\n## )',
        content, re.DOTALL,
    )
    if not m:
        return []

    header, body, tail = m.group(1), m.group(2), m.group(3)
    cutoff = date.today() - timedelta(days=days)

    blocks = re.split(r'(?=^\* \*\*)', body, flags=re.MULTILINE)
    kept_blocks: list[str] = []
    removed_titles: list[str] = []

    for block in blocks:
        if not block.strip():
            kept_blocks.append(block)
            continue

        date_m = re.search(r'추가:\s*(\d{4}-\d{2}-\d{2})', block)
        if date_m:
            try:
                added = date.fromisoformat(date_m.group(1))
            except ValueError:
                kept_blocks.append(block)
                continue
            if added < cutoff:
                title_m = re.search(r'\*\*(.+?)\*\*', block)
                removed_titles.append(title_m.group(1) if title_m else block[:80])
                continue
        kept_blocks.append(block)

    new_body = "".join(kept_blocks)
    new_content = (
        content[: m.start()]
        + header + new_body + tail
        + content[m.end():]
    )
    if removed_titles:
        _write_backlog(new_content)
        print(f"[Backlog] prune: {days}일 초과 항목 {len(removed_titles)}개 제거")
        for t in removed_titles:
            print(f"   - {t}")
    return removed_titles
