"""
Newsletter File Writer
생성된 콘텐츠를 MD 및 HTML 파일로 저장합니다.

다이어그램 인라인 배치 전략
──────────────────────────
각 diagram_spec의 title/description 키워드를 본문 섹션과 비교해
가장 관련성 높은 ## 섹션 바로 뒤에 이미지를 삽입합니다.
관련 섹션을 찾지 못하면 본문 맨 끝에 fallback 배치합니다.
"""
import os
import re
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import OUTPUT_DIR


# ── 슬러그 ────────────────────────────────────────────────────────────────────

def _slugify(text: str, max_len: int = 40) -> str:
    """제목을 파일명용 슬러그로 변환 (ASCII only, URL-safe)."""
    text = text.lower()
    text = text.encode('ascii', errors='ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text[:max_len]


# ── 다이어그램 인라인 배치 ────────────────────────────────────────────────────

# 검색어 추출 시 제외할 일반 단어
_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for',
    'is', 'are', 'was', 'be', 'with', 'vs', 'vs.', 'comparison', 'flow',
    'overview', 'diagram', 'step', 'steps',
}


def _keywords(spec: dict) -> set[str]:
    """diagram_spec에서 의미 있는 키워드를 추출합니다."""
    raw = " ".join([
        spec.get("title", ""),
        spec.get("description", ""),
        spec.get("left_label", ""),
        spec.get("right_label", ""),
        " ".join(spec.get("steps", [])),
        " ".join(spec.get("left_items", [])),
        " ".join(spec.get("right_items", [])),
    ])
    tokens = re.findall(r'[a-zA-Z가-힣]{2,}', raw.lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _section_score(section_text: str, kw: set[str]) -> int:
    """섹션 텍스트와 키워드 집합의 겹치는 단어 수를 반환합니다."""
    words = set(re.findall(r'[a-zA-Z가-힣]{2,}', section_text.lower()))
    return len(words & kw)


def _split_into_sections(article: str) -> list[str]:
    """본문 내부 서브섹션 헤더 기준으로 섹션을 분리합니다 (헤더 포함).

    CO-STAR 5섹션 포맷에서 article 내부는 ### 서브섹션만 허용되므로
    여기서는 ### 단위로 섹션을 자른다. (save_newsletter는 이 함수 호출 전에
    article의 ##를 ###로 강등해두므로 일관성이 유지된다.)
    """
    parts = re.split(r'(?=^### )', article, flags=re.MULTILINE)
    return [p for p in parts if p.strip()]


def _embed_diagrams_md(article: str, diagram_paths: list[str],
                       diagram_specs: list[dict], output_dir: str) -> str:
    """
    각 다이어그램을 가장 관련성 높은 ## 섹션 바로 뒤에 인라인 삽입합니다.

    - 동점이면 먼저 나오는 섹션에 배치
    - 점수가 0이면 (관련 섹션 없음) 본문 맨 끝에 fallback
    - 같은 섹션에 여러 다이어그램이 배치될 수 있음
    """
    if not diagram_paths:
        return article

    sections = _split_into_sections(article)
    if not sections:
        return article

    # {section_idx: [md_img_tag, ...]} — 섹션별 삽입할 이미지 누적
    insertions: dict[int, list[str]] = {}

    fallbacks: list[str] = []  # 관련 섹션 없는 이미지

    for path, spec in zip(diagram_paths, diagram_specs):
        rel = os.path.relpath(path, output_dir)
        alt = spec.get("title", os.path.basename(path))
        img_md = f"\n![{alt}]({rel})\n"

        kw = _keywords(spec)
        scores = [_section_score(s, kw) for s in sections]
        best_score = max(scores)

        if best_score == 0:
            fallbacks.append(img_md)
        else:
            best_idx = scores.index(best_score)
            insertions.setdefault(best_idx, []).append(img_md)

    # 삽입 적용 — 각 섹션 끝에 관련 이미지를 붙임
    result_sections = []
    for i, sec in enumerate(sections):
        result_sections.append(sec.rstrip())
        if i in insertions:
            for img in insertions[i]:
                result_sections.append(img)

    article_with_inline = "\n\n".join(result_sections)

    # fallback — 관련 섹션 없는 이미지는 본문 끝에 추가
    if fallbacks:
        article_with_inline += "\n\n## Diagrams\n" + "".join(fallbacks)

    return article_with_inline


def _embed_diagrams_html(article_html: str, diagram_paths: list[str],
                         diagram_specs: list[dict], output_dir: str) -> str:
    """
    HTML 본문에도 동일한 섹션 매핑 로직으로 이미지를 인라인 삽입합니다.
    <h2> 태그 기준으로 섹션을 분리합니다.
    """
    if not diagram_paths:
        return article_html

    # <h2>...</h2> 기준 분리
    parts = re.split(r'(?=<h2>)', article_html)
    if len(parts) <= 1:
        return article_html + "".join(
            f'<figure style="margin:24px 0;">'
            f'<img src="{os.path.relpath(p, output_dir)}" '
            f'alt="{s.get("title","diagram")}" style="max-width:100%;">'
            f'<figcaption style="font-size:13px;color:#666;margin-top:6px;">'
            f'{s.get("title","")}</figcaption></figure>'
            for p, s in zip(diagram_paths, diagram_specs)
        )

    insertions: dict[int, list[str]] = {}
    fallbacks: list[str] = []

    for path, spec in zip(diagram_paths, diagram_specs):
        rel = os.path.relpath(path, output_dir)
        alt = spec.get("title", "diagram")
        img_html = (
            f'<figure style="margin:24px 0;">'
            f'<img src="{rel}" alt="{alt}" style="max-width:100%;border-radius:4px;">'
            f'<figcaption style="font-size:13px;color:#666;margin-top:6px;">{alt}</figcaption>'
            f'</figure>'
        )

        kw = _keywords(spec)
        # HTML 태그 제거 후 점수 계산
        plain_parts = [re.sub(r'<[^>]+>', ' ', p) for p in parts]
        scores = [_section_score(p, kw) for p in plain_parts]
        best_score = max(scores)

        if best_score == 0:
            fallbacks.append(img_html)
        else:
            best_idx = scores.index(best_score)
            insertions.setdefault(best_idx, []).append(img_html)

    result_parts = []
    for i, part in enumerate(parts):
        result_parts.append(part)
        if i in insertions:
            result_parts.extend(insertions[i])

    html = "".join(result_parts)

    if fallbacks:
        html += '<section class="diagrams"><h2>Diagrams</h2>' + "".join(fallbacks) + "</section>"

    return html


# ── 저장 ─────────────────────────────────────────────────────────────────────

def save_newsletter(
    content: dict,
    topic: dict,
    diagram_paths: list[str],
    date_str: str = None,
    output_dir: str = None,
) -> dict:
    """
    뉴스레터 콘텐츠를 MD + HTML 파일로 저장합니다.
    다이어그램은 관련 섹션 바로 뒤에 인라인 배치됩니다.

    Args:
        content: generate_newsletter()의 결과
        topic: 선택된 주제 dict (URL, 출처 등 메타데이터)
        diagram_paths: SVG 파일 경로 목록
        date_str: 날짜 문자열 (기본: 오늘)
        output_dir: 저장 디렉토리

    Returns:
        {"md_path": ..., "html_path": ..., "slug": ..., "output_dir": ...}
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    title = content.get("title", topic.get("title", "untitled"))
    slug = f"{date_str}-{_slugify(title)}"

    issue_dir = output_dir if output_dir else os.path.join(OUTPUT_DIR, slug)
    os.makedirs(issue_dir, exist_ok=True)

    summary = content.get("summary", "")
    article = content.get("article", "")
    diagram_specs = content.get("diagram_specs", [])
    source_url = topic.get("url", "")

    # ── 본문 내부 ## 헤더를 ###로 강등 (외부 `## 본문`과 레벨 분리, CO-STAR 규칙) ─
    # 강등을 먼저 수행해야 _embed_diagrams_md가 ### 서브섹션 경계를 정확히 인식한다.
    article = re.sub(r'^## ', '### ', article, flags=re.MULTILINE)

    # ── 다이어그램 인라인 배치 (### 서브섹션 경계 기준) ──────────────────────
    article_with_diagrams = _embed_diagrams_md(article, diagram_paths, diagram_specs, issue_dir)

    # ── 배치 로그 ─────────────────────────────────────────────────────────────
    if diagram_paths and diagram_specs:
        print(f"[Writer] 다이어그램 배치:")
        sections = _split_into_sections(article)
        for path, spec in zip(diagram_paths, diagram_specs):
            kw = _keywords(spec)
            scores = [_section_score(s, kw) for s in sections]
            best_score = max(scores) if scores else 0
            if best_score > 0:
                best_sec = sections[scores.index(best_score)]
                sec_header = best_sec.splitlines()[0].strip().lstrip('#').strip()[:40]
                print(f"  [{spec.get('title','?')[:30]}] → '{sec_header}' (score={best_score})")
            else:
                print(f"  [{spec.get('title','?')[:30]}] → fallback (맨 끝)")

    # ── Markdown (CO-STAR 강제 5섹션 포맷) ───────────────────────────────────
    # 1. 제목  2. 작성일  3. Summary  4. 본문  5. References
    md_lines = [
        f"# {title}",
        "",
        date_str,
        "",
        "## Summary",
        "",
        summary,
        "",
        "## 본문",
        "",
        article_with_diagrams,
        "",
        "## References",
        "",
        f"- [{source_url}]({source_url})" if source_url else "- (출처 URL 없음)",
    ]
    md_content = "\n".join(md_lines) + "\n"
    md_path = os.path.join(issue_dir, "newsletter.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # ── HTML (CO-STAR 강제 5섹션 포맷) ───────────────────────────────────────

    def md_to_html(text: str) -> str:
        import html as _html

        # ── 1) 코드 블록을 placeholder 로 먼저 추출 (빈 줄 포함 내부 보호) ─────
        code_blocks: list[str] = []

        def _stash_code(m: re.Match) -> str:
            lang = (m.group(1) or "").strip()
            body = m.group(2)
            # HTML 이스케이프 — highlight.js 가 안전하게 처리할 수 있도록
            escaped = _html.escape(body)
            cls = f' class="language-{lang}"' if lang else ""
            code_blocks.append(f"<pre><code{cls}>{escaped}</code></pre>")
            return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

        text = re.sub(r'```(\w+)?\n(.*?)```', _stash_code, text, flags=re.DOTALL)

        # ── 2) 인라인 코드 / 헤더 / 강조 / 이미지 / 리스트 ────────────────
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<figure><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>',
            text
        )
        text = re.sub(r'(?m)^- (.+)$', r'<li>\1</li>', text)

        # ── 3) 단락 분리 (코드 블록은 이미 placeholder 라 안전) ─────────────
        paragraphs = text.split("\n\n")
        result = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith("\x00CODEBLOCK"):
                result.append(p)  # placeholder 그대로 보존
            elif p.startswith("<li>"):
                result.append(f"<ul>{p}</ul>")
            elif p.startswith(("<h", "<figure", "<ul", "<ol")):
                result.append(p)
            else:
                result.append(f"<p>{p.replace(chr(10), '<br>')}</p>")

        html = "\n".join(result)

        # ── 4) placeholder 복원 ───────────────────────────────────────────
        def _restore(m: re.Match) -> str:
            return code_blocks[int(m.group(1))]

        html = re.sub(r'\x00CODEBLOCK(\d+)\x00', _restore, html)
        return html

    article_html = md_to_html(article_with_diagrams)

    # 5번째 섹션: References — URL을 텍스트와 링크 양쪽에 그대로 노출
    references_html = (
        f'<ul><li><a href="{source_url}" target="_blank" rel="noopener">{source_url}</a></li></ul>'
        if source_url else '<p>(출처 URL 없음)</p>'
    )

    # CSS는 외부 파일로 분리 — 모든 이슈 HTML이 outputs/style.css를 참조
    # 이슈 폴더 깊이가 1단계이므로 상대경로는 항상 ../style.css
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <!-- highlight.js: 코드 블록 신택스 하이라이팅 (CDN) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/styles/github-dark.min.css">
  <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/highlight.min.js"></script>
  <script>document.addEventListener('DOMContentLoaded', () => hljs.highlightAll());</script>
</head>
<body>
  <h1 class="title">{title}</h1>
  <div class="date">{date_str}</div>

  <section class="summary">
    <h2>Summary</h2>
    {md_to_html(summary)}
  </section>

  <section class="article">
    {article_html}
  </section>

  <section class="references">
    <h2>References</h2>
    {references_html}
  </section>
</body>
</html>"""

    html_path = os.path.join(issue_dir, "newsletter.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Writer] 저장 완료:")
    print(f"  MD  → {md_path}")
    print(f"  HTML→ {html_path}")

    return {
        "md_path": md_path,
        "html_path": html_path,
        "slug": slug,
        "output_dir": issue_dir
    }
