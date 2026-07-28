from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..models import (
    Party, Product, StockLedger, PartyLedger, Account, Voucher, VoucherItem,
    PurchaseOrder, GoodsReceiptNote, PurchaseInvoiceModel, PurchaseInvoiceItem, PurchaseReturnModel, AuditLog
)

router = APIRouter(prefix="/purchases", tags=["Purchases & Procurement"])

class PurchaseItemInput(BaseModel):
    product_id: str
    quantity: float
    purchase_rate: float
    discount_percent: float = 0.00

class CreatePurchaseInvoiceSchema(BaseModel):
    bill_number: Optional[str] = None # Auto-generated PUR-2026-XXXXXX if omitted
    supplier_invoice_no: str
    bill_date: date
    supplier_id: str
    warehouse_id: int = 1
    payment_mode: str = "BANK_TRANSFER"
    remarks: Optional[str] = None
    items: List[PurchaseItemInput]
    created_by: str = "SYSTEM_ADMIN"

class PurchaseOrderSchema(BaseModel):
    supplier_id: str
    warehouse_id: int = 1
    expected_delivery_date: Optional[date] = None
    items: List[PurchaseItemInput]
    created_by: str = "SYSTEM_ADMIN"

def generate_next_pur_bill_number(db: Session) -> str:
    count = db.query(PurchaseInvoiceModel).count()
    return f"PUR-2026-{(count + 1):06d}"

def generate_next_po_number(db: Session) -> str:
    count = db.query(PurchaseOrder).count()
    return f"PO-2026-{(count + 1):06d}"

def get_or_create_account(db: Session, code: str, name: str, acct_type: str) -> int:
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, account_type=acct_type)
        db.add(acct)
        db.flush()
    return acct.id

