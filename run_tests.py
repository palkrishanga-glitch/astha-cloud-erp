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

class TestAsthaERPPart13Suite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_ui_ux_design_system_and_templates(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        
        # Verify Part 13 Design Tokens
        self.assertIn("#2563EB", html) # Light Primary
        self.assertIn("#3B82F6", html) # Dark Primary
        self.assertIn("#0F172A", html) # Dark BG
        self.assertIn("#1E293B", html) # Dark Surface
        self.assertIn("#22C55E", html) # Dark Success

        # Verify Keyboard Shortcuts
        self.assertIn("ctrlKey", html)
        self.assertIn("globalSearchInput", html)

if __name__ == "__main__":
    unittest.main()
