from ferc_scraper.http import content_sha256


def test_content_sha256_changes():
    h1 = content_sha256("hello")
    h2 = content_sha256("hello!")
    assert h1 != h2