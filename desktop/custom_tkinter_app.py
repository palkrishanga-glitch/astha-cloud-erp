import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import hashlib
import os
import random
import secrets
import shutil
import smtplib
import sqlite3
import sys
import urllib.parse
import webbrowser
import winsound
from datetime import datetime, timedelta
from email.message import EmailMessage
from time import strftime

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Table, TableStyle
    from reportlab.pdfgen.canvas import Canvas
except ImportError:
    Canvas = None
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import psycopg2
except ImportError:
    psycopg2 = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.0.0"
OTP_SENDER_EMAIL = "pal.7461@gmail.com"
DEFAULT_PUBLIC_BASE_URL = "https://astha-cloud-erp-free-test.onrender.com"

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
ASSET_DIR = os.path.join(RESOURCE_DIR, "assets")
APP_ICON_PNG = os.path.join(ASSET_DIR, "astha_erp_icon.png")
APP_ICON_ICO = os.path.join(ASSET_DIR, "astha_erp_icon.ico")
ONEDRIVE_DIR = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
DATA_DIR = os.environ.get(
    "ASTHA_ERP_STORAGE",
    os.path.join(ONEDRIVE_DIR or BASE_DIR, "ASTHA_ERP_Cloud"),
)
os.makedirs(DATA_DIR, exist_ok=True)
LOCAL_DB_FILE = os.path.join(BASE_DIR, "shop.db")
DB_FILE = os.path.join(DATA_DIR, "shop.db")
if not os.path.exists(DB_FILE) and os.path.exists(LOCAL_DB_FILE):
    shutil.copy(LOCAL_DB_FILE, DB_FILE)
os.chdir(DATA_DIR)
APP_DIRS = [os.path.join(DATA_DIR, name) for name in ["invoices", "exports", "backups", "qr", "assets", "deleted"]]

UI_BG = "#0b1120"
UI_PANEL = "#111827"
UI_PANEL_2 = "#162033"
UI_CARD = "#101826"
UI_BORDER = "#263244"
UI_TEXT_MUTED = "#94a3b8"
UI_PRIMARY = "#2563eb"
UI_PRIMARY_HOVER = "#1d4ed8"
UI_SUCCESS = "#15803d"
UI_DANGER = "#dc2626"

for folder in APP_DIRS:
    os.makedirs(folder, exist_ok=True)

def clean_database_url(value):
    value = (value or "").strip()
    placeholders = ("your-supabase-postgres-url", "[your", "YOUR_PASSWORD", "postgresql://postgres.[")
    if not value or not value.startswith(("postgresql://", "postgres://")) or any(part in value for part in placeholders):
        return ""
    return value

DATABASE_URL = clean_database_url(os.environ.get("ASTHA_DATABASE_URL")) or clean_database_url(os.environ.get("SUPABASE_DB_URI"))
USE_POSTGRES = bool(DATABASE_URL)

def normalize_postgres_sql(sql):
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("REAL", "DOUBLE PRECISION")
    return sql.replace("?", "%s")

class PostgresCursor:
    def __init__(self, raw_cursor):
        self.raw_cursor = raw_cursor

    def execute(self, sql, params=None):
        self.raw_cursor.execute(normalize_postgres_sql(sql), params or ())
        return self

    def fetchone(self):
        return self.raw_cursor.fetchone()

    def fetchall(self):
        return self.raw_cursor.fetchall()

    @property
    def rowcount(self):
        return self.raw_cursor.rowcount

def rollback_if_needed():
    try:
        conn.rollback()
    except Exception:
        pass

if USE_POSTGRES:
    if psycopg2 is None:
        messagebox.showerror(
            "Database Error",
            "psycopg2-binary is required for Supabase/PostgreSQL.\n\nRun: pip install psycopg2-binary",
        )
        sys.exit(1)
    conn = psycopg2.connect(DATABASE_URL)
    cursor = PostgresCursor(conn.cursor())
else:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    name TEXT,
    hsn TEXT,
    batch TEXT,
    expiry TEXT,
    price REAL,
    purchase_price REAL DEFAULT 0,
    sale_price REAL DEFAULT 0,
    unit TEXT DEFAULT 'Pcs',
    quantity REAL,
    gst REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    customer TEXT,
    mobile TEXT,
    total REAL,
    profit REAL DEFAULT 0,
    date TEXT,
    amount_paid REAL DEFAULT 0,
    balance REAL DEFAULT 0,
    due_date TEXT,
    payment_status TEXT DEFAULT 'Unpaid'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile TEXT,
    email TEXT,
    address TEXT,
    gst TEXT,
    balance REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS suppliers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile TEXT,
    email TEXT,
    address TEXT,
    gst TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    amount REAL,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    customer TEXT,
    mobile TEXT,
    amount REAL,
    mode TEXT DEFAULT 'Cash',
    note TEXT,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier TEXT,
    product TEXT,
    quantity REAL,
    rate REAL,
    gst REAL,
    total REAL,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS invoice_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    product TEXT,
    quantity REAL,
    unit TEXT DEFAULT 'Pcs',
    price REAL,
    gst REAL,
    gst_amount REAL,
    total REAL,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS deleted_invoices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    customer TEXT,
    mobile TEXT,
    total REAL,
    profit REAL,
    date TEXT,
    pdf_path TEXT,
    deleted_at TEXT,
    amount_paid REAL DEFAULT 0,
    balance REAL DEFAULT 0,
    due_date TEXT,
    payment_status TEXT DEFAULT 'Unpaid'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT,
    gst TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    pin TEXT,
    pin_code TEXT,
    district TEXT,
    state TEXT,
    country TEXT,
    cloud_backup_path TEXT,
    logo_path TEXT,
    profile_photo_path TEXT,
    email_verified INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS web_auth(
    id INTEGER PRIMARY KEY CHECK (id = 1),
    username TEXT,
    email TEXT,
    google_sub TEXT,
    security_question TEXT,
    security_answer_hash TEXT,
    password_hash TEXT NOT NULL,
    updated_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS public_invoice_links(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT
)
""")

for column_name, column_def in [
    ("username", "TEXT"),
    ("email", "TEXT"),
    ("google_sub", "TEXT"),
    ("security_question", "TEXT"),
    ("security_answer_hash", "TEXT"),
]:
    try:
        cursor.execute(f"ALTER TABLE web_auth ADD COLUMN {column_name} {column_def}")
        conn.commit()
    except Exception:
        rollback_if_needed()

conn.commit()

try:
    cursor.execute("ALTER TABLE sales ADD COLUMN profit REAL DEFAULT 0")
    conn.commit()
except Exception:
    rollback_if_needed()

for table_name, migrations in {
    "sales": [
        ("amount_paid", "REAL DEFAULT 0"),
        ("balance", "REAL DEFAULT 0"),
        ("due_date", "TEXT"),
        ("payment_status", "TEXT DEFAULT 'Unpaid'"),
    ],
    "products": [
        ("purchase_price", "REAL DEFAULT 0"),
        ("sale_price", "REAL DEFAULT 0"),
        ("unit", "TEXT DEFAULT 'Pcs'"),
    ],
    "invoice_items": [
        ("unit", "TEXT DEFAULT 'Pcs'"),
    ],
    "deleted_invoices": [
        ("amount_paid", "REAL DEFAULT 0"),
        ("balance", "REAL DEFAULT 0"),
        ("due_date", "TEXT"),
        ("payment_status", "TEXT DEFAULT 'Unpaid'"),
    ],
    "customers": [
        ("email", "TEXT"),
    ],
    "suppliers": [
        ("email", "TEXT"),
    ],
    "settings": [
        ("pin_code", "TEXT"),
        ("district", "TEXT"),
        ("state", "TEXT"),
        ("country", "TEXT"),
        ("cloud_backup_path", "TEXT"),
        ("logo_path", "TEXT"),
        ("profile_photo_path", "TEXT"),
        ("email_verified", "INTEGER DEFAULT 0"),
    ],
}.items():
    for column_name, column_def in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            conn.commit()
        except Exception:
            rollback_if_needed()

cursor.execute("""
UPDATE products
SET purchase_price = CASE WHEN COALESCE(purchase_price, 0) = 0 THEN COALESCE(price, 0) ELSE purchase_price END,
    sale_price = CASE WHEN COALESCE(sale_price, 0) = 0 THEN COALESCE(price, 0) ELSE sale_price END
""")
conn.commit()

cursor.execute("SELECT id, total, date, balance, due_date, payment_status FROM sales")
for sale_id, total, sale_date, balance, due_date, payment_status in cursor.fetchall():
    updates = {}
    if balance is None or (float(balance or 0) == 0 and payment_status != "Paid"):
        updates["balance"] = float(total or 0)
    if not due_date:
        parsed_date = None
        for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
            try:
                parsed_date = datetime.strptime(sale_date, fmt)
                break
            except (TypeError, ValueError):
                pass
        if parsed_date:
            updates["due_date"] = (parsed_date + timedelta(days=45)).strftime("%d-%m-%Y")
    if not payment_status:
        updates["payment_status"] = "Unpaid"
    if updates:
        assignments = ", ".join([f"{key}=?" for key in updates])
        cursor.execute(
            f"UPDATE sales SET {assignments} WHERE id=?",
            (*updates.values(), sale_id),
        )
conn.commit()

cursor.execute("SELECT * FROM settings")
setting = cursor.fetchone()
FIRST_RUN_SETUP = False

if not setting:
    FIRST_RUN_SETUP = True
    pin_hash = ""
    cursor.execute("""
    INSERT INTO settings(business_name, gst, phone, email, address, pin, pin_code, district, state, country, cloud_backup_path, logo_path, profile_photo_path, email_verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "ASTHA BUILDERS & HARDWARE",
        "23ABCDE1234F1Z5",
        "+91 9876543210",
        "demo@gmail.com",
        "India",
        pin_hash,
        "",
        "",
        "",
        "India",
        "",
        "",
        "",
        0,
    ))
    conn.commit()

