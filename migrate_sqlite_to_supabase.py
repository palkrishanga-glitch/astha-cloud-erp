import os
import sqlite3
import sys

TABLES = [
    "products",
    "sales",
    "customers",
    "suppliers",
    "expenses",
    "payments",
    "purchases",
    "invoice_items",
    "deleted_invoices",
    "settings",
    "web_auth",
    "parties",
    "party_ledgers",
    "vouchers",
    "accounts",
    "audit_logs"
]

def placeholders(count):
    return ", ".join(["%s"] * count)

def main():
    db_url = os.environ.get("ASTHA_DATABASE_URL") or os.environ.get("SUPABASE_DB_URI") or os.environ.get("DATABASE_URL")
    sqlite_path = os.environ.get("ASTHA_SQLITE_PATH", "astha_erp.db")

    if not db_url:
        print("[Migration Warning] Set ASTHA_DATABASE_URL to your Supabase PostgreSQL connection string.")
        return 1
    if not os.path.exists(sqlite_path):
        sqlite_path = "shop.db"
        if not os.path.exists(sqlite_path):
            print(f"[Migration Warning] SQLite database not found: {sqlite_path}")
            return 1

    try:
        import psycopg2
    except ImportError:
        print("[Migration Error] psycopg2-binary package required for Supabase migration.")
        return 1

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(db_url)

    try:
        pg_cur = pg_conn.cursor()
        for table in TABLES:
            try:
                rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
            except sqlite3.OperationalError as exc:
                if "no such table" in str(exc).lower():
                    continue
                raise
            if not rows:
                continue
            columns = rows[0].keys()
            column_sql = ", ".join(columns)
            value_sql = placeholders(len(columns))
            update_sql = ", ".join([f"{column}=EXCLUDED.{column}" for column in columns if column != "id"])
            conflict_sql = "ON CONFLICT (id) DO UPDATE SET " + update_sql if "id" in columns else ""
            sql = f"INSERT INTO {table}({column_sql}) VALUES ({value_sql}) {conflict_sql}"
            for row in rows:
                pg_cur.execute(sql, tuple(row[column] for column in columns))
            print(f"[Migration] {table}: copied {len(rows)} rows to Supabase")

        pg_conn.commit()
        print("[Migration Success] SQLite data successfully migrated to Supabase PostgreSQL.")
        return 0
    except Exception as e:
        pg_conn.rollback()
        print(f"[Migration Failure] Error: {e}")
        return 1
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    sys.exit(main())
