"""Copy bookings and customers from old database to new database.

Usage:
    OLD_DATABASE_URL=postgresql://... python scripts/copy_old_db.py

Requires OLD_DATABASE_URL env var for the source database.
Uses DATABASE_URL from .env for the destination (new) database.
"""

import os
import sys

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = 1000

# Columns to exclude when copying (lowercase for comparison)
BOOKING_EXCLUDE = {"id", "_team_share_total", "team_leader"}
CUSTOMER_EXCLUDE = {"id"}


def log(msg):
    """Print with immediate flush for real-time output."""
    print(msg, flush=True)


def q(name):
    """Double-quote a column name for case-sensitive PostgreSQL identifiers."""
    return f'"{name}"'


def get_connections():
    """Return (old_conn, new_conn) psycopg2 connections."""
    old_url = os.environ.get("OLD_DATABASE_URL")
    new_url = os.environ.get("DATABASE_URL")

    if not old_url:
        log("ERROR: OLD_DATABASE_URL environment variable is required")
        sys.exit(1)
    if not new_url:
        log("ERROR: DATABASE_URL environment variable is required (check .env)")
        sys.exit(1)

    # Normalize postgres:// to postgresql://
    old_url = old_url.replace("postgres://", "postgresql://", 1)
    new_url = new_url.replace("postgres://", "postgresql://", 1)

    old_conn = psycopg2.connect(old_url)
    new_conn = psycopg2.connect(new_url)
    return old_conn, new_conn


def get_table_columns(conn, table_name):
    """Get column names for a table."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s ORDER BY ordinal_position",
            (table_name,),
        )
        return [row[0] for row in cur.fetchall()]


def get_count(conn, table_name):
    """Get row count for a table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]


def upgrade_customer_index(new_conn):
    """Upgrade customer_id index to unique (required for ON CONFLICT)."""
    with new_conn.cursor() as cur:
        # Check if the index already exists and is unique
        cur.execute("""
            SELECT i.relname, ix.indisunique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            WHERE t.relname = 'customer'
              AND i.relname = 'ix_customer_customer_id'
        """)
        row = cur.fetchone()
        if row and row[1]:
            log("  customer_id index is already unique")
            return

        # Drop old non-unique index and create unique one
        log("  Upgrading ix_customer_customer_id to UNIQUE...")
        cur.execute("DROP INDEX IF EXISTS ix_customer_customer_id")
        cur.execute(
            "CREATE UNIQUE INDEX ix_customer_customer_id ON customer (customer_id)"
        )
        new_conn.commit()
        log("  Done — customer_id index is now unique")


def build_column_mapping(old_cols, new_cols, exclude_set):
    """Build (old_name, new_name) pairs via case-insensitive matching."""
    new_cols_map = {c.lower(): c for c in new_cols}
    pairs = []
    for c in old_cols:
        if c.lower() in exclude_set:
            continue
        new_name = new_cols_map.get(c.lower())
        if new_name:
            pairs.append((c, new_name))
    return pairs


def build_upsert_sql(table, new_copy_cols, conflict_col, timestamp_col="_updated_at"):
    """Build an INSERT ... ON CONFLICT DO UPDATE upsert SQL template."""
    cols_csv = ", ".join(q(c) for c in new_copy_cols)
    # %s placeholder per column — used by execute_values template
    placeholders = ", ".join(["%s"] * len(new_copy_cols))

    update_cols = [c for c in new_copy_cols if c.lower() != conflict_col]
    update_set = ", ".join(f"{q(c)} = EXCLUDED.{q(c)}" for c in update_cols)

    return f"""
        INSERT INTO {table} ({cols_csv})
        VALUES %s
        ON CONFLICT ({conflict_col}) DO UPDATE SET {update_set}
        WHERE EXCLUDED.{q(timestamp_col)} > {table}.{q(timestamp_col)}
           OR {table}.{q(timestamp_col)} IS NULL
    """


