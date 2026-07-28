import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from services.api.main import app
from services.api.app.database import Base, get_db
from services.api.app.database_migrations import DatabaseMigrationManager

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_astha_master.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAsthaERPMasterSuite(unittest.TestCase):
    """
    Part 23 Enterprise Quality Assurance & Master Regression Test Suite:
    Executes end-to-end integration tests across all 23 ERP modules.
    """
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_complete_enterprise_erp_lifecycle(self):
        # 1. SETUP OWNER ACCOUNT
        setup_res = self.client.post("/api/v1/auth/setup", json={
            "company_name": "Astha Builders & Hardware",
            "owner_username": "admin",
            "owner_email": "admin@asthabuilders.com",
            "owner_mobile": "9876543210",
            "owner_password": "AdminPassword@123",
            "owner_pin": "123456"
        })
        self.assertEqual(setup_res.status_code, 201)

        # 2. AUTHENTICATION & LOGIN
        login_res = self.client.post("/api/v1/auth/login", json={
            "identifier": "admin",
            "password": "AdminPassword@123"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["role"], "Owner")

        # 3. PARTY MASTER & OPENING BALANCE
        party_res = self.client.post("/api/v1/parties/", json={
            "business_name": "Astha Enterprise Hardware Client",
            "party_type": "CUSTOMER",
            "mobile": "9876543210",
            "address": "Bhubaneswar Market",
            "state": "Odisha",
            "city": "Bhubaneswar",
            "pincode": "751001",
            "opening_balance": 5000.00,
            "opening_balance_type": "DEBIT",
            "opening_balance_date": "2026-04-01"
        })
        self.assertEqual(party_res.status_code, 201)
        party_id = party_res.json()["id"]

        # 4. INVENTORY & STOCK LEDGER
        prod_res = self.client.post("/api/v1/products/", json={
            "sku": "TMT-16MM-SUP",
            "product_name": "TMT Steel Rod 16mm",
            "category_name": "Steel",
            "brand_name": "Tata Tiscon",
            "unit_name": "PCS",
            "hsn_code": "7214",
            "gst_rate": 18.0,
            "purchase_price": 500.0,
            "selling_price": 600.0,
            "cost_price": 500.0,
            "warehouse_name": "Central Warehouse",
            "opening_stock": 100.0,
            "opening_stock_date": "2026-04-01"
        })
        self.assertEqual(prod_res.status_code, 201)
        prod_id = prod_res.json()["product_id"]

        # 5. SALES BILLING & DOUBLE ENTRY ACCOUNTING
        inv_res = self.client.post("/api/v1/sales/", json={
            "invoice_date": "2026-07-28",
            "party_id": party_id,
            "invoice_type": "CREDIT",
            "items": [
                {"product_id": prod_id, "quantity": 10.0, "unit_price": 600.0}
            ]
        })
        self.assertEqual(inv_res.status_code, 201)
        inv_no = inv_res.json()["invoice_no"]

        # 6. DOCUMENT ENGINE (PDF & Thermal)
        pdf_res = self.client.get(f"/api/v1/sales/{inv_no}/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.headers["content-type"], "application/pdf")

        thermal_res = self.client.get(f"/api/v1/sales/{inv_no}/thermal")
        self.assertEqual(thermal_res.status_code, 200)
        self.assertIn("ASTHA BUILDERS & HARDWARE", thermal_res.text)

        # 7. GLOBAL SEARCH ENGINE
        search_res = self.client.get("/api/v1/search?q=TMT")
        self.assertEqual(search_res.status_code, 200)
        self.assertTrue(len(search_res.json()["results"]) > 0)

        # 8. MULTI-PC CLOUD SYNC
        reg_res = self.client.post("/api/v1/sync/register-device", json={
            "device_id": "DEV-001",
            "computer_name": "Billing Counter PC 1",
            "os_name": "Windows 11",
            "assigned_branch": "Main Store"
        })
        self.assertEqual(reg_res.status_code, 201)

        sync_push = self.client.post("/api/v1/sync/push", json={
            "device_id": "DEV-001",
            "batch": [
                {
                    "sync_id": "SYNC-001",
                    "module": "SALES",
                    "action": "CREATE",
                    "payload": {"invoice_no": inv_no, "grand_total": 6000.0},
                    "client_timestamp": "2026-07-28T13:45:00Z"
                }
            ]
        })
        self.assertEqual(sync_push.status_code, 200)

        # 9. BACKUP & RESTORE
        bak_res = self.client.post("/api/v1/backup/create")
        self.assertEqual(bak_res.status_code, 201)
        self.assertEqual(bak_res.json()["status"], "SUCCESS")

        # 10. ASTHA AI ASSISTANT
        ai_res = self.client.post("/api/v1/ai/ask", json={
            "query": "What is our total sales revenue and low stock alerts?"
        })
        self.assertEqual(ai_res.status_code, 200)
        self.assertIn("sales revenue", ai_res.json()["ai_response"])

        # 11. DATABASE MIGRATION MANAGER
        migration_mgr = DatabaseMigrationManager(db_path="./test_astha_master.db")
        ver = migration_mgr.get_current_version()
        self.assertTrue(ver.startswith("v"))

        # 12. FINANCIAL & GST REPORTS
        tb_res = self.client.get("/api/v1/reports/trial-balance")
        self.assertEqual(tb_res.status_code, 200)
        self.assertTrue(tb_res.json()["is_balanced"])

        # 13. MASTER PRODUCTION READINESS CHECKLIST
        prod_chk = self.client.get("/api/v1/reports/production-readiness")
        self.assertEqual(prod_chk.status_code, 200)
        self.assertEqual(prod_chk.json()["overall_status"], "PRODUCTION_READY")

if __name__ == "__main__":
    unittest.main()
