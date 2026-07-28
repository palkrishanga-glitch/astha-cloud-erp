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

class TestAsthaERPPart18Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_astha_ai_assistant_and_analytics(self):
        # 1. Ask Natural Language Query
        ai_res = self.client.post("/api/v1/ai/ask", json={
            "query": "What is our current sales revenue and stock status?"
        })
        self.assertEqual(ai_res.status_code, 200)
        self.assertEqual(ai_res.json()["status"], "SUCCESS")
        self.assertIn("sales revenue", ai_res.json()["ai_response"])

        # 2. Smart Reorder Recommendations
        reorder_res = self.client.get("/api/v1/ai/smart-reorder")
        self.assertEqual(reorder_res.status_code, 200)
        self.assertIn("total_items_to_reorder", reorder_res.json())

        # 3. Dead Stock Analysis
        dead_res = self.client.get("/api/v1/ai/dead-stock")
        self.assertEqual(dead_res.status_code, 200)
        self.assertIn("total_dead_stock_items", dead_res.json())

        # 4. Predictive Sales Forecast
        forecast_res = self.client.get("/api/v1/ai/sales-forecast")
        self.assertEqual(forecast_res.status_code, 200)
        self.assertIn("projected_next_month_revenue", forecast_res.json())

if __name__ == "__main__":
    unittest.main()
