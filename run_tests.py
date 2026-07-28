import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
from services.api.app.auth import validate_password_policy
from utils.barcode_qr import generate_barcode_png_bytes, generate_qr_code_png_bytes
from utils.excel_export import export_data_to_excel

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

class TestAsthaERPPart4Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_party_auto_code_generation(self):
        payload = {
            "business_name": "Balaji Cements Yard",
            "party_type": "SUPPLIER",
            "mobile": "9123456789",
            "address": "Yard 4, Highway",
            "state": "Odisha",
            "city": "Cuttack",
            "pincode": "753001",
            "opening_balance": 100000.00,
            "opening_balance_type": "CREDIT",
            "opening_balance_date": "2026-04-01"
        }
        res = self.client.post("/api/v1/parties/", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["party_code"].startswith("PRT-"))
        self.assertEqual(data["opening_balance_type"], "CREDIT")

    def test_party_excel_export(self):
        res = self.client.get("/api/v1/parties/export/excel")
        self.assertEqual(res.status_code, 200)
        self.assertIn("spreadsheetml", res.headers["content-type"])

    def test_password_policy(self):
        valid, msg = validate_password_policy("AsthaERP@2026")
        self.assertTrue(valid)

    def test_first_time_setup_and_login(self):
        setup_payload = {
            "owner_username": "astha_owner",
            "owner_full_name": "Astha Hardware Owner",
            "owner_email": "owner@astha-hardware.com",
            "owner_mobile": "9876543210",
            "owner_password": "AsthaERP@2026",
            "owner_pin": "9999"
        }
        res = self.client.post("/api/v1/auth/setup", json=setup_payload)
        self.assertEqual(res.status_code, 201)

    def test_barcode_and_qr_generation(self):
        bc_bytes = generate_barcode_png_bytes("AS-2026-1001")
        self.assertTrue(len(bc_bytes) > 100)

        qr_bytes = generate_qr_code_png_bytes("upi://pay?pa=astha@upi&pn=AsthaHardware&am=1500.00")
        self.assertTrue(len(qr_bytes) > 100)

    def test_trial_balance_and_financial_reports(self):
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

if __name__ == "__main__":
    unittest.main()
