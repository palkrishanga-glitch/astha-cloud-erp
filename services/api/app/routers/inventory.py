from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..models import Product, StockLedger, StockTransfer, Category, Brand, Unit, Warehouse, AuditLog
from utils.excel_export import export_data_to_excel
from utils.barcode_qr import generate_barcode_png_bytes, generate_qr_code_png_bytes

router = APIRouter(prefix="/products", tags=["Inventory & Product Master"])

class ProductCreateSchema(BaseModel):
    product_code: Optional[str] = None # Auto-generated e.g. PRD-000001
    barcode: Optional[str] = None
    sku: str
    product_name: str
    short_name: Optional[str] = None
    category_name: str = "General Building Materials"
    brand_name: str = "Generic"
    unit_name: str = "Piece"
    hsn_code: str
    gst_rate: float = 18.00
    tax_type: str = "TAX_EXCLUSIVE"
    
    purchase_price: float
    selling_price: float
    wholesale_price: Optional[float] = None
    retail_price: Optional[float] = None
    dealer_price: Optional[float] = None
    mrp: Optional[float] = None
    minimum_selling_price: Optional[float] = None
    cost_price: float
    
    minimum_stock: float = 0.00
    maximum_stock: float = 10000.00
    reorder_level: float = 10.00
    reorder_quantity: float = 50.00
    
    opening_stock: float = 0.00
    opening_stock_value: float = 0.00
    opening_stock_date: Optional[date] = None
    warehouse_name: str = "Main Central Warehouse"
    description: Optional[str] = None

class StockAdjustmentSchema(BaseModel):
    product_id: str
    warehouse_id: int
    adjustment_type: str = Field(..., description="'INCREASE' or 'DECREASE'")
    quantity: float
    rate: float
    reason: str
    adjusted_by: str = "SYSTEM_ADMIN"

class StockTransferSchema(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    product_id: str
    quantity: float
    remarks: Optional[str] = "Inter-warehouse stock transfer"
    transferred_by: str = "SYSTEM_ADMIN"

def generate_next_product_code(db: Session) -> str:
    count = db.query(Product).count()
    return f"PRD-{(count + 1):06d}"

def get_or_create_category(db: Session, name: str) -> int:
    cat = db.query(Category).filter(Category.name == name).first()
    if not cat:
        cat = Category(name=name)
        db.add(cat)
        db.flush()
    return cat.id

def get_or_create_brand(db: Session, name: str) -> int:
    b = db.query(Brand).filter(Brand.name == name).first()
    if not b:
        b = Brand(name=name)
        db.add(b)
        db.flush()
    return b.id

def get_or_create_unit(db: Session, name: str) -> int:
    u = db.query(Unit).filter(Unit.name == name).first()
    if not u:
        u = Unit(name=name, short_name=name[:3].upper())
        db.add(u)
        db.flush()
    return u.id

def get_or_create_warehouse(db: Session, name: str) -> int:
    w = db.query(Warehouse).filter(Warehouse.name == name).first()
    if not w:
        w = Warehouse(code=f"WH-{name[:3].upper()}", name=name, location="Main Yard")
        db.add(w)
        db.flush()
    return w.id

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreateSchema, db: Session = Depends(get_db)):
    if not payload.product_code:
        payload.product_code = generate_next_product_code(db)

    # SKU uniqueness check
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=400, detail=f"SKU '{payload.sku}' already exists.")

    cat_id = get_or_create_category(db, payload.category_name)
    brand_id = get_or_create_brand(db, payload.brand_name)
    unit_id = get_or_create_unit(db, payload.unit_name)
    wh_id = get_or_create_warehouse(db, payload.warehouse_name)

    barcode_val = payload.barcode or payload.product_code

    product = Product(
        product_code=payload.product_code,
        barcode=barcode_val,
        sku=payload.sku,
        product_name=payload.product_name,
        short_name=payload.short_name,
        category_id=cat_id,
        brand_id=brand_id,
        unit_id=unit_id,
        hsn_code=payload.hsn_code,
        gst_rate=payload.gst_rate,
        cgst_rate=payload.gst_rate / 2.0,
        sgst_rate=payload.gst_rate / 2.0,
        tax_type=payload.tax_type,
        purchase_price=payload.purchase_price,
        selling_price=payload.selling_price,
        wholesale_price=payload.wholesale_price or payload.selling_price,
        retail_price=payload.retail_price or payload.selling_price,
        dealer_price=payload.dealer_price or payload.selling_price,
        mrp=payload.mrp or payload.selling_price,
        minimum_selling_price=payload.minimum_selling_price or payload.purchase_price,
        cost_price=payload.cost_price,
        minimum_stock=payload.minimum_stock,
        maximum_stock=payload.maximum_stock,
        reorder_level=payload.reorder_level,
        reorder_quantity=payload.reorder_quantity,
        opening_stock=payload.opening_stock,
        opening_stock_value=payload.opening_stock_value or (payload.opening_stock * payload.cost_price),
        opening_stock_date=payload.opening_stock_date or date.today(),
        warehouse_id=wh_id,
        description=payload.description,
        status="ACTIVE"
    )
    db.add(product)
    db.flush()

    # Automatically create the first Stock Ledger entry for Opening Stock
    if payload.opening_stock > 0:
        ledger = StockLedger(
            date=product.opening_stock_date,
            product_id=product.id,
            warehouse_id=wh_id,
            voucher_number="STK-OB-001",
            voucher_type="OPENING_STOCK",
            qty_in=payload.opening_stock,
            qty_out=0.00,
            balance_qty=payload.opening_stock,
            rate=payload.cost_price,
            value=payload.opening_stock * payload.cost_price,
            created_by="SYSTEM_ADMIN",
            remarks="Day-Zero Opening Stock Initialization"
        )
        db.add(ledger)

    audit = AuditLog(
        user_id="SYSTEM_ADMIN",
        module="Inventory & Product Master",
        action="CREATE_PRODUCT",
        table_name="products",
        record_id=product.id,
        new_value=f"Created Product {product.product_code} ({product.product_name})",
        status="SUCCESS"
    )
    db.add(audit)
    db.commit()
    db.refresh(product)

    return {
        "status": "SUCCESS",
        "product_id": product.id,
        "product_code": product.product_code,
        "barcode": product.barcode,
        "product_name": product.product_name,
        "opening_stock": float(product.opening_stock)
    }

