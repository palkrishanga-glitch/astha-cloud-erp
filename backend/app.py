import os
import sys
from datetime import datetime, date
from decimal import Decimal
import json
import zipfile

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath("."))

from backend.models import (
    Base, User, Customer, Supplier, Product, SalesInvoice, SalesItem,
    PurchaseInvoice, PurchaseItem, Employee, Expense, AuditLog
)
from backend.authentication import (
    hash_password, generate_jwt_token, require_auth
)

app = Flask(__name__)
CORS(app)

# Database Configuration (Defaults to local SQLite for offline hybrid, PostgreSQL/Supabase ready)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./astha_erp_v2.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Database Schema & Seed Admin User
Base.metadata.create_all(bind=engine)

def seed_default_data():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                name="System Administrator",
                email="admin@asthaerp.com",
                password_hash=hash_password("admin123"),
                role="Admin",
                status="ACTIVE"
            )
            staff = User(
                name="Sales Executive",
                email="staff@asthaerp.com",
                password_hash=hash_password("staff123"),
                role="Staff",
                status="ACTIVE"
            )
            db.add_all([admin, staff])

        if db.query(Customer).count() == 0:
            c1 = Customer(
                customer_code="CUST-001",
                name="Rahul Construction Ltd",
                phone="9876543210",
                address="Plot 42, Industrial Area, Sector 5",
                gst_number="27AAAAA0000A1Z5",
                opening_balance=25000.00,
                credit_limit=500000.00
            )
            c2 = Customer(
                customer_code="CUST-002",
                name="Apex Infrastructure",
                phone="9812345678",
                address="Main Highway Near Toll Gate",
                gst_number="27BBBBB1111B1Z2",
                opening_balance=0.00,
                credit_limit=250000.00
            )
            db.add_all([c1, c2])

        if db.query(Supplier).count() == 0:
            s1 = Supplier(
                supplier_name="Ultratech Cement Distributor",
                phone="9988776655",
                address="Nagpur Depot",
                gst_number="27CCCC0000C1Z8",
                opening_balance=150000.00,
                payment_terms="Net 15 Days"
            )
            s2 = Supplier(
                supplier_name="Tata Tiscon TMT Steel Agency",
                phone="9776655443",
                address="Steel Yard Gate 2",
                gst_number="27DDDD1111D1Z4",
                opening_balance=320000.00,
                payment_terms="Net 30 Days"
            )
            db.add_all([s1, s2])

        if db.query(Product).count() == 0:
            p1 = Product(
                product_code="PRD-001",
                product_name="UltraTech PPC Cement (50kg Bag)",
                category="Cement",
                brand="UltraTech",
                unit="BAGS",
                purchase_price=340.00,
                selling_price=390.00,
                gst_rate=28.00,
                stock_quantity=450.00,
                min_stock_level=50.00,
                hsn_code="2523"
            )
            p2 = Product(
                product_code="PRD-002",
                product_name="Tata Tiscon 12mm TMT Steel Rod",
                category="TMT Steel",
                brand="Tata Tiscon",
                unit="TON",
                purchase_price=58000.00,
                selling_price=64000.00,
                gst_rate=18.00,
                stock_quantity=18.50,
                min_stock_level=5.00,
                hsn_code="7214"
            )
            p3 = Product(
                product_code="PRD-003",
                product_name="Finolex 4-inch PVC Pipe 6m",
                category="Pipes",
                brand="Finolex",
                unit="PCS",
                purchase_price=420.00,
                selling_price=530.00,
                gst_rate=18.00,
                stock_quantity=120.00,
                min_stock_level=20.00,
                hsn_code="3917"
            )
            db.add_all([p1, p2, p3])

        db.commit()
    finally:
        db.close()

seed_default_data()

