from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Party, Product, PartyLedger

router = APIRouter(prefix="/search", tags=["Global Search"])

@router.get("/")
def global_search(q: str = Query(..., min_length=1, description="Search term"), db: Session = Depends(get_db)):
    """
    Global Search API:
    Searches across Parties (name, code, GSTIN, mobile), Products (name, code, barcode), and Invoices (voucher number).
    """
    term = f"%{q.strip()}%"

    # Search Parties
    parties = db.query(Party).filter(
        (Party.party_code.like(term)) |
        (Party.business_name.like(term)) |
        (Party.mobile.like(term)) |
        (Party.gstin.like(term))
    ).limit(10).all()

    # Search Products
    products = db.query(Product).filter(
        (Product.product_code.like(term)) |
        (Product.product_name.like(term)) |
        (Product.barcode.like(term))
    ).limit(10).all()

    # Search Vouchers / Invoices
    vouchers = db.query(PartyLedger).filter(
        PartyLedger.voucher_number.like(term)
    ).limit(10).all()

    return {
        "query": q,
        "results": {
            "parties": [{
                "id": p.id,
                "code": p.party_code,
                "name": p.business_name,
                "type": p.party_type,
                "mobile": p.mobile
            } for p in parties],
            "products": [{
                "id": pr.id,
                "code": pr.product_code,
                "name": pr.product_name,
                "barcode": pr.barcode,
                "price": float(pr.selling_price)
            } for pr in products],
            "vouchers": [{
                "id": v.id,
                "voucher_number": v.voucher_number,
                "type": v.voucher_type,
                "date": str(v.date),
                "debit": float(v.debit),
                "credit": float(v.credit)
            } for v in vouchers]
        }
    }
