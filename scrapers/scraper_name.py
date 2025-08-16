from ferc_scraper.config import get_settings
from ferc_scraper.scraper import run_scraper


def main():
    settings = get_settings()
    run_scraper(settings)


if __name__ == "__main__":
    main()