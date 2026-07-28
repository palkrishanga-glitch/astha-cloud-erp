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

class TestAsthaERPPart7Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_purchase_procurement_workflow(self):
        # 1. Create Supplier Party
        supp_res = self.client.post("/api/v1/parties/", json={
            "business_name": "JSW Steel Ltd Odisha Yard",
            "party_type": "SUPPLIER",
            "mobile": "9937000000",
            "address": "Kalinganagar Industrial Zone",
            "state": "Odisha",
            "city": "Jajpur",
            "pincode": "755026",
            "opening_balance": 0.00,
            "opening_balance_type": "CREDIT",
            "opening_balance_date": "2026-04-01"
        })
        self.assertEqual(supp_res.status_code, 201)
        supplier_id = supp_res.json()["id"]

        # 2. Create Product with 0 Opening Stock
        prod_res = self.client.post("/api/v1/products/", json={
            "sku": "TMT-16MM-JSW",
            "product_name": "JSW Neosteel TMT Bar 16mm",
            "category_name": "TMT Steel",
            "brand_name": "JSW",
            "unit_name": "Ton",
            "hsn_code": "72142090",
            "gst_rate": 18.00,
            "purchase_price": 52000.00,
            "selling_price": 56000.00,
            "cost_price": 52000.00,
            "opening_stock": 0.00
        })
        self.assertEqual(prod_res.status_code, 201)
        product_id = prod_res.json()["product_id"]

        # 3. Create Purchase Order (PO-2026-000001)
        po_res = self.client.post("/api/v1/purchases/order", json={
            "supplier_id": supplier_id,
            "warehouse_id": 1,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 50.00,
                    "purchase_rate": 51500.00
                }
            ]
        })
        self.assertEqual(po_res.status_code, 201)
        self.assertTrue(po_res.json()["po_number"].startswith("PO-2026-"))

        # 4. Create Purchase Invoice (Receive 50 Tonnes at Rs 51,500/Ton)
        pur_res = self.client.post("/api/v1/purchases/", json={
            "supplier_invoice_no": "JSW-INV-99881",
            "bill_date": "2026-07-28",
            "supplier_id": supplier_id,
            "warehouse_id": 1,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 50.00,
                    "purchase_rate": 51500.00
                }
            ]
        })
        self.assertEqual(pur_res.status_code, 201)
        pur_data = pur_res.json()
        self.assertTrue(pur_data["bill_number"].startswith("PUR-2026-"))

        # Total Taxable = 50 * 51,500 = 2,575,000 + 18% GST (463,500) = 3,038,500.00
        self.assertEqual(pur_data["grand_total"], 3038500.00)

        # 5. Verify Stock Increment (0 -> 50 Tonnes)
        prod_check = self.client.get("/api/v1/products/")
        prod_item = [p for p in prod_check.json() if p["id"] == product_id][0]
        self.assertEqual(prod_item["current_stock"], 50.00)
        self.assertEqual(prod_item["purchase_price"], 51500.00)

        # 6. Verify Supplier Ledger Credit Entry (-3,038,500.00 payable balance)
        supp_out = self.client.get(f"/api/v1/parties/{supplier_id}/outstanding")
        self.assertEqual(supp_out.status_code, 200)
        self.assertEqual(supp_out.json()["current_outstanding"], -3038500.00)

    def test_trial_balance_balancing(self):
        res_tb = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(res_tb.status_code, 200)
        self.assertTrue(res_tb.json()["is_balanced"])

if __name__ == "__main__":
    unittest.main()
