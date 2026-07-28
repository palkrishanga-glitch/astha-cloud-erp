import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
from services.api.app.routers.reports import validate_gstin_format

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

class TestAsthaERPPart9Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_gstin_format_validation(self):
        # 1. Valid Odisha GSTIN
        self.assertTrue(validate_gstin_format("21AAAAA0000A1Z5"))

        # 2. Invalid length/characters
        self.assertFalse(validate_gstin_format("INVALID_GSTIN"))

    def test_gstr_reports_and_tax_liability(self):
        # 1. GSTR-1
        g1_res = self.client.get("/api/v1/reports/gstr-1")
        self.assertEqual(g1_res.status_code, 200)
        self.assertIn("total_output_tax_liability", g1_res.json())

        # 2. GSTR-2
        g2_res = self.client.get("/api/v1/reports/gstr-2")
        self.assertEqual(g2_res.status_code, 200)
        self.assertIn("total_input_tax_credit", g2_res.json())

        # 3. GSTR-3B Net Tax Payable
        g3b_res = self.client.get("/api/v1/reports/gstr-3b")
        self.assertEqual(g3b_res.status_code, 200)
        self.assertIn("net_gst_payable_cash", g3b_res.json())

        # 4. HSN Summary
        hsn_res = self.client.get("/api/v1/reports/hsn-summary")
        self.assertEqual(hsn_res.status_code, 200)
        self.assertIsInstance(hsn_res.json(), list)

if __name__ == "__main__":
    unittest.main()
