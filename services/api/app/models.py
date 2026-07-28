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
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)
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
    owner_pin_hash = Column(String(255), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department = Column(String(50), nullable=True)
    designation = Column(String(50), nullable=True)
    status = Column(String(20), default='ACTIVE')
    profile_photo = Column(Text, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    theme_preference = Column(String(20), default='dark')
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
    status = Column(String(20), nullable=False)
    failure_reason = Column(String(200), nullable=True)

class Party(Base):
    __tablename__ = "parties"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    party_code = Column(String(30), unique=True, nullable=False, index=True)
    business_name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    party_type = Column(String(20), nullable=False)
    gstin = Column(String(15), nullable=True, index=True)
    pan = Column(String(10), nullable=True)
    mobile = Column(String(15), nullable=False, index=True)
    alt_mobile = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)
    address_line2 = Column(Text, nullable=True)
    city = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    state = Column(String(50), nullable=False)
    country = Column(String(50), default='India')
    pincode = Column(String(10), nullable=False)
    gst_registration_type = Column(String(30), default='REGISTERED')
    msme_number = Column(String(50), nullable=True)
    business_type = Column(String(30), default='RETAIL')
    credit_limit = Column(Numeric(12, 2), default=0.00)
    credit_days = Column(Integer, default=0)
    opening_balance = Column(Numeric(12, 2), default=0.00)
    opening_balance_type = Column(String(10), default='DEBIT')
    opening_balance_date = Column(Date, nullable=False)
    currency = Column(String(10), default='INR')
    default_payment_mode = Column(String(20), default='CASH')
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    upi_id = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ledgers = relationship("PartyLedger", back_populates="party")
    documents = relationship("PartyDocument", back_populates="party")

class PartyDocument(Base):
    __tablename__ = "party_documents"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    document_name = Column(String(100), nullable=False)
    file_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    party = relationship("Party", back_populates="documents")

class PartyLedger(Base):
    __tablename__ = "party_ledgers"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    voucher_number = Column(String(50), nullable=False)
    voucher_type = Column(String(30), nullable=False)
    reference_number = Column(String(50), nullable=True)
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
    code = Column(String(30), unique=True, nullable=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(200), nullable=True)
    manager_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_code = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(50), unique=True, nullable=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(150), nullable=False, index=True)
    short_name = Column(String(50), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sub_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    hsn_code = Column(String(10), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    cgst_rate = Column(Numeric(5, 2), default=0.00)
    sgst_rate = Column(Numeric(5, 2), default=0.00)
    igst_rate = Column(Numeric(5, 2), default=0.00)
    cess_rate = Column(Numeric(5, 2), default=0.00)
    tax_type = Column(String(20), default='TAX_EXCLUSIVE')
    purchase_price = Column(Numeric(12, 2), nullable=False)
    selling_price = Column(Numeric(12, 2), nullable=False)
    wholesale_price = Column(Numeric(12, 2), nullable=True)
    retail_price = Column(Numeric(12, 2), nullable=True)
    dealer_price = Column(Numeric(12, 2), nullable=True)
    mrp = Column(Numeric(12, 2), nullable=True)
    discount_percentage = Column(Numeric(5, 2), default=0.00)
    minimum_selling_price = Column(Numeric(12, 2), nullable=True)
    cost_price = Column(Numeric(12, 2), nullable=False)
    minimum_stock = Column(Numeric(10, 2), default=0.00)
    maximum_stock = Column(Numeric(10, 2), default=10000.00)
    reorder_level = Column(Numeric(10, 2), default=10.00)
    reorder_quantity = Column(Numeric(10, 2), default=50.00)
    opening_stock = Column(Numeric(10, 2), default=0.00)
    opening_stock_value = Column(Numeric(12, 2), default=0.00)
    opening_stock_date = Column(Date, nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stock_ledgers = relationship("StockLedger", back_populates="product")
    stock_batches = relationship("StockBatch", back_populates="product")

class StockLedger(Base):
    __tablename__ = "stock_ledgers"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    voucher_number = Column(String(50), nullable=False)
    voucher_type = Column(String(30), nullable=False)
    qty_in = Column(Numeric(12, 2), default=0.00)
    qty_out = Column(Numeric(12, 2), default=0.00)
    balance_qty = Column(Numeric(12, 2), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    created_by = Column(String(36), nullable=False)
    remarks = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="stock_ledgers")

class StockBatch(Base):
    __tablename__ = "stock_batches"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    batch_number = Column(String(50), nullable=False)
    lot_number = Column(String(50), nullable=True)
    mfg_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    serial_number = Column(String(50), nullable=True)
    quantity = Column(Numeric(12, 2), default=0.00)
    purchase_rate = Column(Numeric(12, 2), nullable=False)
    selling_rate = Column(Numeric(12, 2), nullable=False)

    product = relationship("Product", back_populates="stock_batches")

class StockTransfer(Base):
    __tablename__ = "stock_transfers"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    transfer_no = Column(String(50), unique=True, nullable=False, index=True)
    transfer_date = Column(Date, nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    remarks = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SalesQuotation(Base):
    __tablename__ = "sales_quotations"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    quotation_no = Column(String(50), unique=True, nullable=False, index=True)
    quotation_date = Column(Date, nullable=False)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default='PENDING')
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DeliveryChallan(Base):
    __tablename__ = "delivery_challans"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    challan_no = Column(String(50), unique=True, nullable=False, index=True)
    challan_date = Column(Date, nullable=False)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    vehicle_number = Column(String(30), nullable=True)
    total_items = Column(Integer, default=0)
    status = Column(String(20), default='DELIVERED')
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SalesInvoiceModel(Base):
    __tablename__ = "sales_invoices"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    financial_year = Column(String(10), nullable=False, default='2026-2027')
    invoice_type = Column(String(20), default='CREDIT')
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    salesman_name = Column(String(100), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    cgst_total = Column(Numeric(12, 2), default=0.00)
    sgst_total = Column(Numeric(12, 2), default=0.00)
    igst_total = Column(Numeric(12, 2), default=0.00)
    cess_total = Column(Numeric(12, 2), default=0.00)
    round_off = Column(Numeric(5, 2), default=0.00)
    grand_total = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(20), default='CASH')
    payment_status = Column(String(20), default='UNPAID')
    amount_paid = Column(Numeric(12, 2), default=0.00)
    balance_due = Column(Numeric(12, 2), default=0.00)
    remarks = Column(Text, nullable=True)
    status = Column(String(20), default='APPROVED')
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    party = relationship("Party")
    items = relationship("SalesInvoiceItem", back_populates="invoice")

class SalesInvoiceItem(Base):
    __tablename__ = "sales_invoice_items"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("sales_invoices.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    hsn_code = Column(String(10), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_name = Column(String(20), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0.00)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    cgst_amount = Column(Numeric(12, 2), default=0.00)
    sgst_amount = Column(Numeric(12, 2), default=0.00)
    igst_amount = Column(Numeric(12, 2), default=0.00)
    line_total = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("SalesInvoiceModel", back_populates="items")
    product = relationship("Product")

class SalesReturnModel(Base):
    __tablename__ = "sales_returns"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    return_no = Column(String(50), unique=True, nullable=False, index=True)
    return_date = Column(Date, nullable=False)
    original_invoice_no = Column(String(50), nullable=False)
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    total_refund_amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    po_date = Column(Date, nullable=False)
    supplier_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default='APPROVED')
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoodsReceiptNote(Base):
    __tablename__ = "goods_receipt_notes"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    grn_number = Column(String(50), unique=True, nullable=False, index=True)
    po_number = Column(String(50), nullable=True)
    supplier_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    received_date = Column(Date, nullable=False)
    received_by = Column(String(100), nullable=False)
    status = Column(String(20), default='RECEIVED')
    created_at = Column(DateTime, default=datetime.utcnow)

class PurchaseInvoiceModel(Base):
    __tablename__ = "purchase_invoices"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    bill_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_invoice_no = Column(String(50), nullable=False, index=True)
    bill_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    supplier_id = Column(String(36), ForeignKey("parties.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    cgst_total = Column(Numeric(12, 2), default=0.00)
    sgst_total = Column(Numeric(12, 2), default=0.00)
    igst_total = Column(Numeric(12, 2), default=0.00)
    grand_total = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(20), default='BANK_TRANSFER')
    payment_status = Column(String(20), default='UNPAID')
    amount_paid = Column(Numeric(12, 2), default=0.00)
    balance_due = Column(Numeric(12, 2), default=0.00)
    remarks = Column(Text, nullable=True)
    status = Column(String(20), default='APPROVED')
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Party")
    items = relationship("PurchaseInvoiceItem", back_populates="purchase")

class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    purchase_id = Column(String(36), ForeignKey("purchase_invoices.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    hsn_code = Column(String(10), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_name = Column(String(20), nullable=False)
    purchase_rate = Column(Numeric(12, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0.00)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    cgst_amount = Column(Numeric(12, 2), default=0.00)
    sgst_amount = Column(Numeric(12, 2), default=0.00)
    line_total = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("PurchaseInvoiceModel", back_populates="items")
    product = relationship("Product")

class PurchaseReturnModel(Base):
    __tablename__ = "purchase_returns"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    return_no = Column(String(50), unique=True, nullable=False, index=True)
    return_date = Column(Date, nullable=False)
    original_bill_number = Column(String(50), nullable=False)
    supplier_id = Column(String(36), ForeignKey("parties.id"), nullable=False)
    total_refund_amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GstHsnMaster(Base):
    __tablename__ = "gst_hsn_master"
    id = Column(Integer, primary_key=True, index=True)
    hsn_code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    cgst_rate = Column(Numeric(5, 2), default=0.00)
    sgst_rate = Column(Numeric(5, 2), default=0.00)
    igst_rate = Column(Numeric(5, 2), default=0.00)

class GstRegister(Base):
    __tablename__ = "gst_registers"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    date = Column(Date, nullable=False, index=True)
    voucher_no = Column(String(50), nullable=False, index=True)
    voucher_type = Column(String(30), nullable=False) # SALE, PURCHASE, SALES_RETURN, PURCHASE_RETURN
    party_id = Column(String(36), ForeignKey("parties.id"), nullable=True)
    gstin = Column(String(15), nullable=True)
    state_code = Column(String(5), nullable=True)
    hsn_code = Column(String(10), nullable=False)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    cgst = Column(Numeric(12, 2), default=0.00)
    sgst = Column(Numeric(12, 2), default=0.00)
    igst = Column(Numeric(12, 2), default=0.00)
    cess = Column(Numeric(12, 2), default=0.00)
    total_tax = Column(Numeric(12, 2), nullable=False)
    is_input = Column(Boolean, default=False) # True = Input Credit (Purchase), False = Output Liability (Sale)

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
    account = relationship("Account")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    role_name = Column(String(50), nullable=True)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    table_name = Column(String(50), nullable=True)
    record_id = Column(String(36), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    machine_name = Column(String(100), nullable=True)
    status = Column(String(20), default='SUCCESS')
    timestamp = Column(DateTime, default=datetime.utcnow)
