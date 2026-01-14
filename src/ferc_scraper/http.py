from __future__ import annotations

import hashlib
import random
import time
from typing import Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)


BLOCK_STATUS_CODES = {403, 404, 409, 420, 429, 500, 502, 503, 504}


class SourceIPHTTPAdapter(HTTPAdapter):
    def __init__(self, source_address: Optional[Tuple[str, int]] = None, *args, **kwargs):
        self._source_address = source_address
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        if self._source_address:
            pool_kwargs["source_address"] = self._source_address
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        if self._source_address:
            proxy_kwargs["source_address"] = self._source_address
        return super().proxy_manager_for(proxy, **proxy_kwargs)


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]


def build_session(source_ip: Optional[str] = None, outbound_proxy_url: Optional[str] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )

    source_addr = (source_ip, 0) if source_ip else None
    adapter = SourceIPHTTPAdapter(source_address=source_addr, pool_maxsize=32, max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    if outbound_proxy_url:
        session.proxies.update({
            "http": outbound_proxy_url,
            "https": outbound_proxy_url,
        })

    return session


class HTTPError(Exception):
    pass


def _should_retry_response(resp: requests.Response) -> bool:
    if resp is None:
        return True
    if resp.status_code in BLOCK_STATUS_CODES:
        return True
    # Occasionally block pages are 200 with captcha; crude heuristic
    text = resp.text[:1024].lower()
    if "captcha" in text or "temporarily unavailable" in text:
        return True
    return False


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def random_jitter_sleep(min_seconds: float = 0.2, max_seconds: float = 0.9) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def _request(session: requests.Session, method: str, url: str, timeout: float, **kwargs) -> requests.Response:
    # Add cache buster on each attempt
    sep = "&" if ("?" in url) else "?"
    url = f"{url}{sep}nocache={int(time.time() * 1000)}"
    return session.request(method=method, url=url, timeout=timeout, **kwargs)


def retrying_fetch(session: requests.Session, url: str, timeout: float, max_attempts: int) -> requests.Response:
    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception_type((requests.RequestException, HTTPError)),
        reraise=True,
    )
    def _do() -> requests.Response:
        random_jitter_sleep()
        response = _request(session, "GET", url, timeout)
        if _should_retry_response(response):
            # Raise to trigger tenacity retry
            raise HTTPError(f"Retryable status {response.status_code}")
        return response

    return _do()