import os
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Party, PartyLedger, AuditLog
from ..schemas import PartyCreate, PartyOut, PartyLedgerOut, PartyOutstandingResponse
from utils.excel_export import export_data_to_excel
from utils.barcode_qr import generate_barcode_png_bytes, generate_qr_code_png_bytes

router = APIRouter(prefix="/parties", tags=["Parties"])

def generate_next_party_code(db: Session) -> str:
    """Auto-generates sequential Party Code (e.g. PRT-000001)."""
    count = db.query(Party).count()
    return f"PRT-{(count + 1):06d}"

@router.post("/", response_model=PartyOut, status_code=status.HTTP_201_CREATED)
def create_party(party_in: PartyCreate, db: Session = Depends(get_db)):
    # Auto-generate Party Code if omitted
    if not party_in.party_code:
        party_in.party_code = generate_next_party_code(db)
    
    # Check duplicate party code
    existing = db.query(Party).filter(Party.party_code == party_in.party_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Party Code '{party_in.party_code}' already exists.")
    
    # Check duplicate GSTIN if provided
    if party_in.gstin:
        existing_gst = db.query(Party).filter(Party.gstin == party_in.gstin).first()
        if existing_gst:
            raise HTTPException(status_code=400, detail=f"GSTIN '{party_in.gstin}' is already registered to another Party.")

    party_data = party_in.model_dump()
    party = Party(**party_data)
    db.add(party)
    db.flush()

    # Automatically create the first ledger transaction for Opening Balance (OB-000001)
    debit_val = party.opening_balance if party.opening_balance_type == "DEBIT" else 0.00
    credit_val = party.opening_balance if party.opening_balance_type == "CREDIT" else 0.00
    running_bal = debit_val - credit_val

    opening_ledger = PartyLedger(
        party_id=party.id,
        date=party.opening_balance_date,
        voucher_number="OB-000001",
        voucher_type="OPENING_BALANCE",
        reference_number="INIT",
        description="Day-Zero Mandatory Opening Balance Entry",
        debit=debit_val,
        credit=credit_val,
        running_balance=running_bal,
        created_by="SYSTEM_ADMIN",
        timestamp=datetime.utcnow()
    )
    db.add(opening_ledger)

    # Audit log entry
    audit = AuditLog(
        user_id="SYSTEM_ADMIN",
        module="Party Management",
        action="CREATE_PARTY",
        table_name="parties",
        record_id=party.id,
        new_value=f"Created Party {party.party_code} ({party.business_name})",
        status="SUCCESS"
    )
    db.add(audit)

    db.commit()
    db.refresh(party)
    return party

@router.get("/", response_model=List[PartyOut])
def list_parties(party_type: Optional[str] = None, status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Party)
    if party_type:
        query = query.filter(Party.party_type == party_type.upper())
    if status_filter:
        query = query.filter(Party.status == status_filter.upper())
    return query.order_by(Party.created_at.desc()).all()

@router.get("/export/excel")
def export_parties_excel(db: Session = Depends(get_db)):
    """Exports active Parties directory to an Excel spreadsheet (.xlsx)."""
    parties = db.query(Party).all()
    headers = ["Party Code", "Business Name", "Type", "Mobile", "GSTIN", "Credit Limit (Rs)", "Opening Balance", "Balance Type", "City", "State"]
    rows = []
    
    for p in parties:
        rows.append([
            p.party_code,
            p.business_name,
            p.party_type,
            p.mobile,
            p.gstin or "N/A",
            float(p.credit_limit),
            float(p.opening_balance),
            p.opening_balance_type,
            p.city,
            p.state
        ])

    excel_bytes = export_data_to_excel("Party Master Directory", headers, rows)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Party_Master_Directory.xlsx"}
    )

@router.get("/{party_id}/ledger", response_model=List[PartyLedgerOut])
def get_party_ledger(party_id: str, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    return db.query(PartyLedger).filter(PartyLedger.party_id == party_id).order_by(PartyLedger.date.asc(), PartyLedger.timestamp.asc()).all()

@router.get("/{party_id}/outstanding", response_model=PartyOutstandingResponse)
def get_party_outstanding(party_id: str, db: Session = Depends(get_db)):
    """
    Calculates Party Outstanding dynamically from Party Ledger entries.
    Formula: Outstanding = Opening Balance + Sales Invoice + Debit Note + Interest - Receipt Voucher - Credit Note - Sales Return
    """
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
        party_type=party.party_type,
        credit_limit=float(party.credit_limit),
        credit_days=party.credit_days,
        opening_balance=float(party.opening_balance),
        opening_balance_type=party.opening_balance_type,
        current_outstanding=current_outstanding,
        is_credit_limit_exceeded=is_exceeded
    )

@router.delete("/{party_id}", status_code=status.HTTP_200_OK)
def delete_party(party_id: str, db: Session = Depends(get_db)):
    """
    Business Rule Enforcement:
    Deleting a Party is strictly prohibited if financial transactions exist.
    """
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    tx_count = db.query(PartyLedger).filter(
        PartyLedger.party_id == party_id,
        PartyLedger.voucher_type != "OPENING_BALANCE"
    ).count()

    if tx_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete Party '{party.business_name}'. Financial transactions exist on ledger. Change status to INACTIVE instead."
        )

    # Delete opening balance ledger and soft-delete party
    db.query(PartyLedger).filter(PartyLedger.party_id == party_id).delete()
    db.delete(party)
    db.commit()
    return {"status": "SUCCESS", "message": f"Party '{party.business_name}' deleted."}
