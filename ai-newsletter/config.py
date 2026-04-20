"""
Configuration for AI Newsletter Automation System
"""
import os

# ─── LLM (OpenAI) ────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-5.4"
OPENAI_MODEL_LIGHT = "gpt-5.4-mini"

# ─── Crawling Settings ───────────────────────────────────────────────────────
MAX_ITEMS_PER_SOURCE = 5       # 소스당 최대 수집 개수
TOTAL_CANDIDATES = 10          # AI 선별 후보 총 개수 (CO-STAR 기준)

# ─── Content Settings ────────────────────────────────────────────────────────
SUMMARY_LENGTH = 400           # 요약글 목표 자수
ARTICLE_MIN_LENGTH = 1000      # 딥다이브 최소 자수
ARTICLE_MAX_LENGTH = 3000      # 딥다이브 최대 자수

# ─── Diagram Settings ────────────────────────────────────────────────────────
DIAGRAM_COLOR_PRIMARY = "#D75656"
DIAGRAM_COLOR_SECONDARY = "#EEEEEE"
DIAGRAM_COLOR_TEXT = "#222222"
DIAGRAM_COLOR_ACCENT = "#FFFFFF"

# ─── Output Settings ─────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
BACKLOG_FILE = os.path.join(os.path.dirname(__file__), "..", "NEWSLETTER_TOPICS.md")

# ─── Sources ─────────────────────────────────────────────────────────────────
SOURCES = ["github_trending", "arxiv", "reddit", "rss_feeds"]

# ─── ArXiv Settings ──────────────────────────────────────────────────────────
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
ARXIV_MAX_RESULTS = 5

# ─── Reddit Settings ─────────────────────────────────────────────────────────
REDDIT_SUBREDDITS = ["MachineLearning", "LocalLLaMA", "mlops"]
REDDIT_TIME_FILTER = "week"    # hour, day, week, month
REDDIT_POST_LIMIT = 5

# ─── RSS / Atom Feeds ────────────────────────────────────────────────────────
# 주요 AI 연구소·미디어 피드. 새 피드는 {"name", "url"} 형태로 추가합니다.
# HTML 페이지(RSS 미제공)는 크롤러가 자동으로 HTML 폴백 스크랩을 시도합니다.
RSS_FEEDS = [
    {"name": "OpenAI News",        "url": "https://openai.com/news/rss.xml"},
    {"name": "BAIR Blog",          "url": "https://bair.berkeley.edu/blog/feed.xml"},
    {"name": "MIT News (AI)",      "url": "https://news.mit.edu/rss/topic/artificial-intelligence2"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "Google Research",    "url": "https://research.google/blog/rss/"},
    {"name": "Anthropic News",     "url": "https://www.anthropic.com/news"},  # HTML → 폴백 스크랩
]
RSS_MAX_ITEMS_PER_FEED = 5