@router.post("/order", status_code=status.HTTP_201_CREATED)
def create_purchase_order(payload: PurchaseOrderSchema, db: Session = Depends(get_db)):
    """Creates formal Purchase Order (PO-2026-XXXXXX)."""
    supplier = db.query(Party).filter(Party.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    po_num = generate_next_po_number(db)
    tot_amt = sum(item.quantity * item.purchase_rate for item in payload.items)

    po = PurchaseOrder(
        po_number=po_num,
        po_date=date.today(),
        supplier_id=supplier.id,
        warehouse_id=payload.warehouse_id,
        expected_delivery_date=payload.expected_delivery_date,
        total_amount=tot_amt,
        status="APPROVED",
        created_by=payload.created_by
    )
    db.add(po)
    db.commit()
    return {"status": "SUCCESS", "po_number": po.po_number, "total_amount": float(po.total_amount)}

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_purchase_invoice(payload: CreatePurchaseInvoiceSchema, db: Session = Depends(get_db)):
    """
    Part 7 Procurement Core Engine:
    1. Increases physical stock in StockLedger (single source of truth).
    2. Updates Product purchase_price and cost_price.
    3. Posts Credit entry to PartyLedger updating Supplier Outstanding.
    4. Posts Double-Entry Accounting Vouchers (Purchase Acct Dr. GST Input ITC Dr. To Trade Creditors Cr.).
    """
    supplier = db.query(Party).filter(Party.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    if not payload.bill_number:
        payload.bill_number = generate_next_pur_bill_number(db)

    subtotal = 0.00
    cgst_total = 0.00
    sgst_total = 0.00
    discount_total = 0.00
    processed_items = []

    for item_in in payload.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID '{item_in.product_id}' not found.")

        gross = item_in.quantity * item_in.purchase_rate
        disc_amt = gross * (item_in.discount_percent / 100.0)
        taxable = gross - disc_amt

        gst_rate = float(product.gst_rate)
        half_tax = (taxable * (gst_rate / 100.0)) / 2.0
        line_tot = taxable + (half_tax * 2)

        subtotal += taxable
        discount_total += disc_amt
        cgst_total += half_tax
        sgst_total += half_tax

        # Update Product purchase price and cost price
        product.purchase_price = item_in.purchase_rate
        product.cost_price = item_in.purchase_rate
        db.add(product)

        processed_items.append({
            "product_id": product.id,
            "hsn_code": product.hsn_code,
            "quantity": item_in.quantity,
            "unit_name": "PCS",
            "purchase_rate": item_in.purchase_rate,
            "discount_percent": item_in.discount_percent,
            "taxable_amount": taxable,
            "gst_rate": gst_rate,
            "cgst_amount": half_tax,
            "sgst_amount": half_tax,
            "line_total": line_tot
        })

    grand_total = round(subtotal + cgst_total + sgst_total, 2)

    # 1. Save Purchase Invoice
    pur = PurchaseInvoiceModel(
        bill_number=payload.bill_number,
        supplier_invoice_no=payload.supplier_invoice_no,
        bill_date=payload.bill_date,
        supplier_id=supplier.id,
        warehouse_id=payload.warehouse_id,
        subtotal=subtotal,
        discount_amount=discount_total,
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        grand_total=grand_total,
        payment_mode=payload.payment_mode,
        payment_status="UNPAID",
        balance_due=grand_total,
        remarks=payload.remarks,
        status="APPROVED",
        created_by=payload.created_by
    )
    db.add(pur)
    db.flush()

    # Save Items & Stock Ledger Entries (qty_in)
    for pi in processed_items:
        item_row = PurchaseInvoiceItem(
            purchase_id=pur.id,
            product_id=pi["product_id"],
            hsn_code=pi["hsn_code"],
            quantity=pi["quantity"],
            unit_name=pi["unit_name"],
            purchase_rate=pi["purchase_rate"],
            discount_percent=pi["discount_percent"],
            taxable_amount=pi["taxable_amount"],
            gst_rate=pi["gst_rate"],
            cgst_amount=pi["cgst_amount"],
            sgst_amount=pi["sgst_amount"],
            line_total=pi["line_total"]
        )
        db.add(item_row)

        # Stock Ledger Increment
        stock_ledgers = db.query(StockLedger).filter(StockLedger.product_id == pi["product_id"]).all()
        curr_bal = sum(float(l.qty_in) - float(l.qty_out) for l in stock_ledgers)
        new_bal = curr_bal + pi["quantity"]

        l_in = StockLedger(
            date=payload.bill_date,
            product_id=pi["product_id"],
            warehouse_id=payload.warehouse_id,
            voucher_number=payload.bill_number,
            voucher_type="PURCHASE",
            qty_in=pi["quantity"],
            qty_out=0.00,
            balance_qty=new_bal,
            rate=pi["purchase_rate"],
            value=pi["quantity"] * pi["purchase_rate"],
            created_by=payload.created_by,
            remarks=f"Purchase Invoice {payload.bill_number} (Ref: {payload.supplier_invoice_no})"
        )
        db.add(l_in)

    # 2. Update Supplier Ledger (Credit Entry for Supplier Outstanding Payable)
    supplier_ledgers = db.query(PartyLedger).filter(PartyLedger.party_id == supplier.id).all()
    curr_supp_bal = sum(float(l.debit) - float(l.credit) for l in supplier_ledgers)
    new_supp_bal = curr_supp_bal - grand_total # Payable balance

    supplier_ledger = PartyLedger(
        party_id=supplier.id,
        date=payload.bill_date,
        voucher_number=payload.bill_number,
        voucher_type="PURCHASE_INVOICE",
        reference_number=payload.supplier_invoice_no,
        description=f"Purchase Invoice {payload.bill_number} (Supplier Ref: {payload.supplier_invoice_no})",
        debit=0.00,
        credit=grand_total,
        running_balance=new_supp_bal,
        created_by=payload.created_by,
        timestamp=datetime.utcnow()
    )
    db.add(supplier_ledger)

    # 3. Double-Entry Accounting Voucher
    creditor_acct = get_or_create_account(db, "2005", "Trade Creditors", "LIABILITY")
    purchase_acct = get_or_create_account(db, "5001", "Purchase Account", "EXPENSE")
    cgst_input_acct = get_or_create_account(db, "1005", "CGST Input Tax Credit", "ASSET")
    sgst_input_acct = get_or_create_account(db, "1006", "SGST Input Tax Credit", "ASSET")

    v = Voucher(
        voucher_no=payload.bill_number,
        voucher_date=payload.bill_date,
        voucher_type="PURCHASE",
        narration=f"Purchase Bill {payload.bill_number} from {supplier.business_name}",
        total_amount=grand_total,
        created_by=payload.created_by
    )
    db.add(v)
    db.flush()

    # Dr. Purchase Account
    db.add(VoucherItem(voucher_id=v.id, account_id=purchase_acct, debit=subtotal, credit=0.00))
    # Dr. CGST Input Tax Credit
    if cgst_total > 0:
        db.add(VoucherItem(voucher_id=v.id, account_id=cgst_input_acct, debit=cgst_total, credit=0.00))
    # Dr. SGST Input Tax Credit
    if sgst_total > 0:
        db.add(VoucherItem(voucher_id=v.id, account_id=sgst_input_acct, debit=sgst_total, credit=0.00))
    # Cr. Trade Creditors (Supplier)
    db.add(VoucherItem(voucher_id=v.id, account_id=creditor_acct, debit=0.00, credit=grand_total))

    db.commit()
    db.refresh(pur)

    return {
        "status": "SUCCESS",
        "bill_number": pur.bill_number,
        "supplier_name": supplier.business_name,
        "grand_total": float(pur.grand_total)
    }
