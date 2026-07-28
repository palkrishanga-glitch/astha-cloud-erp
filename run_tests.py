import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
from services.api.app.schemas_common import APIResponse
from services.api.app.services.erp_service import ERPBusinessService

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

class TestAsthaERPPart11Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_standardized_api_response_schema(self):
        resp = APIResponse(success=True, message="Test Message", data={"key": "val"})
        self.assertTrue(resp.success)
        self.assertEqual(resp.message, "Test Message")
        self.assertEqual(resp.data["key"], "val")
        self.assertIn("Z", resp.timestamp)

    def test_transaction_engine_rollback(self):
        db = TestingSessionLocal()
        
        def failing_action(session):
            p = Base.metadata.tables["parties"]
            # Intentionally cause error to test rollback
            raise ValueError("Forced error for transaction rollback test")

        with self.assertRaises(ValueError):
            ERPBusinessService.execute_transaction_with_rollback(db, failing_action)

        db.close()

    def test_health_api(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
