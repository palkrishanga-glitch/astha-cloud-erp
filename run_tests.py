import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
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

class TestAsthaERPPart6Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_pos_sales_billing_workflow(self):
        # 1. Create Party
        party_res = self.client.post("/api/v1/parties/", json={
            "business_name": "Utkal Builders",
            "party_type": "CUSTOMER",
            "mobile": "9876500000",
            "address": "Infocity Road",
            "state": "Odisha",
            "city": "Bhubaneswar",
            "pincode": "751024",
            "opening_balance": 0.00,
            "opening_balance_type": "DEBIT",
            "opening_balance_date": "2026-04-01"
        })
        self.assertEqual(party_res.status_code, 201)
        party_id = party_res.json()["id"]

        # 2. Create Product with Opening Stock 100 Tonnes
        prod_res = self.client.post("/api/v1/products/", json={
            "sku": "STEEL-BINDING-WIRE",
            "product_name": "GI Binding Wire 18G",
            "category_name": "Steel Accessories",
            "brand_name": "Tata",
            "unit_name": "Kg",
            "hsn_code": "72171010",
            "gst_rate": 18.00,
            "purchase_price": 70.00,
            "selling_price": 85.00,
            "cost_price": 70.00,
            "opening_stock": 100.00
        })
        self.assertEqual(prod_res.status_code, 201)
        product_id = prod_res.json()["product_id"]

        # 3. Create Sales Invoice (Sell 20 Kg)
        inv_res = self.client.post("/api/v1/sales/", json={
            "invoice_date": "2026-07-28",
            "party_id": party_id,
            "warehouse_id": 1,
            "invoice_type": "CREDIT",
            "payment_mode": "CASH",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 20.00,
                    "unit_price": 85.00,
                    "discount_percent": 0.00
                }
            ]
        })
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.json()
        invoice_no = inv_data["invoice_no"]
        self.assertTrue(invoice_no.startswith("INV-2026-"))
        
        # Grand Total = 20 * 85 = 1700 + 18% GST (306) = 2006.00
        self.assertEqual(inv_data["grand_total"], 2006.00)

        # 4. Verify Stock Deduction (100 - 20 = 80)
        prod_check = self.client.get("/api/v1/products/")
        prod_item = [p for p in prod_check.json() if p["id"] == product_id][0]
        self.assertEqual(prod_item["current_stock"], 80.00)

        # 5. Verify Customer Outstanding Increment (0 + 2006 = 2006.00)
        party_out = self.client.get(f"/api/v1/parties/{party_id}/outstanding")
        self.assertEqual(party_out.status_code, 200)
        self.assertEqual(party_out.json()["current_outstanding"], 2006.00)

        # 6. Stream Thermal Receipt
        res_thermal = self.client.get(f"/api/v1/sales/{invoice_no}/thermal")
        self.assertEqual(res_thermal.status_code, 200)
        self.assertIn("ASTHA BUILDERS & HARDWARE", res_thermal.text)

        # 7. Stream ReportLab Invoice PDF
        res_pdf = self.client.get(f"/api/v1/sales/{invoice_no}/pdf")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.headers["content-type"], "application/pdf")

    def test_trial_balance_balancing(self):
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

if __name__ == "__main__":
    unittest.main()