cursor.execute("SELECT * FROM settings")
setting = cursor.fetchone()
APP_PIN = setting[6]

def setting_value(index, default=""):
    return setting[index] if len(setting) > index and setting[index] is not None else default

def is_email_verified():
    return int(setting_value(14, 0) or 0) == 1

def normalize_recovery_answer(answer):
    return (answer or "").strip().lower()

def web_auth_row():
    try:
        cursor.execute("""
        SELECT username, email, password_hash, security_question, security_answer_hash
        FROM web_auth
        WHERE id=1
        """)
        return cursor.fetchone()
    except Exception:
        rollback_if_needed()
        return None

def verify_owner_password(identifier, password):
    row = web_auth_row()
    identifier = (identifier or "").strip().lower()
    if not row or not password:
        return False
    username, email, password_hash, *_rest = row
    return identifier in ((username or "").lower(), (email or "").lower()) and check_password_hash(password_hash, password)

def create_app_icon(master):
    if os.path.exists(APP_ICON_PNG):
        try:
            return tk.PhotoImage(master=master, file=APP_ICON_PNG)
        except tk.TclError:
            pass
    icon = tk.PhotoImage(master=master, width=32, height=32)
    icon.put("#0f172a", to=(0, 0, 32, 32))
    icon.put("#15803d", to=(3, 3, 29, 29))
    icon.put("#22c55e", to=(5, 5, 27, 27))
    icon.put("#0f172a", to=(7, 7, 25, 25))
    icon.put("#ffffff", to=(14, 8, 18, 24))
    icon.put("#ffffff", to=(9, 20, 23, 24))
    icon.put("#86efac", to=(11, 12, 21, 16))
    return icon

def apply_window_icon(win):
    try:
        if os.path.exists(APP_ICON_ICO):
            win.iconbitmap(APP_ICON_ICO)
        if not hasattr(apply_window_icon, "icon"):
            apply_window_icon.icon = create_app_icon(win)
        win.iconphoto(True, apply_window_icon.icon)
    except tk.TclError:
        pass

