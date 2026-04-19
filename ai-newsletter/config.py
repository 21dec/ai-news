"""
Configuration for AI Newsletter Automation System
"""
import os

# ─── API Keys ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ─── Claude Model ────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-opus-4-6"

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
SOURCES = ["github_trending", "arxiv", "reddit"]

# ─── ArXiv Settings ──────────────────────────────────────────────────────────
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
ARXIV_MAX_RESULTS = 5

# ─── Reddit Settings ─────────────────────────────────────────────────────────
REDDIT_SUBREDDITS = ["MachineLearning", "LocalLLaMA", "mlops"]
REDDIT_TIME_FILTER = "week"    # hour, day, week, month
REDDIT_POST_LIMIT = 5
