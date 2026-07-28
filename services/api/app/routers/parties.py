from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Party, PartyLedger, AuditLog
from ..schemas import PartyCreate, PartyOut, PartyLedgerOut, PartyOutstandingResponse

router = APIRouter(prefix="/parties", tags=["Parties"])

@router.post("/", response_model=PartyOut, status_code=status.HTTP_201_CREATED)
def create_party(party_in: PartyCreate, db: Session = Depends(get_db)):
    # Check duplicate party code or GSTIN
    existing = db.query(Party).filter(Party.party_code == party_in.party_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Party Code already exists.")
    
    party = Party(**party_in.model_dump())
    db.add(party)
    db.flush() # get party.id

    # Automatically create the first ledger transaction for Opening Balance
    debit_val = party.opening_balance if party.opening_balance_type == "DEBIT" else 0.00
    credit_val = party.opening_balance if party.opening_balance_type == "CREDIT" else 0.00
    running_bal = debit_val - credit_val

    opening_ledger = PartyLedger(
        party_id=party.id,
        date=party.opening_balance_date,
        voucher_number="OP-001",
        voucher_type="OPENING_BALANCE",
        description="Day-Zero Opening Balance Entry",
        debit=debit_val,
        credit=credit_val,
        running_balance=running_bal,
        created_by="SYSTEM_ADMIN",
        timestamp=datetime.utcnow()
    )
    db.add(opening_ledger)
    db.commit()
    db.refresh(party)
    return party

@router.get("/", response_model=List[PartyOut])
def list_parties(party_type: str = None, db: Session = Depends(get_db)):
    query = db.query(Party)
    if party_type:
        query = query.filter(Party.party_type == party_type.upper())
    return query.all()

@router.get("/{party_id}/ledger", response_model=List[PartyLedgerOut])
def get_party_ledger(party_id: str, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    return db.query(PartyLedger).filter(PartyLedger.party_id == party_id).order_by(PartyLedger.date.asc(), PartyLedger.timestamp.asc()).all()

@router.get("/{party_id}/outstanding", response_model=PartyOutstandingResponse)
def get_party_outstanding(party_id: str, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    ledgers = db.query(PartyLedger).filter(PartyLedger.party_id == party_id).all()
    total_debits = sum(float(l.debit) for l in ledgers)
    total_credits = sum(float(l.credit) for l in ledgers)
    
    current_outstanding = total_debits - total_credits
    is_exceeded = current_outstanding > float(party.credit_limit) if party.credit_limit > 0 else False

    return PartyOutstandingResponse(
        party_id=party.id,
        party_code=party.party_code,
        business_name=party.business_name,
        credit_limit=float(party.credit_limit),
        opening_balance=float(party.opening_balance),
        opening_balance_type=party.opening_balance_type,
        current_outstanding=current_outstanding,
        is_credit_limit_exceeded=is_exceeded
    )
