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
    extra: Optional[dict] = None


def parse_list_page(html: str, base_url: str) -> List[DocumentItem]:
    soup = BeautifulSoup(html, "html.parser")

    items: List[DocumentItem] = []

    # For download-database page: collect anchors to datasets/zip/csv
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        text = a.get_text(strip=True)
        if not href or not text:
            continue
        lower = href.lower()
        if any(ext in lower for ext in (".zip", ".csv", "/dataset/", "/open/")):
            url = href
            if url.startswith("/"):
                url = base_url.rstrip("/") + url
            document_id = url.rsplit("/", 1)[-1]
            # try to find nearby date or size
            meta_text = a.find_parent().get_text(" ", strip=True) if a.find_parent() else text
            published_at = None
            try:
                published_at = date_parser.parse(meta_text, fuzzy=True)
            except Exception:
                published_at = None
            items.append(
                DocumentItem(
                    source="FERC_DB",
                    document_id=document_id,
                    url=url,
                    title=text,
                    published_at=published_at,
                    extra={"context": meta_text[:200]},
                )
            )

    # Deduplicate by URL
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
    parts = []
    main = soup.find("main") or soup
    for p in main.find_all(["p", "li", "td"]):
        text = p.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return "\n".join(parts[:500])