"""
Newsletter Content Validator
=============================
생성된 콘텐츠와 저장된 파일의 품질을 검증합니다.

검증 단계
─────────
Phase 1 — Content (generate_newsletter 반환 직후)
  1. 본문 최소 길이 (500자)
  2. 요약 존재 여부
  3. 문장 완결성 — 마지막 문자가 문장 종결 부호인지
  4. 섹션 구조 — ## 헤더 최소 2개
  5. 열린 코드블록 감지 (``` 홀수 개)

Phase 2 — File (save_newsletter 반환 직후)
  6. MD 파일 크기 ≥ 본문 길이 × 0.8
  7. MD 파일 내 본문 핵심 구절 포함 여부
  8. HTML 파일 </html> 닫힘 태그 확인
  9. HTML 파일 크기 합리성 (최소 2 KB)
  9a. 강제 5섹션 포맷 준수 (제목, 작성일, Summary, 본문, References)
  9b. 금지 메타라인 부재 (Tags, 📅/📌 이모지 메타)

Phase 3 — Image Placement (save_newsletter 반환 직후)
  10. 참조된 이미지 파일 실제 존재 여부
  11. 이미지 참조 수 == diagram_paths 수
  12. 각 이미지가 관련 섹션 ±2 이내에 배치됐는지 (키워드 근접도)
  13. 전체 이미지가 fallback 섹션(## Diagrams)에만 몰리지 않았는지
"""

import os
import re
from dataclasses import dataclass, field


# ── 결과 타입 ──────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    passed: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def fail(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def print_report(self, label: str = ""):
        prefix = f"[Validate{' ' + label if label else ''}]"
        if self.passed and not self.warnings:
            print(f"{prefix} ✅ 모든 검증 통과")
        else:
            status = "✅ PASS (경고 있음)" if self.passed else "❌ FAIL"
            print(f"{prefix} {status}")
            for w in self.warnings:
                print(f"  ⚠️  {w}")
            for e in self.errors:
                print(f"  ❌ {e}")


# ── Phase 1: 콘텐츠 검증 ──────────────────────────────────────────────────────

ARTICLE_MIN_CHARS = 500          # 이 미만이면 truncation 의심
ARTICLE_WARN_CHARS = 800         # 이 미만이면 경고 (짧은 글)
SUMMARY_MIN_CHARS = 50
MIN_SECTION_HEADERS = 2          # ## 헤더 최소 개수

# ── 톤 린트 (CO-STAR Tone 규칙) ──────────────────────────────────────────────
# 문장 끝이나 공백 경계에서 등장하면 경고 — 평서체 "~입니다/~합니다" 외 어미
_DISALLOWED_ENDINGS = [
    "하죠", "해요", "네요", "거든요", "답니다", "더라고요", "군요",
    "했죠", "되죠", "이죠", "였죠", "됐죠",
]
# 과장 / 감정 수식어 — 본문 전체에서 등장 시 경고
_DISALLOWED_HYPE = [
    "놀랍게도", "혁신적인", "엄청난", "충격적인", "획기적인", "드디어", "마침내",
    "압도적인", "굉장한", "어마어마한", "정말", "진짜",
    "매우 ", "아주 ", "무척 ", "몹시 ",
]


def _lint_tone(text: str) -> list[str]:
    """본문에서 금지된 어미·수식어 사용 사례를 찾아 경고 메시지 리스트로 반환."""
    violations: list[str] = []
    # 어미 — "어미." / "어미," / "어미\n" / "어미!" 패턴으로 한정 (단어 중간 오탐 방지)
    for ending in _DISALLOWED_ENDINGS:
        pattern = re.escape(ending) + r'(?=[.,!?\s\n\"\)\]])'
        matches = re.findall(pattern, text)
        if matches:
            violations.append(f"금지 어미 '{ending}' {len(matches)}회 사용")
    # 과장 표현
    for word in _DISALLOWED_HYPE:
        count = text.count(word)
        if count:
            violations.append(f"과장 표현 '{word.strip()}' {count}회 사용")
    # 느낌표 — 마크다운 이미지 `![...](...)` 문법은 제외
    stripped = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)  # remove ![alt](url)
    bang_count = stripped.count("!")
    if bang_count:
        violations.append(f"느낌표(!) {bang_count}회 사용")
    return violations


