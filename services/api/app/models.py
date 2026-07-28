import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Date, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # Owner, Administrator, Manager, Accountant, Sales Executive, Cashier, etc.
    description = Column(Text, nullable=True)

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False) # e.g. 'products:can_change_price', 'invoices:delete'
    module = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    employee_id = Column(String(30), unique=True, nullable=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True, index=True)
    mobile = Column(String(15), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    owner_pin_hash = Column(String(255), nullable=True) # Sensitive action verification
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department = Column(String(50), nullable=True)
    designation = Column(String(50), nullable=True)
    status = Column(String(20), default='ACTIVE') # ACTIVE, INACTIVE, BLOCKED, SUSPENDED, DELETED
    profile_photo = Column(Text, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    theme_preference = Column(String(20), default='dark') # dark, light, system
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    machine_name = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    login_time = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(50), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False) # SUCCESS, FAILED, LOCKED
    failure_reason = Column(String(200), nullable=True)

class Party(Base):
    __tablename__ = "parties"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    party_code = Column(String(30), unique=True, nullable=False, index=True)
    business_name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    party_type = Column(String(20), nullable=False) # 'CUSTOMER', 'SUPPLIER', 'BOTH'
    gstin = Column(String(15), nullable=True, index=True)
    pan = Column(String(10), nullable=True)
    mobile = Column(String(15), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)
    state = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    city = Column(String(50), nullable=False)
    pincode = Column(String(10), nullable=False)
    credit_limit = Column(Numeric(12, 2), default=0.00)
    credit_days = Column(Integer, default=0)
    opening_balance = Column(Numeric(12, 2), default=0.00)
    opening_balance_type = Column(String(10), default='DEBIT') # 'DEBIT' or 'CREDIT'
    opening_balance_date = Column(Date, nullable=False)
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ledgers = relationship("PartyLedger", back_populates="party")

class PartyLedger(Base):
    __tablename__ = "party_ledgers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    voucher_number = Column(String(50), nullable=False)
    voucher_type = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    debit = Column(Numeric(12, 2), default=0.00)
    credit = Column(Numeric(12, 2), default=0.00)
    running_balance = Column(Numeric(12, 2), nullable=False)
    created_by = Column(String(36), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    party = relationship("Party", back_populates="ledgers")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    short_name = Column(String(20), nullable=False)
    conversion_factor = Column(Numeric(10, 2), default=1.00)

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_code = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(50), nullable=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(150), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    hsn_code = Column(String(10), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    purchase_price = Column(Numeric(12, 2), nullable=False)
    selling_price = Column(Numeric(12, 2), nullable=False)
    wholesale_price = Column(Numeric(12, 2), nullable=True)
    retail_price = Column(Numeric(12, 2), nullable=True)
    minimum_stock = Column(Numeric(10, 2), default=0.00)
    maximum_stock = Column(Numeric(10, 2), default=10000.00)
    opening_stock = Column(Numeric(10, 2), default=0.00)
    opening_stock_value = Column(Numeric(12, 2), default=0.00)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockBatch(Base):
    __tablename__ = "stock_batches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    batch_number = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=True)
    serial_number = Column(String(50), nullable=True)
    quantity = Column(Numeric(12, 2), default=0.00)
    purchase_rate = Column(Numeric(12, 2), nullable=False)
    selling_rate = Column(Numeric(12, 2), nullable=False)

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account_type = Column(String(20), nullable=False)
    opening_balance = Column(Numeric(12, 2), default=0.00)
    opening_type = Column(String(10), default='DEBIT')

class Voucher(Base):
    __tablename__ = "vouchers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    voucher_no = Column(String(50), unique=True, nullable=False, index=True)
    voucher_date = Column(Date, nullable=False)
    voucher_type = Column(String(20), nullable=False)
    narration = Column(Text, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("VoucherItem", back_populates="voucher")

class VoucherItem(Base):
    __tablename__ = "voucher_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    voucher_id = Column(String(36), ForeignKey("vouchers.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit = Column(Numeric(12, 2), default=0.00)
    credit = Column(Numeric(12, 2), default=0.00)
    narration = Column(Text, nullable=True)

    voucher = relationship("Voucher", back_populates="items")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    role_name = Column(String(50), nullable=True)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False) # LOGIN, LOGOUT, DELETE_INVOICE, RESTORE_DB, etc.
    table_name = Column(String(50), nullable=True)
    record_id = Column(String(36), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    machine_name = Column(String(100), nullable=True)
    status = Column(String(20), default='SUCCESS')
    timestamp = Column(DateTime, default=datetime.utcnow)
