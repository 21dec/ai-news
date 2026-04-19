"""
Reddit Crawler
r/MachineLearning, r/LocalLLaMA, r/mlops 등에서 인기 포스트를 수집합니다.
Reddit 공개 JSON API를 사용합니다 (인증 불필요).
"""
import requests
from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REDDIT_SUBREDDITS, REDDIT_TIME_FILTER, REDDIT_POST_LIMIT, MAX_ITEMS_PER_SOURCE

HEADERS = {
    "User-Agent": "AI-Newsletter-Bot/1.0 (automated newsletter generator)"
}

NOISE_KEYWORDS = ["hiring", "job", "career", "salary", "rant", "meme", "funny", "weekly thread"]
SIGNAL_KEYWORDS = [
    "release", "paper", "framework", "library", "tool", "benchmark",
    "open", "model", "architecture", "method", "technique", "approach",
    "efficient", "fast", "new", "introduce", "deploy", "inference"
]

def fetch_reddit() -> List[Dict]:
    """
    Reddit 공개 JSON API로 상위 포스트를 수집합니다.

    Returns:
        List of dicts with keys: title, url, description, subreddit, score, source
    """
    results = []

    for subreddit in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"t": REDDIT_TIME_FILTER, "limit": REDDIT_POST_LIMIT * 3}

        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[Reddit] r/{subreddit} 요청 실패: {e}")
            continue

        posts = data.get("data", {}).get("children", [])
        count = 0

        for post in posts:
            if count >= REDDIT_POST_LIMIT:
                break

            p = post.get("data", {})
            title = p.get("title", "").strip()
            score = p.get("score", 0)
            permalink = p.get("permalink", "")
            selftext = p.get("selftext", "").strip()
            is_self = p.get("is_self", True)
            external_url = p.get("url", "")

            # 노이즈 필터링
            title_lower = title.lower()
            if any(kw in title_lower for kw in NOISE_KEYWORDS):
                continue
            if score < 50:
                continue

            # 신호 기반 필터링
            if not any(kw in title_lower for kw in SIGNAL_KEYWORDS):
                continue

            # URL 결정
            post_url = f"https://www.reddit.com{permalink}" if is_self else external_url

            # 설명 구성
            if selftext:
                description = selftext[:300] + ("..." if len(selftext) > 300 else "")
            else:
                description = f"Score: {score:,} | r/{subreddit}"

            # 중복 제거
            if any(r["url"] == post_url for r in results):
                continue

            results.append({
                "source": f"Reddit r/{subreddit}",
                "title": title,
                "url": post_url,
                "description": description,
                "subreddit": subreddit,
                "score": score,
                "extra": f"r/{subreddit} | 🔺 {score:,} upvotes"
            })
            count += 1

    results = results[:MAX_ITEMS_PER_SOURCE]
    print(f"[Reddit] {len(results)}개 수집 완료")
    return results


if __name__ == "__main__":
    items = fetch_reddit()
    for item in items:
        print(f"- [{item['subreddit']}] {item['title'][:80]} (score: {item['score']})")
