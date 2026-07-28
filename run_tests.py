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

class TestAsthaERPPart3Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_password_policy(self):
        # 1. Too short
        valid, msg = validate_password_policy("Short1!")
        self.assertFalse(valid)

        # 2. No uppercase
        valid, msg = validate_password_policy("astha12345!")
        self.assertFalse(valid)

        # 3. Valid Password
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

        # 1. Setup Owner
        res = self.client.post("/api/v1/auth/setup", json=setup_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        owner_id = data["owner_id"]

        # 2. Login via Email
        login_res = self.client.post("/api/v1/auth/login", json={
            "identifier": "owner@astha-hardware.com",
            "password": "AsthaERP@2026"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("token", login_res.json())

        # 3. Login via Mobile
        login_mob = self.client.post("/api/v1/auth/login", json={
            "identifier": "9876543210",
            "password": "AsthaERP@2026"
        })
        self.assertEqual(login_mob.status_code, 200)

        # 4. Verify Owner PIN
        pin_res = self.client.post("/api/v1/auth/verify-owner-pin", json={
            "owner_id": owner_id,
            "owner_pin": "9999"
        })
        self.assertEqual(pin_res.status_code, 200)
        self.assertTrue(pin_res.json()["valid"])

    def test_barcode_and_qr_generation(self):
        bc_bytes = generate_barcode_png_bytes("AS-2026-1001")
        self.assertTrue(len(bc_bytes) > 100)

        qr_bytes = generate_qr_code_png_bytes("upi://pay?pa=astha@upi&pn=AsthaHardware&am=1500.00")
        self.assertTrue(len(qr_bytes) > 100)

    def test_excel_export(self):
        headers = ["Party Code", "Business Name", "Outstanding Balance (Rs)"]
        rows = [
            ["CUST-101", "Astha Constructions", 50000.00],
            ["SUPP-201", "Ultratech Cements Ltd", -120000.00]
        ]
        excel_bytes = export_data_to_excel("Party Outstanding Report", headers, rows)
        self.assertTrue(len(excel_bytes) > 1000)

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

    def test_trial_balance_and_financial_reports(self):
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

if __name__ == "__main__":
    unittest.main()
