# FERC Scraper

A robust Python scraper for FERC with retry logic, optional proxy/source IP binding, and PostgreSQL sink using pg8000. Supports SCD1 and SCD2 storage in schema `test_external`.

Default target is the FERC Download Database index (`https://www.ferc.gov/download-database`). The bundled job (`scrapers/scraper_name.py`) enables full-history dataset ingestion by default into a raw table. To disable, set `INGEST_DATASETS=false`.

## Environment

Required DB env vars:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

Optional:
- `BASE_URL` (default: https://www.ferc.gov/download-database)
- `SCRAPER_MODE` (`dbindex` or `news`; default: `dbindex`)
- `MAX_PAGES` (default: 1; only for `news` mode)
- `SCD_TYPE` (1 or 2; default: 2)
- `FETCH_DETAILS` (default: true; only for `news` mode)
- `CREATE_TABLES` (default: false; set true to let code create tables)
- `OUTBOUND_PROXY_URL`, `SOURCE_IP`
- `DB_SCHEMA` (default: test_external)
- `INGEST_DATASETS` (true/false; default true in `scraper_name.py` job)
- `RAW_TABLE` (default: ferc_raw)

## Run locally

```bash
pip install -r requirements.txt
# Ensure DB tables exist
PYTHONPATH=src python scrapers/scraper_name.py
```

To disable ingestion:
```bash
INGEST_DATASETS=false PYTHONPATH=src python scrapers/scraper_name.py
```

## Docker

```bash
docker build -t ferc-scraper -f Dockerfile .
docker run --rm \
  -e DB_HOST=... -e DB_PORT=5432 -e DB_NAME=... \
  -e DB_USER=... -e DB_PASSWORD=... \
  -e BASE_URL=https://www.ferc.gov/download-database \
  -e SCRAPER_MODE=dbindex \
  -e INGEST_DATASETS=true -e RAW_TABLE=ferc_raw \
  ferc-scraper --max-pages 1
```
