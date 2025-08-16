# FERC Scraper

A robust Python scraper for FERC site content with retry logic, optional proxy/source IP binding, and PostgreSQL sink using pg8000. Supports SCD1 and SCD2 storage in schema `test_external`.

## Environment

Required DB env vars:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

Optional:
- `BASE_URL` (default: https://www.ferc.gov/news-events/news)
- `MAX_PAGES` (default: 1)
- `SCD_TYPE` (1 or 2; default: 2)
- `FETCH_DETAILS` (default: true)
- `OUTBOUND_PROXY_URL`, `SOURCE_IP`
- `DB_SCHEMA` (default: test_external)

## Run locally

```bash
pip install -r requirements.txt
python main.py --max-pages 1
```

## Docker

```bash
docker build -t ferc-scraper -f Dockerfile .
docker run --rm \
  -e DB_HOST=... -e DB_PORT=5432 -e DB_NAME=... \
  -e DB_USER=... -e DB_PASSWORD=... \
  -e BASE_URL=https://www.ferc.gov/news-events/news \
  ferc-scraper --max-pages 1
```
