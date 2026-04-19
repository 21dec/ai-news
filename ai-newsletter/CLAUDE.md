# CLAUDE.md — AI Newsletter 프로젝트 가이드

> 이 파일은 Claude가 이 코드베이스를 다룰 때 참고하는 컨텍스트 문서입니다.
> 새 세션이 시작될 때 이 파일을 먼저 읽고 작업을 시작하세요.

---

## 프로젝트 목적

AI 개발자·엔지니어 대상의 기술 뉴스레터를 **완전 자동화**하는 Python 파이프라인입니다.  
뉴스 수집 → Claude API 선별/생성 → SVG 다이어그램 → MD/HTML 저장 → 백로그 관리까지 한 번에 처리합니다.

---

## 핵심 파일 맵

| 파일 | 역할 | 수정 시 주의사항 |
|------|------|----------------|
| `main.py` | 전체 파이프라인 오케스트레이터 (STEP 1~8) | 단계 순서 변경 시 의존성 확인 |
| `config.py` | 전역 설정 상수 | API 키는 `.env`에서 읽음, 여기에 하드코딩 금지 |
| `crawlers/github_trending.py` | GitHub AI 레포 스크래핑 | BeautifulSoup4 사용, CSS 셀렉터 변경 주의 |
| `crawlers/arxiv.py` | ArXiv XML API 파싱 | 표준 라이브러리(urllib, xml.etree)만 사용 |
| `crawlers/reddit.py` | Reddit JSON API | 인증 불필요, User-Agent 필수 |
| `ai/selector.py` | 주제 선별 + 다양성 가드레일 | `published_history` 파라미터 필수 전달 |
| `ai/generator.py` | 요약+딥다이브 생성 | `diagram_specs` JSON 형식 변경 시 diagrams 모듈도 함께 수정 |
| `ai/spinoff.py` | 파생 주제 3개 자동 생성 | `CATEGORIES` 리스트가 `selector.py`와 공유됨 |
| `diagrams/generator.py` | SVG 인포그래픽 생성 | `comparison` / `flow` 두 타입 지원 |
| `output/writer.py` | MD + HTML 저장, `_slugify()` | HTML 은 외부 `../style.css` 참조 (인라인 `<style>` 없음) |
| `output/index_builder.py` | `outputs/index.html` 생성 + prev/next 네비 주입 | 이슈 폴더 스캔은 `YYYY-MM-DD-slug` 정규식 기반 |
| `output/backlog.py` | `NEWSLETTER_TOPICS.md` 읽기/쓰기 | 파일 경로는 `config.BACKLOG_FILE` 참조 |
| `viewer.py` | 로컬 HTTP 서버 미리보기 | 표준 라이브러리만 사용, 추가 설치 불필요 |

---

## 파이프라인 흐름 (main.py)

```
STEP 1: load_published_history()          → 다양성 가드레일용 발행 이력
STEP 2: fetch_github_trending()           → 크롤링
        fetch_arxiv()
        fetch_reddit()
STEP 3: select_best_topic(candidates,     → 발행 이력 참고 주제 선별
                          published_history)
STEP 4: generate_newsletter(topic)        → 요약 + 딥다이브 + diagram_specs
STEP 5: generate_diagrams(specs, dir)     → SVG 파일 생성
STEP 6: save_newsletter(content, topic,   → MD + HTML 저장
                        diagram_paths)
STEP 6.8: build_all(OUTPUT_DIR)            → outputs/index.html + prev/next 주입
STEP 7: update_backlog(title, url, tags)  → Published 등록
STEP 8: generate_spinoffs(content, topic) → 파생 주제 추출
        add_spinoffs_to_backlog(spinoffs) → Backlog + Spinoffs 섹션 추가
```

---

## 데이터 구조

### 크롤러 아이템 (candidates 리스트 원소)
```python
{
    "source": "GitHub Trending",  # 또는 "ArXiv", "Reddit r/MachineLearning"
    "title": str,
    "url": str,
    "description": str,           # 최대 300자
    "extra": str,                 # "⭐ 1,234 stars" 등 부가 정보
    # 소스별 추가 필드: stars, authors, score, subreddit 등
}
```

### select_best_topic() 반환값 (topic)
```python
{
    **크롤러_아이템,
    "selection_reason": str,
    "pain_point": str,
    "hook": str,                  # 한 줄 훅 문장
    "category": str,              # infra|rag|agent|... 중 하나
    "diversity_note": str,        # 다양성 가드레일 코멘트
}
```