def run_first_time_setup():
    global setting, APP_PIN

    setup = ctk.CTk()
    apply_window_icon(setup)
    setup.geometry("520x430")
    setup.title("ASTHA ERP First Setup")

    ctk.CTkLabel(setup, text="First Time Setup", font=("Segoe UI", 30, "bold")).pack(pady=(34, 8))
    ctk.CTkLabel(setup, text="Create your owner login PIN for this installation", font=("Segoe UI", 13), text_color="#94a3b8").pack(pady=(0, 18))

    business_entry = ctk.CTkEntry(setup, placeholder_text="Business Name", width=320, height=42)
    business_entry.insert(0, setting[1] or "")
    business_entry.pack(pady=8)

    pin_entry = ctk.CTkEntry(setup, placeholder_text="New PIN", show="*", width=320, height=42)
    pin_entry.pack(pady=8)

    confirm_entry = ctk.CTkEntry(setup, placeholder_text="Confirm PIN", show="*", width=320, height=42)
    confirm_entry.pack(pady=8)

    def save_setup():
        global setting, APP_PIN
        new_pin = pin_entry.get().strip()
        confirm_pin = confirm_entry.get().strip()
        business_name = business_entry.get().strip() or "ASTHA ERP"

        if len(new_pin) < 4:
            messagebox.showerror("Setup", "PIN must be at least 4 characters")
            return
        if new_pin != confirm_pin:
            messagebox.showerror("Setup", "PIN and confirm PIN do not match")
            return

        pin_hash = hashlib.sha256(new_pin.encode()).hexdigest()
        cursor.execute("UPDATE settings SET business_name=?, pin=? WHERE id=?", (business_name, pin_hash, setting[0]))
        conn.commit()
        cursor.execute("SELECT * FROM settings WHERE id=?", (setting[0],))
        setting = cursor.fetchone()
        APP_PIN = setting[6]
        messagebox.showinfo("Setup Complete", "Your owner PIN has been saved")
        setup.destroy()

    ctk.CTkButton(setup, text="Save PIN", width=220, height=45, command=save_setup).pack(pady=24)
    pin_entry.bind("<Return>", lambda _event: save_setup())
    confirm_entry.bind("<Return>", lambda _event: save_setup())
    setup.mainloop()

def run_login():
    global setting

    login = ctk.CTk()
    login_icon = create_app_icon(login)
    login.iconphoto(True, login_icon)
    login.geometry("520x620")
    login.title("ASTHA ERP LOGIN")

    ctk.CTkLabel(login, text="ASTHA ERP LOGIN", font=("Segoe UI", 30, "bold")).pack(pady=(34, 10))
    ctk.CTkLabel(login, text="Login with main account username/email and password", font=("Segoe UI", 13), text_color="#94a3b8").pack(pady=(0, 14))

    account_entry = ctk.CTkEntry(login, placeholder_text="Username or email", width=300, height=42)
    account_entry.pack(pady=8)

    password_entry = ctk.CTkEntry(login, placeholder_text="Password", show="*", width=300, height=42)
    password_entry.pack(pady=8)

    ctk.CTkLabel(login, text="Old PIN fallback", font=("Segoe UI", 12), text_color="#64748b").pack(pady=(18, 0))

    pin_entry = ctk.CTkEntry(login, placeholder_text="PIN", show="*", width=300, height=42)
    pin_entry.pack(pady=8)

    def verify_login():
        identifier = account_entry.get().strip()
        password = password_entry.get().strip()
        pin_value = pin_entry.get().strip()
        if identifier and password and verify_owner_password(identifier, password):
            login.destroy()
            return
        if pin_value and hashlib.sha256(pin_value.encode()).hexdigest() == APP_PIN:
            login.destroy()
        else:
            messagebox.showerror("Error", "Invalid username/password or PIN")

    ctk.CTkButton(login, text="Login", width=240, height=45, command=verify_login).pack(pady=(18, 8))

    account_entry.bind("<Return>", lambda _event: verify_login())
    password_entry.bind("<Return>", lambda _event: verify_login())
    pin_entry.bind("<Return>", lambda _event: verify_login())
    login.mainloop()

def launch_desktop_app():
    global setting, APP_PIN, app
    if FIRST_RUN_SETUP or not APP_PIN:
        run_first_time_setup()
    run_login()

    app = ctk.CTk()
    app.title("ASTHA ERP ULTIMATE")
    app.geometry("1600x900")
    apply_window_icon(app)

    try:
        app.state("zoomed")
    except tk.TclError:
        pass

    app.mainloop()

if __name__ == "__main__":
    launch_desktop_app()