@router.get("/")
def list_products(
    low_stock_only: bool = False,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.status == "ACTIVE")
    products = query.all()
    res = []

    for p in products:
        # Calculate balance from Stock Ledger
        l_query = db.query(StockLedger).filter(StockLedger.product_id == p.id)
        if warehouse_id:
            l_query = l_query.filter(StockLedger.warehouse_id == warehouse_id)
        
        ledgers = l_query.all()
        qty_in = sum(float(l.qty_in) for l in ledgers)
        qty_out = sum(float(l.qty_out) for l in ledgers)
        curr_stock = qty_in - qty_out

        if low_stock_only and curr_stock > float(p.reorder_level):
            continue

        res.append({
            "id": p.id,
            "product_code": p.product_code,
            "barcode": p.barcode,
            "sku": p.sku,
            "product_name": p.product_name,
            "hsn_code": p.hsn_code,
            "gst_rate": float(p.gst_rate),
            "purchase_price": float(p.purchase_price),
            "selling_price": float(p.selling_price),
            "cost_price": float(p.cost_price),
            "reorder_level": float(p.reorder_level),
            "current_stock": curr_stock,
            "stock_value": curr_stock * float(p.cost_price),
            "is_low_stock": curr_stock <= float(p.reorder_level)
        })

    return res

