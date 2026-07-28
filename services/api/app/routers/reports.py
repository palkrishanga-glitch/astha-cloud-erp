from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..models import Account, Voucher, VoucherItem, PartyLedger, StockLedger, AuditLog
from utils.excel_export import export_data_to_excel

router = APIRouter(prefix="/reports", tags=["Accounting & Financial Reports"])

class VoucherItemInput(BaseModel):
    account_id: Optional[int] = None
    account_code: Optional[str] = None
    debit: float = 0.00
    credit: float = 0.00
    narration: Optional[str] = None

class CreateVoucherSchema(BaseModel):
    voucher_no: Optional[str] = None
    voucher_date: date
    voucher_type: str = Field(..., description="JOURNAL, RECEIPT, PAYMENT, CONTRA, DEBIT_NOTE, CREDIT_NOTE")
    narration: str
    items: List[VoucherItemInput]
    created_by: str = "SYSTEM_ADMIN"

def generate_next_voucher_no(db: Session, v_type: str) -> str:
    prefix_map = {
        "JOURNAL": "JV",
        "RECEIPT": "RCT",
        "PAYMENT": "PAY",
        "CONTRA": "CTR",
        "DEBIT_NOTE": "DN",
        "CREDIT_NOTE": "CN"
    }
    p = prefix_map.get(v_type.upper(), "VOU")
    count = db.query(Voucher).filter(Voucher.voucher_type == v_type.upper()).count()
    return f"{p}-2026-{(count + 1):06d}"

def get_or_create_account(db: Session, code: str, name: str, acct_type: str) -> Account:
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, account_type=acct_type)
        db.add(acct)
        db.flush()
    return acct

@router.post("/vouchers", status_code=status.HTTP_201_CREATED)
def create_accounting_voucher(payload: CreateVoucherSchema, db: Session = Depends(get_db)):
    # Ensure default cash & bank accounts exist
    get_or_create_account(db, "1001", "Cash Account", "ASSET")
    get_or_create_account(db, "1002", "Bank Account", "ASSET")

    tot_debit = round(sum(item.debit for item in payload.items), 2)
    tot_credit = round(sum(item.credit for item in payload.items), 2)

    if tot_debit != tot_credit:
        raise HTTPException(
            status_code=400,
            detail=f"Unbalanced Transaction Rejected! Total Debit (Rs {tot_debit}) must equal Total Credit (Rs {tot_credit})."
        )

    if tot_debit <= 0:
        raise HTTPException(status_code=400, detail="Voucher total amount must be greater than zero.")

    if not payload.voucher_no:
        payload.voucher_no = generate_next_voucher_no(db, payload.voucher_type)

    v = Voucher(
        voucher_no=payload.voucher_no,
        voucher_date=payload.voucher_date,
        voucher_type=payload.voucher_type.upper(),
        narration=payload.narration,
        total_amount=tot_debit,
        created_by=payload.created_by
    )
    db.add(v)
    db.flush()

    for item in payload.items:
        acct_id = item.account_id
        if not acct_id and item.account_code:
            acct = db.query(Account).filter(Account.code == item.account_code).first()
            if acct:
                acct_id = acct.id

        if not acct_id:
            acct_id = 1

        vi = VoucherItem(
            voucher_id=v.id,
            account_id=acct_id,
            debit=item.debit,
            credit=item.credit,
            narration=item.narration or payload.narration
        )
        db.add(vi)

    audit = AuditLog(
        user_id=payload.created_by,
        module="Accounting & Financials",
        action="CREATE_VOUCHER",
        table_name="vouchers",
        record_id=v.id,
        new_value=f"Created {payload.voucher_type} Voucher {v.voucher_no} (Rs {tot_debit})",
        status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "voucher_no": v.voucher_no,
        "voucher_type": v.voucher_type,
        "total_amount": float(v.total_amount)
    }

