# Nexivo — Project Progress

**Last updated:** July 19, 2026  
**Current version:** v0.5.0

---

## 🎯 Architecture Overview

Nexivo is an **organizational SaaS platform** with pluggable modules. Each company (tenant) enables/disables modules, and each user gets role-based access to the enabled ones.

```
┌──────────────────────────────────────────────────────────────┐
│                     Nexivo Platform                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ BI       │ Finance  │ Mfg      │ DB       │ Data     │ LLM      │
│ Dashboard│ Module   │ Module   │ Manager  │ Upload   │ Gateway  │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────┤
│              Module Management System                           │
│  Company.enabled_modules → User.accessible_modules              │
└──────────────────────────────────────────────────────────────┘
```

### Available Modules

| Module ID | Label | Status |
|-----------|-------|--------|
| `bi_dashboard` | BI Dashboard | ✅ Active |
| `finance` | Finance | ✅ Active |
| `manufacturing` | Manufacturing | ✅ Active |
| `crm` | CRM | 🔲 Ready (future) |
| `db_manager` | Database Manager | ✅ Active |
| `datasets` | Data Upload | ✅ Active |
| `llm` | LLM Gateway | ✅ Active |
| `settings` | Settings | ✅ Active |

---

## 🏗️ Enterprise Architecture (v0.5.0)

### Core App (`backend/apps/core/`)

| Component | Purpose |
|-----------|---------|
| `SoftDeleteMixin` | Business documents are never physically deleted |
| `AuditFieldsMixin` | Every entity tracks created_by, updated_by, timestamps |
| `CompanyIsolationMixin` | Multi-company data isolation |
| `BaseModel` | Combines all mixins for business entities |
| `responses.py` | Standard API responses: success_response, error_response, business_rule_error, not_found_response, forbidden_response |

### Finance Module Enterprise Layer

| Layer | Files | Purpose |
|-------|-------|---------|
| **Views** | `views.py` | All endpoints use standard API response format per API_SPECIFICATION.md §6-§8 |
| **Services** | `services.py` | 6 service classes: FiscalYearService, JournalService, InvoiceService, ReceiptService, PaymentService, ChequeService |
| **Selectors** | `selectors.py` | 6 selector classes for read-only queries |
| **Validators** | `validators.py` | 4 validator classes: InvoiceValidator, ReceiptValidator, PaymentValidator, JournalValidator |
| **Exceptions** | `exceptions.py` | Shared ValidationError for business rules |
| **Posting Engine** | `posting.py` | Accounting Posting Engine (auto journal entries) + LedgerService (trial balance, account balance) |
| **Workflow Engine** | `workflow.py` | State machine for document lifecycle (draft → confirmed → posted) |
| **Tax Engine** | `tax.py` | VAT calculation, withholding tax, VAT summary per TAX_AND_LEGAL_RULES_IRAN.md |

### Accounting Posting Engine

Automatically creates journal vouchers when documents are confirmed:

| Document | Debit | Credit |
|----------|-------|--------|
| Sales Invoice | Customer Receivable (131) | Sales Revenue (401) + VAT Payable (231) |
| Purchase Invoice | Purchase Expense (501) | Supplier Payable (201) + VAT Receivable (133) |
| Receipt | Bank (102) | Customer Receivable (131) |
| Payment | Supplier Payable (201) | Bank (102) |

### Tax Engine

Per TAX_AND_LEGAL_RULES_IRAN.md:

| Component | Purpose |
|-----------|---------|
| `TaxCategory` | Tax behavior: TAXABLE, EXEMPT, ZERO_RATE |
| `TaxCode` | Tax rates: VAT_NORMAL (10%), VAT_EXEMPT (0%) |
| `TaxRule` | Business rules: IF sales_invoice + TAXABLE THEN apply VAT |
| `TaxTransaction` | Immutable audit trail of every tax calculation |
| `TaxEngine` | Service: calculate_vat, calculate_withholding_tax, get_vat_summary |

---

## 🏭 Manufacturing Module (v0.5.0)

Per MANUFACTURING_MODULE.md §4-§14:

### Models

