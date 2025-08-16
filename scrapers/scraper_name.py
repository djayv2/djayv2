from ferc_scraper.config import get_settings, Settings
from ferc_scraper.scraper import run_scraper


def main():
    base = get_settings()
    settings: Settings = base.model_copy(update={
        "scraper_mode": "dbindex",
        "create_tables": False,
    })
    run_scraper(settings)


if __name__ == "__main__":
    main()