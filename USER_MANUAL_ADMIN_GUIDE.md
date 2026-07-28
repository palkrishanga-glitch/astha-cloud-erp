# ASTHA ERP Enterprise (v2.0) — Official User Manual & Administrator Guide

Welcome to **ASTHA ERP Enterprise (v2.0)** for **Astha Builders & Hardware**. This document serves as the official operational guide, administrator manual, installation handbook, and troubleshooting reference.

---

## 📋 1. Target Roles & Responsibilities

| Role | Access Scope & Primary Responsibilities |
| :--- | :--- |
| **Owner** | Unrestricted master system control, financial profit analysis, owner PIN approvals. |
| **Administrator** | System settings, user role management, database migrations, backup & restore operations. |
| **Manager** | Operational management, discount approvals, stock transfers, price list updates. |
| **Accountant** | Double-entry journal vouchers, trial balance, P&L, balance sheet, GSTR filing. |
| **Cashier / POS** | Fast retail sales billing, cash drawer balance management, thermal receipt printing. |
| **Sales Executive** | Quotations, sales orders, delivery challans, customer party management. |
| **Store / Warehouse** | Goods receipt notes (GRN), stock ledger adjustments, barcode label printing. |
| **Auditor** | Read-only inspection of non-deletable audit logs, ledger postings, and tax registers. |

---

## 💻 2. System Requirements & Installation Guide

### Minimum Requirements
- **OS:** Windows 10 / Windows 11 (64-bit)
- **CPU:** Intel Core i3 (4th Gen) or equivalent
- **RAM:** 4 GB
- **Storage:** 10 GB Free SSD Space
- **Display:** 1366 × 768 resolution

### Installation Steps
1. Download `ASTHA_ERP_v2.0.0_Setup.exe` or locate `dist/ASTHA_ERP/ASTHA_ERP.exe`.
2. Launch the installer and follow the setup wizard.
3. Run first-time setup (`POST /api/v1/auth/setup`) to configure company profile (`Astha Builders & Hardware`), owner credentials, and default financial year (`2026-2027`).

---

## ⌨️ 3. Global Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Ctrl + N** | Open New Entry Dialog (Sales Invoice, Product, Party) |
| **Ctrl + S** | Save Current Document / Invoice |
| **Ctrl + P** | Print Invoice (A4 ReportLab PDF or Thermal POS) |
| **Ctrl + F** | Open Global Enterprise Search Modal |
| **Ctrl + E** | Export Report / Data to Excel / CSV / PDF |
| **F5** | Refresh Live Dashboard Data |
| **Esc** | Close Dialog / Cancel Modal |

---

## 🛠️ 4. Troubleshooting & Maintenance Guide

### Application Does Not Start
- **Cause:** Corrupted database file or missing port binding.
- **Solution:** Verify `astha_erp.db` integrity via `GET /api/v1/reports/system-health`. Run emergency repair if required (`POST /api/v1/backup/repair`).

### Database Backup / Restore Failure
- **Cause:** Insufficient disk space or invalid SHA-256 checksum.
- **Solution:** Check free disk space (>1GB). Ensure pre-restore safety snapshot was generated automatically before proceeding.

### Cloud Sync Retry Queue Failure
- **Cause:** Intermittent internet connectivity to Render Web Backend.
- **Solution:** Offline transactions are stored safely in local queue. Once internet reconnects, click **Sync Queue Push** on the dashboard.

---

🐙 **GitHub Repository:** [https://github.com/palkrishanga-glitch/astha-cloud-erp](https://github.com/palkrishanga-glitch/astha-cloud-erp)
