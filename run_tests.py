import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db

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

class TestAsthaERPPart12Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_backup_and_restore(self):
        # 1. Create Backup
        create_res = self.client.post("/api/v1/backup/create")
        self.assertEqual(create_res.status_code, 201)
        data = create_res.json()
        self.assertEqual(data["status"], "SUCCESS")
        backup_file = data["backup_file"]

        # 2. List Backups
        list_res = self.client.get("/api/v1/backup/list")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(len(list_res.json()["backups"]) > 0)

        # 3. Restore Backup
        restore_res = self.client.post("/api/v1/backup/restore", json={
            "backup_file_name": backup_file,
            "owner_pin": "1234"
        })
        self.assertEqual(restore_res.status_code, 200)
        self.assertEqual(restore_res.json()["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
