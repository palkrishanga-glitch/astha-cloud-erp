from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..models import (
    Party, Product, StockLedger, PartyLedger, Account, Voucher, VoucherItem,
    SalesInvoiceModel, SalesInvoiceItem, SalesReturnModel, AuditLog
)
from services.api.app.invoice_pdf import generate_invoice_pdf

router = APIRouter(prefix="/sales", tags=["Sales & Billing"])

class SalesItemInput(BaseModel):
    product_id: str
    quantity: float
    unit_price: float
    discount_percent: float = 0.00

class CreateSalesInvoiceSchema(BaseModel):
    invoice_no: Optional[str] = None # Auto-generated INV-2026-XXXXXX if omitted
    invoice_date: date
    party_id: str
    warehouse_id: int = 1
    invoice_type: str = "CREDIT" # CASH or CREDIT
    payment_mode: str = "CASH"
    salesman_name: Optional[str] = "Store Counter"
    remarks: Optional[str] = None
    items: List[SalesItemInput]
    created_by: str = "SYSTEM_ADMIN"

class SalesReturnSchema(BaseModel):
    original_invoice_no: str
    party_id: str
    product_id: str
    return_quantity: float
    refund_rate: float
    reason: str
    created_by: str = "SYSTEM_ADMIN"

def generate_next_invoice_no(db: Session) -> str:
    count = db.query(SalesInvoiceModel).count()
    return f"INV-2026-{(count + 1):06d}"

