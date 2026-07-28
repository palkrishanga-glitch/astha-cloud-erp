import os
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), nullable=False)
    gstin = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    bank_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Staff") # Admin, Manager, Accountant, Staff
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    is_main = Column(Boolean, default=False)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    address = Column(Text, nullable=True)
    gst_number = Column(String(20), nullable=True)
    opening_balance = Column(Numeric(12, 2), default=0.00)
    credit_limit = Column(Numeric(12, 2), default=0.00)
    customer_group = Column(String(50), default="Retail")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("SalesInvoice", back_populates="customer")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(150), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    gst_number = Column(String(20), nullable=True)
    opening_balance = Column(Numeric(12, 2), default=0.00)
    payment_terms = Column(String(100), nullable=True, default="Net 30 Days")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    purchases = relationship("PurchaseInvoice", back_populates="supplier")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # Cement, TMT Steel, Hardware, Pipes
    brand = Column(String(100), nullable=True)
    unit = Column(String(20), nullable=False, default="PCS") # BAGS, TON, PCS, MTR, KG
    barcode = Column(String(50), unique=True, nullable=True)
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    gst_rate = Column(Numeric(5, 2), nullable=False, default=18.00)
    stock_quantity = Column(Numeric(12, 2), nullable=False, default=0.00)
    min_stock_level = Column(Numeric(12, 2), nullable=False, default=10.00)
    hsn_code = Column(String(20), nullable=True, default="7318")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    quotation_date = Column(Date, default=date.today)
    total_amount = Column(Numeric(12, 2), default=0.00)
    status = Column(String(20), default="PENDING") # PENDING, APPROVED, CONVERTED

class DeliveryChallan(Base):
    __tablename__ = "delivery_challans"

    id = Column(Integer, primary_key=True, index=True)
    challan_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    driver_name = Column(String(100), nullable=True)
    vehicle_number = Column(String(30), nullable=True)
    challan_date = Column(Date, default=date.today)
    status = Column(String(20), default="DISPATCHED")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    po_date = Column(Date, default=date.today)
    total_amount = Column(Numeric(12, 2), default=0.00)
    status = Column(String(20), default="ISSUED")

class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    invoice_type = Column(String(30), default="GST Invoice") # GST Invoice, Retail, Wholesale, Proforma
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    invoice_date = Column(Date, nullable=False, default=date.today)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00)
    cgst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    sgst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    igst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    grand_total = Column(Numeric(12, 2), nullable=False, default=0.00)
    payment_mode = Column(String(50), nullable=False, default="CASH")
    payment_status = Column(String(20), nullable=False, default="PAID")
    vehicle_number = Column(String(30), nullable=True)
    eway_bill_no = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="sales")
    items = relationship("SalesItem", back_populates="invoice", cascade="all, delete-orphan")

class SalesItem(Base):
    __tablename__ = "sales_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("SalesInvoice", back_populates="items")
    product = relationship("Product")

class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_date = Column(Date, nullable=False, default=date.today)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00)
    gst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    grand_total = Column(Numeric(12, 2), nullable=False, default=0.00)
    payment_status = Column(String(20), nullable=False, default="PAID")
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="invoice", cascade="all, delete-orphan")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product")

class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id = Column(Integer, primary_key=True, index=True)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    transfer_date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(String(50), nullable=False)
    salary = Column(Numeric(12, 2), nullable=False, default=0.00)
    joining_date = Column(Date, nullable=False, default=date.today)
    status = Column(String(20), default="ACTIVE")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    attendance_date = Column(Date, default=date.today)
    status = Column(String(20), default="PRESENT") # PRESENT, ABSENT, LEAVE, HALF_DAY

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    expense_date = Column(Date, nullable=False, default=date.today)
    notes = Column(Text, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(120), nullable=False)
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
