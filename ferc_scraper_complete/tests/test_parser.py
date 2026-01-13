from ferc_scraper.parser import parse_list_page, parse_detail_page


def test_parse_list_page_basic():
    html = """
    <html><body>
      <a href="/dataset/example.zip">Example Dataset</a>
      <a href="/open/data.csv">Data CSV</a>
      <a href="https://www.ferc.gov/downloads/another.zip">Another Dataset</a>
    </body></html>
    """
    items = parse_list_page(html, base_url="https://www.ferc.gov")
    assert len(items) == 3
    assert items[0].url.startswith("https://www.ferc.gov/")
    assert items[0].title == "Example Dataset"
    assert items[1].title == "Data CSV"
    assert items[2].title == "Another Dataset"


def test_parse_detail_page_paragraphs():
    html = """
    <html><body><main>
      <p>Para one.</p>
      <p>Para two.</p>
    </main></body></html>
    """
    text = parse_detail_page(html)
    assert "Para one." in text and "Para two." in text