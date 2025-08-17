from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from .parser import DocumentItem


@dataclass
class ChangeDecision:
    should_insert: bool
    should_update: bool


def detect_change_scd2(existing: Dict[str, object], incoming: DocumentItem) -> bool:
    if not existing:
        return True
    fields = [
        ("url", existing.get("url"), incoming.url),
        ("title", existing.get("title"), incoming.title),
        ("published_at", existing.get("published_at"), incoming.published_at),
        ("content_hash", existing.get("content_hash"), incoming.content_hash),
    ]
    for _, old, new in fields:
        if old != new:
            return True
    return False