def copy_bookings(old_conn, new_conn):
    """Copy bookings from old DB to new DB using fast batch inserts."""
    log("\n--- Copying bookings ---")

    old_cols = get_table_columns(old_conn, "bookings")
    new_cols = get_table_columns(new_conn, "bookings")

    copy_pairs = build_column_mapping(old_cols, new_cols, BOOKING_EXCLUDE)
    old_copy_cols = [p[0] for p in copy_pairs]
    new_copy_cols = [p[1] for p in copy_pairs]
    log(f"  Columns to copy: {len(copy_pairs)} (excluded: {BOOKING_EXCLUDE})")

    if "booking_id" not in [c.lower() for c in new_copy_cols]:
        log("ERROR: booking_id column not found in both databases")
        sys.exit(1)

    upsert_sql = build_upsert_sql("bookings", new_copy_cols, "booking_id")

    # Column indices for extracting values from old DB rows
    col_indices = {c: i for i, c in enumerate(old_cols)}
    copy_indices = [col_indices[c] for c in old_copy_cols]

    total = get_count(old_conn, "bookings")
    log(f"  Old DB bookings: {total:,}")

    affected_total = 0
    rows_processed = 0

    with old_conn.cursor(name="bookings_cursor") as old_cur:
        old_cur.itersize = BATCH_SIZE
        old_cur.execute("SELECT * FROM bookings ORDER BY id")

        batch = []
        for row in old_cur:
            batch.append(tuple(row[i] for i in copy_indices))

            if len(batch) >= BATCH_SIZE:
                with new_conn.cursor() as new_cur:
                    psycopg2.extras.execute_values(new_cur, upsert_sql, batch)
                    affected_total += new_cur.rowcount
                rows_processed += len(batch)
                batch = []
                if rows_processed % 50_000 == 0:
                    log(f"  Processed {rows_processed:,} / {total:,} rows...")

        # Final partial batch
        if batch:
            with new_conn.cursor() as new_cur:
                psycopg2.extras.execute_values(new_cur, upsert_sql, batch)
                affected_total += new_cur.rowcount
            rows_processed += len(batch)

    new_conn.commit()
    skipped = rows_processed - affected_total
    log(f"  Rows processed: {rows_processed:,}")
    log(f"  Inserted/updated: {affected_total:,}, Skipped (newer in new DB): {skipped:,}")
    return affected_total, skipped


def copy_customers(old_conn, new_conn):
    """Copy customers from old DB to new DB, deduplicating by customer_id."""
    log("\n--- Copying customers ---")

    old_cols = get_table_columns(old_conn, "customer")
    new_cols = get_table_columns(new_conn, "customer")

    copy_pairs = build_column_mapping(old_cols, new_cols, CUSTOMER_EXCLUDE)
    old_copy_cols = [p[0] for p in copy_pairs]
    new_copy_cols = [p[1] for p in copy_pairs]
    log(f"  Columns to copy: {len(copy_pairs)}")

    if "customer_id" not in [c.lower() for c in new_copy_cols]:
        log("ERROR: customer_id column not found in both databases")
        sys.exit(1)

    upsert_sql = build_upsert_sql("customer", new_copy_cols, "customer_id")

    col_indices = {c: i for i, c in enumerate(old_cols)}
    copy_indices = [col_indices[c] for c in old_copy_cols]

    # Fetch deduplicated: keep latest _updated_at per customer_id
    dedup_sql = """
        SELECT DISTINCT ON (customer_id) *
        FROM customer
        ORDER BY customer_id, _updated_at DESC NULLS LAST
    """

    total_raw = get_count(old_conn, "customer")
    log(f"  Old DB customers (raw): {total_raw:,}")

    affected_total = 0
    dedup_count = 0

    with old_conn.cursor(name="customers_cursor") as old_cur:
        old_cur.itersize = BATCH_SIZE
        old_cur.execute(dedup_sql)

        batch = []
        for row in old_cur:
            dedup_count += 1
            batch.append(tuple(row[i] for i in copy_indices))

            if len(batch) >= BATCH_SIZE:
                with new_conn.cursor() as new_cur:
                    psycopg2.extras.execute_values(new_cur, upsert_sql, batch)
                    affected_total += new_cur.rowcount
                batch = []

        if batch:
            with new_conn.cursor() as new_cur:
                psycopg2.extras.execute_values(new_cur, upsert_sql, batch)
                affected_total += new_cur.rowcount

    new_conn.commit()
    skipped = dedup_count - affected_total
    log(f"  Deduplicated customers: {dedup_count:,} (from {total_raw:,} raw)")
    log(f"  Inserted/updated: {affected_total:,}, Skipped (newer in new DB): {skipped:,}")
    return affected_total, skipped


def main():
    log("=== Copy Old DB to New DB ===\n")

    old_conn, new_conn = get_connections()

    try:
        # Print before counts
        old_bookings = get_count(old_conn, "bookings")
        old_customers = get_count(old_conn, "customer")
        new_bookings = get_count(new_conn, "bookings")
        new_customers = get_count(new_conn, "customer")

        log(f"Before:")
        log(f"  Old DB — bookings: {old_bookings:,}, customers: {old_customers:,}")
        log(f"  New DB — bookings: {new_bookings:,}, customers: {new_customers:,}")

        # Upgrade customer_id index to unique
        log("\n--- Upgrading customer_id index ---")
        upgrade_customer_index(new_conn)

        # Copy data
        b_inserted, b_skipped = copy_bookings(old_conn, new_conn)
        c_inserted, c_skipped = copy_customers(old_conn, new_conn)

        # Print after counts
        new_bookings_after = get_count(new_conn, "bookings")
        new_customers_after = get_count(new_conn, "customer")

        log(f"\nAfter:")
        log(f"  New DB — bookings: {new_bookings_after:,}, customers: {new_customers_after:,}")

        log(f"\nSummary:")
        log(f"  Bookings  — inserted/updated: {b_inserted:,}, skipped: {b_skipped:,}")
        log(f"  Customers — inserted/updated: {c_inserted:,}, skipped: {c_skipped:,}")

    finally:
        old_conn.close()
        new_conn.close()

    log("\nDone!")


if __name__ == "__main__":
    main()
