import logging
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

# Prefer the renamed package ddgs; fallback to duckduckgo_search
try:
    from ddgs import DDGS  # type: ignore
except Exception:  # pragma: no cover
    from duckduckgo_search import DDGS  # type: ignore

from readability import Document
from urllib.parse import urlparse, parse_qs, unquote


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: Optional[str]


@dataclass
class SourceContent:
    title: str
    url: str
    text: str


def _search_via_api(query: str, max_results: int) -> List[SearchResult]:
    results: List[SearchResult] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(
                query=query,
                region="us-en",
                safesearch="moderate",
                max_results=max_results,
            ):
                title = item.get("title") or item.get("source") or ""
                url = item.get("href") or item.get("url") or ""
                snippet = item.get("body") or item.get("snippet")
                if not url:
                    continue
                results.append(SearchResult(title=title, url=url, snippet=snippet))
    except Exception as exc:
        logging.warning("DDG API search failed: %s", exc)
    return results


def _normalize_ddg_href(href: str) -> Optional[str]:
    if not href:
        return None
    # Add scheme if missing
    if href.startswith("//"):
        return "https:" + href
    # Resolve DDG redirect links like /l/?uddg=...
    try:
        parsed = urlparse(href)
        if (parsed.netloc.endswith("duckduckgo.com") or parsed.netloc == "") and parsed.path.startswith("/l/"):
            qs = parse_qs(parsed.query)
            uddg_vals = qs.get("uddg")
            if uddg_vals:
                return unquote(uddg_vals[0])
            # If no uddg, fallback to adding https if path provided
            return "https://duckduckgo.com" + href if not parsed.netloc else href
    except Exception:
        return href
    return href


def _search_via_html(query: str, max_results: int) -> List[SearchResult]:
    results: List[SearchResult] = []
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        resp = s.get("https://duckduckgo.com/html/", params={"q": query}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select("a.result__a, a.result__url"):
            url_raw = a.get("href")
            title = a.get_text(strip=True)
            url = _normalize_ddg_href(url_raw)
            if not url:
                continue
            results.append(SearchResult(title=title, url=url, snippet=None))
            if len(results) >= max_results:
                break
    except Exception as exc:
        logging.warning("DDG HTML scrape failed: %s", exc)
    return results


def web_search(query: str, max_results: int = 6) -> List[SearchResult]:
    results = _search_via_api(query, max_results)
    if not results:
        results = _search_via_html(query, max_results)
    return results


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        if resp.status_code >= 200 and resp.status_code < 400:
            # Normalize whitespace to reduce size
            return resp.text
    except Exception as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
    return None


def extract_main_text(html: str) -> str:
    try:
        doc = Document(html)
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "lxml")
        text = soup.get_text("\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    except Exception:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def gather_sources(query: str, max_results: int = 6, max_chars_per_source: int = 4000) -> List[SourceContent]:
    results = web_search(query, max_results=max_results)
    sources: List[SourceContent] = []
    for r in results:
        html = fetch_url(r.url)
        if not html:
            continue
        text = extract_main_text(html)
        if not text:
            continue
        if len(text) > max_chars_per_source:
            text = text[:max_chars_per_source] + "…"
        # Derive title from page if missing
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.title.string.strip() if soup.title and soup.title.string else None
        title = r.title or title_tag or r.url
        sources.append(SourceContent(title=title, url=r.url, text=text))
        # Be polite
        time.sleep(0.8)
    return sources