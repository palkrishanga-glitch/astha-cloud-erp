from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime

class PartyBase(BaseModel):
    party_code: Optional[str] = None # Auto-generated if omitted (e.g. PRT-000001)
    business_name: str
    contact_person: Optional[str] = None
    party_type: str = Field(..., description="CUSTOMER, SUPPLIER, or BOTH")
    gstin: Optional[str] = None
    pan: Optional[str] = None
    mobile: str
    alt_mobile: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: str
    address_line2: Optional[str] = None
    state: str
    district: Optional[str] = None
    city: str
    pincode: str
    
    # Business Profile
    gst_registration_type: str = "REGISTERED"
    msme_number: Optional[str] = None
    business_type: str = "RETAIL"
    
    # Financial Information
    credit_limit: float = 0.00
    credit_days: int = 0
    opening_balance: float = 0.00
    opening_balance_type: str = Field("DEBIT", description="DEBIT or CREDIT")
    opening_balance_date: date
    currency: str = "INR"
    default_payment_mode: str = "CASH"
    
    # Bank & Settlement
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    
    remarks: Optional[str] = None
    status: str = "ACTIVE"

class PartyCreate(PartyBase):
    pass

class PartyOut(PartyBase):
    id: str
    party_code: str
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
    reference_number: Optional[str]
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
    party_type: str
    credit_limit: float
    credit_days: int
    opening_balance: float
    opening_balance_type: str
    current_outstanding: float
    is_credit_limit_exceeded: bool
