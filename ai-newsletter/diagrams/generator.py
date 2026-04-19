"""
SVG Diagram Generator
CO-STAR 스펙에 맞게 minimal infographic 스타일 SVG 다이어그램을 생성합니다.
- 메인 컬러: #D75656 (레드), #EEEEEE (라이트 그레이)
- 모든 텍스트는 영어
- SVG 생성 후 cairosvg로 PNG 변환 (scale=2)
"""
import os
import sys
from xml.sax.saxutils import escape as xml_escape
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    DIAGRAM_COLOR_PRIMARY, DIAGRAM_COLOR_SECONDARY,
    DIAGRAM_COLOR_TEXT, DIAGRAM_COLOR_ACCENT
)

# 색상 상수
C_RED = DIAGRAM_COLOR_PRIMARY       # #D75656
C_GRAY = DIAGRAM_COLOR_SECONDARY    # #EEEEEE
C_TEXT = DIAGRAM_COLOR_TEXT         # #222222
C_WHITE = DIAGRAM_COLOR_ACCENT      # #FFFFFF
C_LIGHT_RED = "#F0A0A0"
C_DARK_RED = "#B03030"


def _esc(text: str) -> str:
    """SVG 텍스트용 XML 특수문자 이스케이프."""
    return xml_escape(text)


