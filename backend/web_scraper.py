import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import unquote, urlparse

import requests

from .rag_service import rag_service

CACHE_PATH = Path(__file__).resolve().parents[1] / "db" / "web_cache.json"


def _load_cache() -> Dict[str, float]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: Dict[str, float]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _allowlist_domains() -> List[str]:
    domains = os.getenv(
        "WEB_ALLOWLIST_DOMAINS",
        "taconic.com,criver.com,jax.org,colonymanagement.jax.org",
    ).split(",")
    return [d.strip().lower() for d in domains if d.strip()]


def _is_allowed(url: str) -> bool:
    allowed = _allowlist_domains()
    return any(domain in url.lower() for domain in allowed)


def _fetch_url(url: str, timeout: int = 12) -> Optional[str]:
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "BioShoppingAgent/1.0"},
        )
        if response.status_code >= 400:
            return None
        return response.text
    except Exception:
        return None


def refresh_sources(urls: List[str], ttl_seconds: int = 86400) -> List[str]:
    """Fetch and ingest allowlisted URLs. Returns successfully ingested URLs."""
    cache = _load_cache()
    now = time.time()
    ingested: List[str] = []

    for url in urls:
        if not _is_allowed(url):
            continue
        last_fetch = cache.get(url)
        if last_fetch and now - last_fetch < ttl_seconds:
            ingested.append(url)
            continue
        html = _fetch_url(url)
        if not html:
            continue
        rag_service.ingest_html(html, source_name=url)
        cache[url] = now
        ingested.append(url)

    _save_cache(cache)
    return ingested


def default_vendor_urls() -> List[str]:
    env_urls = os.getenv("VENDOR_SOURCE_URLS", "").strip()
    if env_urls:
        return [u.strip() for u in env_urls.split(",") if u.strip()]
    return []


def _extract_search_links(html: str) -> List[str]:
    # DuckDuckGo HTML uses "uddg=" for outbound URLs
    links = []
    for match in re.findall(r"uddg=([^&\"]+)", html):
        url = unquote(match)
        if url.startswith("http"):
            links.append(url)
    # Fallback: capture direct https links in result cards
    links.extend(re.findall(r'href="(https?://[^"]+)"', html))
    return links


def discover_vendor_urls(query: str, max_results: int = 5) -> List[str]:
    """Search the web for vendor pages related to the query, restricted to allowlisted domains."""
    allowed = _allowlist_domains()
    if not query.strip():
        return []

    search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}"
    html = _fetch_url(search_url)
    if not html:
        return []

    candidates = _extract_search_links(html)
    results: List[str] = []
    for url in candidates:
        host = urlparse(url).netloc.lower()
        if any(domain in host for domain in allowed):
            if url not in results:
                results.append(url)
        if len(results) >= max_results:
            break
    if results:
        return results

    # Fallback to vendor homepages if search yields nothing
    fallback = [
        "https://www.jax.org",
        "https://www.criver.com",
        "https://www.taconic.com",
    ]
    return [url for url in fallback if any(domain in url for domain in allowed)][:max_results]