def validate_content(content: dict) -> ValidationResult:
    """
    generate_newsletter() 반환값을 검증합니다.

    Args:
        content: {"title", "summary", "article", "diagram_specs", "tags"}

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    title   = content.get("title", "")
    summary = content.get("summary", "")
    article = content.get("article", "")
    tags    = content.get("tags", [])

    # ── 1. 제목 ──────────────────────────────────────────────────────────────
    if not title.strip():
        result.fail("제목(title)이 비어 있습니다.")

    # ── 2. 요약 존재 여부 ────────────────────────────────────────────────────
    if len(summary) < SUMMARY_MIN_CHARS:
        result.fail(f"요약(summary)이 너무 짧습니다: {len(summary)}자 (최소 {SUMMARY_MIN_CHARS}자)")

    # ── 3. 본문 최소 길이 ────────────────────────────────────────────────────
    art_len = len(article)
    if art_len < ARTICLE_MIN_CHARS:
        result.fail(
            f"본문(article)이 너무 짧습니다: {art_len}자 (최소 {ARTICLE_MIN_CHARS}자). "
            "Claude API 응답이 잘렸을 가능성이 있습니다."
        )
    elif art_len < ARTICLE_WARN_CHARS:
        result.warn(f"본문이 짧습니다: {art_len}자 (권장 {ARTICLE_WARN_CHARS}자 이상)")

    # ── 4. 문장 완결성 ───────────────────────────────────────────────────────
    stripped = article.rstrip()
    if stripped:
        last_char = stripped[-1]
        # 코드블록, 따옴표, 닫는 괄호, 마침표류로 끝나야 정상
        valid_endings = set('.!?`"\'』」）)』]>』}')
        if last_char not in valid_endings:
            result.fail(
                f"본문 마지막 문자가 '{last_char}'로 끝납니다. "
                "문장이 중간에 잘렸을 가능성이 있습니다."
            )

    # ── 5. 섹션 구조 ─────────────────────────────────────────────────────────
    headers = re.findall(r'^##+ .+', article, flags=re.MULTILINE)
    if len(headers) < MIN_SECTION_HEADERS:
        result.warn(
            f"## 헤더가 {len(headers)}개입니다 (권장 {MIN_SECTION_HEADERS}개 이상). "
            "본문 구조가 빈약하거나 일부 누락됐을 수 있습니다."
        )

    # ── 6. 열린 코드블록 감지 ────────────────────────────────────────────────
    backtick_count = article.count("```")
    if backtick_count % 2 != 0:
        result.fail(
            f"코드블록(```) 개수가 홀수({backtick_count})입니다. "
            "열린 코드블록이 닫히지 않았거나 본문이 잘렸을 수 있습니다."
        )

    # ── 7. 태그 ──────────────────────────────────────────────────────────────
    if not tags:
        result.warn("태그(tags)가 없습니다.")

    # ── 8. 톤 린트 (CO-STAR Tone 규칙 — 경고만) ──────────────────────────────
    for v in _lint_tone(article):
        result.warn(f"[톤] {v}")
    for v in _lint_tone(summary):
        result.warn(f"[톤-요약] {v}")

    return result


# ── Phase 2: 파일 검증 ────────────────────────────────────────────────────────

MD_SIZE_RATIO_MIN = 0.7    # 저장된 MD 크기 / article 길이 최소 비율
HTML_MIN_BYTES    = 2_000  # HTML 최소 파일 크기

# CO-STAR 강제 5섹션 포맷 — 정확히 이 헤더가 이 순서로 존재해야 함
REQUIRED_SECTIONS = ["## Summary", "## 본문", "## References"]
# 금지 패턴 — 구버전 메타정보 흔적
FORBIDDEN_PATTERNS = [
    (r'\*\*Tags\*\*', "**Tags** 라인 (구 포맷의 태그 메타)"),
    (r'> 📅.*\|.*📌', "이모지 메타라인 (📅 날짜 | 📌 출처)"),
    (r'^## Deep Dive\s*$', "구버전 '## Deep Dive' 헤더 (현재는 '## 본문')"),
    (r'^\*원문 출처:', "구버전 footer 라인 (현재는 ## References 섹션)"),
]


def _check_required_format(md: str, result: ValidationResult) -> None:
    """저장된 MD가 강제 5섹션 포맷을 준수하는지 검사 (Phase 2 - 9a, 9b)."""
    # ── 9a-1. 제목: 첫 번째 비어있지 않은 줄이 H1 ──────────────────────────
    first_line = next((ln for ln in md.splitlines() if ln.strip()), "")
    if not first_line.startswith("# ") or first_line.startswith("## "):
        result.fail(f"첫 번째 요소가 H1 제목(`# `)이 아닙니다: '{first_line[:40]}'")

    # ── 9a-2. 작성일: YYYY-MM-DD 라인이 본문 상단 200자 안에 ─────────────
    head = md[:200]
    if not re.search(r'^\d{4}-\d{2}-\d{2}\s*$', head, re.MULTILINE):
        result.fail("문서 상단에 'YYYY-MM-DD' 작성일 라인을 찾을 수 없습니다.")

    # ── 9a-3. 필수 섹션 헤더 존재 + 순서 ────────────────────────────────
    positions = []
    for req in REQUIRED_SECTIONS:
        # 라인 시작 매칭
        m = re.search(rf'^{re.escape(req)}\s*$', md, re.MULTILINE)
        if not m:
            result.fail(f"필수 섹션 '{req}' 헤더를 찾을 수 없습니다.")
            positions.append(None)
        else:
            positions.append(m.start())

    valid_positions = [p for p in positions if p is not None]
    if len(valid_positions) == len(REQUIRED_SECTIONS):
        if valid_positions != sorted(valid_positions):
            result.fail(
                f"섹션 순서가 잘못되었습니다. 정상 순서: "
                f"{' → '.join(REQUIRED_SECTIONS)}"
            )

    # ── 9a-4. 최상위 ## 헤더는 정확히 3개여야 함 ────────────────────────
    top_level_headers = re.findall(r'^## (?!#)(.+)$', md, re.MULTILINE)
    if len(top_level_headers) != 3:
        # 정확히 Summary/본문/References만 있어야 함
        extras = [h for h in top_level_headers
                  if f"## {h}" not in REQUIRED_SECTIONS]
        if extras:
            result.fail(
                f"최상위 ## 헤더가 {len(top_level_headers)}개입니다 (정확히 3개 필요). "
                f"내부 소제목은 ###를 사용하세요. 비허용 헤더: {extras[:3]}"
            )

    # ── 9b. 금지 패턴 검사 ───────────────────────────────────────────────
    for pattern, label in FORBIDDEN_PATTERNS:
        if re.search(pattern, md, re.MULTILINE):
            result.fail(f"금지된 메타라인이 포함됨: {label}")


def validate_files(saved: dict, content: dict) -> ValidationResult:
    """
    save_newsletter() 반환값과 저장된 파일을 검증합니다.

    Args:
        saved:   {"md_path", "html_path", "slug", "output_dir"}
        content: generate_newsletter() 결과 (본문 비교용)

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    md_path   = saved.get("md_path", "")
    html_path = saved.get("html_path", "")
    article   = content.get("article", "")

    # ── 8. MD 파일 존재 확인 ─────────────────────────────────────────────────
    if not os.path.exists(md_path):
        result.fail(f"MD 파일이 존재하지 않습니다: {md_path}")
    else:
        md_size = os.path.getsize(md_path)
        art_len = len(article.encode("utf-8"))

        # ── 9. MD 파일 크기 비율 ─────────────────────────────────────────────
        if art_len > 0:
            ratio = md_size / art_len
            if ratio < MD_SIZE_RATIO_MIN:
                result.fail(
                    f"저장된 MD 파일 크기({md_size}B)가 본문 길이({art_len}B)의 "
                    f"{ratio:.0%}입니다 (최소 {MD_SIZE_RATIO_MIN:.0%}). "
                    "파일 저장 중 내용이 잘렸을 수 있습니다."
                )

        # ── 10. 핵심 구절 포함 여부 + 5섹션 포맷 준수 ───────────────────────
        with open(md_path, encoding="utf-8") as f:
            saved_md = f.read()

        if len(article) > 200:
            probe = article[100:130].strip()  # 본문 중간 샘플
            if probe and probe not in saved_md:
                result.fail(
                    f"저장된 MD 파일에서 본문 일부를 찾을 수 없습니다. "
                    f"탐색 구절: '{probe[:30]}...'. "
                    "저장 과정에서 내용이 손실됐을 수 있습니다."
                )

        # ── 9a, 9b. CO-STAR 강제 5섹션 포맷 검증 ───────────────────────────
        _check_required_format(saved_md, result)

    # ── 11. HTML 파일 존재 확인 ──────────────────────────────────────────────
    if not os.path.exists(html_path):
        result.fail(f"HTML 파일이 존재하지 않습니다: {html_path}")
    else:
        html_size = os.path.getsize(html_path)

        # ── 12. HTML 최소 크기 ───────────────────────────────────────────────
        if html_size < HTML_MIN_BYTES:
            result.fail(
                f"HTML 파일이 너무 작습니다: {html_size}B (최소 {HTML_MIN_BYTES}B). "
                "렌더링 오류 또는 저장 실패일 수 있습니다."
            )

        # ── 13. HTML 닫힘 태그 ───────────────────────────────────────────────
        with open(html_path, encoding="utf-8") as f:
            html_tail = f.read()[-200:]  # 마지막 200자만
        if "</html>" not in html_tail.lower():
            result.fail(
                "HTML 파일이 </html>로 끝나지 않습니다. "
                "파일이 도중에 잘렸을 수 있습니다."
            )

    return result