def _wrap_text(text: str, max_chars: int = 28) -> list[str]:
    """텍스트를 지정된 길이로 줄바꿈."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text[:max_chars]]


def _svg_comparison(spec: dict, width: int = 800, height: int = 420) -> str:
    """기존 vs 신규 비교 다이어그램 SVG 생성."""
    title = spec.get("title", "Comparison")
    left_label = spec.get("left_label", "Before")
    right_label = spec.get("right_label", "After")
    left_items = spec.get("left_items", [])
    right_items = spec.get("right_items", [])

    max_items = max(len(left_items), len(right_items), 1)
    item_height = 36
    box_height = max(200, 80 + max_items * item_height)
    height = box_height + 120
    col_w = (width - 120) // 2
    left_x = 40
    right_x = left_x + col_w + 40

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="Inter, Arial, sans-serif">']

    # 배경
    lines.append(f'<rect width="{width}" height="{height}" fill="{C_WHITE}" rx="12"/>')

    # 제목
    lines.append(f'<text x="{width//2}" y="38" text-anchor="middle" '
                 f'font-size="18" font-weight="700" fill="{C_TEXT}">{_esc(title)}</text>')
    lines.append(f'<line x1="60" y1="50" x2="{width-60}" y2="50" stroke="{C_GRAY}" stroke-width="1.5"/>')

    # 좌측 박스 (기존)
    lines.append(f'<rect x="{left_x}" y="65" width="{col_w}" height="{box_height}" '
                 f'fill="{C_GRAY}" rx="8"/>')
    lines.append(f'<rect x="{left_x}" y="65" width="{col_w}" height="40" '
                 f'fill="#BBBBBB" rx="8"/>')
    lines.append(f'<rect x="{left_x}" y="85" width="{col_w}" height="20" fill="#BBBBBB"/>')
    lines.append(f'<text x="{left_x + col_w//2}" y="91" text-anchor="middle" '
                 f'font-size="14" font-weight="700" fill="{C_TEXT}">{_esc(left_label)}</text>')

    for i, item in enumerate(left_items):
        y = 65 + 52 + i * item_height
        # 불릿
        lines.append(f'<circle cx="{left_x + 18}" cy="{y + 10}" r="4" fill="#999999"/>')
        for j, line in enumerate(_wrap_text(item, 30)):
            lines.append(f'<text x="{left_x + 30}" y="{y + 14 + j * 16}" '
                         f'font-size="12" fill="{C_TEXT}">{_esc(line)}</text>')

    # 화살표 (중앙)
    arr_x = left_x + col_w + 20
    arr_y = height // 2
    lines.append(f'<circle cx="{arr_x}" cy="{arr_y}" r="16" fill="{C_RED}"/>')
    lines.append(f'<text x="{arr_x}" y="{arr_y + 6}" text-anchor="middle" '
                 f'font-size="18" font-weight="700" fill="{C_WHITE}">→</text>')

    # 우측 박스 (신규)
    lines.append(f'<rect x="{right_x}" y="65" width="{col_w}" height="{box_height}" '
                 f'fill="{C_GRAY}" rx="8" stroke="{C_RED}" stroke-width="2"/>')
    lines.append(f'<rect x="{right_x}" y="65" width="{col_w}" height="40" '
                 f'fill="{C_RED}" rx="8"/>')
    lines.append(f'<rect x="{right_x}" y="85" width="{col_w}" height="20" fill="{C_RED}"/>')
    lines.append(f'<text x="{right_x + col_w//2}" y="91" text-anchor="middle" '
                 f'font-size="14" font-weight="700" fill="{C_WHITE}">{_esc(right_label)}</text>')

    for i, item in enumerate(right_items):
        y = 65 + 52 + i * item_height
        lines.append(f'<circle cx="{right_x + 18}" cy="{y + 10}" r="4" fill="{C_RED}"/>')
        for j, line in enumerate(_wrap_text(item, 30)):
            lines.append(f'<text x="{right_x + 30}" y="{y + 14 + j * 16}" '
                         f'font-size="12" fill="{C_TEXT}">{_esc(line)}</text>')

    # 하단 레이블
    lines.append(f'<text x="{left_x + col_w//2}" y="{height - 12}" text-anchor="middle" '
                 f'font-size="11" fill="#999999">Traditional Approach</text>')
    lines.append(f'<text x="{right_x + col_w//2}" y="{height - 12}" text-anchor="middle" '
                 f'font-size="11" fill="{C_RED}" font-weight="600">New Approach</text>')

    lines.append('</svg>')
    return "\n".join(lines)


def _svg_flow(spec: dict, width: int = 800) -> str:
    """워크플로우 플로우 다이어그램 SVG 생성."""
    title = spec.get("title", "Workflow")
    steps = spec.get("steps", [])
    if not steps:
        steps = ["Step 1", "Step 2", "Step 3"]

    step_w = 140
    step_h = 60
    padding = 20
    arrow_w = 30
    total_w = len(steps) * (step_w + arrow_w) - arrow_w + padding * 2
    width = max(width, total_w)
    height = 160

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="Inter, Arial, sans-serif">']
    lines.append(f'<rect width="{width}" height="{height}" fill="{C_WHITE}" rx="12"/>')
    lines.append(f'<text x="{width//2}" y="32" text-anchor="middle" '
                 f'font-size="16" font-weight="700" fill="{C_TEXT}">{_esc(title)}</text>')

    start_x = padding
    y = 55

    for i, step in enumerate(steps):
        x = start_x + i * (step_w + arrow_w)
        color = C_RED if i % 2 == 0 else C_GRAY
        text_color = C_WHITE if i % 2 == 0 else C_TEXT
        border = f'stroke="{C_RED}" stroke-width="2"' if i % 2 != 0 else ""

        lines.append(f'<rect x="{x}" y="{y}" width="{step_w}" height="{step_h}" '
                     f'fill="{color}" rx="6" {border}/>')

        # 단계 번호
        lines.append(f'<text x="{x + 10}" y="{y + 16}" '
                     f'font-size="10" font-weight="700" fill="{C_RED if i % 2 != 0 else C_LIGHT_RED}">STEP {i+1}</text>')

        # 텍스트 줄바꿈
        wrapped = _wrap_text(step, 18)
        line_y = y + 30
        for line in wrapped[:2]:
            lines.append(f'<text x="{x + step_w//2}" y="{line_y}" text-anchor="middle" '
                         f'font-size="12" font-weight="600" fill="{text_color}">{_esc(line)}</text>')
            line_y += 15

        # 화살표
        if i < len(steps) - 1:
            ax = x + step_w + 5
            ay = y + step_h // 2
            lines.append(f'<line x1="{ax}" y1="{ay}" x2="{ax + arrow_w - 10}" y2="{ay}" '
                         f'stroke="{C_RED}" stroke-width="2" marker-end="url(#arr)"/>')

    # 화살표 마커 정의
    lines.insert(1, f'''<defs>
  <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
    <path d="M0,0 L0,6 L8,3 z" fill="{C_RED}"/>
  </marker>
</defs>''')

    lines.append('</svg>')
    return "\n".join(lines)


def generate_diagrams(diagram_specs: list[dict], output_dir: str, slug: str) -> list[str]:
    """
    diagram_specs에 따라 SVG → PNG 다이어그램을 생성하고 PNG 경로 목록을 반환합니다.

    Args:
        diagram_specs: generator.py에서 생성된 스펙 리스트
        output_dir: 저장 디렉토리
        slug: 파일명 접두사 (날짜+제목 슬러그)

    Returns:
        생성된 PNG 파일 경로 리스트
    """
    import cairosvg

    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for i, spec in enumerate(diagram_specs, 1):
        diagram_type = spec.get("type", "comparison")
        svg_filename = f"{slug}_diagram_{i}.svg"
        png_filename = f"{slug}_diagram_{i}.png"
        svg_filepath = os.path.join(output_dir, svg_filename)
        png_filepath = os.path.join(output_dir, png_filename)

        if diagram_type == "comparison":
            svg_content = _svg_comparison(spec)
        elif diagram_type == "flow":
            svg_content = _svg_flow(spec)
        else:
            svg_content = _svg_comparison(spec)

        with open(svg_filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)

        cairosvg.svg2png(url=svg_filepath, write_to=png_filepath, scale=2)

        paths.append(png_filepath)
        print(f"[Diagrams] 생성 완료: {svg_filename} → {png_filename}")

    return paths
