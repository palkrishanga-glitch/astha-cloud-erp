import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_party_and_outstanding():
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

    # 1. Create Party
    res = client.post("/api/v1/parties/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["party_code"] == "CUST-101"
    party_id = data["id"]

    # 2. Check Party Ledger (Opening balance should be posted automatically as OP-001)
    res_ledger = client.get(f"/api/v1/parties/{party_id}/ledger")
    assert res_ledger.status_code == 200
    ledger_items = res_ledger.json()
    assert len(ledger_items) == 1
    assert ledger_items[0]["voucher_number"] == "OP-001"
    assert ledger_items[0]["debit"] == 50000.00

    # 3. Check Outstanding Calculation
    res_out = client.get(f"/api/v1/parties/{party_id}/outstanding")
    assert res_out.status_code == 200
    out_data = res_out.json()
    assert out_data["current_outstanding"] == 50000.00
    assert out_data["is_credit_limit_exceeded"] is False
