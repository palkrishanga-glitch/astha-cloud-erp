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

class TestAsthaERPPart16Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_document_management_pdf_thermal_whatsapp_email(self):
        # 1. Create Party
        party_res = self.client.post("/api/v1/parties/", json={
            "business_name": "Astha Hardware Client",
            "party_type": "CUSTOMER",
            "mobile": "9876543210",
            "address": "Bhubaneswar Market",
            "state": "Odisha",
            "city": "Bhubaneswar",
            "pincode": "751001",
            "opening_balance": 0.00,
            "opening_balance_type": "DEBIT",
            "opening_balance_date": "2026-04-01"
        })
        self.assertEqual(party_res.status_code, 201)
        party_id = party_res.json()["id"]

        # 2. Create Product
        prod_res = self.client.post("/api/v1/products/", json={
            "sku": "TMT-12MM",
            "product_name": "TMT Rebar 12mm",
            "category_name": "Steel",
            "brand_name": "Tata Tiscon",
            "unit_name": "PCS",
            "hsn_code": "7214",
            "gst_rate": 18.0,
            "purchase_price": 450.0,
            "selling_price": 550.0,
            "cost_price": 450.0,
            "warehouse_name": "Main Central Warehouse",
            "opening_stock": 500.0,
            "opening_stock_date": "2026-04-01"
        })
        self.assertEqual(prod_res.status_code, 201)
        prod_id = prod_res.json()["product_id"]

        # 3. Create POS Sales Invoice
        inv_res = self.client.post("/api/v1/sales/", json={
            "invoice_date": "2026-07-28",
            "party_id": party_id,
            "invoice_type": "CASH",
            "items": [
                {"product_id": prod_id, "quantity": 10.0, "unit_price": 550.0}
            ]
        })
        self.assertEqual(inv_res.status_code, 201)
        inv_no = inv_res.json()["invoice_no"]

        # 4. Test ReportLab PDF Download
        pdf_res = self.client.get(f"/api/v1/sales/{inv_no}/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.headers["content-type"], "application/pdf")
        self.assertTrue(len(pdf_res.content) > 100)

        # 5. Test 3-inch POS Thermal Receipt Text
        thermal_res = self.client.get(f"/api/v1/sales/{inv_no}/thermal")
        self.assertEqual(thermal_res.status_code, 200)
        self.assertIn("ASTHA BUILDERS & HARDWARE", thermal_res.text)

        # 6. Test WhatsApp Sharing URL Generator
        wa_res = self.client.get(f"/api/v1/sales/{inv_no}/whatsapp")
        self.assertEqual(wa_res.status_code, 200)
        self.assertIn("https://wa.me/919876543210", wa_res.json()["whatsapp_url"])

        # 7. Test Email Document Dispatch
        email_res = self.client.post(f"/api/v1/sales/{inv_no}/email", json={
            "recipient_email": "client@asthabuilders.com"
        })
        self.assertEqual(email_res.status_code, 200)
        self.assertEqual(email_res.json()["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