# ── Phase 3: 이미지 위치 검증 ────────────────────────────────────────────────

# writer.py와 동일한 stopwords (순환 import 방지를 위해 직접 정의)
_IMG_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for',
    'is', 'are', 'was', 'be', 'with', 'vs', 'vs.', 'comparison', 'flow',
    'overview', 'diagram', 'step', 'steps',
}
# 이미지가 이 섹션에 있으면 인라인 배치 실패로 간주
FALLBACK_SECTION_HEADER = "Diagrams"
# 관련 섹션과의 최대 허용 거리 (섹션 수 단위)
MAX_SECTION_DISTANCE = 2


def _img_keywords(spec: dict) -> set[str]:
    raw = " ".join([
        spec.get("title", ""),
        spec.get("description", ""),
        spec.get("left_label", ""),
        spec.get("right_label", ""),
        " ".join(spec.get("steps", [])),
    ])
    tokens = re.findall(r'[a-zA-Z가-힣]{2,}', raw.lower())
    return {t for t in tokens if t not in _IMG_STOPWORDS}


def _best_section_idx(sections: list[str], kw: set[str]) -> tuple[int, int]:
    """가장 관련성 높은 섹션 인덱스와 점수를 반환합니다."""
    best_idx, best_score = 0, 0
    for i, sec in enumerate(sections):
        words = set(re.findall(r'[a-zA-Z가-힣]{2,}', sec.lower()))
        score = len(words & kw)
        if score > best_score:
            best_score, best_idx = score, i
    return best_idx, best_score