| Model | Description |
|-------|-------------|
| `BOM` | Bill of Material header (versioned, approval workflow) |
| `BOMLine` | BOM components with quantity, cost, consumption type |
| `Routing` | Production operation sequence |
| `RoutingOperation` | Individual operation with work center, time, quality check |
| `WorkCenter` | Production resource (machine, line, department, vendor) |
| `ProductionOrder` | Main manufacturing transaction (draft→approved→started→completed) |
| `MaterialConsumption` | Material issued to production |
| `FinishedGoodsReceipt` | Finished products received from production |

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET/POST` | `/api/v1/manufacturing/boms/` | List or create BOMs |
| `GET/PUT/DELETE` | `/api/v1/manufacturing/boms/{id}/` | BOM CRUD |
| `POST` | `/api/v1/manufacturing/boms/{id}/approve/` | Approve BOM |
| `GET/POST` | `/api/v1/manufacturing/routings/` | List or create routings |
| `GET/POST` | `/api/v1/manufacturing/work-centers/` | List or create work centers |
| `GET/POST` | `/api/v1/manufacturing/production-orders/` | List or create production orders |
| `POST` | `/api/v1/manufacturing/production-orders/{id}/approve/` | Approve PO |
| `POST` | `/api/v1/manufacturing/production-orders/{id}/start/` | Start production |
| `POST` | `/api/v1/manufacturing/production-orders/{id}/complete/` | Complete production |
| `GET/POST` | `/api/v1/manufacturing/material-consumptions/` | Record material consumption |
| `GET/POST` | `/api/v1/manufacturing/finished-goods-receipts/` | Record finished goods |
| `GET` | `/api/v1/manufacturing/summary/` | Manufacturing dashboard |

---

## 🧪 Test Infrastructure

### Test Coverage Summary

| Module | Tests | Status |
|--------|-------|--------|
| `accounts` | 14 | ✅ All pass |
| `dashboards` | (via CI) | ✅ |
| `datasets` | ~50 | ✅ All pass |
| `db_manager` | ~30 | ✅ All pass |
| `finance` | 61 | ✅ All pass |
| `manufacturing` | 18 | ✅ All pass |
| `llm` | ~20 | ✅ All pass |
| **Total** | **~193** | ✅ **All pass** |

### Finance Test Breakdown

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests.py` | 23 | CRUD, module gates, invoice confirm, voucher balancing, search, summary |
| `tests_posting.py` | 18 | PostingEngine, LedgerService, WorkflowEngine, integration tests |
| `tests_tax.py` | 20 | TaxEngine VAT, withholding, summary, rule matching, fiscal year validation |

---

## 📁 Project Structure (Updated)

```
Nexivo/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # Auth, users, org hierarchy, module management
│   │   ├── core/              # Enterprise base: mixins, responses, permissions
│   │   │   ├── models.py      # SoftDeleteMixin, AuditFieldsMixin, BaseModel
│   │   │   └── responses.py   # Standard API response functions
│   │   ├── dashboards/        # BI Dashboard module
│   │   ├── datasets/          # Data upload & query module
│   │   ├── db_manager/        # Database management module
│   │   ├── finance/           # Finance module (Iranian accounting + enterprise)
│   │   │   ├── models.py      # All finance + tax models
│   │   │   ├── services.py    # 6 service classes
│   │   │   ├── selectors.py   # 6 selector classes
│   │   │   ├── validators.py  # 4 validator classes
│   │   │   ├── exceptions.py  # Shared ValidationError
│   │   │   ├── posting.py     # Accounting Posting Engine + LedgerService
│   │   │   ├── workflow.py    # Workflow Engine state machine
│   │   │   ├── tax.py         # Tax Engine (VAT, withholding)
│   │   │   ├── views.py       # Standard API responses throughout
│   │   │   ├── tests.py       # 23 tests
│   │   │   ├── tests_posting.py # 18 tests
│   │   │   └── tests_tax.py   # 20 tests
│   │   ├── manufacturing/     # Manufacturing module
│   │   │   ├── models.py      # BOM, Routing, WorkCenter, ProductionOrder
│   │   │   ├── serializers.py # Full CRUD serializers
│   │   │   ├── views.py       # CRUD + workflow actions
│   │   │   ├── admin.py       # Django admin registration
│   │   │   ├── tests.py       # 18 tests
│   │   │   └── urls.py        # 16 URL patterns
│   │   └── llm/               # LLM Gateway module
│   └── nexivo/
│       ├── settings.py
│       └── urls.py
├── frontend/
│   └── src/
│       ├── pages/finance/     # 10-page RTL finance UI
│       └── api/               # Finance + LLM API clients
└── docs/
    └── Financial/             # 15 enterprise architecture spec files
```

