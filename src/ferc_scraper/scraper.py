from __future__ import annotations

import logging
from typing import List

from .config import Settings
from .http import build_session, retrying_fetch, content_sha256, random_jitter_sleep
from .parser import parse_list_page, parse_detail_page, DocumentItem
from .storage import PostgresStorage


logger = logging.getLogger(__name__)


def _build_page_url(base_url: str, page_index: int) -> str:
    # If template placeholder exists, use it
    if "{page}" in base_url:
        return base_url.format(page=page_index)
    # Otherwise, append page= parameter
    sep = "&" if ("?" in base_url) else "?"
    return f"{base_url}{sep}page={page_index}"


def run_scraper(settings: Settings) -> int:
    session = build_session(source_ip=settings.source_ip, outbound_proxy_url=settings.outbound_proxy_url)

    total_items = 0
    with PostgresStorage(settings) as storage:
        storage.ensure_schema_and_tables()

        for page in range(settings.max_pages):
            page_url = _build_page_url(settings.base_url, page)
            try:
                resp = retrying_fetch(session, page_url, timeout=settings.request_timeout_seconds, max_attempts=settings.max_retries)
            except Exception as ex:
                logger.warning("Failed to fetch list page %s: %s", page_url, ex)
                continue
            items = parse_list_page(resp.text, settings.base_url)
            logger.info("Parsed %d items from %s", len(items), page_url)

            if settings.fetch_details:
                for it in items:
                    try:
                        detail_resp = retrying_fetch(
                            session, it.url, timeout=settings.request_timeout_seconds, max_attempts=settings.max_retries
                        )
                        it.content_text = parse_detail_page(detail_resp.text)
                        it.content_hash = content_sha256(it.content_text or "")
                    except Exception as ex:
                        logger.warning("Failed to fetch detail %s: %s", it.url, ex)
                        it.content_text = None
                        it.content_hash = None
                    random_jitter_sleep(0.1, 0.4)
            else:
                for it in items:
                    it.content_text = None
                    it.content_hash = None

            storage.upsert_documents(items)
            total_items += len(items)
            random_jitter_sleep(0.3, 1.0)

    return total_items