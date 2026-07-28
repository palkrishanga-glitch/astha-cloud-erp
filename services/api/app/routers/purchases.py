from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models import Party, PartyLedger, Product, StockBatch

router = APIRouter(prefix="/purchases", tags=["Purchase Management"])

class PurchaseInvoiceItemSchema(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit: str = "Pcs"
    purchase_rate: float
    gst_rate: float = 18.0
    batch_number: Optional[str] = "BATCH-001"
    expiry_date: Optional[date] = None

class PurchaseInvoiceCreateSchema(BaseModel):
    supplier_id: str
    supplier_name: str
    invoice_number: str
    invoice_date: date
    warehouse_id: int = 1
    items: List[PurchaseInvoiceItemSchema]
    payment_mode: str = "CREDIT"
    narration: Optional[str] = "Goods Purchased"

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_purchase_invoice(payload: PurchaseInvoiceCreateSchema, db: Session = Depends(get_db)):
    """
    Creates a Purchase Invoice:
    1. Validates Supplier Party account.
    2. Updates or creates physical Inventory Stock Batches in target Warehouse.
    3. Posts a Credit transaction to Supplier Ledger (increasing Payable liability).
    """
    supplier = db.query(Party).filter(Party.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier party not found")

    # 1. Calculate Purchase Totals
    subtotal = sum(item.quantity * item.purchase_rate for item in payload.items)
    gst_total = sum((item.quantity * item.purchase_rate * item.gst_rate) / 100 for item in payload.items)
    grand_total = subtotal + gst_total

    # 2. Increment Stock Batches in Warehouse
    for item in payload.items:
        batch = db.query(StockBatch).filter(
            StockBatch.product_id == item.product_id,
            StockBatch.warehouse_id == payload.warehouse_id,
            StockBatch.batch_number == item.batch_number
        ).first()

        if batch:
            batch.quantity += item.quantity
        else:
            new_batch = StockBatch(
                product_id=item.product_id,
                warehouse_id=payload.warehouse_id,
                batch_number=item.batch_number,
                expiry_date=item.expiry_date,
                quantity=item.quantity,
                purchase_rate=item.purchase_rate,
                selling_rate=item.purchase_rate * 1.20 # 20% default margin
            )
            db.add(new_batch)

    # 3. Post Supplier Ledger Entry (Credit = Amount Payable to Supplier)
    ledgers = db.query(PartyLedger).filter(PartyLedger.party_id == payload.supplier_id).all()
    current_bal = sum(float(l.debit) for l in ledgers) - sum(float(l.credit) for l in ledgers)
    new_bal = current_bal - grand_total # Credit increases payable balance

    supplier_ledger_entry = PartyLedger(
        party_id=payload.supplier_id,
        date=payload.invoice_date,
        voucher_number=payload.invoice_number,
        voucher_type="PURCHASE_INVOICE",
        description=f"Purchase Invoice: {payload.narration}",
        debit=0.00,
        credit=grand_total,
        running_balance=new_bal,
        created_by="SYSTEM_USER",
        timestamp=datetime.utcnow()
    )
    db.add(supplier_ledger_entry)
    db.commit()

    return {
        "status": "SUCCESS",
        "invoice_number": payload.invoice_number,
        "supplier": payload.supplier_name,
        "subtotal": subtotal,
        "gst_total": gst_total,
        "grand_total": grand_total,
        "inventory_updated": True
    }

@router.get("/")
def list_purchase_invoices(db: Session = Depends(get_db)):
    """Returns list of supplier purchases."""
    entries = db.query(PartyLedger).filter(PartyLedger.voucher_type == "PURCHASE_INVOICE").all()
    return [{
        "voucher_number": e.voucher_number,
        "date": str(e.date),
        "supplier_id": e.party_id,
        "amount": float(e.credit),
        "description": e.description
    } for e in entries]
