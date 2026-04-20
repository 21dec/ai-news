# CLAUDE.md — AI Newsletter 프로젝트 가이드

> 이 파일은 Claude가 이 코드베이스를 다룰 때 참고하는 컨텍스트 문서입니다.
> 새 세션이 시작될 때 이 파일을 먼저 읽고 작업을 시작하세요.

---

## 프로젝트 목적

AI 개발자·엔지니어 대상의 기술 뉴스레터를 **완전 자동화**하는 파이프라인입니다.
뉴스 수집 → 주제 선별 → 본문 생성 → SVG 다이어그램 → MD/HTML 저장 → 인덱스/네비 갱신 →
백로그 관리 → GitHub push 까지 하나의 스케줄 실행으로 처리합니다.

## LLM 실행 아키텍처

이 시스템은 **OpenAI GPT-5.4 API**를 사용합니다.
`uv run python main.py` 로 크롤링부터 발행까지 완전 자동화됩니다.

- **Python `ai/` 모듈**: OpenAI API 를 호출하여 주제 선별(`selector.py`),
  본문 생성(`generator.py`), 스핀오프 추출(`spinoff.py`)을 수행합니다.
- **Python 인프라**: 크롤링, 파일 저장, MD→HTML 렌더링, PNG 다이어그램 생성,
  5섹션 포맷 검증, 톤 검증, 인덱스/네비 빌드, 백로그 파일 I/O.
- **환경변수**: `OPENAI_API_KEY` 필수 (`.env` 파일 또는 환경변수로 설정).
- **엔트리포인트**: `main.py` — 8단계 파이프라인을 순차 실행합니다.

---

## 핵심 파일 맵

| 파일 | 역할 | 수정 시 주의사항 |
|------|------|----------------|
| `main.py` | 운영 엔트리포인트 (`uv run python main.py`) | 8단계 파이프라인 순차 실행 |
| `config.py` | 전역 설정 상수 | `OPENAI_API_KEY` / `OPENAI_MODEL` |
| `crawlers/github_trending.py` | GitHub AI 레포 스크래핑 | BeautifulSoup4 사용, CSS 셀렉터 변경 주의 |
| `crawlers/arxiv.py` | ArXiv XML API 파싱 | 표준 라이브러리(urllib, xml.etree)만 사용 |
| `crawlers/reddit.py` | Reddit JSON API | 인증 불필요, User-Agent 필수 |
| `ai/selector.py` | GPT-5.4 주제 선별 | 다양성 가드레일 포함 |
| `ai/generator.py` | GPT-5.4 본문 생성 | CO-STAR 톤·포맷 강제, 재시도 로직 |
| `ai/spinoff.py` | GPT-5.4 스핀오프 추출 | 적응형 cap 연동 |
| `diagrams/generator.py` | SVG 인포그래픽 생성 | `comparison` / `flow` 두 타입 지원 |
| `output/writer.py` | MD + HTML 저장, `_slugify()` | HTML 은 외부 `../style.css` 참조 (인라인 `<style>` 없음) |
| `output/index_builder.py` | `outputs/index.html` 생성 + prev/next 네비 주입 | 이슈 폴더 스캔은 `YYYY-MM-DD-slug` 정규식 기반 |
| `output/backlog.py` | `NEWSLETTER_TOPICS.md` 읽기/쓰기 | 파일 경로는 `config.BACKLOG_FILE` 참조 |
| `viewer.py` | 로컬 HTTP 서버 미리보기 | 표준 라이브러리만 사용, 추가 설치 불필요 |

---

## 파이프라인 흐름 (스케줄 태스크 `daily-ai-newsletter`)