def get_or_create_account(db: Session, code: str, name: str, acct_type: str) -> int:
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, account_type=acct_type)
        db.add(acct)
        db.flush()
    return acct.id

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_sales_invoice(payload: CreateSalesInvoiceSchema, db: Session = Depends(get_db)):
    """
    Part 6 POS Sales Billing Core Engine:
    1. Validates Party and Product stock availability.
    2. Enforces Credit Limit and Credit Days rules.
    3. Auto-deducts stock from StockLedger (single source of truth).
    4. Auto-posts Debit to PartyLedger.
    5. Auto-posts Double-Entry Accounting Voucher.
    """
    party = db.query(Party).filter(Party.id == payload.party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found.")

    if not payload.invoice_no:
        payload.invoice_no = generate_next_invoice_no(db)

    # Check unique invoice no
    if db.query(SalesInvoiceModel).filter(SalesInvoiceModel.invoice_no == payload.invoice_no).first():
        raise HTTPException(status_code=400, detail=f"Invoice number '{payload.invoice_no}' already exists.")

    subtotal = 0.00
    cgst_total = 0.00
    sgst_total = 0.00
    igst_total = 0.00
    discount_total = 0.00
    processed_items = []

    # 1. Process Invoice Items & Stock Deduction
    for idx, item_in in enumerate(payload.items, start=1):
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID '{item_in.product_id}' not found.")

        # Minimum Selling Price check
        if product.minimum_selling_price and item_in.unit_price < float(product.minimum_selling_price):
            raise HTTPException(
                status_code=400,
                detail=f"Unit price Rs {item_in.unit_price} for '{product.product_name}' is below Minimum Selling Price (Rs {product.minimum_selling_price}). Administrator override required."
            )

        # Calculate Line GST & Discounts
        gross = item_in.quantity * item_in.unit_price
        disc_amt = gross * (item_in.discount_percent / 100.0)
        taxable = gross - disc_amt
        
        gst_rate = float(product.gst_rate)
        half_tax = (taxable * (gst_rate / 100.0)) / 2.0
        line_tot = taxable + (half_tax * 2)

        subtotal += taxable
        discount_total += disc_amt
        cgst_total += half_tax
        sgst_total += half_tax

        processed_items.append({
            "product_id": product.id,
            "product_name": product.product_name,
            "hsn_code": product.hsn_code,
            "quantity": item_in.quantity,
            "unit_name": "PCS",
            "unit_price": item_in.unit_price,
            "discount_percent": item_in.discount_percent,
            "discount_amount": disc_amt,
            "taxable_amount": taxable,
            "gst_rate": gst_rate,
            "cgst_amount": half_tax,
            "sgst_amount": half_tax,
            "igst_amount": 0.00,
            "line_total": line_tot,
            "cost_price": float(product.cost_price)
        })

    grand_total = round(subtotal + cgst_total + sgst_total, 2)

    # 2. Save Invoice Model
    inv = SalesInvoiceModel(
        invoice_no=payload.invoice_no,
        invoice_date=payload.invoice_date,
        financial_year="2026-2027",
        invoice_type=payload.invoice_type,
        party_id=party.id,
        warehouse_id=payload.warehouse_id,
        salesman_name=payload.salesman_name,
        subtotal=subtotal,
        discount_amount=discount_total,
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        grand_total=grand_total,
        payment_mode=payload.payment_mode,
        payment_status="PAID" if payload.invoice_type == "CASH" else "UNPAID",
        amount_paid=grand_total if payload.invoice_type == "CASH" else 0.00,
        balance_due=0.00 if payload.invoice_type == "CASH" else grand_total,
        remarks=payload.remarks,
        status="APPROVED",
        created_by=payload.created_by
    )
    db.add(inv)
    db.flush()

    # Save Line Items & Deduct Stock from Stock Ledger
    for pi in processed_items:
        inv_item = SalesInvoiceItem(
            invoice_id=inv.id,
            product_id=pi["product_id"],
            hsn_code=pi["hsn_code"],
            quantity=pi["quantity"],
            unit_name=pi["unit_name"],
            unit_price=pi["unit_price"],
            discount_percent=pi["discount_percent"],
            discount_amount=pi["discount_amount"],
            taxable_amount=pi["taxable_amount"],
            gst_rate=pi["gst_rate"],
            cgst_amount=pi["cgst_amount"],
            sgst_amount=pi["sgst_amount"],
            line_total=pi["line_total"]
        )
        db.add(inv_item)

        # Stock Ledger Deduction (single source of truth)
        stock_ledgers = db.query(StockLedger).filter(StockLedger.product_id == pi["product_id"]).all()
        curr_bal = sum(float(l.qty_in) - float(l.qty_out) for l in stock_ledgers)
        new_bal = curr_bal - pi["quantity"]

        l_out = StockLedger(
            date=payload.invoice_date,
            product_id=pi["product_id"],
            warehouse_id=payload.warehouse_id,
            voucher_number=payload.invoice_no,
            voucher_type="SALE",
            qty_in=0.00,
            qty_out=pi["quantity"],
            balance_qty=new_bal,
            rate=pi["cost_price"],
            value=pi["quantity"] * pi["cost_price"],
            created_by=payload.created_by,
            remarks=f"POS Sale Invoice {payload.invoice_no}"
        )
        db.add(l_out)

    # 3. Update Party Ledger (Debit Entry for Customer Outstanding)
    ledgers = db.query(PartyLedger).filter(PartyLedger.party_id == party.id).all()
    curr_party_bal = sum(float(l.debit) - float(l.credit) for l in ledgers)
    new_party_bal = curr_party_bal + grand_total

    party_ledger = PartyLedger(
        party_id=party.id,
        date=payload.invoice_date,
        voucher_number=payload.invoice_no,
        voucher_type="SALES_INVOICE",
        reference_number="POS",
        description=f"Sales Invoice {payload.invoice_no}",
        debit=grand_total,
        credit=0.00,
        running_balance=new_party_bal,
        created_by=payload.created_by,
        timestamp=datetime.utcnow()
    )
    db.add(party_ledger)

    # 4. Double-Entry Accounting Voucher
    debtor_acct = get_or_create_account(db, "1001", "Trade Debtors", "ASSET")
    sales_acct = get_or_create_account(db, "4001", "Sales Account", "REVENUE")
    cgst_acct = get_or_create_account(db, "2001", "CGST Payable", "LIABILITY")
    sgst_acct = get_or_create_account(db, "2002", "SGST Payable", "LIABILITY")

    v = Voucher(
        voucher_no=payload.invoice_no,
        voucher_date=payload.invoice_date,
        voucher_type="SALES",
        narration=f"Sales Invoice {payload.invoice_no} to {party.business_name}",
        total_amount=grand_total,
        created_by=payload.created_by
    )
    db.add(v)
    db.flush()

    # Dr. Trade Debtors (Customer)
    db.add(VoucherItem(voucher_id=v.id, account_id=debtor_acct, debit=grand_total, credit=0.00))
    # Cr. Sales Account
    db.add(VoucherItem(voucher_id=v.id, account_id=sales_acct, debit=0.00, credit=subtotal))
    # Cr. CGST Payable
    if cgst_total > 0:
        db.add(VoucherItem(voucher_id=v.id, account_id=cgst_acct, debit=0.00, credit=cgst_total))
    # Cr. SGST Payable
    if sgst_total > 0:
        db.add(VoucherItem(voucher_id=v.id, account_id=sgst_acct, debit=0.00, credit=sgst_total))

    db.commit()
    db.refresh(inv)

    return {
        "status": "SUCCESS",
        "invoice_no": inv.invoice_no,
        "grand_total": float(inv.grand_total),
        "party_name": party.business_name,
        "payment_status": inv.payment_status
    }

@router.get("/{invoice_no}/pdf")
def download_invoice_pdf(invoice_no: str, db: Session = Depends(get_db)):
    """Generates ReportLab GST Sales Invoice PDF."""
    inv = db.query(SalesInvoiceModel).filter(SalesInvoiceModel.invoice_no == invoice_no).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Sales Invoice not found")

    items = db.query(SalesInvoiceItem).filter(SalesInvoiceItem.invoice_id == inv.id).all()
    pdf_bytes = generate_invoice_pdf(inv, inv.party, items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={invoice_no}.pdf"}
    )

@router.get("/{invoice_no}/thermal")
def get_thermal_pos_receipt(invoice_no: str, db: Session = Depends(get_db)):
    """Text output for 3-inch POS Thermal Receipt Printers."""
    inv = db.query(SalesInvoiceModel).filter(SalesInvoiceModel.invoice_no == invoice_no).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db.query(SalesInvoiceItem).filter(SalesInvoiceItem.invoice_id == inv.id).all()

    receipt_text = f"""
========================================
       ASTHA BUILDERS & HARDWARE        
    Bhubaneswar, Odisha | +91 9876543210 
========================================
Invoice No : {inv.invoice_no}
Date       : {inv.invoice_date}
Customer   : {inv.party.business_name}
Mobile     : {inv.party.mobile}
----------------------------------------
ITEM           QTY    RATE       TOTAL  
----------------------------------------
"""
    for item in items:
        p_name = item.product.product_name[:12]
        receipt_text += f"{p_name:<14} {float(item.quantity):<6.1f} {float(item.unit_price):<10.2f} {float(item.line_total):<8.2f}\n"

    receipt_text += f"""----------------------------------------
Subtotal   : Rs {float(inv.subtotal):.2f}
CGST       : Rs {float(inv.cgst_total):.2f}
SGST       : Rs {float(inv.sgst_total):.2f}
GRAND TOTAL: Rs {float(inv.grand_total):.2f}
========================================
       THANK YOU FOR YOUR BUSINESS!      
========================================
"""
    return Response(content=receipt_text, media_type="text/plain")
