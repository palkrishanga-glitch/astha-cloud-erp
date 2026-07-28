from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime

class PartyBase(BaseModel):
    party_code: str
    business_name: str
    contact_person: Optional[str] = None
    party_type: str = Field(..., description="CUSTOMER, SUPPLIER, or BOTH")
    gstin: Optional[str] = None
    pan: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    address: str
    state: str
    district: Optional[str] = None
    city: str
    pincode: str
    credit_limit: float = 0.00
    credit_days: int = 0
    opening_balance: float = 0.00
    opening_balance_type: str = Field("DEBIT", description="DEBIT or CREDIT")
    opening_balance_date: date
    status: str = "ACTIVE"

class PartyCreate(PartyBase):
    pass

class PartyOut(PartyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PartyLedgerOut(BaseModel):
    id: str
    party_id: str
    date: date
    voucher_number: str
    voucher_type: str
    description: Optional[str]
    debit: float
    credit: float
    running_balance: float
    created_by: str
    timestamp: datetime

    class Config:
        from_attributes = True

class PartyOutstandingResponse(BaseModel):
    party_id: str
    party_code: str
    business_name: str
    credit_limit: float
    opening_balance: float
    opening_balance_type: str
    current_outstanding: float
    is_credit_limit_exceeded: bool
