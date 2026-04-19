"""
RSS / Atom Feed Crawler
주요 AI 연구소·미디어의 공개 피드를 수집합니다.
- OpenAI News, BAIR Blog, MIT News AI, MIT Technology Review AI,
  Google Research Blog, Anthropic News 등
외부 의존성을 추가하지 않기 위해 표준 라이브러리(urllib, xml.etree)를 사용하며,
피드가 비정상(HTML 페이지, 404 등)일 때에는 BeautifulSoup 로 최소한의 목록만
뽑아 오도록 폴백을 둡니다.
"""
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from html import unescape
from typing import List, Dict, Optional
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import RSS_FEEDS, RSS_MAX_ITEMS_PER_FEED, MAX_ITEMS_PER_SOURCE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Newsletter-Bot/1.0; +newsletter)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/html;q=0.5, */*;q=0.1",
}

# Atom / RSS 네임스페이스
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    """HTML 태그 제거 및 공백 정규화."""
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def _text_of(el: Optional[ET.Element]) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _fetch(url: str, timeout: int = 15) -> Optional[bytes]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"[RSS] {url} 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"[RSS] {url} 예기치 못한 오류: {e}")
        return None


def _parse_rss(root: ET.Element) -> List[Dict]:
    """RSS 2.0 (<rss><channel><item>...) 포맷 파싱."""
    items = []
    for item in root.iterfind(".//item"):
        title = _text_of(item.find("title"))
        link = _text_of(item.find("link"))
        desc_raw = _text_of(item.find("description")) or _text_of(
            item.find("content:encoded", NS)
        )
        if not title or not link:
            continue
        items.append({
            "title": _strip_html(title),
            "url": link,
            "description": _strip_html(desc_raw),
        })
    return items


def _parse_atom(root: ET.Element) -> List[Dict]:
    """Atom (<feed><entry>...) 포맷 파싱."""
    items = []
    for entry in root.iterfind("atom:entry", NS):
        title = _text_of(entry.find("atom:title", NS))
        # atom:link href
        link = ""
        for link_el in entry.findall("atom:link", NS):
            rel = link_el.get("rel", "alternate")
            if rel == "alternate" or not link:
                link = link_el.get("href", link)
        summary = _text_of(entry.find("atom:summary", NS)) or _text_of(
            entry.find("atom:content", NS)
        )
        if not title or not link:
            continue
        items.append({
            "title": _strip_html(title),
            "url": link,
            "description": _strip_html(summary),
        })
    return items


def _parse_feed(xml_bytes: bytes) -> List[Dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    # 루트 태그로 포맷 판별
    tag = root.tag.lower()
    if tag.endswith("rss"):
        return _parse_rss(root)
    if tag.endswith("feed"):
        return _parse_atom(root)
    # RDF 등 기타: item 태그가 있으면 RSS 처럼 시도
    return _parse_rss(root)


def _fallback_html_scrape(url: str, xml_bytes: bytes) -> List[Dict]:
    """
    RSS 가 아닌 HTML 페이지(예: anthropic.com/news) 용 최소 스크랩.
    BeautifulSoup 가 있으면 사용, 없으면 정규식으로 링크/제목만 추출.
    """
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        return []

    try:
        soup = BeautifulSoup(xml_bytes, "html.parser")
    except Exception:
        return []

    items: List[Dict] = []
    seen = set()
    # 휴리스틱: <a> 중 /news/ 또는 제목스러운 앵커
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        text = _strip_html(a.get_text())
        if len(text) < 12:
            continue
        if href.startswith("/"):
            # 절대 URL 화
            base = re.match(r"https?://[^/]+", url)
            if not base:
                continue
            href = base.group(0) + href
        if href in seen:
            continue
        # anthropic.com 등: /news/<slug> 패턴만 채택
        if "/news/" not in href and "/research/" not in href and "/blog/" not in href:
            continue
        seen.add(href)
        items.append({
            "title": text,
            "url": href,
            "description": "",
        })
        if len(items) >= 20:
            break
    return items


def _fetch_feed(feed_url: str, source_name: str, limit: int) -> List[Dict]:
    raw = _fetch(feed_url)
    if raw is None:
        return []

    parsed = _parse_feed(raw)
    if not parsed:
        # RSS 파싱 실패 → HTML 폴백 (anthropic.com/news 등)
        parsed = _fallback_html_scrape(feed_url, raw)

    results = []
    for entry in parsed[:limit]:
        title = entry.get("title", "").strip()
        url = entry.get("url", "").strip()
        if not title or not url:
            continue
        desc = (entry.get("description") or "")[:300]
        if entry.get("description") and len(entry["description"]) > 300:
            desc += "..."
        results.append({
            "source": source_name,
            "title": title,
            "url": url,
            "description": desc or f"{source_name} 게시물",
            "extra": f"Source: {source_name}",
        })
    return results


def fetch_rss_feeds() -> List[Dict]:
    """
    config.RSS_FEEDS 에 정의된 모든 피드를 수집합니다.

    Returns:
        List of dicts with keys: source, title, url, description, extra
    """
    all_results: List[Dict] = []
    per_feed_limit = RSS_MAX_ITEMS_PER_FEED

    for feed in RSS_FEEDS:
        name = feed.get("name", feed.get("url", "unknown"))
        url = feed.get("url", "")
        if not url:
            continue

        items = _fetch_feed(url, name, per_feed_limit)

        # 중복 제거 (URL 기준, 전체 결과 통합)
        for it in items:
            if any(r["url"] == it["url"] for r in all_results):
                continue
            all_results.append(it)

        print(f"[RSS] {name}: {len(items)}개")

    # 전체 상한
    all_results = all_results[: MAX_ITEMS_PER_SOURCE * max(1, len(RSS_FEEDS))]
    print(f"[RSS] 총 {len(all_results)}개 수집 완료")
    return all_results


if __name__ == "__main__":
    items = fetch_rss_feeds()
    for item in items:
        print(f"- [{item['source']}] {item['title'][:80]}")
        if item.get("description"):
            print(f"    {item['description'][:100]}")
