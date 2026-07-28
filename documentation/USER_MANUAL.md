# ASTHA ERP ENTERPRISE — USER MANUAL & OPERATIONAL GUIDE

Welcome to **ASTHA ERP Enterprise** built specifically for **Astha Builders & Hardware**.

---

## 1. System Requirements & Installation

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **RAM:** 4 GB minimum (8 GB recommended)
- **Disk Space:** 500 MB free disk space
- **Database:** PostgreSQL (Supabase Cloud Sync) or Direct Offline SQLite

---

## 2. Login & User Permissions

| Role | Access Level | Description |
| :--- | :--- | :--- |
| **Admin** | Full Control | System configuration, database backup, audit logs, user creation |
| **Manager** | Operations | Sales, Purchases, Stock adjustments, Customer & Supplier directory |
| **Accountant** | Financials | GST returns, Journal vouchers, Ledger posting, Reports |
| **Staff** | Billing | POS sales invoicing, Customer search, Inventory check |

---

## 3. Core Operational Modules

### 🛒 Sales Billing (POS Terminal)
1. Select Customer from the directory or choose **Cash Customer**.
2. Scan barcode or search material (e.g. *UltraTech PPC Cement*, *Tata Tiscon TMT Steel*).
3. Enter Quantity and Rate. CGST, SGST, and IGST lines calculate automatically.
4. Click **Print & Save Invoice** to generate A4/Thermal GST receipt PDF.

### 📦 Inventory & Stock Ledger
- Stock levels auto-deduct upon sales invoice posting and auto-increase upon purchase invoice entry.
- Automatic **Low Stock Alerts** trigger when stock falls below minimum threshold.

### 💾 Backup & Data Safety
- Automatic daily snapshots stored locally in `./backups`.
- Click **Generate Instant Database Backup** under Settings to generate a complete `.zip` / `.sql` archive.
