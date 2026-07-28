from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Dict, Any

from ..models import Party, Product, StockLedger, PartyLedger, Account, Voucher, VoucherItem, AuditLog

class ERPBusinessService:
    """
    Part 11 Business Logic Engine & Service Layer Pattern:
    Enforces business rules, database transactions, and decoupled service execution.
    """
    
    @staticmethod
    def calculate_party_outstanding(db: Session, party_id: str) -> float:
        """Dynamic Party Outstanding = Debits - Credits."""
        ledgers = db.query(PartyLedger).filter(PartyLedger.party_id == party_id).all()
        return sum(float(l.debit) - float(l.credit) for l in ledgers)

    @staticmethod
    def calculate_product_stock(db: Session, product_id: str, warehouse_id: int = None) -> float:
        """Dynamic Product Stock = Qty In - Qty Out."""
        query = db.query(StockLedger).filter(StockLedger.product_id == product_id)
        if warehouse_id:
            query = query.filter(StockLedger.warehouse_id == warehouse_id)
        ledgers = query.all()
        return sum(float(l.qty_in) - float(l.qty_out) for l in ledgers)

    @staticmethod
    def execute_transaction_with_rollback(db: Session, action_fn, *args, **kwargs):
        """Executes multi-step business logic within a strict DB transaction block."""
        try:
            result = action_fn(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise e