@router.get("/trial-balance")
def get_trial_balance(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    records = []
    tot_debits = 0.00
    tot_credits = 0.00

    for acct in accounts:
        items = db.query(VoucherItem).filter(VoucherItem.account_id == acct.id).all()
        d_sum = sum(float(i.debit) for i in items)
        c_sum = sum(float(i.credit) for i in items)

        net_bal = d_sum - c_sum
        d_val = net_bal if net_bal > 0 else 0.00
        c_val = abs(net_bal) if net_bal < 0 else 0.00

        tot_debits += d_val
        tot_credits += c_val

        records.append({
            "account_code": acct.code,
            "account_name": acct.name,
            "account_type": acct.account_type,
            "debit": d_val,
            "credit": c_val
        })

    is_balanced = abs(tot_debits - tot_credits) < 0.01

    return {
        "is_balanced": is_balanced,
        "total_debit": round(tot_debits, 2),
        "total_credit": round(tot_credits, 2),
        "accounts": records
    }

@router.get("/profit-and-loss")
def get_profit_and_loss(db: Session = Depends(get_db)):
    items = db.query(VoucherItem).all()
    
    total_sales = 0.00
    total_purchases = 0.00
    total_expenses = 0.00

    for item in items:
        acct_type = item.account.account_type if hasattr(item, "account") and item.account else "EXPENSE"
        
        if acct_type == "REVENUE":
            total_sales += float(item.credit) - float(item.debit)
        elif acct_type == "EXPENSE":
            if item.account.code == "5001":
                total_purchases += float(item.debit) - float(item.credit)
            else:
                total_expenses += float(item.debit) - float(item.credit)

    gross_profit = total_sales - total_purchases
    net_profit = gross_profit - total_expenses

    return {
        "total_sales_revenue": round(total_sales, 2),
        "cost_of_goods_sold": round(total_purchases, 2),
        "gross_profit": round(gross_profit, 2),
        "operating_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2)
    }

@router.get("/balance-sheet")
def get_balance_sheet(db: Session = Depends(get_db)):
    pnl = get_profit_and_loss(db)
    net_profit = pnl["net_profit"]

    accounts = db.query(Account).all()
    assets = []
    liabilities = []
    tot_assets = 0.00
    tot_liabilities = 0.00

    for acct in accounts:
        items = db.query(VoucherItem).filter(VoucherItem.account_id == acct.id).all()
        bal = sum(float(i.debit) - float(i.credit) for i in items)

        if acct.account_type == "ASSET":
            assets.append({"account": acct.name, "amount": bal})
            tot_assets += bal
        elif acct.account_type in ["LIABILITY", "CAPITAL"]:
            liabilities.append({"account": acct.name, "amount": abs(bal)})
            tot_liabilities += abs(bal)

    tot_liabilities += net_profit

    return {
        "total_assets": round(tot_assets, 2),
        "total_liabilities_and_equity": round(tot_liabilities, 2),
        "net_profit_added": round(net_profit, 2),
        "assets": assets,
        "liabilities": liabilities
    }

@router.get("/cash-book")
def get_cash_book(db: Session = Depends(get_db)):
    cash_acct = get_or_create_account(db, "1001", "Cash Account", "ASSET")

    items = db.query(VoucherItem).filter(VoucherItem.account_id == cash_acct.id).all()
    txs = []
    bal = 0.00

    for i in items:
        d = float(i.debit)
        c = float(i.credit)
        bal += d - c
        txs.append({
            "voucher_no": i.voucher.voucher_no if i.voucher else "N/A",
            "date": str(i.voucher.voucher_date) if i.voucher else "N/A",
            "narration": i.narration,
            "cash_in": d,
            "cash_out": c,
            "running_balance": round(bal, 2)
        })

    return {
        "current_cash_balance": round(bal, 2),
        "transactions": txs
    }

@router.get("/bank-book")
def get_bank_book(db: Session = Depends(get_db)):
    bank_acct = get_or_create_account(db, "1002", "Bank Account", "ASSET")

    items = db.query(VoucherItem).filter(VoucherItem.account_id == bank_acct.id).all()
    txs = []
    bal = 0.00

    for i in items:
        d = float(i.debit)
        c = float(i.credit)
        bal += d - c
        txs.append({
            "voucher_no": i.voucher.voucher_no if i.voucher else "N/A",
            "date": str(i.voucher.voucher_date) if i.voucher else "N/A",
            "narration": i.narration,
            "deposit": d,
            "withdrawal": c,
            "running_balance": round(bal, 2)
        })

    return {
        "current_bank_balance": round(bal, 2),
        "transactions": txs
    }

@router.get("/day-book")
def get_day_book(day: Optional[date] = None, db: Session = Depends(get_db)):
    target_date = day or date.today()
    vouchers = db.query(Voucher).filter(Voucher.voucher_date == target_date).all()
    
    res = []
    for v in vouchers:
        res.append({
            "voucher_no": v.voucher_no,
            "voucher_type": v.voucher_type,
            "narration": v.narration,
            "total_amount": float(v.total_amount),
            "created_by": v.created_by
        })

    return {
        "date": str(target_date),
        "total_transactions": len(vouchers),
        "day_book": res
    }