### generate_newsletter() 반환값 (content)
```python
{
    "title": str,                 # 한국어 뉴스레터 제목
    "summary": str,               # 400자 내외 요약
    "article": str,               # 1000~3000자 딥다이브 (마크다운)
                                  # 내부 소제목은 ###부터 사용 (## 사용 시 writer가 자동 강등)
    "diagram_specs": [            # 1~3개
        {
            "type": "comparison" | "flow",
            "title": str,         # 영어
            # comparison: left_label, right_label, left_items, right_items
            # flow: steps (list[str])
        }
    ],
    "tags": list[str],            # 백로그 다양성 가드레일 전용 (출력 파일에는 노출 안 됨)
}
```

> ⚠️ **출력 파일 강제 5섹션 포맷**: `tags`는 백로그(`NEWSLETTER_TOPICS.md`)의 카테고리 추적 용도로만 사용됩니다.
> `outputs/*/newsletter.md`에는 태그·출처명·이모지 메타라인이 일절 포함되지 않습니다.
> 자세한 포맷 규칙은 `../CO-STAR.md`의 Response 섹션 참조.

### generate_spinoffs() 반환값
```python
[
    {
        "title": str,             # 한국어 주제 제목
        "description": str,       # 1-2문장 설명
        "category": str,          # 10개 카테고리 중 하나
        "tags": list[str],
        "rationale": str,         # 파생 근거
        "source_article": str,    # 원본 뉴스레터 제목
    }
]
```

### load_published_history() 반환값
```python
[
    {
        "title": str,
        "date": "YYYY-MM-DD",
        "url": str,
        "tags": list[str],        # 카테고리 태그 (다양성 가드레일에서 사용)
    }
]
```

---

## 다양성 가드레일 동작 원리

`ai/selector.py`의 `_extract_category_frequency()` 함수가 최근 4편의 카테고리 빈도를 집계합니다.  
특정 카테고리가 2회 이상 등장하면 Claude 프롬프트에 `⚠️ 편중 경고`가 자동 삽입됩니다.

```python
# 예시: infra가 최근 4편 중 2번 → 경고 추가
overused = ["infra"]
# 프롬프트에 삽입: "⚠️ #infra 카테고리가 2회 이상 등장했습니다. 최대한 피해주세요."
```

지원 카테고리 10개 (`ai/spinoff.py`의 `CATEGORIES`와 공유):
`infra`, `framework`, `agent`, `rag`, `training`, `evaluation`, `multimodal`, `tooling`, `architecture`, `security`

---

## 백로그 파일 위치 및 구조

```
경로: ../NEWSLETTER_TOPICS.md  (config.BACKLOG_FILE)
     = ai-newsletter 폴더의 상위 폴더
```

`output/backlog.py`가 이 파일을 관리합니다. 섹션 파싱은 정규식 기반이므로 **헤더 텍스트를 임의로 변경하면 파싱이 깨집니다**.

```markdown
## 📋 [Backlog] 작성 대기 중인 주제    ← 이 텍스트 변경 금지
## ✍️ [In Progress] 작성 중            ← 이 텍스트 변경 금지
## ✅ [Published] 발행 완료            ← 이 텍스트 변경 금지
## 💡 [New Ideas / Spinoffs]           ← 이 텍스트 변경 금지
```

---

## 출력 파일 구조

```
outputs/                                       ← Render.com static publish root
├── style.css                                  ← 전역 스타일시트 (브랜드 팔레트)
├── index.html                                 ← 이슈 목록 페이지 (자동 생성)
└── 2025-01-15-vllm-pagedattention-/
    ├── newsletter.md       ← 마크다운 원문 (강제 5섹션 포맷)
    ├── newsletter.html     ← 브라우저 미리보기용 HTML
    │                        (../style.css 링크 + 하단 prev/next 네비 주입)
    ├── *_diagram_1.svg     ← comparison 다이어그램
    └── *_diagram_2.svg     ← flow 다이어그램
```

### 스타일 / 네비게이션 아키텍처

- **CSS 분리**: 모든 HTML 은 `outputs/style.css` 를 참조 (개별 이슈는 `../style.css`, 인덱스는 `style.css`).
  브랜드 팔레트 — `--bg:#FFFFFF`, `--text:#111111`, `--link:#4F46E5` (indigo-600).
  본문 최대폭 `720px`, Inter + JetBrains Mono 구글 폰트, 반응형 + `prefers-color-scheme: dark` 대응.
- **인덱스 자동 생성**: `output/index_builder.py` 의 `build_index()` 가
  `outputs/*/newsletter.md` 의 첫 H1 을 제목으로 수집해 날짜 역순으로 `outputs/index.html` 을 재작성.
- **포스트 네비게이션**: 같은 모듈의 `update_post_navigation()` 가 각 `newsletter.html` 하단에
  `<!-- POST-NAV:START --> ... <!-- POST-NAV:END -->` 블록을 주입/갱신한다.
  블록 내부는 `← 이전 글 / 전체 목록 / 다음 글 →` 3-칼럼 그리드.
