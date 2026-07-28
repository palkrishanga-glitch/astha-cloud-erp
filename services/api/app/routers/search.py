from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Party, Product, SalesInvoiceModel, PurchaseInvoiceModel, Voucher

router = APIRouter(prefix="/search", tags=["Global Enterprise Search"])

@router.get("/")
def global_enterprise_search(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    """
    Part 10 Global Enterprise Search Engine:
    Queries Parties, Products, Sales Invoices, Purchase Bills, and Vouchers simultaneously.
    """
    search_term = f"%{q.strip()}%"

    # 1. Search Parties
    parties = db.query(Party).filter(
        (Party.business_name.ilike(search_term)) |
        (Party.party_code.ilike(search_term)) |
        (Party.gstin.ilike(search_term)) |
        (Party.mobile.ilike(search_term))
    ).limit(10).all()

    # 2. Search Products
    products = db.query(Product).filter(
        (Product.product_name.ilike(search_term)) |
        (Product.product_code.ilike(search_term)) |
        (Product.sku.ilike(search_term)) |
        (Product.barcode.ilike(search_term)) |
        (Product.hsn_code.ilike(search_term))
    ).limit(10).all()

    # 3. Search Sales Invoices
    sales = db.query(SalesInvoiceModel).filter(
        SalesInvoiceModel.invoice_no.ilike(search_term)
    ).limit(10).all()

    # 4. Search Purchase Bills
    purchases = db.query(PurchaseInvoiceModel).filter(
        (PurchaseInvoiceModel.bill_number.ilike(search_term)) |
        (PurchaseInvoiceModel.supplier_invoice_no.ilike(search_term))
    ).limit(10).all()

    # 5. Search Vouchers
    vouchers = db.query(Voucher).filter(
        (Voucher.voucher_no.ilike(search_term)) |
        (Voucher.narration.ilike(search_term))
    ).limit(10).all()

    results = []

    for p in parties:
        results.append({
            "entity": "PARTY",
            "title": p.business_name,
            "subtitle": f"Code: {p.party_code} | GSTIN: {p.gstin or 'N/A'} | Mobile: {p.mobile}",
            "id": p.id
        })

    for pr in products:
        results.append({
            "entity": "PRODUCT",
            "title": pr.product_name,
            "subtitle": f"Code: {pr.product_code} | SKU: {pr.sku} | Price: Rs {float(pr.selling_price)}",
            "id": pr.id
        })

    for s in sales:
        results.append({
            "entity": "SALES_INVOICE",
            "title": f"Invoice {s.invoice_no}",
            "subtitle": f"Date: {s.invoice_date} | Total: Rs {float(s.grand_total)} | Status: {s.payment_status}",
            "id": s.id
        })

    for pur in purchases:
        results.append({
            "entity": "PURCHASE_BILL",
            "title": f"Bill {pur.bill_number}",
            "subtitle": f"Supplier Ref: {pur.supplier_invoice_no} | Date: {pur.bill_date} | Total: Rs {float(pur.grand_total)}",
            "id": pur.id
        })

    for v in vouchers:
        results.append({
            "entity": "VOUCHER",
            "title": f"{v.voucher_type} Voucher {v.voucher_no}",
            "subtitle": f"Date: {v.voucher_date} | Total: Rs {float(v.total_amount)} | {v.narration}",
            "id": v.id
        })

    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }
