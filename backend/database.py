"""
database.py – MySQL connection pool utility.
Uses mysql-connector-python pooled connections.
All queries go through get_db_connection() context manager.
NEVER uses f-strings for SQL — all queries are parameterised.
"""
import logging
from contextlib import contextmanager
from typing import Generator

import mysql.connector
from mysql.connector import pooling, Error as MySQLError

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Connection Pool (singleton) ───────────────────────────────────────────────
_pool: pooling.MySQLConnectionPool | None = None


def _create_pool() -> pooling.MySQLConnectionPool:
    return pooling.MySQLConnectionPool(
        pool_name="hms_pool",
        pool_size=settings.db_pool_size,
        pool_reset_session=True,
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        autocommit=False,
        time_zone="+00:00",
    )


def get_pool() -> pooling.MySQLConnectionPool:
    """Return (or lazily create) the global connection pool."""
    global _pool
    if _pool is None:
        _pool = _create_pool()
        logger.info("MySQL connection pool created (size=%d)", settings.db_pool_size)
    return _pool


@contextmanager
def get_db_connection() -> Generator[mysql.connector.MySQLConnection, None, None]:
    """
    Yield a pooled connection.
    Auto-commits on clean exit, rolls back on exception.
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            ...
    """
    conn = get_pool().get_connection()
    try:
        yield conn
        conn.commit()
    except MySQLError as exc:
        conn.rollback()
        logger.error("MySQL error — rolled back: %s", exc)
        raise
    except Exception as exc:
        conn.rollback()
        logger.error("Unexpected error — rolled back: %s", exc)
        raise
    finally:
        conn.close()


def execute_query(
    sql: str,
    params: tuple | dict | None = None,
    *,
    fetch_one: bool = False,
    fetch_all: bool = False,
    last_row_id: bool = False,
    conn: mysql.connector.MySQLConnection | None = None,
) -> dict | list[dict] | int | None:
    """
    Convenience wrapper for parameterised queries.
    Pass `conn` to run inside an existing transaction.
    """
    def _run(c: mysql.connector.MySQLConnection):
        cursor = c.cursor(dictionary=True)
        cursor.execute(sql, params)
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        if last_row_id:
            return cursor.lastrowid
        return cursor.rowcount

    if conn is not None:
        return _run(conn)

    with get_db_connection() as c:
        return _run(c)