- **호출 시점**: `main.py` STEP 6.8 에서 `build_all()` 이 호출되어
  인덱스와 전체 포스트의 prev/next 가 매 발행마다 일관되게 갱신된다.
- **Render.com 배포**: `outputs/` 를 static publish root 로 지정하면
  `/` → `index.html`, `/2025-01-15-slug/newsletter.html` 구조로 즉시 서비스된다.

### 강제 5섹션 포맷 (newsletter.md)

```markdown
# {제목}

{YYYY-MM-DD}

## Summary

{400자 내외}

## 본문

{딥다이브 본문 + 인라인 다이어그램, 내부 소제목은 ###부터}

## References

- [{source_url}]({source_url})
```

`output/validate.py`의 `_check_required_format()`가 위 구조를 강제하며,
태그·출처명·`## Deep Dive`·이모지 메타라인은 모두 금지 패턴으로 등록되어 있습니다.

뷰어(`viewer.py`)는 `outputs/` 폴더를 스캔해 이슈 목록을 자동으로 구성합니다.

---

## 다이어그램 디자인 규칙

- 컬러 팔레트: 메인 `#D75656` (레드), 서브 `#EEEEEE` (라이트 그레이)
- **모든 텍스트는 영어** (CO-STAR 명시 요구사항)
- 스타일: Minimal Infographic
- 형식: SVG (외부 의존성 없음)
- `comparison` 타입: 기존 방식(회색) vs 신규 방식(레드) 병렬 비교
- `flow` 타입: 홀수 단계는 레드 배경, 짝수 단계는 회색 배경

---

## 자주 하는 작업

### 새 크롤러 소스 추가
1. `crawlers/new_source.py` 생성 — `fetch_new_source() -> list[dict]` 형식 준수
2. `crawlers/__init__.py`에 import 추가
3. `main.py` STEP 2에 호출 추가
4. `config.py`에 관련 설정 상수 추가

### Claude 모델 변경
`config.py`의 `CLAUDE_MODEL` 값을 수정합니다.
```python
CLAUDE_MODEL = "claude-sonnet-4-6"  # 빠른 실행
CLAUDE_MODEL = "claude-opus-4-6"    # 고품질 (기본값)
```

### 다이어그램 타입 추가
`diagrams/generator.py`에 `_svg_새타입()` 함수를 추가하고,
`generate_diagrams()` 함수의 타입 분기에 등록합니다.

### 발행 이력 초기화
`NEWSLETTER_TOPICS.md`의 `✅ [Published]` 섹션 내용을 수동으로 지웁니다.
다양성 가드레일이 빈 이력으로 리셋됩니다.

---

## 환경 요구사항

- **uv** — 가상환경 및 패키지 관리자 (필수). `pip` 직접 사용 금지.
- Python 3.10+ — `.python-version` 파일로 버전 고정됨
- 환경 변수: `ANTHROPIC_API_KEY` (필수, `.env` 파일 또는 shell export)
- 네트워크: GitHub, ArXiv, Reddit 접근 가능해야 함

---

## uv 사용 규칙 (필독)

이 프로젝트는 **uv 가상환경**에서만 실행해야 합니다.

```bash
# ✅ 올바른 실행 방법
uv run python main.py
uv run python viewer.py
uv run python -m pytest

# ❌ 금지 — 시스템 Python 직접 사용
python main.py
pip install <패키지>
```

**패키지 추가 시**에도 반드시 uv를 사용합니다:
```bash
uv add <패키지명>        # 추가 (pyproject.toml + uv.lock 자동 업데이트)
uv remove <패키지명>     # 제거
uv sync                  # uv.lock 기준으로 환경 재현
```

의존성 파일 위치:
- `pyproject.toml` — 프로젝트 메타데이터 및 의존성 선언
- `uv.lock` — 버전 잠금 파일 (커밋에 포함, 직접 편집 금지)
- `.python-version` — Python 버전 고정 (`3.10`)
- `.venv/` — 실제 가상환경 디렉토리 (git 제외)

## 알려진 제약사항

- **ArXiv API**: 간헐적으로 403 응답 → 재시도 로직 없음, 실패 시 0개 반환하고 계속 진행
- **Reddit API**: 인증 없는 공개 API 사용 → rate limit 가능성 있음 (일반 사용에는 문제없음)
- **GitHub Trending**: HTML 스크래핑 → GitHub UI 변경 시 CSS 셀렉터 업데이트 필요
- **다이어그램 한글**: SVG 내 텍스트는 영어만 사용 (CO-STAR 요구사항)
- **viewer.py**: 표준 라이브러리만 사용하므로 마크다운 렌더링 없음 (raw 텍스트로 표시)
