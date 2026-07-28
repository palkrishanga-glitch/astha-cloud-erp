from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Party, PartyLedger
from ..invoice_pdf import create_invoice_pdf

router = APIRouter(prefix="/sales", tags=["Sales Invoices"])

class SalesInvoiceItemSchema(BaseModel):
    product: str
    quantity: float
    unit: str = "Pcs"
    price: float
    gst: float = 18.0

class SalesInvoiceCreateSchema(BaseModel):
    invoice_no: str
    customer: str
    mobile: str
    payment_mode: str = "CASH"
    payment_status: str = "PAID"
    amount_paid: float
    items: List[SalesInvoiceItemSchema]

@router.post("/")
def create_sales_invoice(payload: SalesInvoiceCreateSchema, db: Session = Depends(get_db)):
    # Calculate invoice totals
    subtotal = sum(i.quantity * i.price for i in payload.items)
    gst_total = sum((i.quantity * i.price * i.gst) / 100 for i in payload.items)
    grand_total = subtotal + gst_total
    balance_due = max(0.0, grand_total - payload.amount_paid)

    return {
        "invoice_no": payload.invoice_no,
        "customer": payload.customer,
        "subtotal": subtotal,
        "gst_total": gst_total,
        "grand_total": grand_total,
        "amount_paid": payload.amount_paid,
        "balance_due": balance_due,
        "status": "CREATED"
    }

@router.get("/{invoice_no}/pdf")
def generate_invoice_pdf_endpoint(invoice_no: str, db: Session = Depends(get_db)):
    """Generates and returns printable PDF GST Invoice."""
    invoice_data = {
        "invoice_no": invoice_no,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "customer": "Astha Constructions",
        "mobile": "9876543210",
        "payment_mode": "CASH",
        "payment_status": "Paid",
        "total": 33288.00,
        "amount_paid": 33288.00,
        "balance": 0.00
    }
    
    business_info = {
        "business_name": "ASTHA BUILDERS & HARDWARE",
        "gst": "21AAAAA0000A1Z5",
        "phone": "+91 98765 43210",
        "address": "Hardware Yard, Bhubaneswar, Odisha"
    }

    items_data = [
        {"product": "Ultratech Cement OPC 53", "quantity": 50, "unit": "Bags", "price": 380.00, "gst": 28.0, "total": 24320.00},
        {"product": "TMT Steel Rods 12mm", "quantity": 2, "unit": "Bundles", "price": 3800.00, "gst": 18.0, "total": 8968.00}
    ]

    pdf_bytes = create_invoice_pdf(invoice_data, business_info, items_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={invoice_no}.pdf"}
    )
