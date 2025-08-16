from __future__ import annotations

import argparse
import logging
import os

from ferc_scraper.config import get_settings, Settings
from ferc_scraper.scraper import run_scraper


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FERC Web Scraper")
    p.add_argument("--base-url", dest="base_url", default=os.getenv("BASE_URL"))
    p.add_argument("--max-pages", dest="max_pages", type=int, default=os.getenv("MAX_PAGES"))
    p.add_argument("--scd-type", dest="scd_type", type=int, choices=[1, 2], default=os.getenv("SCD_TYPE"))
    p.add_argument("--no-details", dest="fetch_details", action="store_false")
    p.set_defaults(fetch_details=None)
    return p


def merge_cli_into_settings(settings: Settings, args: argparse.Namespace) -> Settings:
    updates = {}
    if args.base_url:
        updates["base_url"] = args.base_url
    if args.max_pages is not None:
        updates["max_pages"] = int(args.max_pages)
    if args.scd_type is not None:
        updates["scd_type"] = int(args.scd_type)
    if args.fetch_details is not None:
        updates["fetch_details"] = bool(args.fetch_details)
    return settings.model_copy(update=updates)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = build_arg_parser()
    args = parser.parse_args()

    settings = get_settings()
    settings = merge_cli_into_settings(settings, args)

    total = run_scraper(settings)
    logging.getLogger(__name__).info("Completed. Total items processed: %d", total)


if __name__ == "__main__":
    main()