def validate_image_placement(saved: dict, content: dict,
                              diagram_paths: list[str]) -> ValidationResult:
    """
    저장된 MD 파일 내 이미지 배치가 적절한지 검증합니다.

    Args:
        saved:         save_newsletter() 반환값
        content:       generate_newsletter() 결과 (diagram_specs 포함)
        diagram_paths: 실제 생성된 SVG 파일 경로 목록

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    md_path       = saved.get("md_path", "")
    diagram_specs = content.get("diagram_specs", [])

    if not diagram_paths:
        return result  # 다이어그램 없으면 검증 불필요

    if not os.path.exists(md_path):
        result.fail(f"MD 파일이 없어 이미지 위치 검증을 수행할 수 없습니다: {md_path}")
        return result

    with open(md_path, encoding="utf-8") as f:
        saved_md = f.read()

    # ── 10. 참조된 이미지 파일 실존 확인 ─────────────────────────────────────
    referenced_imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', saved_md)
    md_dir = os.path.dirname(md_path)
    missing = []
    for rel_path in referenced_imgs:
        abs_path = os.path.normpath(os.path.join(md_dir, rel_path))
        if not os.path.exists(abs_path):
            missing.append(rel_path)

    if missing:
        result.fail(
            f"MD에서 참조하는 이미지 파일 {len(missing)}개가 존재하지 않습니다: "
            + ", ".join(missing[:3])
        )

    # ── 11. 이미지 참조 수 일치 ──────────────────────────────────────────────
    expected = len(diagram_paths)
    actual   = len(referenced_imgs)
    if actual != expected:
        result.fail(
            f"이미지 참조 수 불일치: MD에 {actual}개 참조, 생성된 파일 {expected}개. "
            "일부 이미지가 누락됐거나 중복 삽입됐을 수 있습니다."
        )

    # ── 12. 각 이미지의 섹션 근접도 검사 ─────────────────────────────────────
    # MD 파일을 섹션(## 기준)으로 분리하고, 각 이미지가 몇 번째 섹션에 있는지 파악
    sections = re.split(r'(?=^## )', saved_md, flags=re.MULTILINE)
    sections = [s for s in sections if s.strip()]

    # 이미지별 위치 섹션 인덱스 매핑
    img_section_map: dict[str, int] = {}
    for i, sec in enumerate(sections):
        for ref in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', sec):
            img_section_map[ref] = i

    placement_issues = []
    for path, spec in zip(diagram_paths, diagram_specs):
        rel = os.path.relpath(path, md_dir)
        if rel not in img_section_map:
            continue  # 참조 자체가 없으면 check 10에서 이미 잡힘

        actual_sec_idx = img_section_map[rel]
        actual_sec_header = sections[actual_sec_idx].splitlines()[0].strip().lstrip('#').strip()

        # fallback 섹션 여부 확인
        if actual_sec_header == FALLBACK_SECTION_HEADER:
            kw = _img_keywords(spec)
            if kw:  # 키워드가 아예 없으면 fallback이 합리적
                placement_issues.append(
                    f"'{spec.get('title', '?')[:35]}' → "
                    f"관련 섹션을 찾지 못해 '{FALLBACK_SECTION_HEADER}'에 fallback 배치됨"
                )
            continue

        # 최적 섹션과의 거리 계산
        kw = _img_keywords(spec)
        if not kw:
            continue

        best_idx, best_score = _best_section_idx(sections, kw)
        if best_score == 0:
            continue  # 관련 섹션 없음 — fallback이 맞음

        distance = abs(actual_sec_idx - best_idx)
        if distance > MAX_SECTION_DISTANCE:
            best_header = sections[best_idx].splitlines()[0].strip().lstrip('#').strip()[:35]
            placement_issues.append(
                f"'{spec.get('title', '?')[:35]}' → "
                f"실제 위치: '{actual_sec_header[:30]}' / "
                f"최적 위치: '{best_header}' (거리: {distance}섹션)"
            )

    if placement_issues:
        for issue in placement_issues:
            result.warn(f"이미지 배치 부적절: {issue}")

    # ── 13. 전체 이미지 fallback 집중 여부 ───────────────────────────────────
    if referenced_imgs and all(
        img_section_map.get(ref, -1) == img_section_map.get(referenced_imgs[0], -2)
        for ref in referenced_imgs
    ):
        first_sec_idx = img_section_map.get(referenced_imgs[0])
        if first_sec_idx is not None:
            first_header = sections[first_sec_idx].splitlines()[0].strip().lstrip('#').strip()
            if first_header == FALLBACK_SECTION_HEADER:
                result.warn(
                    f"모든 이미지({len(referenced_imgs)}개)가 '{FALLBACK_SECTION_HEADER}' 섹션에만 "
                    "집중돼 있습니다. 인라인 배치가 실패했을 수 있습니다."
                )

    return result


def run_image_placement_validation(saved: dict, content: dict,
                                   diagram_paths: list[str]) -> bool:
    """이미지 위치를 검증하고 결과를 출력합니다. 실패 시 False 반환."""
    result = validate_image_placement(saved, content, diagram_paths)
    result.print_report("Image Placement")
    return result.passed


# ── 통합 실행 헬퍼 ────────────────────────────────────────────────────────────

def run_content_validation(content: dict) -> bool:
    """
    콘텐츠를 검증하고 결과를 출력합니다.
    실패 시 False 반환 (파이프라인 중단 결정은 호출자가 함).
    """
    result = validate_content(content)
    result.print_report("Content")
    return result.passed


def run_file_validation(saved: dict, content: dict) -> bool:
    """
    저장된 파일을 검증하고 결과를 출력합니다.
    실패 시 False 반환.
    """
    result = validate_files(saved, content)
    result.print_report("File")
    return result.passed
