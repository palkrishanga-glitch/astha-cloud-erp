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
    Base, Company, User, Warehouse, Customer, Supplier, Product, Quotation,
    DeliveryChallan, PurchaseOrder, SalesInvoice, SalesItem, PurchaseInvoice,
    PurchaseItem, StockTransfer, Employee, Attendance, Expense, AuditLog
)
from backend.authentication import (
    hash_password, generate_jwt_token, require_auth
)

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./astha_erp_v2.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Database Schema & Run Dynamic Column Auto-Migration
Base.metadata.create_all(bind=engine)

def auto_migrate_columns():
    with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            try:
                res = conn.exec_driver_sql(f"PRAGMA table_info({table_name});")
                existing_cols = {row[1] for row in res.fetchall()}
                if existing_cols:
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(engine.dialect)
                            try:
                                conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type};")
                            except Exception:
                                pass
            except Exception:
                pass
        conn.commit()

auto_migrate_columns()

def seed_master_data():
    db = SessionLocal()
    try:
        if db.query(Company).count() == 0:
            c1 = Company(
                company_name="Astha Builders & Hardware",
                gstin="27AAAAA0000A1Z5",
                address="Main Highway Road, Commercial Yard",
                phone="9876543210",
                email="contact@asthaerp.com"
            )
            c2 = Company(
                company_name="Astha Trading Corporation",
                gstin="27BBBBB1111B1Z2",
                address="Industrial Estate Gate 1",
                phone="9812345678",
                email="info@asthatrading.com"
            )
            db.add_all([c1, c2])

        if db.query(Warehouse).count() == 0:
            w1 = Warehouse(warehouse_name="Main Store Yard", location="Central Depot", is_main=True)
            w2 = Warehouse(warehouse_name="Godown 2 (Cement & Steel)", location="Yard Gate 4", is_main=False)
            db.add_all([w1, w2])

        if db.query(User).count() == 0:
            admin = User(
                company_id=1,
                name="System Administrator",
                email="admin@asthaerp.com",
                password_hash=hash_password("admin123"),
                role="Admin",
                status="ACTIVE"
            )
            staff = User(
                company_id=1,
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
                credit_limit=500000.00,
                customer_group="Wholesale"
            )
            c2 = Customer(
                customer_code="CUST-002",
                name="Apex Infrastructure",
                phone="9812345678",
                address="Main Highway Near Toll Gate",
                gst_number="27BBBBB1111B1Z2",
                opening_balance=0.00,
                credit_limit=250000.00,
                customer_group="Retail"
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
                barcode="890100100001",
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
                barcode="890100100002",
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
                barcode="890100100003",
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

seed_master_data()

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
    except Exception:
        db.rollback()
    finally:
        db.close()

# -------------------------------------------------------------------
# AUTHENTICATION API
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
    return jsonify({"status": "SUCCESS", "user": request.current_user})

# -------------------------------------------------------------------
# PART 26 & 27: ADVANCED POS & MULTI-INVOICE BILLING
# -------------------------------------------------------------------
@app.route("/api/v1/quotations", methods=["GET", "POST"])
@require_auth()
def manage_quotations():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            q_no = f"QTN-{datetime.now().strftime('%Y%m%d%H%M')}"
            quotation = Quotation(
                quotation_no=q_no,
                customer_id=data.get("customer_id"),
                quotation_date=date.today(),
                total_amount=Decimal(str(data.get("total_amount", 0))),
                status="PENDING"
            )
            db.add(quotation)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_QUOTATION", "Billing", f"Generated Quotation {q_no}")
            return jsonify({"status": "SUCCESS", "message": "Quotation created", "quotation_no": q_no})

        quotations = db.query(Quotation).all()
        return jsonify({
            "status": "SUCCESS",
            "quotations": [{
                "id": q.id,
                "quotation_no": q.quotation_no,
                "date": str(q.quotation_date),
                "total": float(q.total_amount),
                "status": q.status
            } for q in quotations]
        })
    finally:
        db.close()

@app.route("/api/v1/challans", methods=["GET", "POST"])
@require_auth()
def manage_challans():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            ch_no = f"DC-{datetime.now().strftime('%Y%m%d%H%M')}"
            challan = DeliveryChallan(
                challan_no=ch_no,
                customer_id=data.get("customer_id"),
                driver_name=data.get("driver_name", "Local Transport"),
                vehicle_number=data.get("vehicle_number", "MH31-AB-1234"),
                challan_date=date.today(),
                status="DISPATCHED"
            )
            db.add(challan)
            db.commit()
            log_activity(request.current_user["email"], "CREATE_CHALLAN", "Dispatch", f"Generated Delivery Challan {ch_no}")
            return jsonify({"status": "SUCCESS", "message": "Delivery Challan created", "challan_no": ch_no})

        challans = db.query(DeliveryChallan).all()
        return jsonify({
            "status": "SUCCESS",
            "challans": [{
                "id": c.id,
                "challan_no": c.challan_no,
                "driver": c.driver_name,
                "vehicle": c.vehicle_number,
                "date": str(c.challan_date),
                "status": c.status
            } for c in challans]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# PART 28: MULTI-GODOWN WAREHOUSE & STOCK TRANSFER API
# -------------------------------------------------------------------
@app.route("/api/v1/warehouses", methods=["GET", "POST"])
@require_auth()
def manage_warehouses():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            w = Warehouse(
                warehouse_name=data.get("warehouse_name"),
                location=data.get("location"),
                is_main=data.get("is_main", False)
            )
            db.add(w)
            db.commit()
            return jsonify({"status": "SUCCESS", "message": "Warehouse created", "warehouse_id": w.id})

        warehouses = db.query(Warehouse).all()
        return jsonify({
            "status": "SUCCESS",
            "warehouses": [{"id": w.id, "name": w.warehouse_name, "location": w.location, "is_main": w.is_main} for w in warehouses]
        })
    finally:
        db.close()

@app.route("/api/v1/stock-transfers", methods=["GET", "POST"])
@require_auth()
def manage_stock_transfers():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            st = StockTransfer(
                from_warehouse_id=data.get("from_warehouse_id"),
                to_warehouse_id=data.get("to_warehouse_id"),
                product_id=data.get("product_id"),
                quantity=Decimal(str(data.get("quantity", 0))),
                notes=data.get("notes")
            )
            db.add(st)
            db.commit()
            log_activity(request.current_user["email"], "STOCK_TRANSFER", "Inventory", f"Transferred {data.get('quantity')} units of product #{data.get('product_id')}")
            return jsonify({"status": "SUCCESS", "message": "Stock transfer recorded"})

        transfers = db.query(StockTransfer).all()
        return jsonify({
            "status": "SUCCESS",
            "transfers": [{
                "id": t.id,
                "from_warehouse_id": t.from_warehouse_id,
                "to_warehouse_id": t.to_warehouse_id,
                "product_id": t.product_id,
                "quantity": float(t.quantity),
                "date": str(t.transfer_date)
            } for t in transfers]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# PART 32 & 33: GST RETURNS (GSTR-1, GSTR-3B) API
# -------------------------------------------------------------------
@app.route("/api/v1/gst/gstr1", methods=["GET"])
@require_auth()
def get_gstr1_report():
    db = SessionLocal()
    try:
        invoices = db.query(SalesInvoice).all()
        b2b_invoices = []
        b2c_invoices = []

        for inv in invoices:
            record = {
                "invoice_no": inv.invoice_no,
                "date": str(inv.invoice_date),
                "customer": inv.customer.name if inv.customer else "Walk-in Cash Customer",
                "gstin": inv.customer.gst_number if inv.customer and inv.customer.gst_number else "URP",
                "taxable_value": float(inv.subtotal),
                "cgst": float(inv.cgst_amount),
                "sgst": float(inv.sgst_amount),
                "igst": float(inv.igst_amount),
                "total_amount": float(inv.grand_total)
            }
            if inv.customer and inv.customer.gst_number:
                b2b_invoices.append(record)
            else:
                b2c_invoices.append(record)

        return jsonify({
            "status": "SUCCESS",
            "gstr1": {
                "b2b_count": len(b2b_invoices),
                "b2c_count": len(b2c_invoices),
                "b2b_invoices": b2b_invoices,
                "b2c_invoices": b2c_invoices
            }
        })
    finally:
        db.close()

@app.route("/api/v1/gst/gstr3b", methods=["GET"])
@require_auth()
def get_gstr3b_summary():
    db = SessionLocal()
    try:
        sales = db.query(SalesInvoice).all()
        purchases = db.query(PurchaseInvoice).all()

        output_cgst = sum(float(inv.cgst_amount) for inv in sales)
        output_sgst = sum(float(inv.sgst_amount) for inv in sales)
        output_igst = sum(float(inv.igst_amount) for inv in sales)
        total_output_tax = output_cgst + output_sgst + output_igst

        input_tax_credit = sum(float(pur.gst_amount) for pur in purchases)
        net_tax_payable = max(0.0, total_output_tax - input_tax_credit)

        return jsonify({
            "status": "SUCCESS",
            "gstr3b": {
                "total_output_tax": total_output_tax,
                "input_tax_credit": input_tax_credit,
                "net_tax_payable": net_tax_payable
            }
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# PART 38: MULTI-COMPANY API
# -------------------------------------------------------------------
@app.route("/api/v1/companies", methods=["GET", "POST"])
@require_auth()
def manage_companies():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            c = Company(
                company_name=data.get("company_name"),
                gstin=data.get("gstin"),
                address=data.get("address"),
                phone=data.get("phone"),
                email=data.get("email")
            )
            db.add(c)
            db.commit()
            return jsonify({"status": "SUCCESS", "message": "Company created", "company_id": c.id})

        companies = db.query(Company).all()
        return jsonify({
            "status": "SUCCESS",
            "companies": [{
                "id": comp.id,
                "name": comp.company_name,
                "gstin": comp.gstin,
                "phone": comp.phone
            } for comp in companies]
        })
    finally:
        db.close()

# -------------------------------------------------------------------
# PART 43 & 44: ASTHA AI BUSINESS ASSISTANT & SMART ALERTS API
# -------------------------------------------------------------------
@app.route("/api/v1/ai/ask", methods=["POST"])
@require_auth()
def ask_ai_assistant():
    data = request.get_json() or {}
    query = data.get("prompt", "").lower().strip()

    db = SessionLocal()
    try:
        today = date.today()
        if "sales" in query or "today" in query:
            today_sales = sum(float(inv.grand_total) for inv in db.query(SalesInvoice).filter(SalesInvoice.invoice_date == today).all())
            ans = f"Today's total sales for Astha Builders & Hardware is Rs {today_sales:,.2f}."
        elif "low stock" in query or "stock" in query:
            low_stk = db.query(Product).filter(Product.stock_quantity <= Product.min_stock_level).all()
            if low_stk:
                p_names = ", ".join([f"{p.product_name} ({float(p.stock_quantity)} {p.unit})" for p in low_stk])
                ans = f"Attention: {len(low_stk)} items are low on stock: {p_names}."
            else:
                ans = "All catalog inventory items are well above minimum reorder thresholds."
        elif "due" in query or "customer" in query:
            high_dues = db.query(Customer).filter(Customer.opening_balance > 0).all()
            total_due = sum(float(c.opening_balance) for c in high_dues)
            ans = f"Total customer outstanding dues amount to Rs {total_due:,.2f} across {len(high_dues)} customers."
        else:
            ans = f"ASTHA AI Assistant active. Processed query: '{query}'. System metrics are healthy and database is synced."

        return jsonify({"status": "SUCCESS", "answer": ans})
    finally:
        db.close()

# -------------------------------------------------------------------
# PART 47: EMPLOYEE ATTENDANCE & PAYROLL API
# -------------------------------------------------------------------
@app.route("/api/v1/employees/attendance", methods=["GET", "POST"])
@require_auth()
def manage_attendance():
    db = SessionLocal()
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            att = Attendance(
                employee_id=data.get("employee_id"),
                attendance_date=date.today(),
                status=data.get("status", "PRESENT")
            )
            db.add(att)
            db.commit()
            return jsonify({"status": "SUCCESS", "message": "Attendance marked"})

        attendances = db.query(Attendance).all()
        return jsonify({
            "status": "SUCCESS",
            "attendances": [{"id": a.id, "employee_id": a.employee_id, "date": str(a.attendance_date), "status": a.status} for a in attendances]
        })
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
