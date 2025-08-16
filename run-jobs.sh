#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="ferc-scraper"

docker build -t "$IMAGE_NAME" -f Dockerfile .

docker run --rm \
  -e DB_HOST="${DB_HOST:?missing}" \
  -e DB_PORT="${DB_PORT:-5432}" \
  -e DB_NAME="${DB_NAME:?missing}" \
  -e DB_USER="${DB_USER:?missing}" \
  -e DB_PASSWORD="${DB_PASSWORD:?missing}" \
  -e DB_SCHEMA="${DB_SCHEMA:-test_external}" \
  -e BASE_URL="${BASE_URL:-https://www.ferc.gov/news-events/news}" \
  -e MAX_PAGES="${MAX_PAGES:-1}" \
  -e SCD_TYPE="${SCD_TYPE:-2}" \
  -e FETCH_DETAILS="${FETCH_DETAILS:-true}" \
  -e SOURCE_IP="${SOURCE_IP:-}" \
  -e OUTBOUND_PROXY_URL="${OUTBOUND_PROXY_URL:-}" \
  "$IMAGE_NAME" "$@"