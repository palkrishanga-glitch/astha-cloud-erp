import os
import shutil
import sqlite3
from datetime import datetime

DB_PATH = "./astha_erp.db"
BACKUP_DIR = "./backups"

class DatabaseMigrationManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_migration_table()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_migration_table(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    migration_name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'SUCCESS'
                );
            """)
            conn.commit()

    def get_current_version(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM db_migrations WHERE status='SUCCESS' ORDER BY id DESC LIMIT 1;")
            row = cursor.fetchone()
            return row[0] if row else "v1.0.0"

    def create_safety_backup(self) -> str:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"pre_migration_{timestamp}.db")
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_file)
        return backup_file

    def apply_migration(self, version: str, migration_name: str, up_sql: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM db_migrations WHERE version=?;", (version,))
            if cursor.fetchone():
                return True # Migration already applied

            # Create backup before applying
            self.create_safety_backup()

            try:
                cursor.executescript(up_sql)
                cursor.execute(
                    "INSERT INTO db_migrations (version, migration_name, status) VALUES (?, ?, 'SUCCESS');",
                    (version, migration_name)
                )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                cursor.execute(
                    "INSERT INTO db_migrations (version, migration_name, status) VALUES (?, ?, 'FAILED');",
                    (version, migration_name)
                )
                conn.commit()
                raise RuntimeError(f"Migration {version} failed: {str(e)}")

    def rollback_migration(self, version: str, down_sql: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executescript(down_sql)
                cursor.execute("DELETE FROM db_migrations WHERE version=?;", (version,))
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"Rollback {version} failed: {str(e)}")

    def verify_integrity(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            return res[0] if res else "FAIL"

def run_latest_migrations():
    manager = DatabaseMigrationManager()

    # Migration v2.0.1: Add Performance Indexes
    v2_0_1_up = """
        CREATE INDEX IF NOT EXISTS idx_sales_inv_no ON sales_invoices(invoice_no);
        CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_invoices(invoice_date);
        CREATE INDEX IF NOT EXISTS idx_stock_prod_id ON stock_ledgers(product_id);
        CREATE INDEX IF NOT EXISTS idx_party_mobile ON parties(mobile);
    """
    manager.apply_migration("v2.0.1", "Add Performance Indexes", v2_0_1_up)
    return manager.get_current_version()
