# AI Newsletter Automation

AI 개발자·엔지니어를 위한 **기술 뉴스레터 자동 생성 시스템**입니다.  
GitHub Trending, ArXiv, Reddit에서 뉴스를 수집하고, Claude API로 콘텐츠를 생성하며, 백로그를 자동으로 관리합니다.

---

## 주요 기능

**뉴스 수집**: GitHub Trending(AI/ML 레포), ArXiv(cs.AI·cs.LG·cs.CL 최신 논문), Reddit(r/MachineLearning·r/LocalLLaMA·r/mlops)에서 실용적인 기술 소식을 자동 크롤링합니다.

**AI 선별 (다양성 가드레일)**: Claude가 CO-STAR 프레임워크 기준으로 가장 actionable한 주제 1개를 선택합니다. 발행 이력을 참고해 최근 4편에서 동일 카테고리가 반복되면 자동으로 다른 카테고리를 선택합니다.

**콘텐츠 생성**: 요약글(400자 내외)과 딥다이브 글(1000~3000자)을 Chain-of-Thought 방식으로 생성합니다. 아키텍처 비교·코드 스니펫 포함.

**SVG 다이어그램 자동 생성**: 기존 vs 신규 비교(comparison) 또는 워크플로우(flow) 타입의 인포그래픽을 자동으로 생성합니다. 디자인 팔레트: `#D75656`, `#EEEEEE`.

**스핀오프 자동화**: 발행 후 Claude가 파생 주제 3개를 자동 추출하여 백로그에 추가합니다. 글 1편이 다음 글감 3편을 낳는 구조입니다.

**로컬 뷰어**: 블로그 포스팅 전 HTML 미리보기와 Markdown 뷰를 브라우저에서 확인할 수 있습니다.

---

## 빠른 시작

### 1. uv 설치 (처음 한 번만)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 가상환경 및 패키지 설치

```bash
cd ai-newsletter
uv sync
```

`uv sync` 한 번으로 `.venv` 생성과 패키지 설치가 모두 완료됩니다.

### 3. API 키 설정

```bash
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 입력
```

### 4. 뉴스레터 생성

```bash
uv run python main.py
```

### 5. 로컬 뷰어로 확인

```bash
uv run python viewer.py           # http://localhost:8000
uv run python viewer.py --latest  # 최신 뉴스레터 바로 열기
uv run python viewer.py --port 8080
```

---

## 프로젝트 구조

```
ai-newsletter/
│
├── main.py                  # 전체 파이프라인 오케스트레이터
├── viewer.py                # 로컬 미리보기 서버
├── config.py                # 전역 설정 (소스, 모델, 색상 등)
├── pyproject.toml           # 프로젝트 메타데이터 및 의존성 (uv)
├── uv.lock                  # 의존성 버전 잠금 파일
├── .python-version          # Python 버전 고정 (3.10)
├── .venv/                   # uv가 관리하는 가상환경 (git 제외)
├── .env.example             # API 키 템플릿
│
├── crawlers/                # 뉴스 수집 모듈
│   ├── github_trending.py   # GitHub AI/ML 트렌딩 레포
│   ├── arxiv.py             # ArXiv 최신 논문 (cs.AI, cs.LG, cs.CL)
│   └── reddit.py            # Reddit 상위 포스트
│
├── ai/                      # Claude API 연동
│   ├── selector.py          # 주제 선별 + 다양성 가드레일
│   ├── generator.py         # 요약 + 딥다이브 콘텐츠 생성
│   └── spinoff.py           # 파생 주제 자동 생성
│
├── diagrams/
│   └── generator.py         # SVG 다이어그램 생성 (comparison / flow)
│
├── output/
│   ├── writer.py            # MD + HTML 파일 저장
│   └── backlog.py           # NEWSLETTER_TOPICS.md 읽기/쓰기
│
└── outputs/                 # 생성된 뉴스레터 (자동 생성)
    └── YYYY-MM-DD-slug/
        ├── newsletter.md
        ├── newsletter.html
        └── *_diagram_*.svg
```

