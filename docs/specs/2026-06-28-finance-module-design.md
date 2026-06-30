# Finance Module (KKTIG → Web) — Design & Roadmap

**Date:** 2026-06-28
**Author:** Brainstorming session (user + assistant)
**Status:** Draft — pending approval
**Source project:** [myazdanpanah/KKTIG](https://github.com/myazdanpanah/KKTIG) (Python desktop, CustomTkinter + SQL Server)

---

## 1. Executive Summary

This document specifies the conversion of **KKTIG** — a Python desktop financial tool for
issuing invoices, registering payments, and tracking debts/credits — into a **web module
inside the Nexivo platform** (Django + React).

Two goals shape the design:

1. **Generalize** the software so it serves **any type of company** (travel, retail,
   consulting, manufacturing, …), not just the original travel agency.
2. **Integrate with Nexivo** so all financial data flows into Nexivo's existing
   dashboards and charts for reporting.

After login, every user sees a **workspace launcher** offering two modules:

- **Nexivo** — analytics, dashboards, BI (existing)
- **Finance** — invoicing, payments, debts, approvals, document generation (new)

The launcher is **always shown**; no auto-redirect.

---

## 2. Background — What KKTIG Is Today

KKTIG is a mature desktop application (≈6,000 LOC) composed of four parts:

| File | Role | Lines |
|------|------|------:|
| `Invoice_app.py` | Main CustomTkinter GUI: login, data entry, approvals, payments, debt/credit tracking | 5,930 |
| `reportbro_service.py` | Flask microservice — ReportBro **template designer** + PDF renderer (port 5001) | 254 |
| `final_file_service.py` | Flask microservice — generates final invoice PDFs from approval requests (port 5000) | 615 |
| `service_monitor.py` | System-tray monitor for the file service | 343 |

**Current stack:** Python, CustomTkinter, SQL Server (pyodbc), pandas/openpyxl,
jdatetime (Jalali calendar), DocxTemplate, ReportBro, Flask.

### 2.1 Current data model (SQL Server, 11 tables)

- `users` — 14 granular boolean permission flags (can_view, can_pay, can_issue,
  can_approve, can_edit_template, …)
- `payers` — customers with `parent_code` hierarchy (B2B subsidiaries) and
  `customer_type` (legal/natural), national/economic IDs
- `invoices` — letter_number, payer, type, amount, issue_date, file_path
- `payments` — payment_code, payer, date, amount, tracking_number, description
- `manual_debts` — payer, description, amount, date, notes
- `credits` — payer, amount, credit_date, description, invoice_number
- `letter_sequences` / `available_letter_numbers` — atomic per-payer/year letter numbering
- `approval_requests` — submit → approve/reject workflow, with service/flight/hotel JSON payloads
- `final_files` — generated PDFs (VARBINARY blob or path), linked to approval requests
- `service_categories` — hierarchical service types (parent_id), seeded with
  Visa/Bus/Train/Tour/Package/CIP
- `company_settings` — single-row tenant settings (bank accounts, logo, signature, stamp, manager)

### 2.2 Domain behaviors that must be preserved

- **Dual accounting model** — invoice-centric (document generation) **and** account-centric
  (running balance per customer). Formula: `مانده = بدهکار − بستانکار`.
- **Atomic letter numbering** — `YYYY/CODE/NNNNN` per payer + year, with number
  reservation/release for the approval workflow (prevents duplicate numbers).
- **Approval workflow** — request (submit) → pending → approve/reject → final file
  generation. Reserved numbers are released on rejection.
- **Document generation** — three document kinds:
  - Invoice (صورتحساب) — line items table + seller/buyer boxes
  - Payment notice letter (صورتحساب/اطلاعیه واریز)
  - Creditor notice letter (بستانکاری)
  - Engines: DocxTemplate (Word letters) + ReportBro (PDF) + HTML/CSS (invoice preview)
- **Excel import** — multi-file, auto-detects type by columns (هتل→hotel, مسیر→flight,
  else service), Persian/English digit normalization, Jalali date parsing.
- **Jalali calendar + Persian digits** everywhere in the UI and documents.
- **Currency:** IRR (ریال). No tax calculation (tax embedded in uploaded data).
- **14 permissions** controlling every action.

### 2.3 Multi-tenancy in the desktop app

Today the app is **single-tenant** (one SQL Server DB, one `company_settings` row).
The web version must become **multi-tenant SaaS** — many companies, isolated data.

---

## 3. Goals & Non-Goals

### Goals

1. Reproduce 100% of KKTIG's financial workflow in the browser.
2. Support **any industry**, configured per tenant — not hardcoded to travel.
3. Multi-tenant SaaS: each company isolated, with its own users, payers, invoices, settings.
4. Feed all financial data into Nexivo dashboards/charts automatically.
5. Preserve the working ReportBro PDF/Word document pipeline (lowest-risk path).
6. Post-login **module launcher** (Nexivo | Finance), always shown.

### Non-Goals (out of scope for v1)

- Real-time payment gateway integration / online checkout.
- Double-entry general ledger / formal accounting statements (balance sheet, P&L).
  The module is **receivables-focused** (who owes what); formal bookkeeping is a future phase.
- Multi-currency (IRR only for v1; FX support deferred).
- Tax calculation engine (tax lives inside imported data; not computed).
- Mobile-native apps (web is responsive; no iOS/Android builds).

---

## 4. Architecture

### 4.1 Approach chosen — A: Migrate into Nexivo

Finance is built as **new Django apps inside the existing Nexivo project**. Nexivo's
accounts RBAC, datasets (Excel) pipeline, and dashboards are reused; ReportBro keeps
running as a Flask microservice that Django proxies to.

**Rationale (vs. standalone project / pure Flask wrap):**

- The stated goal — "mix with Nexivo for reports and charts" — is **free** under this
  approach because Finance models live in the same DB as dashboards.
- Multi-tenancy is achieved by extending Nexivo's `Company` model rather than building
  a parallel tenant system.
- The ReportBro pipeline stays untouched (it already speaks HTTP), so the riskiest
  part (PDF generation) is de-risked.

### 4.2 Component map

```
┌──────────────────────────────────────────────────────────────────┐
│                         React Frontend                            │
│  LauncherPage ──┬──▶ modules/nexivo/   (analytics, dashboards)   │
│                 └──▶ modules/finance/  (invoicing, payments, …)  │
└───────────────┬──────────────────────────────┬───────────────────┘
                │ REST/JSON (JWT)                │ PDF proxy + template mgmt
┌───────────────▼────────────────┐  ┌───────────▼──────────────────┐
│        Django Backend           │  │  ReportBro Service (Flask)    │
│  apps/accounts  (auth, tenants, │  │  /designer  /save-template    │
│                 module access)  │  │  /render    /load-template    │
│  apps/invoices (core finance)   │  │  port 5001 (kept as-is)       │
│  apps/templates (PDF mgmt+proxy)│  └───────────────────────────────┘
│  apps/datasets (Excel import)   │
│  apps/dashboards (charts)       │  ┌───────────────────────────────┐
│  Celery worker (PDF gen async)  │──▶│  PostgreSQL                   │
└─────────────────────────────────┘  │  Redis (Celery broker)        │
                                     └───────────────────────────────┘
```

### 4.3 Two modes of the ReportBro service

- **Designer mode** — only the `can_edit_template` permission (admin) opens the
  `/designer` route inside an iframe; everyone else uses ready-made templates.
- **Render mode** — Django's `templates` app calls `POST /render` to produce PDFs,
  either synchronously (small) or via Celery (batch/large). ReportBro remains a
  local Flask service for now; "later we connect it to IPs" means the Django
  setting `REPORTBRO_BASE_URL` simply changes from `http://127.0.0.1:5001` to the
  remote IP.

### 4.4 Industry generalization (the key design decision)

The customer confirmed: **industry-specific fields must live in proper relational
tables, not JSON blobs.** We use a configurable **field-definition + field-value**
pattern so new industries are added by *configuring tables*, never by altering schema:

```
ItemType (per tenant: Flight, Hotel, Service, SKU, Consulting Hour, …)
   └─ ItemTypeField (the schema: "route", "hotel_name", "qty", …)
          └─ ItemFieldValue (the actual data on each line item)
```

Every line item carries the **universal financial core** (ref, customer, debt,
credit, balance) as real columns; industry detail lives in the field-value tables.
This gives the flexibility of JSON with queryable, typed, indexable storage.

---

## 5. Data Model

All Finance models are **tenant-scoped** via `company = FK(Company)` and every query
filters on the requesting user's company. Nexivo's existing `Company`, `Division`,
`Team`, `User`, `CustomRole` are reused and extended.

### 5.1 New fields on existing models

**`accounts.User`** — add Finance access flags. Two strategies, **permission flags**
chosen to mirror KKTIG's proven model:

| Field | Type | Maps from KKTIG |
|-------|------|-----------------|
| `finance_access` | Boolean | can_view (gate to module) |
| `can_view_finance` | Boolean | can_view |
| `can_pay` | Boolean | can_pay |
| `can_issue` | Boolean | can_issue |
| `can_manage_payers` | Boolean | can_manage_companies |
| `can_delete_history` | Boolean | can_delete_history |
| `can_delete_payment` | Boolean | can_delete_payment |
| `can_export` | Boolean | can_export |
| `can_submit` | Boolean | can_submit |
| `can_approve` | Boolean | can_approve |
| `can_edit_template` | Boolean | can_edit_template |
| `can_manage_settings` | Boolean | can_manage_settings |
| `nexivo_access` | Boolean | new — gate to Nexivo module |
| `last_module` | CharField | new — remembers last chosen launcher module |

A `ModuleAccess` helper computes `{nexivo, finance}` availability from these flags.

### 5.2 `apps/invoices` models (new)

> Table names in brackets are the KKTIG origin.

#### `Payer` [payers] — customers, tenant-scoped, hierarchical
```
company        FK(Company)            -- tenant
code           CharField(10)          -- short code, unique per tenant
parent         FK(self, null)         -- B2B subsidiary hierarchy
name           CharField(255)
customer_type  CharField (legal|natural)
national_id, economic_code, registration_number
address, postal_code, phone, mobile, email
is_active, created_at, updated_at
unique_together: (company, code)
```
`@property balance` = Σ(invoices.amount open) + Σ(manual_debts) − Σ(payments) − Σ(credits)

#### `ItemType` [service_categories] — per-tenant line-item types
```
company        FK(Company)
parent         FK(self, null)         -- nested categories
name           CharField(100)         -- "پرواز", "هتل", "خدمات", "SKU", …
code           CharField(20)          -- VISA, BUS, FLIGHT, RETAIL, …
is_active, display_order
unique_together: (company, code)
```

#### `ItemTypeField` — the per-type schema (drives forms, tables, imports)
```
item_type      FK(ItemType, related=fields)
key            CharField(40)          -- "route", "hotel_name", "qty"
label          CharField(100)         -- Persian display label
field_type     CharField (text|number|date|select)
options        JSONField(default=list) -- for select fields
required       Boolean
display_order  Integer
unique_together: (item_type, key)
```

#### `ItemFieldValue` — the actual data (real rows, not JSON)
```
line_item      FK(LineItem, related=values)
field          FK(ItemTypeField)
value_text     TextField(blank)
value_number   BigIntegerField(null)
value_date     DateField(null)
```
Value is stored in the typed column matching `field.field_type`.

#### `Invoice` [invoices] — a statement/bill, tenant-scoped
```
company        FK(Company)
letter_number  CharField(50)          -- "1404/10012/00042"
payer          FK(Payer)
invoice_type   FK(ItemType)           -- which service kind
issue_date     DateField              -- Gregorian; rendered as Jalali
period_range   CharField              -- "۱ تا ۱۵ خرداد ۱۴۰۴"
status         CharField (draft|submitted|approved|rejected)
amount         BigIntegerField        -- computed total (IRR)
created_by     FK(User)
file_path      FileField(null)        -- generated PDF
created_at, updated_at
unique_together: (company, letter_number)
```

#### `LineItem` — one row of an invoice (the financial core + type)
```
invoice        FK(Invoice, related=items)
item_type      FK(ItemType)
ref            CharField              -- contract/agreement number
customer_name  CharField              -- passenger / buyer name
description    CharField              -- service/route/SKU description
date           CharField              -- Jalali string from source data
notes          CharField
debt           BigIntegerField        -- بدهکار (IRR)
credit         BigIntegerField        -- بستانکار (IRR)
balance        BigIntegerField        -- debt - credit (computed)
order          Integer
# industry detail → ItemFieldValue rows (query via .values)
```

#### `Payment` [payments]
```
company, payer  (FK)
payment_code    CharField
payment_date    DateField
amount          BigIntegerField
tracking_number CharField
description     TextField
registered_by   FK(User)
created_at
```

#### `ManualDebt` [manual_debts]
```
company, payer  (FK)
description, amount, date, notes, created_at
```

#### `Credit` [credits]
```
company, payer  (FK)
amount, credit_date, description, invoice_number, created_at
```

#### `ApprovalRequest` [approval_requests]
```
company        FK(Company)
requester      FK(User)
payer          FK(Payer)
letter_number  CharField
letter_date    CharField
period_range   CharField
item_payload   (denormalized snapshot for review)
status         CharField (pending|approved|rejected)
reserved_numbers JSONField
final_letter_number CharField(null)
approved_by, approved_at, rejection_reason
created_at
```

#### `GeneratedFile` [final_files] — the produced PDF/Word artifacts
```
approval_request FK(ApprovalRequest, related=files)
letter_number, file_type (invoice|notice|creditor)
file          FileField              -- stored in media/
file_name, created_at, last_accessed, is_deleted_from_disk
```

#### `LetterSequence` [letter_sequences + available_letter_numbers]
```
company, payer, year_2digit
last_number     Integer
# reservation logic in a manager/model method, transaction-locked
```

### 5.3 `apps/templates` models (new)

```
ReportTemplate
  company       FK(Company)
  name          CharField             -- "قالب صورتحساب پرواز"
  doc_kind      CharField (invoice|notice|creditor)
  item_type     FK(ItemType, null)    -- optional per-type template
  template_json JSONField             -- ReportBro definition (.rpt)
  is_default    Boolean
  version, updated_by, created_at, updated_at
```
This replaces the filesystem `.rpt` files in `reportbro_service` with a queryable,
tenant-scoped, versioned table. The ReportBro service's `/save-template` &
`/load-template` routes become thin proxies that read/write this table via Django.

### 5.4 Reused Nexivo models

- `Company`, `Division`, `Team`, `User`, `CustomRole` (accounts) — extended as above.
- `Dataset` (datasets) — Excel uploads; a **new dataset source type** `finance_import`
  is added so imports can be tracked and re-played.
- `Dashboard`, `Widget`, `DashboardAssignment` (dashboards) — unchanged; Finance adds
  **virtual datasets** that the widget query engine can read (see §7).

---

## 6. Post-Login Workspace Launcher

After successful authentication the user lands on **`LauncherPage`**, always. It is not
skipped even if the user has access to only one module (consistent UX, future-proofs
adding modules).

```
┌─────────────────────────────────────────────────────────┐
│   خوش آمدید، <name>          [ Nexivo | Finance | ⚙ ]   │
│   ماژول مورد نظر را انتخاب کنید                          │
│                                                         │
│   ┌──────────────┐         ┌──────────────────┐         │
│   │   📊 Nexivo   │         │  💰 Finance       │         │
│   │   داشبوردها   │         │   صورت‌حساب‌ها    │         │
│   │   و گزارش‌ها   │         │   پرداخت‌ها       │         │
│   │               │         │   بدهی‌ها          │         │
│   └──────────────┘         └──────────────────┘         │
│                                                         │
│   آخرین ماژول: Finance          [ ادامه → ]              │
└─────────────────────────────────────────────────────────┘
```

- Tiles enabled/disabled by `nexivo_access` / `finance_access`.
- "آخرین ماژول" (last module) pre-highlighted, one-click resume via the **ادامه** button.
- A persistent sidebar/topbar toggle lets users switch modules without returning to the
  launcher.
- Selecting a tile sets `user.last_module` and routes to that module's home.

**Routing:**
- `/` → `LauncherPage`
- `/nexivo/*` → existing analytics pages
- `/finance/*` → new Finance pages (FinanceApp shell with its own sidebar)

---

## 7. Finance Module UI (React)

A dedicated `modules/finance/` shell mirrors the desktop tab structure:

| Page | KKTIG origin | Purpose |
|------|--------------|---------|
| `Dashboard` | — | KPIs: total receivable, overdue, monthly collection, top debtors |
| `Payers` | ManagePayersDialog | CRUD customers + hierarchy tree + per-payer balance |
| `New Invoice` | App.create_*_tab | Build invoice from Excel import **or** manual entry; live preview |
| `Invoices` | history tab | List, filter (payer/date/status), regenerate PDF, delete |
| `Payments` | AddPaymentDialog / CompanyTransactions | Register payments, per-payer ledger, running balance |
| `Debts & Credits` | manual_debts / credits | Manual adjustments to a payer's account |
| `Approvals` | workflow tab | Submit → pending → approve/reject; reserved-number handling |
| `Generated Files` | final_files | Browse/download produced PDFs & Word letters |
| `Template Designer` | reportbro /designer | ReportBro designer in iframe (admin only) |
| `Settings` | SettingsDialog | Company info, bank accounts, logo/signature/stamp, item types, letter-number format, services |

### 7.1 Excel import (multi-file, per-service)

Reuses Nexivo's `datasets` pipeline with a Finance-specific importer:

1. User uploads **one or more** Excel files, tagging each with an item type (flight/hotel/service/…).
2. Backend auto-detects type by columns (هتل→hotel, مسیر→flight, else service) — same
   heuristics as `detect_file_type()` in KKTIG — but type is also user-overridable.
3. Persian→English digit normalization + Jalali→Gregorian date parsing run server-side
   (port of the helper functions in KKTIG).
4. Each row becomes a `LineItem` + its `ItemFieldValue` rows; rows grouped into an `Invoice`.
5. Import is transactional; a `Dataset` record tracks it for audit/re-play.

### 7.2 Documents & PDF generation

- **Templates** are stored as `ReportTemplate.template_json` (ReportBro `.rpt` format),
  one default per `doc_kind`, optionally specialized per `ItemType`.
- Generating a document: Django builds the data payload (seller/buyer boxes, paginated
  line items, totals, signature/stamp) and `POST /render` to ReportBro → returns PDF bytes
  → stored as `GeneratedFile.file` and streamed to the browser.
- The three KKTIG HTML/CSS templates (invoice, notice, creditor) and the Word templates
  (`template.docx`, `template_creditor.docx`, `template - subdevision.docx`) are ported as
  default `ReportTemplate` rows seeded via a data migration.
- Celery handles batch generation (e.g., regenerate all invoices for a payer in a period).

---

## 8. Nexivo Integration (Reports & Charts)

All four requested reports become **pre-built dashboards** over Finance models:

| Report | Source | Suggested chart |
|--------|--------|-----------------|
| Revenue by service type | `LineItem` grouped by `item_type` | donut + bar |
| Customer debt aging | `Payer.balance` bucketed by invoice age | stacked bar by age band |
| Monthly/weekly sales trends | `Invoice.amount` over time | line + area |
| Top customers by volume/revenue | aggregate per `Payer` | leader_kpi / bar |
| *(bonus)* Cash flow | payments in vs outstanding | dual-axis line |

**Mechanism:** the dashboards app gains a **virtual finance dataset** — widgets can query
Finance models through the existing `query_config` engine without needing an uploaded
`Dataset` row. This avoids duplicating financial data into the BI tables. Tenant scoping is
inherited from the user's `company`.

---

## 9. Multi-Tenancy & Permissions

- **Tenant isolation** — every Finance model has `company = FK(Company)`; a queryset
  manager enforces `company = request.user.company` automatically (no cross-tenant leaks).
- **Module access** — `nexivo_access` / `finance_access` gates the launcher tiles and routes.
- **Permissions** — the 14 KKTIG flags become per-user booleans (§5.1). They are enforced
  via a small permission decorator/DRF permission class:
  ```python
  @finance_permission("can_issue")
  class InvoiceCreateView(...)
  ```
- **Roles** — Nexivo's `CustomRole` can bundle permission sets; an admin role maps to
  all-flags-true, an agent role to `can_view + can_issue + can_submit`, etc.

---

## 10. Security & Compliance

- JWT auth (existing in Nexivo); all Finance endpoints require a valid company-scoped token.
- File uploads validated (type, size); generated PDFs stored under `media/` with
  tenant-partitioned paths.
- Atomic letter numbering under DB transaction + row lock (ports KKTIG's
  `reserve/release` logic) to prevent duplicate numbers under concurrency.
- Audit log for sensitive actions (approve/reject, delete payment/history) — extends
  Nexivo's existing `PermissionAuditLog` pattern.
- Persian-digit / Jalali helpers centralized in a shared `apps/invoices/utils.py` so every
  layer (model, API, document) formats consistently.

- **Note on secrets in the current repo:** `db_config.json` in KKTIG contains hardcoded SQL
  Server credentials. These must **not** be carried over; the web version uses Django
  settings + environment variables (already Nexivo's pattern via `python-decouple`).

---

## 11. Migration of Existing Services

| KKTIG component | Web destination | Strategy |
|-----------------|-----------------|----------|
| `SQLServerDatabase` (pyodbc) | Django ORM (`apps/invoices`) | Rewrite; data migrated via a one-off script |
| `Invoice_app.py` (CustomTkinter) | React (`modules/finance/`) | Rewrite UI; reuse business logic as Django services |
| `reportbro_service.py` (Flask) | **Kept as-is**, proxied by `apps/templates` | Lowest risk; later pointed at a remote IP |
| `final_file_service.py` (Flask) | Folded into `apps/templates` + Celery | Its logic merges into Django services |
| `service_monitor.py` (tray) | Celery + admin UI status panel | Replaced by background workers |
| `.docx` letter templates | `ReportTemplate` seed data | Ported to ReportBro JSON via data migration |
| SQL Server data | PostgreSQL | ETL script (pyodbc → Django ORM `bulk_create`) |

### 11.1 Data migration approach

A management command `migrate_kktig_data` reads the old SQL Server DB through pyodbc,
maps rows to the new ORM models (resolving tenants → `Company`), and bulk-inserts into
PostgreSQL. Run once per tenant. Idempotent via `letter_number` uniqueness.

---

## 12. Roadmap

Phased delivery. Each phase is independently shippable and ends with a demo.

### Phase 0 — Foundation (week 1)
- [ ] Extend `accounts.User` with module-access + Finance permission flags (migration)
- [ ] Add `nexivo_access` / `finance_access` and `ModuleAccess` helper
- [ ] Build `LauncherPage` (always-shown workspace switcher) + routing (`/`, `/finance/*`)
- [ ] Persian/Jalali helpers in `apps/invoices/utils.py`
- [ ] Tenant-scoping queryset manager (base mixin)
- [ ] **Demo:** login → launcher → toggle between empty Nexivo & Finance shells

### Phase 1 — Core Finance models & payers (week 2)
- [ ] `apps/invoices`: Payer, ItemType, ItemTypeField, ItemFieldValue, LineItem, Invoice
- [ ] Payer CRUD API + hierarchy tree UI (B2B subsidiaries)
- [ ] Per-payer running balance property + endpoint
- [ ] Item-type configuration UI (define fields per type → drives forms later)
- [ ] **Demo:** manage customers, define a custom item type with fields, see balance

### Phase 2 — Invoice creation & Excel import (weeks 3–4)
- [ ] New Invoice page (manual entry + live preview)
- [ ] Multi-file Excel importer (port `detect_file_type` + digit/date helpers)
- [ ] Atomic letter-number sequence (transaction-locked reserve/release)
- [ ] Invoice list/filter/regenerate
- [ ] **Demo:** import a real KKTIG multi-file Excel set → produces invoices with letter numbers

### Phase 3 — Payments, debts, credits, approvals (weeks 5–6)
- [ ] Payment registration + per-payer ledger + running balance updates
- [ ] Manual debts & credits
- [ ] Approval workflow (submit → approve/reject, reserved-number release)
- [ ] 14 permissions enforced on every endpoint
- [ ] **Demo:** full invoice lifecycle end-to-end with role-based access

### Phase 4 — Document generation (week 7)
- [ ] Stand up ReportBro Flask service; `REPORTBRO_BASE_URL` configurable
- [ ] `apps/templates`: ReportTemplate model + seed defaults (invoice/notice/creditor)
- [ ] PDF generation via Celery; GeneratedFile storage
- [ ] Template Designer iframe (admin / `can_edit_template` only)
- [ ] **Demo:** generate & download invoice + payment-notice PDFs; edit a template live

### Phase 5 — Nexivo dashboards integration (week 8)
- [ ] Virtual finance dataset for the widget query engine
- [ ] Pre-built dashboards: revenue by type, aging, trends, top customers, cash flow
- [ ] Row-level tenant scoping on every chart
- [ ] **Demo:** one-click view of financial KPIs & charts inside Nexivo

### Phase 6 — Multi-tenant & data migration (week 9)
- [ ] Full tenant isolation verification (cross-company access tests)
- [ ] `migrate_kktig_data` command (SQL Server → PostgreSQL)
- [ ] Onboarding flow for a new tenant (create Company → seed item types → settings)
- [ ] **Demo:** run two isolated tenants side by side; migrate a real KKTIG dataset

### Phase 7 — Hardening & polish (week 10)
- [ ] Audit logging for approve/reject/delete actions
- [ ] Responsive layout; dark theme consistency (matches Nexivo)
- [ ] Error handling, loading states, empty states
- [ ] Performance: indexes on (company, payer, issue_date), pagination
- [ ] Docs: API (drf-spectacular), admin guide, user guide (FA)
- [ ] **Demo:** production-ready v1

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ReportBro service stability under load | Med | High | Celery queue + retries; keep service replaceable; PDF proxy isolates it |
| Letter-number race conditions | Med | High | DB transaction + row-level lock; port KKTIG's proven reserve/release |
| Excel format drift across tenants | Med | Med | Auto-detect + user override; import preview + dry-run validation |
| Generalization breaks travel-specific UX | Low | Med | Travel config shipped as a preset; fields fully configurable per tenant |
| Migration of live SQL Server data | Med | High | Idempotent command; run on a copy first; uniqueness guards |
| 14 permissions complexity | Low | Med | Permission decorator + role bundles; comprehensive tests |

---

## 14. Open Questions (to resolve before/during implementation)

1. **Onboarding new tenants** — self-service signup, or admin-provisioned only? (Default: admin-provisioned for v1.)
2. **Backup/restore** — KKTIG had DB backup/restore in-app. Carry over a per-tenant export/import, or rely on PostgreSQL backups? (Default: rely on PG backups for v1.)
3. **Template sharing** — should default templates be editable per tenant, or locked to platform defaults? (Default: editable per tenant, seeded from defaults.)
4. **Approval rules** — single approver (current) or multi-step? (Default: single approver for v1.)
5. **Numbering format** — keep `YYYY/CODE/NNNNN` hardcoded, or make the format a per-tenant setting? (Default: per-tenant setting seeded to the KKTIG format.)

---

## 15. Appendix — Glossary

| Term | Meaning |
|------|---------|
| بدهکار (Debt) | Amount the customer owes (debit) |
| بستانکار (Credit) | Amount paid / credited |
| مانده (Balance) | بدهکار − بستانکار (running balance) |
| Payer | A customer (B2B or B2C) |
| Letter number | Atomic invoice/statement ID: `YYYY/CODE/NNNNN` |
| ItemType | A category of line item (flight, hotel, SKU, …) — configurable per tenant |
| Tenant | A `Company` with isolated Finance + Nexivo data |
| ReportBro | Open-source report/PDF designer used by KKTIG |
