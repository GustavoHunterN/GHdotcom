import logging
import os
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import errorcode

load_dotenv()

logger = logging.getLogger(__name__)

# Safety cap when limit=None (full home list)
_MAX_ROWS = 500


def _parse_stargazers(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


class DatabaseConnector:
    """MySQL connection and repository-table persistence (no GitHub calls)."""

    def __init__(self) -> None:
        self.connection = None
        self.cursor = None
        self._connect()

    def _connect(self) -> None:
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "3306"))
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                connection_timeout=10,
            )
        except mysql.connector.Error as exc:
            if exc.errno == 2003:
                raise ConnectionError(
                    f"Cannot connect to MySQL at {host}:{port}. "
                    "Ensure mysqld (or Docker) is running and DB_HOST / DB_PORT match. "
                    "On macOS, error 61 usually means nothing is listening on that port."
                ) from exc
            raise
        self.cursor = self.connection.cursor()

    def __enter__(self) -> "DatabaseConnector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self.cursor is not None:
            try:
                self.cursor.close()
            except mysql.connector.Error:
                logger.debug("Cursor close failed", exc_info=True)
            self.cursor = None
        if self.connection is not None:
            try:
                self.connection.close()
            except mysql.connector.Error:
                logger.debug("Connection close failed", exc_info=True)
            self.connection = None

    def list_stored_repo_names(self) -> list[str]:
        """Return the `name` column for all rows in `repos`, or [] if the table is missing."""
        try:
            self.cursor.execute("SELECT name FROM repos")
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as exc:
            if exc.errno == errorcode.ER_NO_SUCH_TABLE:
                return []
            raise

    def list_stored_repo_ids(self) -> list[str]:
        """Return GitHub ``id`` values for all rows in ``repos`` (as strings), or [] if missing table."""
        try:
            self.cursor.execute("SELECT `id` FROM repos")
            return [str(row[0]) for row in self.cursor.fetchall() if row[0] is not None]
        except mysql.connector.Error as exc:
            if exc.errno == errorcode.ER_NO_SUCH_TABLE:
                return []
            raise

    def list_stored_repo_updated_at(self) -> dict[str, str]:
        """
        Map ``id`` -> ``updated_at`` as stored in the DB (GitHub ISO timestamps).
        Used to skip writes when the API payload is not newer than the stored row.
        Returns {} if the table or column is missing.
        """
        try:
            self.cursor.execute("SELECT `id`, `updated_at` FROM repos")
            out: dict[str, str] = {}
            for row in self.cursor.fetchall():
                if row[0] is None or row[1] is None:
                    continue
                out[str(row[0])] = str(row[1])
            return out
        except mysql.connector.Error as exc:
            if exc.errno == errorcode.ER_NO_SUCH_TABLE:
                return {}
            if exc.errno == errorcode.ER_BAD_FIELD_ERROR:
                logger.debug(
                    "repos.updated_at not present; cannot skip by timestamp until next schema sync"
                )
                return {}
            raise

    def drop_repos_table(self) -> None:
        """Remove `repos` entirely (clean resync). Safe if the table does not exist."""
        self.cursor.execute("DROP TABLE IF EXISTS `repos`")
        self.connection.commit()
        logger.info("Dropped table `repos`")

    def ensure_repos_table_for_row(self, row: dict) -> None:
        """
        Ensure `repos` exists and has every column needed for ``row``.
        New GitHub fields (e.g. temp_clone_token) are added with ALTER TABLE so inserts do not fail.
        """
        parts = []
        for key in row:
            col = f"`{key}`"
            if key == "id":
                parts.append(f"{col} VARCHAR(255) PRIMARY KEY")
            else:
                parts.append(f"{col} TEXT")
        columns_sql = ",\n            ".join(parts)
        query = f"""
        CREATE TABLE IF NOT EXISTS repos (
            {columns_sql}
        )
        """
        self.cursor.execute(query)
        self.connection.commit()

        self.cursor.execute("SHOW COLUMNS FROM `repos`")
        existing = {r[0] for r in self.cursor.fetchall()}
        for key in row:
            if key in existing:
                continue
            if key == "id":
                logger.warning(
                    "Skipping ALTER for column 'id': table exists without id; check schema manually."
                )
                continue
            self.cursor.execute(f"ALTER TABLE `repos` ADD COLUMN `{key}` TEXT")
            logger.info("Extended `repos` schema: added column %r", key)
        self.connection.commit()

    def insert_repo_row(self, row: dict) -> None:
        """Insert one row into `repos` (caller ensures schema and missing-only policy)."""
        columns = ", ".join(f"`{k}`" for k in row)
        placeholders = ", ".join(["%s"] * len(row))
        values = tuple(row.values())
        query = f"INSERT INTO repos ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.connection.commit()

    def update_repo_row(self, row: dict) -> None:
        """
        UPDATE all columns except ``id`` for the row identified by ``id`` (primary key).
        Does not change table DDL; caller should ``ensure_repos_table_for_row`` first if schema may have grown.
        """
        if "id" not in row:
            raise ValueError("update_repo_row requires an 'id' key")
        set_cols = {k: v for k, v in row.items() if k != "id"}
        if not set_cols:
            logger.warning(
                "update_repo_row: no columns to update for id=%r; skipping UPDATE",
                row.get("id"),
            )
            return
        assignments = ", ".join(f"`{k}` = %s" for k in set_cols)
        values = list(set_cols.values())
        values.append(row["id"])
        query = f"UPDATE `repos` SET {assignments} WHERE `id` = %s"
        self.cursor.execute(query, tuple(values))
        self.connection.commit()

    def upsert_repo_row(self, row: dict) -> int:
        """
        Insert or update one row by primary key ``id`` using ``INSERT ... ON DUPLICATE KEY UPDATE``.

        MySQL reports affected rows as **1** for a new insert and **2** for an update to an existing row.
        Returns that number (or 0 if the driver does not expose it reliably).
        """
        if "id" not in row:
            raise ValueError("upsert_repo_row requires an 'id' key")
        update_keys = [k for k in row if k != "id"]
        if not update_keys:
            raise ValueError("upsert_repo_row needs at least one column besides id")

        columns = ", ".join(f"`{k}`" for k in row)
        placeholders = ", ".join(["%s"] * len(row))
        values = tuple(row.values())
        update_clause = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in update_keys)
        query = (
            f"INSERT INTO `repos` ({columns}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_clause}"
        )
        self.cursor.execute(query, values)
        self.connection.commit()
        rc = self.cursor.rowcount
        return int(rc) if rc is not None else 0

    def list_repos(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Stored repositories for UI/API: name, description, language, stars, url,
        optional full_name, homepage, preview_image (see GitHub API fields when synced).

        ``limit=None`` uses HOME_REPO_MAX from env (default 100), capped at 500.
        """
        if limit is None:
            cap = int(os.getenv("HOME_REPO_MAX", "100"))
        else:
            cap = int(limit)
        cap = max(1, min(cap, _MAX_ROWS))

        try:
            self.cursor.execute(
                "SELECT * FROM repos ORDER BY `name` ASC LIMIT %s",
                (cap,),
            )
        except mysql.connector.Error as exc:
            if exc.errno == errorcode.ER_NO_SUCH_TABLE:
                return []
            raise

        if not self.cursor.description:
            return []
        columns = [col[0] for col in self.cursor.description]
        raw_rows = self.cursor.fetchall()
        out: list[dict[str, Any]] = []
        for row in raw_rows:
            d = dict(zip(columns, row, strict=True))
            hp = d.get("homepage")
            if hp is not None and str(hp).strip():
                home_url = str(hp).strip()
            else:
                home_url = None
            out.append(
                {
                    "name": d.get("name"),
                    "description": d.get("description"),
                    "language": d.get("language"),
                    "stars": _parse_stargazers(d.get("stargazers_count")),
                    "url": d.get("html_url"),
                    "full_name": d.get("full_name"),
                    "homepage": home_url,
                    # If you add a column later (e.g. screenshot URL), map it here as preview_image.
                    "preview_image": d.get("preview_image_url") or d.get("og_image_url"),
                }
            )
        return out

    def list_repos_preview(self, limit: int = 100) -> list[dict[str, Any]]:
        """Same rows as list_repos; default higher limit for JSON-style consumers."""
        return self.list_repos(limit=limit)
