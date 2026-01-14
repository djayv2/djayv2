from __future__ import annotations

import hashlib
import os
import tempfile
from typing import Tuple

import requests

from .http import retrying_fetch


def download_file(session: requests.Session, url: str, timeout: float, max_attempts: int) -> Tuple[str, str, int]:
    resp = retrying_fetch(session, url, timeout=timeout, max_attempts=max_attempts)
    # Stream to temp file
    fd, tmp_path = tempfile.mkstemp(prefix="ferc_dl_", suffix=os.path.splitext(url)[-1][:10])
    os.close(fd)
    sha256 = hashlib.sha256()
    size = 0
    with open(tmp_path, "wb") as f:
        chunk_size = 1024 * 64
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if not chunk:
                continue
            f.write(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return tmp_path, sha256.hexdigest(), size