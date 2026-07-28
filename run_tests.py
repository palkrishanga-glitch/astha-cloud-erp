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

class TestAsthaERPPart8Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_double_entry_accounting_and_vouchers(self):
        # 1. Reject Unbalanced Voucher
        unbal_res = self.client.post("/api/v1/reports/vouchers", json={
            "voucher_date": "2026-07-28",
            "voucher_type": "JOURNAL",
            "narration": "Unbalanced test entry",
            "items": [
                {"account_code": "1001", "debit": 1000.00, "credit": 0.00},
                {"account_code": "1002", "debit": 0.00, "credit": 500.00}
            ]
        })
        self.assertEqual(unbal_res.status_code, 400)
        self.assertIn("Unbalanced Transaction Rejected", unbal_res.json()["detail"])

        # 2. Create Balanced Contra Voucher (Cash to Bank deposit Rs 25,000)
        contra_res = self.client.post("/api/v1/reports/vouchers", json={
            "voucher_date": "2026-07-28",
            "voucher_type": "CONTRA",
            "narration": "Cash deposit into SBI Bank Account",
            "items": [
                {"account_code": "1002", "debit": 25000.00, "credit": 0.00}, # Dr. Bank (1002)
                {"account_code": "1001", "debit": 0.00, "credit": 25000.00}  # Cr. Cash (1001)
            ]
        })
        self.assertEqual(contra_res.status_code, 201)
        self.assertTrue(contra_res.json()["voucher_no"].startswith("CTR-2026-"))

        # 3. Verify Cash Book (-25,000.00 cash balance after deposit)
        cash_res = self.client.get("/api/v1/reports/cash-book")
        self.assertEqual(cash_res.status_code, 200)
        self.assertEqual(cash_res.json()["current_cash_balance"], -25000.00)

        # 4. Verify Bank Book (+25,000.00 bank balance)
        bank_res = self.client.get("/api/v1/reports/bank-book")
        self.assertEqual(bank_res.status_code, 200)
        self.assertEqual(bank_res.json()["current_bank_balance"], 25000.00)

        # 5. Verify Trial Balance
        tb_res = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(tb_res.status_code, 200)
        self.assertTrue(tb_res.json()["is_balanced"])

        # 6. Verify Profit & Loss
        pnl_res = self.client.get("/api/v1/reports/profit-and-loss")
        self.assertEqual(pnl_res.status_code, 200)
        self.assertIn("net_profit", pnl_res.json())

        # 7. Verify Day Book
        day_res = self.client.get("/api/v1/reports/day-book")
        self.assertEqual(day_res.status_code, 200)
        self.assertEqual(day_res.json()["total_transactions"], 1)

if __name__ == "__main__":
    unittest.main()
