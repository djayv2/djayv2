from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


@dataclass
class DocumentItem:
    source: str
    document_id: str
    url: str
    title: str
    published_at: Optional[datetime]
    content_text: Optional[str] = None
    content_hash: Optional[str] = None


def parse_list_page(html: str, base_url: str) -> List[DocumentItem]:
    soup = BeautifulSoup(html, "html.parser")

    items: List[DocumentItem] = []

    # Fallback strategy: find article cards and list items with anchors
    for article in soup.select("article, .views-row, li a[href]"):
        a = article.find("a", href=True)
        if not a:
            continue
        url = a.get("href")
        if url and url.startswith("/"):
            url = base_url.rstrip("/") + url
        title = (a.get_text(strip=True) or "").strip()
        if not url or not title:
            continue
        # Try to detect date in nearby elements
        date_text = None
        date_el = article.find(["time", "span", "div"], attrs={"class": lambda c: c and ("date" in c or "time" in c)})
        if date_el:
            date_text = date_el.get_text(strip=True)
        published_at = None
        if date_text:
            try:
                published_at = date_parser.parse(date_text, fuzzy=True)
            except Exception:
                published_at = None
        document_id = url.rsplit("/", 1)[-1]
        items.append(DocumentItem(source="FERC", document_id=document_id, url=url, title=title, published_at=published_at))

    # De-duplicate by url keeping first occurrence
    seen = set()
    unique: List[DocumentItem] = []
    for it in items:
        if it.url in seen:
            continue
        seen.add(it.url)
        unique.append(it)

    return unique


def parse_detail_page(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Heuristic: concatenated paragraphs
    parts = []
    main = soup.find("main") or soup
    for p in main.find_all(["p", "li"]):
        text = p.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return "\n".join(parts[:500])