```
STEP 1: Python — load_published_history()          → 다양성 가드레일용 발행 이력
STEP 2: Python — fetch_github_trending()            → 크롤링 결과 JSON 으로 덤프
        Python — fetch_arxiv()
        Python — fetch_reddit()
        Python — fetch_rss_feeds()                  → OpenAI / BAIR / MIT News /
                                                      MIT Tech Review / Google Research /
                                                      Anthropic 6개 RSS·HTML 피드
STEP 3: Claude 세션 — 후보를 읽고 1건 선별
        (발행 이력 + 카테고리 빈도 + hook 기준)
STEP 4: Claude 세션 — 5섹션 포맷 newsletter.md 를 Write 툴로 직접 작성
        (title, 날짜, Summary ≤400자, 본문 1000~3000자 + ### 소제목,
         References; 태그·이모지·메타라인 금지; ~합니다 정형체 유지)
STEP 4.5: Claude 세션 — diagram_specs(JSON) 결정 → Python 으로 SVG 생성
STEP 5: Python — diagrams.generate_diagrams(specs, issue_dir, slug)
STEP 6: Python — writer.save_newsletter() 또는 Claude 가 직접 작성한 MD 재사용 후
        MD → HTML 변환 및 ../style.css 링크 포함
STEP 6.5: Python — run_content_validation + run_file_validation + 톤 린트
STEP 6.8: Python — output.index_builder.build_all(OUTPUT_DIR)
                   (outputs/index.html + 모든 newsletter.html 의 prev/next 주입)
STEP 7: Python — output.backlog.update_backlog(title, source_url, tags, date)
STEP 8: Claude 세션 — 파생 주제 2~3개 JSON 결정
        Python — output.backlog.add_spinoffs_to_backlog(spinoffs, date)
STEP 9: Bash — git add ai-newsletter/outputs NEWSLETTER_TOPICS.md
              → git commit → git push origin main
```

각 STEP 의 Python 호출은 `uv run python -c "..."` 형태로 수행하거나
소규모 헬퍼 스크립트를 통해 실행합니다.

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

## 백로그 증가 억제 정책 (2026-04-19)

초기 설계에서 매 발행마다 스핀오프 2~3개를 무조건 생성해 백로그가
기하급수적으로 누적되는 문제가 있었습니다. 현재는 아래 4단 방어선으로
증가 속도를 상쇄합니다.

1. **적응형 스핀오프 cap** — `output.backlog.recommended_spinoff_count()`
   가 현재 백로그 크기를 보고 권장 개수를 결정합니다.
   - `< 5` → 3 개, `5~9` → 2 개, `10~14` → 1 개, `>= 15` → 0 개.
   - 스케줄 태스크 STEP 5 는 이 값 이하만 생성합니다.
2. **중복 차단** — `add_spinoffs_to_backlog(dedup=True)` (기본값)이
   Published + 기존 Backlog 제목과 Jaccard 유사도 ≥ 0.55 인 항목을
   자동 제외합니다. 스킵된 항목은 stdout 에 로그만 남고 백로그에
   들어가지 않습니다.
3. **백로그 우선 선별** — 스케줄 태스크 STEP 2 는 fresh 크롤링보다
   먼저 백로그에서 1) 하루 이상 경과 + 2) 카테고리 과편중 아님 조건의
   항목을 찾습니다. 선택되면 save 단계에서 백로그 원본 bullet 을 제거해
   **백로그를 실제로 소진**합니다. 이 흐름이 장기적으로 증가를 상쇄하는
   핵심 메커니즘입니다.
4. **주 1회 prune** — 일요일(`date +%u` = 7) 실행 시
   `prune_old_spinoffs(days=30)` 로 30일 초과한 미소비 스핀오프를 제거.

### 관련 API (`output/backlog.py`)

- `load_backlog_items() -> list[dict]` — `📋 Backlog` 섹션 파싱
- `count_backlog_items() -> int` — 백로그 크기
- `recommended_spinoff_count(size=None) -> int` — 적응형 cap
- `is_duplicate_title(title, existing, threshold=0.55) -> bool` — 키워드 Jaccard
- `filter_duplicate_spinoffs(spinoffs) -> (kept, dropped)`
- `prune_old_spinoffs(days=30) -> list[str]` — 제거된 title 반환

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
별도 설정 불필요. LLM 작업은 스케줄 태스크를 실행하는 Claude 세션의
모델을 그대로 사용합니다. `config.CLAUDE_MODEL` 은 레거시 상수입니다.

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
- 환경 변수: 없음 (ANTHROPIC_API_KEY 는 더 이상 사용하지 않음)
- 네트워크: GitHub, ArXiv, Reddit, github.com (git push) 접근 가능해야 함

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
