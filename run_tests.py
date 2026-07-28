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

class TestAsthaERPPart17Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_production_readiness_checklist(self):
        res = self.client.get("/api/v1/reports/production-readiness")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["overall_status"], "PRODUCTION_READY")
        chk = data["checklist"]
        
        # Verify 18 checklist points
        self.assertEqual(chk["application_builds_successfully"], "PASS")
        self.assertEqual(chk["desktop_starts_successfully"], "PASS")
        self.assertEqual(chk["web_backend_starts_successfully"], "PASS")
        self.assertEqual(chk["database_migrations_successful"], "PASS")
        self.assertEqual(chk["inventory_verified"], "PASS")
        self.assertEqual(chk["accounting_verified"], "PASS")
        self.assertEqual(chk["gst_verified"], "PASS")
        self.assertEqual(chk["reports_verified"], "PASS")
        self.assertEqual(chk["backup_verified"], "PASS")
        self.assertEqual(chk["restore_verified"], "PASS")
        self.assertEqual(chk["synchronization_verified"], "PASS")
        self.assertEqual(chk["authentication_verified"], "PASS")
        self.assertEqual(chk["authorization_verified"], "PASS")
        self.assertEqual(chk["logging_verified"], "PASS")
        self.assertEqual(chk["audit_verified"], "PASS")
        self.assertEqual(chk["performance_verified"], "PASS")
        self.assertEqual(chk["security_verified"], "PASS")
        self.assertEqual(chk["no_critical_errors"], "PASS")

if __name__ == "__main__":
    unittest.main()
