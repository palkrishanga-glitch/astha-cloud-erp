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

class TestAsthaERPPart10Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_executive_dashboard_cards(self):
        res = self.client.get("/api/v1/reports/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        cards = data["cards"]
        
        # Verify 17 main dashboard card metrics
        self.assertIn("today_sales", cards)
        self.assertIn("today_purchases", cards)
        self.assertIn("today_receipts", cards)
        self.assertIn("today_payments", cards)
        self.assertIn("cash_balance", cards)
        self.assertIn("bank_balance", cards)
        self.assertIn("accounts_receivable", cards)
        self.assertIn("accounts_payable", cards)
        self.assertIn("inventory_value", cards)
        self.assertIn("low_stock_count", cards)
        self.assertIn("net_profit", cards)

    def test_system_health(self):
        res = self.client.get("/api/v1/reports/system-health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["system_status"], "ONLINE")

    def test_global_enterprise_search(self):
        # Create a party to search
        self.client.post("/api/v1/parties/", json={
            "business_name": "Astha Steel Traders",
            "party_type": "CUSTOMER",
            "mobile": "9999900000",
            "address": "Main Street",
            "state": "Odisha",
            "city": "Bhubaneswar",
            "pincode": "751001",
            "opening_balance": 0.00,
            "opening_balance_type": "DEBIT",
            "opening_balance_date": "2026-04-01"
        })

        res = self.client.get("/api/v1/search/?q=Astha")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["total_results"] > 0)
        self.assertEqual(data["results"][0]["entity"], "PARTY")

if __name__ == "__main__":
    unittest.main()
