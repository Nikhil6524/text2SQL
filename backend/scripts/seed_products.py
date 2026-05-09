from __future__ import annotations

import argparse
import os
import random
from typing import Iterable, List, Tuple
from urllib.parse import urlparse, urlunparse

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv


PRODUCT_NAMES = [
    "Echo Speaker",
    "Nimbus Laptop",
    "Aurora Phone",
    "Zenith Tablet",
    "Pulse Earbuds",
    "Orbit Camera",
    "Summit Watch",
    "Voyage Drone",
    "Atlas Router",
    "Harbor Monitor",
    "Cobalt Keyboard",
    "Lumen Lamp",
    "Vertex Scooter",
    "Cascade Blender",
    "Sierra Backpack",
]

PLACES = [
    "New York",
    "San Francisco",
    "Austin",
    "Seattle",
    "Chicago",
    "Boston",
    "Denver",
    "Miami",
    "Portland",
    "Atlanta",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed product rows into a Postgres database."
    )
    parser.add_argument(
        "--db-name",
        default=None,
        help="Database name to use (default: from connection URL)",
    )
    parser.add_argument(
        "--table-name",
        default="products",
        help="Table name to create/use (default: products)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100,
        help="Number of rows to insert (default: 100)",
    )
    parser.add_argument(
        "--database-url",
        help="Optional Postgres connection URL to use instead of .env settings",
    )
    return parser.parse_args()


def load_database_url(override_url: str | None) -> str:
    if override_url:
        return override_url
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(script_dir, ".."))
    env_path = os.path.join(backend_dir, ".env")
    example_path = os.path.join(backend_dir, ".env.example")

    if os.path.exists(env_path):
        load_dotenv(env_path)
    elif os.path.exists(example_path):
        load_dotenv(example_path)
    else:
        load_dotenv()

    database_url = os.getenv("AIVEN_POSTGRES_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Missing AIVEN_POSTGRES_URL or DATABASE_URL in environment")
    return database_url


def base_admin_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError("Invalid database URL")
    if parsed.scheme in {"http", "https"}:
        parsed = parsed._replace(scheme="postgresql")
    # Use the database from the URL (Aiven often does not expose 'postgres').
    if parsed.path and parsed.path != "/":
        return urlunparse(parsed)
    return urlunparse(parsed._replace(path="/postgres"))


def extract_db_name(database_url: str) -> str | None:
    parsed = urlparse(database_url)
    if parsed.path and parsed.path != "/":
        return parsed.path.lstrip("/")
    return None


def database_url_for(database_url: str, db_name: str) -> str:
    parsed = urlparse(database_url)
    if parsed.scheme in {"http", "https"}:
        parsed = parsed._replace(scheme="postgresql")
    return urlunparse(parsed._replace(path=f"/{db_name}"))


def ensure_database_exists(admin_url: str, db_name: str) -> None:
    conn = psycopg2.connect(admin_url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}" ).format(sql.Identifier(db_name)))
    finally:
        conn.close()


def ensure_table(conn: psycopg2.extensions.connection, table_name: str) -> None:
    create_table_sql = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            place TEXT NOT NULL,
            cost NUMERIC(12, 2) NOT NULL,
            rating NUMERIC(2, 1) NOT NULL,
            depreciation_per_year NUMERIC(5, 2) NOT NULL
        );
        """
    ).format(table=sql.Identifier(table_name))

    with conn.cursor() as cur:
        cur.execute(create_table_sql)


def clear_table(conn: psycopg2.extensions.connection, table_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY;").format(sql.Identifier(table_name)))


def generate_rows(count: int) -> List[Tuple[str, str, float, float, float]]:
    random.seed(42)
    rows: List[Tuple[str, str, float, float, float]] = []
    for idx in range(count):
        name = random.choice(PRODUCT_NAMES)
        place = random.choice(PLACES)
        base_cost = random.uniform(49.0, 1999.0)
        rating = round(random.uniform(3.2, 4.9), 1)
        depreciation = round(base_cost * random.uniform(0.05, 0.18), 2)
        # Make names slightly distinct across rows.
        labeled_name = f"{name} {idx + 1:03d}"
        rows.append((labeled_name, place, round(base_cost, 2), rating, depreciation))
    return rows


def insert_rows(
    conn: psycopg2.extensions.connection,
    table_name: str,
    rows: Iterable[Tuple[str, str, float, float, float]],
) -> None:
    insert_sql = sql.SQL(
        "INSERT INTO {table} (name, place, cost, rating, depreciation_per_year) VALUES %s"
    ).format(table=sql.Identifier(table_name))

    with conn.cursor() as cur:
        execute_values(cur, insert_sql, list(rows))


def main() -> None:
    args = parse_args()
    database_url = load_database_url(args.database_url)
    current_db = extract_db_name(database_url)
    db_name = args.db_name or current_db or "products_db"
    admin_url = base_admin_url(database_url)
    target_url = database_url_for(database_url, db_name)

    if current_db is None or db_name != current_db:
        ensure_database_exists(admin_url, db_name)

    conn = psycopg2.connect(target_url)
    try:
        ensure_table(conn, args.table_name)
        clear_table(conn, args.table_name)
        rows = generate_rows(args.rows)
        insert_rows(conn, args.table_name, rows)
        conn.commit()
    finally:
        conn.close()

    print(f"Seeded {args.rows} rows into {db_name}.{args.table_name}.")


if __name__ == "__main__":
    main()
