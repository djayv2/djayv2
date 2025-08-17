from ferc_scraper.parser import parse_list_page, parse_detail_page


def test_parse_list_page_basic():
    html = """
    <html><body>
      <div class="views-row"><a href="/news-events/news/example-item">Example Title</a><span class="date">Jan 1, 2024</span></div>
      <article><a href="https://www.ferc.gov/another">Another</a><time datetime="2024-02-02">Feb 2, 2024</time></article>
    </body></html>
    """
    items = parse_list_page(html, base_url="https://www.ferc.gov")
    assert len(items) == 2
    assert items[0].url.startswith("https://www.ferc.gov/")
    assert items[0].title == "Example Title"


def test_parse_detail_page_paragraphs():
    html = """
    <html><body><main>
      <p>Para one.</p>
      <p>Para two.</p>
    </main></body></html>
    """
    text = parse_detail_page(html)
    assert "Para one." in text and "Para two." in text