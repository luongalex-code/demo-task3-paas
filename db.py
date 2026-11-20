"""Short-lived MySQL connections for the study notes module."""

import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from flask import current_app
from pymysql.constants import CLIENT, ER
from pymysql.cursors import DictCursor


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CA = PROJECT_ROOT / "certs" / "ap-southeast-2-bundle.pem"
NOTES_SCHEMA = PROJECT_ROOT / "sql" / "notes.sql"


class DatabaseUnavailable(Exception):
    """The notes database is unavailable or its configuration is incomplete."""


def connection_options():
    host = os.environ.get("DB_HOST")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    if not all((host, user, password)):
        raise DatabaseUnavailable

    try:
        port = int(os.environ.get("DB_PORT", "3306"))
    except ValueError:
        raise DatabaseUnavailable from None
    if not 1 <= port <= 65535:
        raise DatabaseUnavailable

    ca_bundle = PROJECT_ROOT / Path(os.environ.get("DB_CA_BUNDLE") or DEFAULT_CA)
    if not ca_bundle.is_file():
        raise DatabaseUnavailable

    return {
        "host": host,
        "port": port,
        "database": os.environ.get("DB_NAME") or "cloudlabdb",
        "user": user,
        "password": password,
        "ssl_ca": str(ca_bundle),
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "client_flag": CLIENT.FOUND_ROWS,
        "autocommit": True,
        "connect_timeout": 3,
        "read_timeout": 5,
        "write_timeout": 5,
    }


def ensure_notes_table(cursor):
    try:
        cursor.execute("SELECT 1 FROM notes LIMIT 0")
    except pymysql.err.ProgrammingError as error:
        if error.args[0] != ER.NO_SUCH_TABLE:
            raise
        cursor.execute(NOTES_SCHEMA.read_text(encoding="utf-8"))


@contextmanager
def db_cursor():
    try:
        with pymysql.connect(**connection_options()) as connection:
            with connection.cursor() as cursor:
                ensure_notes_table(cursor)
                yield cursor
    except (pymysql.MySQLError, OSError) as error:
        code = error.args[0] if error.args and isinstance(error.args[0], int) else None
        current_app.logger.warning("Notes database operation failed (%s, code=%s)", type(error).__name__, code)
        raise DatabaseUnavailable from None
