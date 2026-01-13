from datetime import datetime

from ferc_scraper.parser import DocumentItem
from ferc_scraper.scd import detect_change_scd2


def test_detect_change_scd2():
    existing = {
        "url": "https://a",
        "title": "t1",
        "published_at": datetime(2024, 1, 1),
        "content_hash": "h1",
    }
    same = DocumentItem(source="FERC", document_id="1", url="https://a", title="t1", published_at=datetime(2024, 1, 1), content_hash="h1")
    assert not detect_change_scd2(existing, same)

    changed = DocumentItem(source="FERC", document_id="1", url="https://b", title="t1", published_at=datetime(2024, 1, 1), content_hash="h1")
    assert detect_change_scd2(existing, changed)