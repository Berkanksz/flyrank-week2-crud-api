"""Repository: the only module in this app that talks to the database.

Routes in main.py call these functions and never see SQL or the driver.
Swapping storage (memory -> SQLite -> Postgres) only changes this file.
"""
import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

# Read .env into the environment. Variables that are already set
# (for example by docker compose) win over the file.
load_dotenv()

# Example tasks inserted only on the very first run (when the table is empty).
SEED_TASKS = [
    ("Buy milk", False),
    ("Learn FastAPI", True),
    ("Complete internship assignment", False),
]


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return url


@contextmanager
def get_db():
    """One connection per call. psycopg commits on success, rolls back on error, then closes."""
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        yield conn


def init_db():
    """Create the tasks table if it is missing and seed it once."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id    SERIAL  PRIMARY KEY,
                title TEXT    NOT NULL,
                done  BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        # Same first-run rule as A2. The whole block is one transaction,
        # so the three seed rows are inserted all together or not at all.
        count = conn.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        if count == 0:
            with conn.cursor() as cur:
                cur.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", SEED_TASKS)