---

## 설정 (`config.py`)

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `CLAUDE_MODEL` | `claude-opus-4-6` | 사용할 Claude 모델 |
| `MAX_ITEMS_PER_SOURCE` | `5` | 소스당 최대 수집 개수 |
| `SUMMARY_LENGTH` | `400` | 요약글 목표 자수 |
| `ARTICLE_MIN_LENGTH` | `1000` | 딥다이브 최소 자수 |
| `ARTICLE_MAX_LENGTH` | `3000` | 딥다이브 최대 자수 |
| `ARXIV_CATEGORIES` | `cs.AI, cs.LG, cs.CL` | ArXiv 수집 카테고리 |
| `REDDIT_TIME_FILTER` | `week` | Reddit 기간 필터 |
| `DIAGRAM_COLOR_PRIMARY` | `#D75656` | 다이어그램 메인 컬러 |

---

## 파이프라인 흐름

```
[1] 발행 이력 로드 (다양성 가드레일용)
      ↓
[2] 크롤링: GitHub Trending + ArXiv + Reddit
      ↓
[3] AI 선별: 발행 이력 참고 → 카테고리 균형 유지
      ↓
[4] 콘텐츠 생성: 요약(400자) + 딥다이브(1000~3000자)
      ↓
[5] SVG 다이어그램 생성 (1~3개)
      ↓
[6] 파일 저장: outputs/YYYY-MM-DD-slug/ 폴더
      ↓
[7] 백로그 업데이트: Published 등록 + 태그 기록
      ↓
[8] 스핀오프 생성: 파생 주제 3개 → Backlog에 자동 추가
```

---

## 백로그 관리 (`NEWSLETTER_TOPICS.md`)

백로그 파일은 프로젝트 상위 폴더(`../NEWSLETTER_TOPICS.md`)에 위치합니다.

- **📋 Backlog**: 작성 대기 중인 주제 (스핀오프 자동 추가)
- **✍️ In Progress**: 현재 작성 중
- **✅ Published**: 발행 완료 (날짜·태그 자동 기록)
- **💡 New Ideas / Spinoffs**: 파생 글감 이력

각 발행 항목에 카테고리 태그(`#infra`, `#rag`, `#agent` 등)가 자동으로 붙어 다음 선별 시 다양성 가드레일의 기준 데이터로 활용됩니다.

### 지원 카테고리

`infra` · `framework` · `agent` · `rag` · `training` · `evaluation` · `multimodal` · `tooling` · `architecture` · `security`

---

## 타겟 독자

AI 엔지니어, 백엔드 개발자, IT 아키텍트를 대상으로 합니다. 코드·아키텍처 레벨의 실용적인 기술 소식에 집중하며, RAG·WASM·In-process 같은 기술 용어는 설명 없이 사용합니다.

---

## 의존성 관리 (uv)

이 프로젝트는 [uv](https://docs.astral.sh/uv/)를 사용해 가상환경과 패키지를 관리합니다.  
`requirements.txt` 대신 `pyproject.toml`과 `uv.lock`을 사용합니다.

```bash
# 패키지 추가
uv add <패키지명>

# 패키지 제거
uv remove <패키지명>

# 잠금 파일 기준으로 재설치
uv sync

# 가상환경 경로 확인
uv run which python
```

> **주의**: 모든 Python 실행은 반드시 `uv run python ...` 형식을 사용해야 합니다.  
> `python main.py`처럼 직접 실행하지 마세요.

## 환경 요구사항

- [uv](https://docs.astral.sh/uv/) (패키지·가상환경 관리자)
- Python 3.10+ (uv가 자동으로 관리)
- 환경 변수: `ANTHROPIC_API_KEY` (필수)
- 네트워크: GitHub, ArXiv, Reddit 접근 가능해야 함

---

## 라이선스

MIT