---

## 📝 Recent Changes (July 19, 2026)

### v0.5.0 — Enterprise Architecture & Manufacturing Module

**Finance Enterprise Upgrade:**
- Created `core/` app with SoftDeleteMixin, AuditFieldsMixin, CompanyIsolationMixin, BaseModel
- Added standard API response functions (success_response, error_response, business_rule_error, etc.)
- Built service layer (6 classes), selector layer (6 classes), validator layer (4 classes)
- Built Accounting Posting Engine — auto journal entries from invoice/receipt/payment confirmation
- Built Workflow Engine — state machine for document lifecycle
- Built Tax Engine — VAT calculation, withholding tax, VAT summary per TAX_AND_LEGAL_RULES_IRAN.md
- Moved TaxCategory/TaxCode/TaxRule/TaxTransaction into models.py to eliminate circular import
- Added fiscal_year None validation with auto-lookup
- All 61 finance tests passing

**Manufacturing Module Foundation:**
- Created 8 models: BOM, BOMLine, Routing, RoutingOperation, WorkCenter, ProductionOrder, MaterialConsumption, FinishedGoodsReceipt
- Full CRUD serializers with nested BOM lines and routing operations
- CRUD views with standard API response format, module gate, workflow actions
- ProductionOrder cost fields are read-only (computed from MaterialConsumption)
- WorkCenter uses unique_together(company, code) for multi-tenant safety
- Django admin registered for all manufacturing models
- Registered in MODULE_CHOICES for module gating
- All 18 manufacturing tests passing

### v0.4.0 — Test Infrastructure & Coverage

- **Shared Test Helper**: Extracted `create_test_company()` and `create_test_user()` to `accounts/tests_helpers.py`
- **Finance Module Tests**: 25+ tests covering CRUD, module gates, invoice confirmation, journal voucher balancing
- **LLM Gateway Tests**: 20+ tests covering provider CRUD, API key encryption, chat sessions, usage stats

### v0.3.0 — Full Integration & Testing

- **Finance Module (v0.2.0)**: Complete 10-page RTL finance UI
- **LLM Gateway (v0.2.0)**: Unified LLM service layer supporting Ollama, OpenAI, Gemini, Anthropic
- **Module Management System**: Company-level `enabled_modules` JSON field, `RequireModule` DRF permission class

---

## 🚀 Roadmap

### ✅ Completed
- [x] Enterprise core mixins (soft delete, audit, company isolation)
- [x] Standard API response format
- [x] Finance service/selector/validator layers
- [x] Accounting Posting Engine
- [x] Workflow Engine state machine
- [x] Tax Engine (VAT, withholding)
- [x] Manufacturing Module foundation (BOM, Routing, WorkCenter, ProductionOrder)
- [x] 79+ tests passing

### 🔜 In Progress / Next
- [ ] MRP Engine (Material Requirement Planning) — §8-§10 of MANUFACTURING_MODULE.md
- [ ] Manufacturing Cost Engine (standard/actual/FIFO costing) — §15-§17
- [ ] Workflows Engine (cross-module approval routing) — WORKFLOW_ENGINE.md
- [ ] CRM Module
- [ ] HR / Payroll Module
- [ ] Inventory Management Module
- [ ] Quality Management Module
- [ ] Procurement Module
- [ ] Project Management Module
- [ ] Audit Trail & Reporting

### 🔮 Future
- [ ] Text-to-SQL for BI Dashboard
- [ ] Invoice OCR with LlamaIndex
- [ ] Mobile app (React Native)
- [ ] Multi-language support (FA/EN/AR)
- [ ] SSO integration (SAML/OIDC)