@router.post("/adjust-stock")
def adjust_stock(payload: StockAdjustmentSchema, db: Session = Depends(get_db)):
    """
    Part 5 Stock Adjustment:
    Adjust stock up or down with mandatory reason and automatic Stock Ledger entry.
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Calculate current balance
    ledgers = db.query(StockLedger).filter(StockLedger.product_id == product.id).all()
    curr_balance = sum(float(l.qty_in) - float(l.qty_out) for l in ledgers)

    qty_in = payload.quantity if payload.adjustment_type == "INCREASE" else 0.00
    qty_out = payload.quantity if payload.adjustment_type == "DECREASE" else 0.00
    new_balance = curr_balance + qty_in - qty_out

    ledger = StockLedger(
        date=date.today(),
        product_id=product.id,
        warehouse_id=payload.warehouse_id,
        voucher_number=f"ADJ-{(len(ledgers) + 1):04d}",
        voucher_type="STOCK_ADJUSTMENT",
        qty_in=qty_in,
        qty_out=qty_out,
        balance_qty=new_balance,
        rate=payload.rate,
        value=payload.quantity * payload.rate,
        created_by=payload.adjusted_by,
        remarks=f"Stock Adjustment ({payload.adjustment_type}): {payload.reason}"
    )
    db.add(ledger)
    db.commit()

    return {
        "status": "SUCCESS",
        "product_id": product.id,
        "previous_stock": curr_balance,
        "new_stock": new_balance,
        "adjustment_type": payload.adjustment_type
    }

@router.post("/transfer-stock")
def transfer_stock(payload: StockTransferSchema, db: Session = Depends(get_db)):
    """
    Part 5 Inter-Warehouse Stock Transfer:
    Transfers stock from Warehouse A -> Warehouse B updating both ledger balances.
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    transfer_no = f"TRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # 1. Outgoing entry from source warehouse
    l_out = StockLedger(
        date=date.today(),
        product_id=product.id,
        warehouse_id=payload.from_warehouse_id,
        voucher_number=transfer_no,
        voucher_type="STOCK_TRANSFER",
        qty_in=0.00,
        qty_out=payload.quantity,
        balance_qty=0.00, # recalculated
        rate=float(product.cost_price),
        value=payload.quantity * float(product.cost_price),
        created_by=payload.transferred_by,
        remarks=f"Stock Transfer Out -> WH {payload.to_warehouse_id}: {payload.remarks}"
    )
    db.add(l_out)

    # 2. Incoming entry to target warehouse
    l_in = StockLedger(
        date=date.today(),
        product_id=product.id,
        warehouse_id=payload.to_warehouse_id,
        voucher_number=transfer_no,
        voucher_type="STOCK_TRANSFER",
        qty_in=payload.quantity,
        qty_out=0.00,
        balance_qty=0.00,
        rate=float(product.cost_price),
        value=payload.quantity * float(product.cost_price),
        created_by=payload.transferred_by,
        remarks=f"Stock Transfer In <- WH {payload.from_warehouse_id}: {payload.remarks}"
    )
    db.add(l_in)

    st = StockTransfer(
        transfer_no=transfer_no,
        transfer_date=date.today(),
        from_warehouse_id=payload.from_warehouse_id,
        to_warehouse_id=payload.to_warehouse_id,
        product_id=product.id,
        quantity=payload.quantity,
        remarks=payload.remarks,
        created_by=payload.transferred_by
    )
    db.add(st)
    db.commit()

    return {"status": "SUCCESS", "transfer_no": transfer_no, "quantity": payload.quantity}

@router.get("/export/excel")
def export_products_excel(db: Session = Depends(get_db)):
    """Exports Product Inventory & Stock Valuation Register to Excel (.xlsx)."""
    products = db.query(Product).all()
    headers = ["Product Code", "Barcode", "SKU", "Product Name", "HSN Code", "GST Rate (%)", "Selling Price", "Cost Price", "Reorder Level", "Stock Value (Rs)"]
    rows = []

    for p in products:
        ledgers = db.query(StockLedger).filter(StockLedger.product_id == p.id).all()
        curr_stock = sum(float(l.qty_in) - float(l.qty_out) for l in ledgers)
        
        rows.append([
            p.product_code,
            p.barcode or "N/A",
            p.sku,
            p.product_name,
            p.hsn_code,
            float(p.gst_rate),
            float(p.selling_price),
            float(p.cost_price),
            float(p.reorder_level),
            curr_stock * float(p.cost_price)
        ])

    excel_bytes = export_data_to_excel("Stock Valuation Register", headers, rows)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Stock_Valuation_Register.xlsx"}
    )

@router.get("/{product_id}/barcode/image")
def get_product_barcode_image(product_id: str, db: Session = Depends(get_db)):
    """Streams Code128 Barcode PNG image for product labeling."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    code = product.barcode or product.product_code
    img_bytes = generate_barcode_png_bytes(code)
    return Response(content=img_bytes, media_type="image/png")

@router.get("/{product_id}/qr/image")
def get_product_qr_image(product_id: str, db: Session = Depends(get_db)):
    """Streams Product QR Code PNG image."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    qr_text = f"ASTHA-PRODUCT|CODE:{product.product_code}|NAME:{product.product_name}|PRICE:{product.selling_price}|HSN:{product.hsn_code}"
    img_bytes = generate_qr_code_png_bytes(qr_text)
    return Response(content=img_bytes, media_type="image/png")
