import os
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Staff") # Admin, Manager, Accountant, Staff
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

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
    unit = Column(String(20), nullable=False, default="PCS") # BAGS, TON, PCS, MTR
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    gst_rate = Column(Numeric(5, 2), nullable=False, default=18.00)
    stock_quantity = Column(Numeric(12, 2), nullable=False, default=0.00)
    min_stock_level = Column(Numeric(12, 2), nullable=False, default=10.00)
    hsn_code = Column(String(20), nullable=True, default="7318")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    invoice_date = Column(Date, nullable=False, default=date.today)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00)
    cgst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    sgst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    igst_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    grand_total = Column(Numeric(12, 2), nullable=False, default=0.00)
    payment_mode = Column(String(50), nullable=False, default="CASH") # CASH, BANK, UPI, CREDIT
    payment_status = Column(String(20), nullable=False, default="PAID")
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

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(String(50), nullable=False)
    salary = Column(Numeric(12, 2), nullable=False, default=0.00)
    joining_date = Column(Date, nullable=False, default=date.today)
    status = Column(String(20), default="ACTIVE")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False) # Transport, Salary, Electricity, Maintenance, Other
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