# Helper for Audit Logging
def log_activity(user_email, action, module, description):
    db = SessionLocal()
    try:
        log = AuditLog(
            user_email=user_email,
            action=action,
            module=module,
            description=description
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 1: AUTHENTICATION API
# -------------------------------------------------------------------
@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "ERROR", "message": "Email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.status == "ACTIVE").first()
        if not user or user.password_hash != hash_password(password):
            return jsonify({"status": "ERROR", "message": "Invalid email or password"}), 401

        token = generate_jwt_token(user.id, user.name, user.email, user.role)
        log_activity(user.email, "USER_LOGIN", "Authentication", f"User {user.name} logged in successfully")

        return jsonify({
            "status": "SUCCESS",
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        })
    finally:
        db.close()

@app.route("/api/v1/auth/me", methods=["GET"])
@require_auth()
def get_current_user():
    return jsonify({
        "status": "SUCCESS",
        "user": request.current_user
    })

# -------------------------------------------------------------------
# MODULE 2 & 3: DASHBOARD ANALYTICS API
# -------------------------------------------------------------------
@app.route("/api/v1/dashboard/metrics", methods=["GET"])
@require_auth()
def get_dashboard_metrics():
    db = SessionLocal()
    try:
        today = date.today()

        today_sales = sum(float(inv.grand_total) for inv in db.query(SalesInvoice).filter(SalesInvoice.invoice_date == today).all())
        today_purchases = sum(float(pur.grand_total) for pur in db.query(PurchaseInvoice).filter(PurchaseInvoice.invoice_date == today).all())
        total_sales = sum(float(inv.grand_total) for inv in db.query(SalesInvoice).all())
        total_purchases = sum(float(pur.grand_total) for pur in db.query(PurchaseInvoice).all())

        customer_dues = sum(float(c.opening_balance) for c in db.query(Customer).all())
        supplier_dues = sum(float(s.opening_balance) for s in db.query(Supplier).all())
        inventory_val = sum(float(p.stock_quantity) * float(p.selling_price) for p in db.query(Product).all())
        low_stock_cnt = db.query(Product).filter(Product.stock_quantity <= Product.min_stock_level).count()

        return jsonify({
            "status": "SUCCESS",
            "metrics": {
                "today_sales": today_sales,
                "today_purchases": today_purchases,
                "total_sales": total_sales,
                "total_purchases": total_purchases,
                "customer_due": customer_dues,
                "supplier_due": supplier_dues,
                "inventory_value": inventory_val,
                "low_stock_count": low_stock_cnt,
                "monthly_profit": total_sales - total_purchases
            }
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 4 & 5: CUSTOMER & LEDGER API
# -------------------------------------------------------------------
@app.route("/api/v1/customers", methods=["GET", "POST"])
@require_auth()
def manage_customers():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            cust_code = f"CUST-00{db.query(Customer).count() + 1}"
            customer = Customer(
                customer_code=cust_code,
                name=data.get("name"),
                phone=data.get("phone"),
                address=data.get("address"),
                gst_number=data.get("gst_number"),
                opening_balance=Decimal(str(data.get("opening_balance", 0))),
                credit_limit=Decimal(str(data.get("credit_limit", 100000)))
            )
            db.add(customer)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_CUSTOMER", "Customer Management", f"Created customer {customer.name}")
            return jsonify({"status": "SUCCESS", "message": "Customer added successfully", "customer_id": customer.id})

        customers = db.query(Customer).all()
        return jsonify({
            "status": "SUCCESS",
            "customers": [{
                "id": c.id,
                "code": c.customer_code,
                "name": c.name,
                "phone": c.phone,
                "address": c.address,
                "gst_number": c.gst_number,
                "opening_balance": float(c.opening_balance),
                "credit_limit": float(c.credit_limit)
            } for c in customers]
        })
    finally:
        db.close()

@app.route("/api/v1/customers/<int:customer_id>/ledger", methods=["GET"])
@require_auth()
def get_customer_ledger(customer_id):
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return jsonify({"status": "ERROR", "message": "Customer not found"}), 404

        invoices = db.query(SalesInvoice).filter(SalesInvoice.customer_id == customer_id).all()
        ledger_entries = [{
            "date": str(customer.created_at.date()),
            "description": "Opening Balance",
            "debit": float(customer.opening_balance) if customer.opening_balance > 0 else 0.0,
            "credit": 0.0,
            "balance": float(customer.opening_balance)
        }]

        running_bal = float(customer.opening_balance)
        for inv in invoices:
            running_bal += float(inv.grand_total)
            ledger_entries.append({
                "date": str(inv.invoice_date),
                "description": f"Sales Invoice #{inv.invoice_no}",
                "debit": float(inv.grand_total),
                "credit": 0.0,
                "balance": running_bal
            })

        return jsonify({
            "status": "SUCCESS",
            "customer": {"id": customer.id, "name": customer.name, "outstanding": running_bal},
            "ledger": ledger_entries
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 6: SUPPLIER MANAGEMENT API
# -------------------------------------------------------------------
@app.route("/api/v1/suppliers", methods=["GET", "POST"])
@require_auth()
def manage_suppliers():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            supplier = Supplier(
                supplier_name=data.get("supplier_name"),
                phone=data.get("phone"),
                address=data.get("address"),
                gst_number=data.get("gst_number"),
                opening_balance=Decimal(str(data.get("opening_balance", 0))),
                payment_terms=data.get("payment_terms", "Net 30 Days")
            )
            db.add(supplier)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_SUPPLIER", "Supplier Management", f"Created supplier {supplier.supplier_name}")
            return jsonify({"status": "SUCCESS", "message": "Supplier created", "supplier_id": supplier.id})

        suppliers = db.query(Supplier).all()
        return jsonify({
            "status": "SUCCESS",
            "suppliers": [{
                "id": s.id,
                "name": s.supplier_name,
                "phone": s.phone,
                "address": s.address,
                "gst_number": s.gst_number,
                "opening_balance": float(s.opening_balance),
                "payment_terms": s.payment_terms
            } for s in suppliers]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 7 & 8: PRODUCT & INVENTORY API
# -------------------------------------------------------------------
@app.route("/api/v1/products", methods=["GET", "POST"])
@require_auth()
def manage_products():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            prd_code = f"PRD-00{db.query(Product).count() + 1}"
            product = Product(
                product_code=prd_code,
                product_name=data.get("product_name"),
                category=data.get("category", "Hardware"),
                brand=data.get("brand", "Generic"),
                unit=data.get("unit", "PCS"),
                purchase_price=Decimal(str(data.get("purchase_price", 0))),
                selling_price=Decimal(str(data.get("selling_price", 0))),
                gst_rate=Decimal(str(data.get("gst_rate", 18))),
                stock_quantity=Decimal(str(data.get("stock_quantity", 0))),
                min_stock_level=Decimal(str(data.get("min_stock_level", 10))),
                hsn_code=data.get("hsn_code", "7318")
            )
            db.add(product)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_PRODUCT", "Inventory System", f"Created product {product.product_name}")
            return jsonify({"status": "SUCCESS", "message": "Product created", "product_id": product.id})

        products = db.query(Product).all()
        return jsonify({
            "status": "SUCCESS",
            "products": [{
                "id": p.id,
                "code": p.product_code,
                "name": p.product_name,
                "category": p.category,
                "brand": p.brand,
                "unit": p.unit,
                "purchase_price": float(p.purchase_price),
                "selling_price": float(p.selling_price),
                "gst_rate": float(p.gst_rate),
                "stock_quantity": float(p.stock_quantity),
                "min_stock_level": float(p.min_stock_level),
                "is_low_stock": float(p.stock_quantity) <= float(p.min_stock_level)
            } for p in products]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 10: POS SALES BILLING API
# -------------------------------------------------------------------
@app.route("/api/v1/sales", methods=["GET", "POST"])
@require_auth()
def manage_sales():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            customer_id = data.get("customer_id")
            items_data = data.get("items", [])

            if not items_data:
                return jsonify({"status": "ERROR", "message": "Sales invoice requires at least one item"}), 400

            inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            subtotal = Decimal("0.00")
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")

            invoice_items = []
            for item in items_data:
                product_id = item.get("product_id")
                qty = Decimal(str(item.get("quantity", 1)))
                rate = Decimal(str(item.get("rate", 0)))
                gst_pct = Decimal(str(item.get("gst_rate", 18)))

                line_subtotal = qty * rate
                line_tax = line_subtotal * (gst_pct / Decimal("100"))

                subtotal += line_subtotal
                cgst += line_tax / Decimal("2")
                sgst += line_tax / Decimal("2")

                # Deduct Stock Quantity
                prd = db.query(Product).filter(Product.id == product_id).first()
                if prd:
                    prd.stock_quantity -= qty

                invoice_items.append(SalesItem(
                    product_id=product_id,
                    quantity=qty,
                    rate=rate,
                    gst_rate=gst_pct,
                    total_amount=line_subtotal + line_tax
                ))

            grand_total = subtotal + cgst + sgst

            sales_invoice = SalesInvoice(
                invoice_no=inv_no,
                customer_id=customer_id,
                invoice_date=date.today(),
                subtotal=subtotal,
                cgst_amount=cgst,
                sgst_amount=sgst,
                igst_amount=Decimal("0.00"),
                grand_total=grand_total,
                payment_mode=data.get("payment_mode", "CASH"),
                payment_status="PAID",
                items=invoice_items
            )

            db.add(sales_invoice)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_INVOICE", "Sales Billing", f"Generated Invoice #{inv_no} worth Rs {grand_total:,.2f}")
            return jsonify({"status": "SUCCESS", "message": "Invoice created", "invoice_no": inv_no, "grand_total": float(grand_total)})

        invoices = db.query(SalesInvoice).order_by(SalesInvoice.id.desc()).all()
        return jsonify({
            "status": "SUCCESS",
            "invoices": [{
                "id": inv.id,
                "invoice_no": inv.invoice_no,
                "customer": inv.customer.name if inv.customer else "Walk-in Cash Customer",
                "invoice_date": str(inv.invoice_date),
                "grand_total": float(inv.grand_total),
                "payment_mode": inv.payment_mode
            } for inv in invoices]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 18: GLOBAL SEARCH API
# -------------------------------------------------------------------
@app.route("/api/v1/search", methods=["GET"])
@require_auth()
def global_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"status": "SUCCESS", "results": []})

    db = SessionLocal()
    try:
        custs = db.query(Customer).filter(Customer.name.ilike(f"%{q}%")).all()
        prods = db.query(Product).filter(Product.product_name.ilike(f"%{q}%")).all()
        supps = db.query(Supplier).filter(Supplier.supplier_name.ilike(f"%{q}%")).all()
        invs = db.query(SalesInvoice).filter(SalesInvoice.invoice_no.ilike(f"%{q}%")).all()

        results = []
        for c in custs:
            results.append({"type": "Customer", "title": c.name, "subtitle": f"Phone: {c.phone} | Code: {c.customer_code}"})
        for p in prods:
            results.append({"type": "Product", "title": p.product_name, "subtitle": f"Stock: {float(p.stock_quantity)} {p.unit} | Price: Rs {float(p.selling_price)}"})
        for s in supps:
            results.append({"type": "Supplier", "title": s.supplier_name, "subtitle": f"Phone: {s.phone}"})
        for i in invs:
            results.append({"type": "Sales Invoice", "title": i.invoice_no, "subtitle": f"Grand Total: Rs {float(i.grand_total):,.2f} | Date: {i.invoice_date}"})

        return jsonify({"status": "SUCCESS", "query": q, "results": results})
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 19: INTELLIGENT NOTIFICATIONS API
# -------------------------------------------------------------------
@app.route("/api/v1/notifications", methods=["GET"])
@require_auth()
def get_notifications():
    db = SessionLocal()
    try:
        notifications = []
        low_stock_prods = db.query(Product).filter(Product.stock_quantity <= Product.min_stock_level).all()
        for p in low_stock_prods:
            notifications.append({
                "id": f"low-stock-{p.id}",
                "level": "WARNING",
                "title": f"⚠️ Low Stock Alert: {p.product_name}",
                "message": f"Remaining: {float(p.stock_quantity)} {p.unit} (Min Threshold: {float(p.min_stock_level)})"
            })

        high_dues = db.query(Customer).filter(Customer.opening_balance > 10000).all()
        for c in high_dues:
            notifications.append({
                "id": f"due-{c.id}",
                "level": "INFO",
                "title": f"📌 Customer Payment Due: {c.name}",
                "message": f"Outstanding Dues: Rs {float(c.opening_balance):,.2f}"
            })

        return jsonify({"status": "SUCCESS", "notifications": notifications})
    finally:
        db.close()

# -------------------------------------------------------------------
# MODULE 21: AUTOMATIC BACKUP API
# -------------------------------------------------------------------
@app.route("/api/v1/backup/create", methods=["POST"])
@require_auth(['Admin'])
def create_backup():
    try:
        if not os.path.exists("./backups"):
            os.makedirs("./backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_file = f"./backups/ASTHA_ERP_BACKUP_{ts}.zip"
        with zipfile.ZipFile(bak_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists("astha_erp_v2.db"):
                zipf.write("astha_erp_v2.db", arcname="astha_erp_v2.db")
        log_activity(request.current_user["email"], "CREATE_BACKUP", "Database System", f"Generated database backup: {bak_file}")
        return jsonify({"status": "SUCCESS", "message": "Backup generated successfully", "backup_path": bak_file})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# -------------------------------------------------------------------
# MODULE 23: AUDIT LOGS API
# -------------------------------------------------------------------
@app.route("/api/v1/audit-logs", methods=["GET"])
@require_auth(['Admin'])
def get_audit_logs():
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()
        return jsonify({
            "status": "SUCCESS",
            "audit_logs": [{
                "id": l.id,
                "user": l.user_email,
                "action": l.action,
                "module": l.module,
                "description": l.description,
                "timestamp": str(l.created_at)
            } for l in logs]
        })
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
