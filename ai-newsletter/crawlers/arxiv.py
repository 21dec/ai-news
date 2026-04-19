"""
ArXiv Crawler
최신 AI/ML 논문을 수집합니다.
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ARXIV_CATEGORIES, ARXIV_MAX_RESULTS

ARXIV_API_URL = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}

PRACTICAL_KEYWORDS = [
    "efficient", "fast", "lightweight", "inference", "deployment",
    "framework", "pipeline", "system", "architecture", "agent",
    "rag", "retrieval", "fine-tun", "quantiz", "benchmark",
    "evaluation", "tool", "benchmark", "open-source", "practical"
]

def fetch_arxiv() -> List[Dict]:
    """
    ArXiv API를 통해 최신 AI 논문을 수집합니다.
    cs.AI, cs.LG, cs.CL 카테고리에서 최근 논문 중 실용적인 것을 선별합니다.

    Returns:
        List of dicts with keys: title, url, description, authors, source
    """
    results = []

    for category in ARXIV_CATEGORIES:
        params = urllib.parse.urlencode({
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": ARXIV_MAX_RESULTS,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        })
        url = f"{ARXIV_API_URL}?{params}"

        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                xml_data = resp.read()
        except Exception as e:
            print(f"[ArXiv] {category} 요청 실패: {e}")
            continue

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            print(f"[ArXiv] XML 파싱 실패: {e}")
            continue

        entries = root.findall("atom:entry", NS)
        for entry in entries:
            title_el = entry.find("atom:title", NS)
            summary_el = entry.find("atom:summary", NS)
            id_el = entry.find("atom:id", NS)
            authors_els = entry.findall("atom:author/atom:name", NS)

            if not all([title_el, summary_el, id_el]):
                continue

            title = title_el.text.strip().replace("\n", " ")
            summary = summary_el.text.strip().replace("\n", " ")
            paper_url = id_el.text.strip()
            authors = ", ".join(el.text for el in authors_els[:3])
            if len(authors_els) > 3:
                authors += " et al."

            # 실용적인 논문 필터링
            combined = (title + " " + summary).lower()
            if not any(kw in combined for kw in PRACTICAL_KEYWORDS):
                continue

            # 중복 제거
            if any(r["url"] == paper_url for r in results):
                continue

            results.append({
                "source": "ArXiv",
                "title": title,
                "url": paper_url,
                "description": summary[:300] + ("..." if len(summary) > 300 else ""),
                "authors": authors,
                "category": category,
                "extra": f"Category: {category} | Authors: {authors}"
            })

    # 최대 개수 제한
    from config import MAX_ITEMS_PER_SOURCE
    results = results[:MAX_ITEMS_PER_SOURCE]
    print(f"[ArXiv] {len(results)}개 수집 완료")
    return results


if __name__ == "__main__":
    items = fetch_arxiv()
    for item in items:
        print(f"- {item['title'][:80]}")
        print(f"  {item['description'][:100]}")
