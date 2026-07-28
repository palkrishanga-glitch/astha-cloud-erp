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

class TestAsthaERPPart5Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_product_creation_and_stock_ledger(self):
        payload = {
            "sku": "TMT-12MM-JSW",
            "product_name": "JSW Neosteel TMT Bar 12mm",
            "category_name": "TMT Steel",
            "brand_name": "JSW",
            "unit_name": "Ton",
            "hsn_code": "72142090",
            "gst_rate": 18.00,
            "purchase_price": 54000.00,
            "selling_price": 58000.00,
            "cost_price": 54000.00,
            "opening_stock": 10.00,
            "reorder_level": 5.00
        }
        res = self.client.post("/api/v1/products/", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["product_code"].startswith("PRD-"))
        self.assertEqual(data["opening_stock"], 10.00)
        product_id = data["product_id"]

        # Check stock list
        res_list = self.client.get("/api/v1/products/")
        self.assertEqual(res_list.status_code, 200)
        prod_item = [p for p in res_list.json() if p["id"] == product_id][0]
        self.assertEqual(prod_item["current_stock"], 10.00)

        # Stock Adjustment (INCREASE 5 Tons)
        res_adj = self.client.post("/api/v1/products/adjust-stock", json={
            "product_id": product_id,
            "warehouse_id": 1,
            "adjustment_type": "INCREASE",
            "quantity": 5.00,
            "rate": 54000.00,
            "reason": "Physical stock count verification"
        })
        self.assertEqual(res_adj.status_code, 200)
        self.assertEqual(res_adj.json()["new_stock"], 15.00)

        # Stream Barcode Image
        res_bc = self.client.get(f"/api/v1/products/{product_id}/barcode/image")
        self.assertEqual(res_bc.status_code, 200)
        self.assertEqual(res_bc.headers["content-type"], "image/png")

        # Stream QR Image
        res_qr = self.client.get(f"/api/v1/products/{product_id}/qr/image")
        self.assertEqual(res_qr.status_code, 200)
        self.assertEqual(res_qr.headers["content-type"], "image/png")

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

    def test_first_time_setup(self):
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

    def test_trial_balance_and_financial_reports(self):
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

if __name__ == "__main__":
    unittest.main()
