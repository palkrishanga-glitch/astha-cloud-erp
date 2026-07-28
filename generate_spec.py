import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header
        self.drawString(54, 750, "ASTHA ERP — Enterprise Specification Blueprint")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidential | Astha Builders & Hardware")
        self.line(54, 52, 558, 52)
        self.restoreState()

def build_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "ASTHA_ERP_Master_Specification.pdf")
    
    # 0.75-inch margins: Width is 612, Height is 792. Printable area is width 504, height 648
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0D9488'),
        alignment=1,
        spaceAfter=30
    )
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0D9488'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'SectionH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    def p(text, style=body_style):
        story.append(Paragraph(text, style))

    def s(height=8):
        story.append(Spacer(1, height))

    def h1(text):
        story.append(Paragraph(text, h1_style))
        s(4)

    def h2(text):
        story.append(Paragraph(text, h2_style))
        s(3)

    def h3(text):
        story.append(Paragraph(text, h3_style))
        s(2)

    def page_break():
        story.append(PageBreak())

    def make_styled_table(raw_data, col_widths):
        formatted_data = []
        for i, row in enumerate(raw_data):
            formatted_row = []
            for col in row:
                if i == 0:
                    formatted_row.append(Paragraph(f"<b>{col}</b>", table_header_style))
                else:
                    formatted_row.append(Paragraph(str(col), table_text_style))
            formatted_data.append(formatted_row)
        
        t = Table(formatted_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))
        story.append(t)
        s(8)

    # ================= COVER PAGE =================
    story.append(Spacer(1, 100))
    story.append(Paragraph("ASTHA ERP", title_style))
    story.append(Paragraph("Enterprise-Grade Cloud-Enabled ERP for Astha Builders & Hardware", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Decorative line
    line_table = Table([[""]], colWidths=[300])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor('#0D9488')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 120))
    
    story.append(Paragraph("<b>System Specification & Blueprint Document</b>", meta_style))
    story.append(Paragraph("<b>Target Platforms:</b> Windows Desktop (Offline-First) + Web Admin + Mobile Companion", meta_style))
    story.append(Paragraph("<b>Document Version:</b> 1.0.0 (Release Draft)", meta_style))
    story.append(Paragraph("<b>Date of Issue:</b> July 28, 2026", meta_style))
    story.append(Paragraph("<b>Prepared by:</b> Antigravity AI Systems Architect Group", meta_style))
    story.append(Paragraph("<b>Status:</b> Approved for Implementation Planning", meta_style))
    page_break()

    # ================= TABLE OF CONTENTS / SUMMARY =================
    h1("Document Overview & Table of Contents")
    p("This document serves as the primary system specification, database catalog, and design blueprint for ASTHA ERP, a custom enterprise solution designed specifically for Astha Builders & Hardware. It details all requirements for building an offline-first system capable of scaling to future Android/iOS releases, with seamless cloud synchronization and robust double-entry accounting integrity.")
    s(10)
    
    toc_data = [
        ["Section", "Contents", "Target Page"],
        ["1. Executive Summary & Vision", "Target Business, High-level Goals, Offline-First Architecture", "3"],
        ["2. Technology Stack & Deployment", "Desktop, Web, Mobile stacks, sync mechanism details", "4"],
        ["3. Project Directory Architecture", "Monorepo organization, microservices, frontends, shareables", "5"],
        ["4. Unified Database Catalog", "Detailed schema specs, key relationships, indices, data-types", "6"],
        ["5. Authentication & Permissions", "RBAC model matrix, granular permission codes, JWT auth", "10"],
        ["6. Customer & Supplier Modules", "Outstanding ledgers, aging logic, credit limit rules", "11"],
        ["7. Inventory & Warehouse Module", "Categories, reorder logic, barcodes, batch/expiry control", "12"],
        ["8. Sales, Billing & GST Engine", "GST invoices, point of sale (POS) shortcuts, challans, HSN", "13"],
        ["9. Double-Entry Accounting Core", "Chart of accounts, transaction journals, contra, trial balance", "14"],
        ["10. Integrations & Utility Engines", "WhatsApp API, ESC/POS barcode printing, AES-256 backup", "16"],
        ["11. QA & Implementation Plan", "Testing strategy, development phases, and roadmap milestones", "17"]
    ]
    make_styled_table(toc_data, [130, 310, 64])
    page_break()

    # ================= 1. EXECUTIVE SUMMARY & VISION =================
    h1("1. Executive Summary & Vision")
    p("<b>Astha Builders & Hardware</b> operates a high-volume retail and wholesale distribution network for construction materials, building supplies, hardware items, and paint products. With multiple warehouses, delivery yards, and high-frequency counter sales, the business faces complex logistical and financial operations.")
    
    h2("Core Challenges & Business Needs")
    p("• <b>Connectivity Constraints:</b> Retail yards and warehouses are frequently located in areas with intermittent internet access. If internet connectivity drops, counter billing and stock movements must continue without interruption.")
    p("• <b>Inventory Complexity:</b> Items vary widely (bulk cement bags, steel bars in bundles, liquid paint in batches with expiry, loose nuts and bolts). Warehouse transfers and automated reorder alerts are essential to avoid project supply disruptions.")
    p("• <b>Accounting Integrity:</b> Operations span cash sales, high-value credit sales, partial customer collections, and bulk supplier credits. Ad-hoc accounting sheets fail to prevent revenue leakage. The system requires a strict double-entry ledger engine.")
    p("• <b>Regulatory Compliance:</b> Tax compliance requires error-free GST invoicing, calculation of CGST, SGST, IGST, and generation of GSTR reports (GSTR-1, GSTR-3B) with active HSN/SAC code cataloging.")
    
    h2("The Unified Solution")
    p("ASTHA ERP is designed as a hybrid platform that solves these problems through a distributed system:")
    p("• <b>Desktop App (EXE):</b> Installed at retail counters. It operates on a local database (SQLite) for extreme speed and offline independence. All sales invoices, cash collection receipts, and inventory picks are saved locally.")
    p("• <b>Cloud Server (FastAPI + PostgreSQL):</b> Hosts the master data. Serves as the central clearinghouse for inventory reconciliation, consolidated accounting, and owner-facing reports.")
    p("• <b>Sync Engine:</b> Runs quietly in the background on the desktop clients. When connectivity is available, it pushes local transaction changesets and pulls catalog updates, handling data conflicts deterministically.")
    page_break()

    # ================= 2. TECHNOLOGY STACK & DEPLOYMENT =================
    h1("2. Technology Stack & Deployment")
    p("To ensure a cross-platform, long-term supportable system, the software stack uses modern, performant, and memory-safe tools across three primary vectors.")
    s(6)
    
    stack_data = [
        ["Layer", "Technology Selected", "Purpose & Rationale"],
        ["Desktop Frontend", "React 19 + TypeScript + Vite + TailwindCSS", "Responsive, interactive, easy component reuse across desktop and web applications."],
        ["Desktop Wrapper", "Tauri v2 + Rust Process Management", "Generates lightweight (under 20MB), high-performance Windows executables (EXE) with direct printer access."],
        ["Local Database", "SQLite 3", "Extremely fast embedded database requiring zero configuration, storing offline transactions."],
        ["Web Portal", "Next.js 15 (React 19) + TailwindCSS", "Provides a cloud-hosted, zero-install admin dashboard for multi-branch monitoring and accounting."],
        ["Backend API", "FastAPI (Python 3.12 / 3.14)", "Asynchronous, high-performance web framework for syncing, reporting, and integration scripts."],
        ["Cloud Database", "PostgreSQL 16", "Enterprise relational database with robust row-level security and JSONB indexing for audit trails."],
        ["Sync Transport", "WebSockets + HTTP Delta Payloads", "Ensures instant messaging for active connections, falling back to HTTP batches during sync recovery."],
        ["ORM & Migrations", "SQLAlchemy + Alembic", "Ensures uniform database queries and simple schema versioning across dev and production envs."]
    ]
    make_styled_table(stack_data, [80, 160, 264])
    
    h2("Offline-First Sync Engine Specification")
    p("The system enforces a write-locally, sync-globally data flow. The local desktop app reads and writes exclusively to the local SQLite database. A dedicated sync worker operates in a separate Rust thread within Tauri:")
    p("1. <b>Change Queue:</b> Every write operation (e.g., creating a sales invoice) inserts a row into a `sync_queue` table containing the table name, action type (INSERT, UPDATE), timestamp, and a JSON payload of the changes.")
    p("2. <b>Push Sequence:</b> When internet is active, the sync client pushes local queue entries in order of transaction timestamp. The cloud server validates the transaction, applies business rules, and saves it to PostgreSQL.")
    p("3. <b>Pull Sequence:</b> The cloud server broadcasts catalog updates (new items, changed prices, supplier credit revisions) using WebSockets or SSE (Server-Sent Events) to listening desktop nodes.")
    p("4. <b>Conflict Resolution Protocol:</b>")
    p("   - <i>Ledger/Invoices:</i> Invoices are assigned unique alphanumeric serial codes prefixed by the local branch identifier. Since invoice sequences are distinct per branch, duplicate primary keys are avoided. If edits collide, Last-Write-Wins (LWW) is enforced by comparing record-level update timestamps.")
    p("   - <i>Stock Levels:</i> Real-time inventory is tracked using raw stock movement cards (debit/credit records). Instead of overwriting total stock quantities, the sync engine applies the delta shift (e.g., subtracting 10 bags of cement). This allows concurrent offline sales at different branches to merge without corrupting totals.")
    page_break()

    # ================= 3. FOLDER STRUCTURE =================
    h1("3. Project Directory Architecture")
    p("The ASTHA ERP codebase is organized as a monorepo, separating application runtimes while sharing core logic, validation schemas, and database types. This layout ensures maximum code reusability and minimizes drift between the Web and Desktop builds.")
    s(8)

    # Preformatted code-like structure represented as paragraphs/tables to ensure beautiful spacing
    folder_data = [
        ["Directory Path", "Domain", "Contents & Purpose"],
        ["/apps/desktop", "Desktop client", "Tauri core configurations, window handlers, serial/USB print modules, SQLite hooks."],
        ["/apps/web", "Cloud Web portal", "Next.js admin portal, reporting dashboard, configurations panel, multi-branch view."],
        ["/packages/shared", "Shared code", "TypeScript definitions, common interfaces, mathematical discount/tax validators, regex utilities."],
        ["/packages/db-schema", "Database logic", "Alembic migrations, standard tables definitions, local SQLite structure definitions."],
        ["/services/api", "Cloud Backend", "FastAPI app code, database routers, tax engines, report compilers, SMS/WhatsApp engines."],
        ["/services/sync-server", "Sync Engine", "WebSocket hubs, conflict resolution logic, queue consumers, network status health monitors."],
        ["/scripts", "Maintenance", "Automated backup cron scripts, security audits, database seeders for testing."]
    ]
    make_styled_table(folder_data, [130, 90, 284])
    
    h2("Detailed Microservice Architecture Layout")
    p("The diagram below illustrates the communications between the monorepo layers and dependencies:")
    
    arch_table = [
        ["Local Counter POS (Tauri EXE)", "Sync Transport", "Cloud Infrastructure"],
        ["Tauri Webview UI (React)\n  ↓ (Local IPC)\nTauri Rust Backend\n  ↓ (SQL queries)\nSQLite Local File", "HTTP POST /sync\nWebSockets (Real-time events)\nAES-256 Encrypted payloads\nDelta sync changesets", "FastAPI Gateway\n  ↓ (Async requests)\nCloud Workers / Task Queue\n  ↓ (SQLAlchemy)\nPostgreSQL Database\n  ↓ (Cloud Storage)\nAWS S3 (Daily Backups)"]
    ]
    make_styled_table(arch_table, [168, 168, 168])
    page_break()

    # ================= 4. UNIFIED DATABASE CATALOG =================
    h1("4. Unified Database Catalog")
    p("The tables below detail the foundational PostgreSQL (Cloud) and SQLite (Local) database structures. All primary keys are UUIDs generated by the client to support offline creation without server-side sequence allocation. Monotonically increasing numbers (like invoice IDs) use client-side unique prefixes.")
    s(10)
    
    # 4.1 Users & Roles
    h2("4.1 Authentication & User Access Tables")
    p("<b>Table Name:</b> `roles` (System Role Definitions)")
    roles_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "INT", "PRIMARY KEY", "Unique ID for the role (1 = Admin, 2 = Manager, 3 = Accountant, 4 = Sales, 5 = Store, 6 = Cashier)."],
        ["name", "VARCHAR(30)", "NOT NULL, UNIQUE", "The name of the role (e.g., 'Accountant')."],
        ["description", "TEXT", "NULLABLE", "Details of user responsibilities for this role."]
    ]
    make_styled_table(roles_data, [90, 100, 100, 214])

    p("<b>Table Name:</b> `users` (User Credentials & Status)")
    users_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Unique client-generated ID."],
        ["username", "VARCHAR(50)", "NOT NULL, UNIQUE", "Alphanumeric login identifier."],
        ["email", "VARCHAR(100)", "NULLABLE", "Contact email address for recovery."],
        ["password_hash", "VARCHAR(255)", "NOT NULL", "Password hash stored using Argon2id algorithm."],
        ["role_id", "INT", "FOREIGN KEY (roles.id)", "Assigned security role mapping."],
        ["is_active", "BOOLEAN", "NOT NULL, DEFAULT TRUE", "Active flag. Set to false to disable access."],
        ["created_at", "TIMESTAMP", "NOT NULL, DEFAULT NOW()", "Date and time the account was created."]
    ]
    make_styled_table(users_data, [90, 100, 120, 194])
    s(10)
    
    # 4.2 Customer & Supplier Modules
    h2("4.2 Customer & Supplier Ledger Tables")
    p("<b>Table Name:</b> `customers` (Customer Directory & Constraints)")
    cust_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Customer UUID."],
        ["name", "VARCHAR(100)", "NOT NULL", "Full name of the contact person."],
        ["company_name", "VARCHAR(100)", "NULLABLE", "Name of the firm (e.g., 'Astha Builders')."],
        ["phone", "VARCHAR(15)", "NOT NULL", "Primary mobile number for WhatsApp alerts."],
        ["email", "VARCHAR(100)", "NULLABLE", "Primary email address."],
        ["gstin", "VARCHAR(15)", "NULLABLE", "15-character Indian Goods and Services Tax Identification Number."],
        ["credit_limit", "NUMERIC(12,2)", "DEFAULT 0.00", "Maximum outstanding ledger balance allowed."],
        ["opening_balance", "NUMERIC(12,2)", "DEFAULT 0.00", "Initial balance before using this system."],
        ["opening_type", "VARCHAR(2)", "DEFAULT 'DR'", "DR (Debit / Receivable) or CR (Credit / Payable)."],
        ["created_at", "TIMESTAMP", "DEFAULT NOW()", "System insertion time."]
    ]
    make_styled_table(cust_data, [90, 100, 120, 194])
    page_break()

    p("<b>Table Name:</b> `customer_ledgers` (Running Customer Ledger Cards)")
    cust_ledger_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Ledger entry UUID."],
        ["customer_id", "UUID", "FK (customers.id)", "Link to target customer."],
        ["txn_date", "DATE", "NOT NULL", "Date of transaction activity."],
        ["voucher_type", "VARCHAR(10)", "NOT NULL", "Voucher class: 'SALE', 'RECEIPT', 'RETURN', 'OPENING'."],
        ["voucher_id", "UUID", "NOT NULL", "UUID of matching document (Sales Invoice, Receipt Voucher, etc.)."],
        ["debit", "NUMERIC(12,2)", "DEFAULT 0.00", "Amount receivable from customer (increases outstanding balance)."],
        ["credit", "NUMERIC(12,2)", "DEFAULT 0.00", "Amount received from customer (reduces outstanding balance)."],
        ["running_balance", "NUMERIC(12,2)", "NOT NULL", "Calculated balance after transaction is posted."],
        ["remarks", "TEXT", "NULLABLE", "Transaction description or invoice details."]
    ]
    make_styled_table(cust_ledger_data, [90, 100, 120, 194])

    p("<b>Table Name:</b> `suppliers` (Supplier Directory)")
    supp_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Supplier UUID."],
        ["name", "VARCHAR(100)", "NOT NULL", "Vendor name or point of contact."],
        ["company_name", "VARCHAR(100)", "NOT NULL", "Registered supplier business name."],
        ["phone", "VARCHAR(15)", "NOT NULL", "Primary mobile number."],
        ["gstin", "VARCHAR(15)", "NULLABLE", "Indian GST identification number."],
        ["opening_balance", "NUMERIC(12,2)", "DEFAULT 0.00", "Initial balance on vendor ledger."],
        ["opening_type", "VARCHAR(2)", "DEFAULT 'CR'", "DR (Receivable/Refund) or CR (Payable/Liability)."]
    ]
    make_styled_table(supp_data, [90, 100, 120, 194])
    s(10)

    # 4.3 Inventory & Stock Tables
    h2("4.3 Inventory & Warehouse Stock Tables")
    p("<b>Table Name:</b> `items` (Product Catalog Catalog)")
    items_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Product identifier."],
        ["name", "VARCHAR(150)", "NOT NULL", "Name of product (e.g., 'Ultratech Cement OPC 53')."],
        ["sku", "VARCHAR(50)", "UNIQUE", "Stock Keeping Unit code."],
        ["barcode", "VARCHAR(50)", "NULLABLE", "UPC, EAN, or custom system barcode for scanning."],
        ["category_id", "INT", "FOREIGN KEY", "Product Category classification."],
        ["brand_id", "INT", "FOREIGN KEY", "Product brand (e.g., 'TATA', 'Birla')."],
        ["primary_unit_id", "INT", "FOREIGN KEY", "Base stock unit (e.g., 'Bag', 'Box')."],
        ["secondary_unit_id", "INT", "NULLABLE, FK", "Sub-stock unit for retail splits (e.g., 'kg', 'Piece')."],
        ["hsn_code", "VARCHAR(8)", "NOT NULL", "Harmonized System of Nomenclature code for GST mapping."],
        ["gst_rate", "NUMERIC(5,2)", "NOT NULL", "Integrated GST tax percentage (e.g., 18.00, 28.00)."],
        ["reorder_level", "NUMERIC(10,2)", "DEFAULT 10.00", "Minimum stock level threshold for alerts."],
        ["is_active", "BOOLEAN", "DEFAULT TRUE", "Item availability toggle."]
    ]
    make_styled_table(items_data, [90, 100, 110, 204])
    page_break()

    p("<b>Table Name:</b> `stocks` (Warehouse-Batch Mapping / Inventory State)")
    stocks_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Unique stock batch identifier."],
        ["item_id", "UUID", "FK (items.id)", "Link to catalog item."],
        ["warehouse_id", "INT", "FOREIGN KEY", "Link to specific warehouse or yard."],
        ["batch_no", "VARCHAR(50)", "NOT NULL", "Manufacturer batch number for tracking and audits."],
        ["expiry_date", "DATE", "NULLABLE", "Product expiration date (critical for chemical paints/cements)."],
        ["qty", "NUMERIC(12,2)", "DEFAULT 0.00", "Physical stock count currently on hand."],
        ["purchase_rate", "NUMERIC(12,2)", "NOT NULL", "Purchase cost per unit before GST."],
        ["sale_rate", "NUMERIC(12,2)", "NOT NULL", "Target selling rate before GST."]
    ]
    make_styled_table(stocks_data, [90, 100, 120, 194])
    s(10)

    # 4.4 Sales & GST Billing
    h2("4.4 Sales Invoicing & GST Logging Tables")
    p("<b>Table Name:</b> `sales_invoices` (Sales Invoices Ledger)")
    sales_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Invoice UUID."],
        ["invoice_no", "VARCHAR(30)", "NOT NULL, UNIQUE", "Formatted invoice number (e.g., 'AS-26-0001')."],
        ["invoice_date", "DATE", "NOT NULL", "Date of sale transaction."],
        ["customer_id", "UUID", "FK (customers.id)", "Link to target customer."],
        ["warehouse_id", "INT", "FOREIGN KEY", "Warehouse inventory source."],
        ["sub_total", "NUMERIC(12,2)", "NOT NULL", "Sum of items net rates before taxes and discounts."],
        ["discount_amount", "NUMERIC(12,2)", "DEFAULT 0.00", "Total discount deducted from gross value."],
        ["cgst", "NUMERIC(12,2)", "DEFAULT 0.00", "Total Central GST collected (intrastate)."],
        ["sgst", "NUMERIC(12,2)", "DEFAULT 0.00", "Total State GST collected (intrastate)."],
        ["igst", "NUMERIC(12,2)", "DEFAULT 0.00", "Total Integrated GST collected (interstate)."],
        ["total_amount", "NUMERIC(12,2)", "NOT NULL", "Final invoice value (Subtotal - Discount + GST)."],
        ["payment_mode", "VARCHAR(20)", "NOT NULL", "Payment method: 'CASH', 'CREDIT', 'BANK', 'UPI', 'MIXED'."],
        ["payment_status", "VARCHAR(15)", "NOT NULL", "Payment status: 'PAID', 'UNPAID', 'PARTIAL'."],
        ["sync_status", "BOOLEAN", "DEFAULT FALSE", "Offline sync confirmation flag."]
    ]
    make_styled_table(sales_data, [90, 100, 120, 194])

    p("<b>Table Name:</b> `sales_invoice_items` (Invoice Line Items)")
    sales_items_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Line item ID."],
        ["invoice_id", "UUID", "FK (invoices.id)", "Link to parent invoice."],
        ["item_id", "UUID", "FK (items.id)", "Link to product catalog."],
        ["batch_no", "VARCHAR(50)", "NOT NULL", "Selected item batch code."],
        ["qty", "NUMERIC(12,2)", "NOT NULL", "Quantity purchased."],
        ["rate", "NUMERIC(12,2)", "NOT NULL", "Selling rate per unit (excl. GST)."],
        ["discount_percent", "NUMERIC(5,2)", "DEFAULT 0.00", "Line discount rate percentage."],
        ["cgst_rate", "NUMERIC(5,2)", "NOT NULL", "Central GST rate applied (e.g., 9.00)."],
        ["sgst_rate", "NUMERIC(5,2)", "NOT NULL", "State GST rate applied (e.g., 9.00)."],
        ["igst_rate", "NUMERIC(5,2)", "NOT NULL", "Integrated GST rate applied (e.g., 18.00)."],
        ["total_amount", "NUMERIC(12,2)", "NOT NULL", "Final line total (Qty * Net Rate + Tax)."]
    ]
    make_styled_table(sales_items_data, [90, 100, 120, 194])
    page_break()

    # 4.5 Financial & Double Entry Accounting Engine
    h2("4.5 Accounting System & General Ledger Tables")
    p("<b>Table Name:</b> `accounts` (Chart of Accounts)")
    accounts_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "INT", "PRIMARY KEY", "Ledger Account account code (e.g., 1001, 2005)."],
        ["code", "VARCHAR(20)", "NOT NULL, UNIQUE", "Chart of accounts grouping identifier."],
        ["name", "VARCHAR(100)", "NOT NULL", "Account name (e.g., 'State Bank of India A/c')."],
        ["parent_id", "INT", "NULLABLE, FK", "Parent account ID for nested groups."],
        ["account_type", "VARCHAR(20)", "NOT NULL", "Class: 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense'."],
        ["opening_balance", "NUMERIC(12,2)", "DEFAULT 0.00", "Day-zero ledger balance."],
        ["opening_type", "VARCHAR(2)", "DEFAULT 'DR'", "DR (Debit) or CR (Credit) indicator."]
    ]
    make_styled_table(accounts_data, [90, 100, 120, 194])

    p("<b>Table Name:</b> `vouchers` (General Vouchers Ledger)")
    vouchers_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Voucher ID."],
        ["voucher_no", "VARCHAR(30)", "NOT NULL, UNIQUE", "Unique transaction reference code (e.g., 'JV-26-0001')."],
        ["voucher_date", "DATE", "NOT NULL", "Entry creation date."],
        ["voucher_type", "VARCHAR(15)", "NOT NULL", "Class: 'JOURNAL', 'RECEIPT', 'PAYMENT', 'CONTRA'."],
        ["narration", "TEXT", "NULLABLE", "Overall transaction description."],
        ["total_amount", "NUMERIC(12,2)", "NOT NULL", "Voucher transaction total."]
    ]
    make_styled_table(vouchers_data, [90, 100, 120, 194])

    p("<b>Table Name:</b> `voucher_items` (Accounting Double-Entry Split Items)")
    v_items_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Double entry split item ID."],
        ["voucher_id", "UUID", "FK (vouchers.id)", "Link to parent voucher."],
        ["account_id", "INT", "FK (accounts.id)", "Target Chart of Accounts ledger."],
        ["debit", "NUMERIC(12,2)", "DEFAULT 0.00", "Amount debited (must be 0.00 if credit has value)."],
        ["credit", "NUMERIC(12,2)", "DEFAULT 0.00", "Amount credited (must be 0.00 if debit has value)."],
        ["narration", "TEXT", "NULLABLE", "Row-level memo or notes."]
    ]
    make_styled_table(v_items_data, [90, 100, 120, 194])
    
    h2("4.6 Security Audit Logs Table")
    p("<b>Table Name:</b> `audit_logs` (Internal Security & Transaction Trails)")
    audit_data = [
        ["Column Name", "Data Type", "Constraints", "Description"],
        ["id", "UUID", "PRIMARY KEY", "Log record identifier."],
        ["user_id", "UUID", "FOREIGN KEY", "User who performed the action."],
        ["action", "VARCHAR(50)", "NOT NULL", "Action description: 'DELETE_INVOICE', 'EDIT_LEDGER', etc."],
        ["table_name", "VARCHAR(50)", "NOT NULL", "Target database table affected."],
        ["record_id", "UUID", "NOT NULL", "Target record identifier."],
        ["old_value", "JSONB", "NULLABLE", "JSON snapshot of data state before change."],
        ["new_value", "JSONB", "NULLABLE", "JSON snapshot of data state after change."],
        ["ip_address", "VARCHAR(45)", "NOT NULL", "Origin IP address of user."],
        ["created_at", "TIMESTAMP", "DEFAULT NOW()", "Action execution time."]
    ]
    make_styled_table(audit_data, [90, 100, 120, 194])
    page_break()

    # ================= 5. AUTHENTICATION & ROLES =================
    h1("5. Authentication & User Roles")
    p("ASTHA ERP implements strict role-based access control (RBAC). In offline desktop mode, session tokens are securely signed using a local private key and verified by the desktop app database. In online mode, operations query the FastAPI OAuth2 service to retrieve JWT (JSON Web Tokens).")
    
    h2("System Role Definitions")
    p("• <b>Admin:</b> Has access to all system modules, global configurations, database back-ups, user creation, log reviews, and final accounting reconciliations.")
    p("• <b>Manager:</b> Supervises daily inventory levels, approves stock adjustments, oversees purchase order processes, and views standard client reports.")
    p("• <b>Accountant:</b> Enters journal vouchers, reviews tax filings (CGST, SGST, IGST), reconciles ledgers, and compiles financial statements (Trial Balance, P&L, Balance Sheet).")
    p("• <b>Sales Staff:</b> Creates sales quotations, converts quotations to sales orders, generates GST invoices, and tracks customer credit statuses.")
    p("• <b>Store Staff:</b> Updates stock receipts, processes warehouse transfers, prints barcodes, and logs item updates.")
    p("• <b>Cashier:</b> Manages daily point-of-sale billing, cash registers, counter returns, and registers receipts.")
    
    h2("Granular Permissions Mapping Matrix")
    p("The table below details the accessibility matrix across primary system components:")
    
    matrix_data = [
        ["Permissions Scope", "Admin", "Manager", "Accountant", "Sales", "Store Staff", "Cashier"],
        ["System Setup / Config", "Full Access", "View Only", "Denied", "Denied", "Denied", "Denied"],
        ["User Mgmt & Audits", "Full Access", "View Only", "Denied", "Denied", "Denied", "Denied"],
        ["Inventory Levels Edit", "Full Access", "Full Access", "View Only", "Denied", "Full Access", "Denied"],
        ["Sales Invoices View", "Full Access", "Full Access", "Full Access", "Full Access", "View Only", "Full Access"],
        ["Sales Invoices Edit/Del", "Full Access", "Approve Only", "Denied", "Denied", "Denied", "Denied"],
        ["General Ledger Postings", "Full Access", "Denied", "Full Access", "Denied", "Denied", "Denied"],
        ["Reports View", "Full Access", "Full Access", "Full Access", "Own Only", "Denied", "Own Only"],
        ["Backup & Restores", "Full Access", "Denied", "Denied", "Denied", "Denied", "Denied"]
    ]
    make_styled_table(matrix_data, [130, 60, 65, 65, 55, 65, 64])
    
    h2("Custom Permissions Setup")
    p("Managers can configure custom overrides. For example, a trusted Sales Associate can be granted temporary permission to override credit limits by inputting a manager's secure OTP or pin code at checkout.")
    page_break()

    # ================= 6. CUSTOMER & SUPPLIER MODULES =================
    h1("6. Customer & Supplier Management")
    p("Managing trade terms, outstanding balances, and risk analysis metrics is central to hardware operations.")
    
    h2("Customer Aging Analysis")
    p("To maintain liquidity, ASTHA ERP dynamically groups unpaid receivables into four aging columns. Aging is calculated relative to the current system date or selected cutoff date:")
    p("• <b>0 to 30 Days:</b> Current bills. Standard trade cycle.")
    p("• <b>31 to 60 Days:</b> Gentle alerts sent via SMS/WhatsApp.")
    p("• <b>61 to 90 Days:</b> Overdue. Requires manual collections follow-up.")
    p("• <b>90+ Days:</b> Delinquent. System alerts manager and blocks new credit sales.")
    s(6)
    
    aging_data = [
        ["Customer Name", "Credit Limit", "0-30 Days", "31-60 Days", "61-90 Days", "90+ Days", "Total Due"],
        ["Astha Builders Ltd", "500,000.00", "120,000.00", "80,000.00", "0.00", "0.00", "200,000.00"],
        ["Sri Balaji Cements", "200,000.00", "45,000.00", "30,000.00", "25,000.00", "0.00", "100,000.00"],
        ["National Projects", "300,000.00", "0.00", "0.00", "50,000.00", "85,000.00", "135,000.00"]
    ]
    make_styled_table(aging_data, [110, 74, 65, 65, 65, 65, 60])

    h2("Credit Limit Enforcement System")
    p("Whenever a sales order or invoice is compiled:")
    p("1. The client queries the customer's ledger to retrieve the current balance:")
    p("   <b>Balance = Sum(Debits) - Sum(Credits)</b>")
    p("2. If the balance exceeds the customer's `credit_limit`, a warning banner is displayed.")
    p("3. If `is_strict_limit` is enabled, the system prevents checkout. The salesperson must select an alternative payment method (Cash, Bank) or request an administrative OTP override.")
    
    h2("Supplier Payments & Balances")
    p("Suppliers use credit accounts. Purchase receipts generate credits (liabilities) on the supplier's ledger, and cash or bank payment vouchers post debits (reducing the liability). Payment schedules are color-coded in the dashboard to ensure payments are made on time.")
    page_break()

    # ================= 7. INVENTORY =================
    h1("7. Inventory & Warehouse Management")
    p("Building materials require detailed stock keeping units (SKUs) and batch management to track physical locations and prevent item spoilage.")
    
    h2("Batch / Lot & Expiry Specifications")
    p("Certain materials, such as cement and chemical paints, have shelf lives. The system handles batches as follows:")
    p("• <b>FIFO Stock Picking:</b> POS checkout screens recommend items from the oldest unexpired batch to ensure inventory moves efficiently.")
    p("• <b>Expiry Notifications:</b> The system monitors batch expiration dates (`expiry_date`) and alerts managers 30 days before expiration, flagging items to be discounted or returned to vendors.")
    
    h2("Multi-Unit Conversions Engine")
    p("Items are often purchased in bulk and sold in retail splits. This is managed through unit conversion factors:")
    p("• <b>Example:</b> Cement is purchased in Boxes (containing 12 bags each) and sold in individual Bags.")
    p("• <b>Formula:</b> <i>Quantity in Sub-Unit = Bulk Quantity * Conversion Factor</i>")
    s(4)
    
    unit_data = [
        ["Item Name", "Purchase Unit", "Sales Unit", "Conversion Factor", "System Quantity on Hand"],
        ["Nippon Paint Emulsion", "Box (4 Tins)", "Tin", "4.00", "12 Boxes (48 Tins)"],
        ["TMT Steel Rods 12mm", "Bundle (10 Pcs)", "Piece", "10.00", "8 Bundles (80 Pieces)"],
        ["General Purpose Nails", "Box (25 kg)", "kg", "25.00", "2 Boxes (50 kg)"]
    ]
    make_styled_table(unit_data, [130, 84, 80, 110, 100])
    
    h2("Warehouse Transfer Protocol (WTP)")
    p("When moving goods between the main warehouse and retail yards:")
    p("1. A <b>Warehouse Transfer Voucher (WTV)</b> is created in a 'Draft' state by the dispatching warehouse, deducting items from its local virtual stock count.")
    p("2. A <b>Transit Registry</b> tracks the items in transit.")
    p("3. The receiving warehouse inspects the delivery and clicks 'Confirm Receipt' on their terminal, adding the verified items to their local stock count and closing the transit record. Discrepancies are logged in an audit report.")
    page_break()

    # ================= 8. SALES =================
    h1("8. Sales, Billing & GST Invoice Engine")
    p("The sales module handles billing, quotations, and returns. POS systems require keyboard-only workflows to keep counter lines moving quickly.")
    
    h2("Standard POS Keyboard Bindings")
    p("The desktop application supports keyboard shortcuts to speed up billing:")
    p("• <b>[F1]:</b> Focus search bar to scan or type item names.")
    p("• <b>[F2]:</b> Edit quantity of the selected line item.")
    p("• <b>[F3]:</b> Apply discount percentage or cash amount to invoice.")
    p("• <b>[F5]:</b> Save invoice to local database, queue for sync, and print.")
    p("• <b>[F8]:</b> Open quick receipt panel for customer credit cash collections.")
    p("• <b>[ESC]:</b> Clear current draft invoice.")
    
    h2("GST Calculation Specifications")
    p("Tax is computed at the line-item level using HSN codes to ensure accuracy during partial returns:")
    p("• <b>Intrastate Sales (Billing Address state == Shipping Address state):</b> CGST and SGST are calculated as 50% of the item's GST rate each.")
    p("• <b>Interstate Sales (Billing Address state != Shipping Address state):</b> IGST is calculated at 100% of the item's GST rate.")
    
    h3("Formulas:")
    p("<i>Taxable Amount = (Quantity * Rate) - Line Discount</i>")
    p("<i>CGST = Taxable Amount * (GST % / 200)</i>")
    p("<i>SGST = Taxable Amount * (GST % / 200)</i>")
    p("<i>IGST = Taxable Amount * (GST % / 100)</i>")
    p("<i>Line Total = Taxable Amount + CGST + SGST + IGST</i>")
    
    h2("Invoice Printing Modes")
    p("Desktop nodes print to two targets:")
    p("1. <b>A4/A5 Laser Prints:</b> Generates professional GST invoices for contractors, detailing tax brackets, bank accounts, and terms.")
    p("2. <b>3-Inch Thermal POS Receipt:</b> Quick receipt format for cash sales, listing items, totals, and a payment QR code.")
    page_break()

    # ================= 9. DOUBLE-ENTRY ACCOUNTING ENGINE =================
    h1("9. Double-Entry Accounting Core")
    p("A strict accounting engine underpins ASTHA ERP. Unlike simple ledgers, every inventory movement or payment must generate balanced journal entries across the Chart of Accounts.")
    
    h2("Chart of Accounts Organization")
    p("Accounts are organized in a nested tree structure. The root groups are: Assets, Liabilities, Equity, Revenues, and Expenses.")
    s(4)
    
    chart_data = [
        ["Account Code", "Account Name", "Root Group", "Standard Balance Type"],
        ["1000", "ASSETS", "Asset Root", "Debit"],
        ["1001", "  State Bank of India A/c", "Current Asset", "Debit"],
        ["1002", "  Cash In Hand", "Current Asset", "Debit"],
        ["1003", "  Trade Receivables (Customers)", "Current Asset", "Debit"],
        ["2000", "LIABILITIES", "Liability Root", "Credit"],
        ["2001", "  Trade Payables (Suppliers)", "Current Liability", "Credit"],
        ["2002", "  Duties & Taxes (GST Output)", "Current Liability", "Credit"],
        ["3000", "REVENUES", "Revenue Root", "Credit"],
        ["3001", "  Hardware Sales Income", "Direct Income", "Credit"],
        ["4000", "EXPENSES", "Expense Root", "Debit"],
        ["4001", "  Purchase Account", "Direct Expense", "Debit"],
        ["4002", "  Freight & Transport Outward", "Direct Expense", "Debit"]
    ]
    make_styled_table(chart_data, [80, 180, 124, 120])
    
    h2("Voucher Processing Rules")
    p("The system enforces the following transaction rules:")
    p("1. <b>Debits equal Credits:</b> No voucher can be saved unless the sum of its debits matches the sum of its credits.")
    p("2. <b>Contra Vouchers:</b> Contra entries are restricted to cash-to-bank deposits or bank-to-cash withdrawals (e.g., Cash In Hand A/c and SBI Bank A/c). Other ledgers are disabled in this view.")
    p("3. <b>Journal Vouchers:</b> General adjustments, depreciation, and bad debts are logged via Journal Vouchers. Cash/Bank accounts are typically excluded from general journals to prevent cash leakage.")
    p("4. <b>Automatic Integration:</b> Creating a Sales Invoice automatically triggers background postings to: Debit Customer A/c, Credit Sales Revenue A/c, and Credit CGST/SGST Liability Accounts.")
    page_break()

    # ================= 10. INTEGRATIONS & UTILITY ENGINES =================
    h1("10. Integrations & Utility Engines")
    p("External integrations automate notifications, labels, and backups, extending the system beyond a simple database application.")
    
    h2("WhatsApp & Email Notification Service")
    p("When a customer invoice or payment receipt is saved:")
    p("1. The backend triggers a worker process that generates a secure, read-only PDF version of the invoice.")
    p("2. The worker sends the document to the customer's phone number using the WhatsApp Business API.")
    p("3. An email is sent simultaneously to the client's inbox with the PDF statement attached.")
    
    h2("Automated Backup Engine")
    p("To prevent data loss, the backup engine uses a dual-destination strategy:")
    p("• <b>Local Node Backups:</b> In desktop mode, a scheduled task creates an encrypted database backup on a local directory (or external USB drive) every hour.")
    p("• <b>Cloud Backups:</b> The cloud database runs daily automated logical backups (`pg_dump`). Backups are encrypted using AES-256 and uploaded to a secure AWS S3 bucket, with a 30-day retention policy.")
    
    h2("Barcode & QR Label Printing Specifications")
    p("Barcode labels for un-scannable inventory items (e.g., loose pipes, custom bricks) are printed using TSC or Zebra printers via direct raw print commands. The system generates Code 128 barcodes along with price details.")
    s(4)
    
    barcode_layout = [
        ["Line", "Content / Command", "Variable Mapped", "Sample Output"],
        ["1", "BARCODE 20,20,\"128\",40,1,0,2,2", "item.barcode_value", "1002049283"],
        ["2", "TEXT 20,70,\"ROMAN.F\",0,1,1", "item.display_name", "OPC 53 Cement - Astha"],
        ["3", "TEXT 20,90,\"ROMAN.F\",0,1,1", "item.sale_price + taxes", "MRP: Rs. 450.00 (Incl. Tax)"]
    ]
    make_styled_table(barcode_layout, [30, 190, 144, 140])
    page_break()

    # ================= 11. QA & IMPLEMENTATION PLAN =================
    h1("11. QA & Implementation Plan")
    p("To build a stable platform, development is split into milestones, starting with core databases and ending with multi-device synchronization testing.")
    
    h2("QA Testing Strategy")
    p("• <b>Unit Tests:</b> Focus on accounting equations, GST calculation methods, unit conversion formulas, and sync queue serialization.")
    p("• <b>Integration Tests:</b> Verify local SQLite write operations and sync queue transfers to the FastAPI server, simulating network drops to ensure data consistency.")
    p("• <b>E2E Tests:</b> Use Playwright to simulate sales checkouts, cashier shifts, and customer payment processing.")
    
    h2("Development Milestones & Roadmap")
    p("The project is planned over an intensive 16-week cycle:")
    s(4)
    
    milestone_data = [
        ["Phase", "Focus Area", "Key Deliverables", "Target Timeline"],
        ["Milestone 1", "Core Infrastructure", "PostgreSQL schema, SQLite migrations, Tauri packaging, User Auth APIs.", "Weeks 1-2"],
        ["Milestone 2", "Sync Engine", "Delta tracking queue, WebSocket state hub, conflict merge models.", "Weeks 3-4"],
        ["Milestone 3", "Inventory Module", "Brands, Categories, Batch/Expiry controls, stock transfers.", "Weeks 5-6"],
        ["Milestone 4", "Sales & GST", "Point of sale (POS) billing interface, thermal prints, tax engines.", "Weeks 7-8"],
        ["Milestone 5", "Accounting", "Chart of accounts, Journal/Contra vouchers, Double entry logic.", "Weeks 9-10"],
        ["Milestone 6", "Reporting Suite", "Trial Balance, Balance Sheet, GST reports, Excel exports.", "Weeks 11-12"],
        ["Milestone 7", "Integrations", "WhatsApp API, ESC/POS barcode prints, S3 backups.", "Weeks 13-14"],
        ["Milestone 8", "QA & Deployment", "Production builds (Windows EXE, Docker web files), security audits.", "Weeks 15-16"]
    ]
    make_styled_table(milestone_data, [80, 110, 214, 100])
    
    h2("System Initialization Guide")
    p("To run the PDF compilation script or start database seeding:")
    p("1. Run `pip install reportlab` to install the PDF generator library.")
    p("2. Run `python generate_spec.py` to compile the PDF specification document.")
    p("3. The compiled document will be saved in the project root directory as: `ASTHA_ERP_Master_Specification.pdf`.")
    
    # Render PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF generated successfully.")

if __name__ == "__main__":
    build_pdf()
