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

class TestAsthaERPFullSuite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_party_creation_and_outstanding(self):
        payload = {
            "party_code": "CUST-101",
            "business_name": "Astha Constructions",
            "contact_person": "Rajesh Kumar",
            "party_type": "CUSTOMER",
            "gstin": "21AAAAA0000A1Z5",
            "mobile": "9876543210",
            "address": "Plot 42, Industrial Area",
            "state": "Odisha",
            "city": "Bhubaneswar",
            "pincode": "751001",
            "credit_limit": 500000.00,
            "credit_days": 30,
            "opening_balance": 50000.00,
            "opening_balance_type": "DEBIT",
            "opening_balance_date": "2026-04-01"
        }

        res = self.client.post("/api/v1/parties/", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["party_code"], "CUST-101")

        # Check Outstanding
        res_out = self.client.get(f"/api/v1/parties/{data['id']}/outstanding")
        self.assertEqual(res_out.status_code, 200)
        self.assertEqual(res_out.json()["current_outstanding"], 50000.00)

    def test_pdf_invoice_endpoint(self):
        res = self.client.get("/api/v1/sales/INV-2026-001/pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertTrue(len(res.content) > 1000)

    def test_trial_balance_and_financial_reports(self):
        # 1. Trial Balance
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

        # 2. Profit & Loss
        res_pnl = self.client.get("/api/v1/reports/profit-and-loss")
        self.assertEqual(res_pnl.status_code, 200)
        self.assertIn("net_profit", res_pnl.json())

        # 3. Balance Sheet
        res_bs = self.client.get("/api/v1/reports/balance-sheet")
        self.assertEqual(res_bs.status_code, 200)
        self.assertTrue(res_bs.json()["is_balanced"])

        # 4. GSTR-1 Report
        res_gst = self.client.get("/api/v1/reports/gstr-1")
        self.assertEqual(res_gst.status_code, 200)

    def test_global_search(self):
        res = self.client.get("/api/v1/search/?q=Astha")
        self.assertEqual(res.status_code, 200)
        self.assertIn("results", res.json())

if __name__ == "__main__":
    unittest.main()
