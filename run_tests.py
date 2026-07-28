import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
from services.api.app.database_migrations import DatabaseMigrationManager, run_latest_migrations

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_astha.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAsthaERPPart22Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_database_migration_manager(self):
        manager = DatabaseMigrationManager(db_path="./test_astha.db")
        
        # 1. Apply Migration v2.0.1
        up_sql = "CREATE INDEX IF NOT EXISTS idx_test_party ON parties(mobile);"
        success = manager.apply_migration("v2.0.1", "Add Test Performance Index", up_sql)
        self.assertTrue(success)

        # 2. Check Version
        curr_ver = manager.get_current_version()
        self.assertEqual(curr_ver, "v2.0.1")

        # 3. Verify Database Integrity
        integrity = manager.verify_integrity()
        self.assertEqual(integrity, "ok")

if __name__ == "__main__":
    unittest.main()
