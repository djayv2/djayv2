from __future__ import annotations

import logging
from typing import List
import os

from .config import Settings
from .http import build_session, retrying_fetch, content_sha256, random_jitter_sleep
from .parser import parse_list_page, parse_detail_page, DocumentItem
from .storage import PostgresStorage
from .selenium_client import SeleniumHTTPClient


logger = logging.getLogger(__name__)


def _build_page_url(base_url: str, page_index: int) -> str:
    if "{page}" in base_url:
        return base_url.format(page=page_index)
    sep = "&" if ("?" in base_url) else "?"
    return f"{base_url}{sep}page={page_index}"


def _fetch_page_with_fallback(session, url: str, settings: Settings) -> str:
    """Fetch page content with fallback to Selenium if needed"""
    try:
        # Try regular HTTP first
        resp = retrying_fetch(session, url, timeout=settings.request_timeout_seconds, max_attempts=settings.max_retries)
        
        # Check if we got blocked by Cloudflare
        if resp.status_code == 403 or "just a moment" in resp.text.lower():
            logger.warning("Detected Cloudflare protection, switching to Selenium")
            return _fetch_with_selenium(url, settings)
            
        return resp.text
        
    except Exception as e:
        logger.warning(f"HTTP request failed: {e}, trying Selenium")
        return _fetch_with_selenium(url, settings)


def _fetch_with_selenium(url: str, settings: Settings) -> str:
    """Fetch page using Selenium to bypass Cloudflare"""
    try:
        with SeleniumHTTPClient(headless=True, timeout=settings.request_timeout_seconds) as selenium_client:
            content = selenium_client.get_page_with_retry(url, max_retries=settings.max_retries)
            if content:
                return content
            else:
                raise Exception("Selenium failed to fetch content")
    except Exception as e:
        logger.error(f"Selenium fetch failed: {e}")
        raise


def run_scraper(settings: Settings) -> int:
    session = build_session(source_ip=settings.source_ip, outbound_proxy_url=settings.outbound_proxy_url)

    total_items = 0
    with PostgresStorage(settings) as storage:
        if settings.create_tables:
            storage.ensure_schema_and_tables()

        if settings.scraper_mode == "dbindex":
            page_url = settings.base_url
            try:
                page_content = _fetch_page_with_fallback(session, page_url, settings)
            except Exception as ex:
                logger.warning("Failed to fetch db index %s: %s", page_url, ex)
                return 0
            items = parse_list_page(page_content, settings.base_url)
            for it in items:
                # For binary datasets, skip detail fetch
                it.content_text = None
                it.content_hash = None
            storage.upsert_documents(items)
            total_items += len(items)

            # Optional deep ingest of CSV datasets
            if os.getenv("INGEST_DATASETS", "false").lower() in {"1", "true", "yes"}:
                from .downloader import download_file
                from .ingest import ingest_csv
                import zipfile

                for it in items:
                    url_lower = it.url.lower()
                    if url_lower.endswith(".csv") or url_lower.endswith(".csv.gz") or url_lower.endswith(".zip"):
                        try:
                            tmp_path, sha, size = download_file(session, it.url, settings.request_timeout_seconds, settings.max_retries)
                            logger.info("Downloaded %s (%d bytes)", it.url, size)
                            data_bytes = None
                            if tmp_path.endswith(".gz"):
                                import gzip
                                with gzip.open(tmp_path, "rb") as g:
                                    data_bytes = g.read()
                            elif tmp_path.endswith(".zip"):
                                with zipfile.ZipFile(tmp_path, 'r') as zf:
                                    # pick first CSV
                                    for name in zf.namelist():
                                        if name.lower().endswith('.csv'):
                                            with zf.open(name) as f:
                                                data_bytes = f.read()
                                            break
                            else:
                                with open(tmp_path, 'rb') as f:
                                    data_bytes = f.read()
                            if data_bytes:
                                raw_table = os.getenv("RAW_TABLE", "ferc_raw")
                                ingested = ingest_csv(storage, settings.db_schema, raw_table, data_bytes, it.url)
                                logger.info("Ingested %d rows from %s", ingested, it.url)
                        except Exception as ex:
                            logger.warning("Ingest failed for %s: %s", it.url, ex)
                        finally:
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
            return total_items

        # fallback: news mode
        for page in range(settings.max_pages):
            page_url = _build_page_url(settings.base_url, page)
            try:
                page_content = _fetch_page_with_fallback(session, page_url, settings)
            except Exception as ex:
                logger.warning("Failed to fetch list page %s: %s", page_url, ex)
                continue
            items = parse_list_page(page_content, settings.base_url)
            logger.info("Parsed %d items from %s", len(items), page_url)

            if settings.fetch_details:
                for it in items:
                    try:
                        detail_content = _fetch_page_with_fallback(session, it.url, settings)
                        it.content_text = parse_detail_page(detail_content)
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