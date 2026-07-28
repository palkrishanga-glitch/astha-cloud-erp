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

class TestAsthaERPPart14Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_cloud_sync_engine(self):
        # 1. Register Device
        reg_res = self.client.post("/api/v1/sync/register-device", json={
            "device_id": "POS-COUNTER-01",
            "computer_name": "Astha POS Terminal 1",
            "os_name": "Windows 11 Enterprise",
            "assigned_branch": "Bhubaneswar Main Branch"
        })
        self.assertEqual(reg_res.status_code, 201)
        self.assertEqual(reg_res.json()["status"], "SUCCESS")

        # 2. Push Offline Sync Queue Batch
        push_res = self.client.post("/api/v1/sync/push", json={
            "device_id": "POS-COUNTER-01",
            "batch": [
                {
                    "sync_id": "SYNC-001",
                    "module": "SALES",
                    "action": "CREATE",
                    "payload": {"invoice_no": "INV-2026-000001", "total": 1500.00},
                    "client_timestamp": "2026-07-28T13:34:00Z"
                }
            ]
        })
        self.assertEqual(push_res.status_code, 200)
        self.assertEqual(push_res.json()["processed_count"], 1)

        # 3. Pull Incremental Updates
        pull_res = self.client.get("/api/v1/sync/pull?device_id=POS-COUNTER-01")
        self.assertEqual(pull_res.status_code, 200)
        self.assertEqual(pull_res.json()["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
