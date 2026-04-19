"""
GitHub Trending Crawler
AI/ML 관련 트렌딩 레포지토리를 수집합니다.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MAX_ITEMS_PER_SOURCE

AI_KEYWORDS = [
    "llm", "ai", "ml", "deep-learning", "machine-learning", "neural",
    "transformer", "diffusion", "rag", "agent", "gpt", "claude", "llama",
    "vector", "embedding", "inference", "fine-tun", "train", "model",
    "pytorch", "tensorflow", "huggingface", "langchain", "openai"
]

def fetch_github_trending(language: str = "python", since: str = "daily") -> List[Dict]:
    """
    GitHub Trending에서 AI/ML 관련 레포지토리를 수집합니다.

    Returns:
        List of dicts with keys: title, url, description, stars, language, source
    """
    url = f"https://github.com/trending/{language}?since={since}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[GitHub Trending] 요청 실패: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.Box-row")

    results = []
    for article in articles:
        if len(results) >= MAX_ITEMS_PER_SOURCE:
            break

        # 레포 이름 및 URL
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        repo_path = h2["href"].strip("/")
        repo_url = f"https://github.com/{repo_path}"
        repo_name = repo_path.replace("/", " / ")

        # 설명
        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # 스타 수
        stars_tag = article.select_one("a[href$='/stargazers']")
        stars = stars_tag.get_text(strip=True).replace(",", "") if stars_tag else "0"

        # AI 관련 필터링
        combined = (repo_name + " " + description).lower()
        if not any(kw in combined for kw in AI_KEYWORDS):
            continue

        results.append({
            "source": "GitHub Trending",
            "title": repo_name,
            "url": repo_url,
            "description": description,
            "stars": stars,
            "language": language,
            "extra": f"⭐ {stars} stars"
        })

    print(f"[GitHub Trending] {len(results)}개 수집 완료")
    return results


if __name__ == "__main__":
    items = fetch_github_trending()
    for item in items:
        print(f"- {item['title']}: {item['description'][:80]}")
