from __future__ import annotations

import csv
import gzip
import io
import os
from typing import Iterable, List, Optional

from .config import Settings
from .parser import DocumentItem
from .storage import PostgresStorage


def ensure_raw_table(storage: PostgresStorage, schema: str, table_name: str) -> None:
    assert storage._conn is not None
    cur = storage._conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
            id bigserial PRIMARY KEY,
            source_url text NOT NULL,
            row_data jsonb NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    storage._conn.commit()


def ingest_csv(storage: PostgresStorage, schema: str, table_name: str, csv_bytes: bytes, source_url: str) -> int:
    ensure_raw_table(storage, schema, table_name)
    assert storage._conn is not None
    cur = storage._conn.cursor()

    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8", errors="ignore")))
    count = 0
    for row in reader:
        cur.execute(
            f"INSERT INTO {schema}.{table_name} (source_url, row_data) VALUES (%s, %s)",
            (source_url, row),
        )
        count += 1
        if count % 1000 == 0:
            storage._conn.commit()
    storage._conn.commit()
    return count