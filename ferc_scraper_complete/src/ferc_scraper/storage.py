from __future__ import annotations

import contextlib
import logging
from typing import Iterable, List, Optional, Sequence, Tuple

import pg8000

from .config import Settings
from .parser import DocumentItem
from .scd import detect_change_scd2


logger = logging.getLogger(__name__)


class PostgresStorage:
	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._conn: Optional[pg8000.Connection] = None

	def connect(self) -> None:
		if self._conn is not None:
			return
		ssl = None
		if self._settings.db_sslmode in {"require", "verify-ca", "verify-full", "prefer"}:
			ssl = True
		self._conn = pg8000.connect(
			user=self._settings.db_user,
			password=self._settings.db_password,
			host=self._settings.db_host,
			port=self._settings.db_port,
			database=self._settings.db_name,
			ssl_context=ssl,
			timeout=self._settings.db_connect_timeout_seconds,
			application_name=self._settings.application_name,
		)
		self._conn.autocommit = False

	def close(self) -> None:
		if self._conn is not None:
			try:
				self._conn.close()
			finally:
				self._conn = None

	def __enter__(self) -> "PostgresStorage":
		self.connect()
		return self

	def __exit__(self, exc_type, exc, tb) -> None:
		if self._conn is None:
			return
		if exc_type is None:
			self._conn.commit()
		else:
			self._conn.rollback()
		self.close()

	# DDL
	def ensure_schema_and_tables(self) -> None:
		assert self._conn is not None
		schema = self._settings.db_schema
		cur = self._conn.cursor()
		try:
			cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
		except Exception as exc:
			logger.warning("Skipping schema creation for %s due to error: %s", schema, exc)

		# SCD1 table
		cur.execute(
			f"""
			CREATE TABLE IF NOT EXISTS {schema}.ferc_documents_scd1 (
				document_id text PRIMARY KEY,
				source text NOT NULL,
				url text NOT NULL,
				title text NOT NULL,
				published_at timestamptz NULL,
				content_hash text NULL,
				content_text text NULL,
				created_at timestamptz NOT NULL DEFAULT now(),
				updated_at timestamptz NOT NULL DEFAULT now()
			)
			"""
		)

		# SCD2 table
		cur.execute(
			f"""
			CREATE TABLE IF NOT EXISTS {schema}.ferc_documents_scd2 (
				surrogate_id bigserial PRIMARY KEY,
				document_id text NOT NULL,
				source text NOT NULL,
				url text NOT NULL,
				title text NOT NULL,
				published_at timestamptz NULL,
				content_hash text NULL,
				content_text text NULL,
				valid_from timestamptz NOT NULL DEFAULT now(),
				valid_to timestamptz NULL,
				is_current boolean NOT NULL DEFAULT true,
				created_at timestamptz NOT NULL DEFAULT now()
			)
			"""
		)
		cur.execute(
			f"CREATE INDEX IF NOT EXISTS idx_{schema}_ferc_docs_scd2_docid ON {schema}.ferc_documents_scd2 (document_id)"
		)
		cur.execute(
			f"CREATE INDEX IF NOT EXISTS idx_{schema}_ferc_docs_scd2_current ON {schema}.ferc_documents_scd2 (document_id) WHERE is_current"
		)

		self._conn.commit()

	# Sinks
	def upsert_documents(self, items: Sequence[DocumentItem]) -> None:
		if not items:
			return
		assert self._conn is not None
		if self._settings.scd_type == 1:
			self._upsert_scd1(items)
		else:
			self._upsert_scd2(items)

	def _upsert_scd1(self, items: Sequence[DocumentItem]) -> None:
		assert self._conn is not None
		schema = self._settings.db_schema
		cur = self._conn.cursor()
		sql = (
			f"""
			INSERT INTO {schema}.ferc_documents_scd1 (
				document_id, source, url, title, published_at, content_hash, content_text, created_at, updated_at
			) VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now())
			ON CONFLICT (document_id) DO UPDATE SET
				source = EXCLUDED.source,
				url = EXCLUDED.url,
				title = EXCLUDED.title,
				published_at = EXCLUDED.published_at,
				content_hash = EXCLUDED.content_hash,
				content_text = EXCLUDED.content_text,
				updated_at = now()
			"""
		)
		for it in items:
			cur.execute(
				sql,
				(
					it.document_id,
					it.source,
					it.url,
					it.title,
					it.published_at,
					it.content_hash,
					it.content_text,
				),
			)
		self._conn.commit()

	def _upsert_scd2(self, items: Sequence[DocumentItem]) -> None:
		assert self._conn is not None
		schema = self._settings.db_schema
		cur = self._conn.cursor()

		for it in items:
			cur.execute(
				f"SELECT surrogate_id, url, title, published_at, content_hash FROM {schema}.ferc_documents_scd2 WHERE document_id = %s AND is_current = TRUE LIMIT 1",
				(it.document_id,),
			)
			row = cur.fetchone()
			existing = None
			if row:
				existing = {
					"surrogate_id": row[0],
					"url": row[1],
					"title": row[2],
					"published_at": row[3],
					"content_hash": row[4],
				}

			changed = detect_change_scd2(existing or {}, it)
			if not existing:
				cur.execute(
					f"""
					INSERT INTO {schema}.ferc_documents_scd2 (
						document_id, source, url, title, published_at, content_hash, content_text, valid_from, is_current
					) VALUES (%s, %s, %s, %s, %s, %s, %s, now(), TRUE)
					""",
					(
						it.document_id,
						it.source,
						it.url,
						it.title,
						it.published_at,
						it.content_hash,
						it.content_text,
					),
				)
			elif changed:
				cur.execute(
					f"UPDATE {schema}.ferc_documents_scd2 SET is_current = FALSE, valid_to = now() WHERE surrogate_id = %s",
					(existing["surrogate_id"],),
				)
				cur.execute(
					f"""
					INSERT INTO {schema}.ferc_documents_scd2 (
						document_id, source, url, title, published_at, content_hash, content_text, valid_from, is_current
					) VALUES (%s, %s, %s, %s, %s, %s, %s, now(), TRUE)
					""",
					(
						it.document_id,
						it.source,
						it.url,
						it.title,
						it.published_at,
						it.content_hash,
						it.content_text,
					),
				)
			else:
				# No change: nothing to do
				pass

		self._conn.commit()