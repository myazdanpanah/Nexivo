# Nexivo — Project Progress

**Last updated:** July 19, 2026  
**Current version:** v0.4.0

---

## 🎯 Architecture Overview

Nexivo is an **organizational SaaS platform** with pluggable modules. Each company (tenant) enables/disables modules, and each user gets role-based access to the enabled ones.

```
┌──────────────────────────────────────────────────────────────┐
│                     Nexivo Platform                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ BI       │ Finance  │ CRM      │ DB       │ Data     │ LLM      │
│ Dashboard│ Module   │ (future) │ Manager  │ Upload   │ Gateway  │
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
| `crm` | CRM | 🔲 Ready (future) |
| `db_manager` | Database Manager | ✅ Active |
| `datasets` | Data Upload | ✅ Active |
| `llm` | LLM Gateway | ✅ Active |
| `settings` | Settings | ✅ Active |

---

## 📁 Project Structure

```
Nexivo/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # Auth, users, org hierarchy, module management
│   │   │   ├── models.py      # Company, Division, Team, User, CustomRole
│   │   │   ├── views.py       # Auth, user mgmt, org mgmt, module endpoints
│   │   │   ├── permissions.py # RequireModule DRF permission class
│   │   │   ├── tests_helpers.py  # Shared test fixtures (create_test_company, etc.)
│   │   │   └── urls.py
│   │   ├── dashboards/        # BI Dashboard module
│   │   │   ├── models.py      # Dashboard, Page, Widget, Assignment, Notification
│   │   │   └── urls.py
│   │   ├── datasets/          # Data upload & query module
│   │   │   ├── models.py      # Dataset, DataFilter
│   │   │   └── urls.py
│   │   ├── db_manager/        # Database management module
│   │   │   ├── models.py      # ExternalDatabase, DatabasePermission, GoogleSheetsSync
│   │   │   ├── services/      # Business logic
│   │   │   └── urls.py
│   │   ├── finance/           # Finance module (Iranian accounting standards)
│   │   │   ├── models.py      # Kol, Tafzili, Invoice, Receipt, Cheque, Voucher, etc.
│   │   │   ├── serializers.py
│   │   │   ├── views.py       # All finance CRUD + module gate
│   │   │   ├── tests.py       # Finance module unit tests
│   │   │   └── urls.py
│   │   └── llm/               # LLM Gateway module
│   │       ├── models.py      # LLMProvider (encrypted keys), UsageLog, ChatSession/Message
│   │       ├── service.py     # Unified gateway: Ollama, OpenAI, Gemini, Anthropic
│   │       ├── views.py       # Provider CRUD, test, chat, usage stats + rate limiting
│   │       ├── tests.py       # LLM Gateway module unit tests
│   │       ├── serializers.py
│   │       └── urls.py
│   └── nexivo/
│       ├── settings.py
│       └── urls.py
├── frontend/
│   └── src/
│       ├── App.tsx            # All routes including /settings/ai, /finance
│       ├── pages/
│       │   ├── LLMSettingsPage.tsx    # System-level AI provider management
│       │   ├── SettingsPage.tsx       # Module mgmt + org structure tabs
│       │   ├── ... (other pages)
│       │   └── finance/
│       │       ├── FinanceLayout.tsx  # RTL sidebar layout
│       │       ├── FinanceDashboard.tsx
│       │       ├── ChartOfAccountsPage.tsx
│       │       ├── InvoicesPage.tsx
│       │       ├── ReceiptsPage.tsx
│       │       ├── PaymentsPage.tsx
│       │       ├── ChequesPage.tsx
│       │       ├── CustomersPage.tsx
│       │       ├── SuppliersPage.tsx
│       │       └── VouchersPage.tsx
│       └── api/
│           ├── llm.ts         # LLM API client
│           └── finance.ts     # Finance API client
└── docs/
```

---

## 🧪 Test Infrastructure (NEW — v0.4.0)

### Shared Test Helper

`backend/apps/accounts/tests_helpers.py` provides reusable fixtures for all test suites:

| Helper | Purpose |
|--------|---------|
| `create_test_company()` | Creates a Company with all modules enabled |
| `create_test_user()` | Creates a user assigned to a test company |
| `ALL_MODULES` | List of all module IDs for test fixtures |

### Test Coverage Summary

| Module | Test File | Tests | Status |
|--------|-----------|-------|--------|
| `accounts` | `tests.py` | 14 | ✅ All pass |
| `dashboards` | (via CI) | — | ✅ |
| `datasets` | `tests.py`, `tests_aggregation.py`, `tests_superset.py`, `tests_parsers.py` | ~50 | ✅ All pass |
| `db_manager` | `tests.py` | ~30 | ✅ All pass |
| `finance` | `tests.py` (NEW) | ~25 | ✅ All pass |
| `llm` | `tests.py` (NEW) | ~20 | ✅ All pass |
| **Total** | | **~180+** | ✅ **All pass** |

---

## 🤖 LLM Gateway (v0.2.0)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ NL Query Bar │  │ Upload OCR  │  │ Insight Cards       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Django)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LLM Gateway (Service Layer)              │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐  │   │
│  │  │ Ollama  │  │ OpenAI  │  │ Gemini  │  │Claude  │  │   │
│  │  │ Gemma 4 │  │ GPT-4o  │  │ Flash   │  │3.5 Son │  │   │
│  │  │(Local)  │  │         │  │         │  │        │  │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  Security:                                                  │
│  • API keys encrypted at rest (Fernet + Django SECRET_KEY)  │
│  • Rate limiting: 10 req/min chat, 10 req/min test          │
│  • Chat history capped at 50 messages                       │
│  • Company-scoped queries everywhere                         │
└─────────────────────────────────────────────────────────────┘
```

### Backend Models

| Model | Purpose |
|-------|---------|
| `LLMProvider` | Per-company provider config (Ollama/OpenAI/Gemini/Anthropic/DeepSeek) |
| `LLMUsageLog` | Track API usage: tokens, duration, feature |
| `LLMChatSession` | Persistent chat sessions |
| `LLMChatMessage` | Individual messages (capped at 50 per session) |

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET/POST` | `/api/v1/llm/providers/` | List or create providers |
| `GET/PUT/DELETE` | `/api/v1/llm/providers/{id}/` | Provider CRUD |
| `POST` | `/api/v1/llm/providers/{id}/activate/` | Set active provider |
| `POST` | `/api/v1/llm/providers/test/` | Test connection |
| `POST` | `/api/v1/llm/chat/` | Send chat message |
| `GET` | `/api/v1/llm/sessions/` | List chat sessions |
| `GET` | `/api/v1/llm/sessions/{id}/` | Get session with messages |
| `DELETE` | `/api/v1/llm/sessions/{id}/` | Delete session |
| `GET` | `/api/v1/llm/usage/` | Usage statistics |

### Security Features

1. **API Key Encryption**: Fernet symmetric encryption derived from Django SECRET_KEY. Keys stored encrypted in DB, decrypted on access via property.
2. **Rate Limiting**: DRF throttling — 10 req/min for chat, 10 req/min for test endpoints.
3. **Chat History Cap**: Maximum 50 messages per session sent to LLM to prevent context overflow.
4. **API Key Masking**: Provider list/detail responses mask keys as `••••••••xxxx`.
5. **Company Scoping**: All queries scoped to `request.user.company`.

### Frontend

| Route | Page | Purpose |
|-------|------|---------|
| `/settings/ai` | LLMSettingsPage | System-level AI provider management |

---

## 💰 Finance Module (v0.2.0)

### Iranian Accounting Standards (Sepidar-Compatible)

The finance module follows Iranian accounting conventions with full Tafzili (detail account) support.

### Models

| Model | Description |
|-------|-------------|
| `FiscalYear` | Iranian fiscal year (e.g., 1404/03/31) |
| `KolAccount` | Level 1: Main account (حساب کل) |
| `MoinAccount` | Level 2: Sub-account (حساب معین) |
| `TafziliAccount` | Level 3+: Detail account (تفضیلی) with 3 levels |
| `Customer` | Customer contact (مشتری) |
| `Supplier` | Supplier/vendor (تامین‌کننده) |
| `Invoice` | Sales invoice (فاکتور فروش) |
| `InvoiceItem` | Invoice line items |
| `Receipt` | Customer payment receipt (رسید دریافت) |
| `Payment` | Supplier payment receipt (رسید پرداخت) |
| `Cheque` | Cheque tracking (چک) — received/issued |
| `JournalVoucher` | Manual journal entries (سند حسابداری) |
| `JournalEntry` | Voucher debit/credit lines |

### Chart of Accounts Structure

```
حساب‌های کل (Kol)
├── ۱۰۰۰ دارایی‌ها (Assets)
│   ├── ۱۱۰۰ دارایی‌های جاری
│   │   ├── ۱۱۱۰ صندوق
│   │   ├── ۱۱۲۰ بانک
│   │   ├── ۱۱۳۰ حساب‌های دریافتنی
│   │   └── ۱۱۴۰ موجودی کالا
│   └── ۱۲۰۰ دارایی‌های غیرجاری
├── ۲۰۰۰ بدهی‌ها (Liabilities)
│   ├── ۲۱۰۰ بدهی‌های جاری
│   └── ۲۲۰۰ بدهی‌های غیرجاری
├── ۳۰۰۰ حقوق صاحبان سهام (Equity)
├── ۴۰۰۰ درآمدها (Revenue)
│   ├── ۴۱۰۰ درآمد فروش
│   └── ۴۲۰۰ درآمد خدمات
└── ۵۰۰۰ هزینه‌ها (Expenses)
    ├── ۵۱۰۰ بهای تمام‌شده کالای فروش رفته
    └── ۵۲۰۰ هزینه‌های عملیاتی
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/finance/dashboard/` | Summary KPIs |
| `GET/POST` | `/api/v1/finance/kols/` | Chart of Accounts (tree) |
| `GET/POST` | `/api/v1/finance/tafzilis/` | Detail accounts |
| `GET/POST` | `/api/v1/finance/invoices/` | Invoices (with items) |
| `POST` | `/api/v1/finance/invoices/{id}/confirm/` | Confirm invoice |
| `GET/POST` | `/api/v1/finance/receipts/` | Receipts |
| `GET/POST` | `/api/v1/finance/payments/` | Payments |
| `GET/POST` | `/api/v1/finance/cheques/` | Cheques |
| `GET/POST` | `/api/v1/finance/vouchers/` | Journal vouchers |
| `POST` | `/api/v1/finance/vouchers/{id}/confirm/` | Confirm voucher |
| `GET/POST` | `/api/v1/finance/customers/` | Customers |
| `GET/POST` | `/api/v1/finance/suppliers/` | Suppliers |
| `GET` | `/api/v1/finance/fiscal-years/` | Fiscal years |

---

## 🔐 Module Management System

### How It Works

1. **Company Level**: Each company has an `enabled_modules` JSON field listing which modules are active.
2. **User Level**: Users see only modules their company has enabled AND their role permits.
3. **Backend Enforcement**: Every API endpoint has a module gate that returns 403 if the module is disabled.

### Module Gates Applied

| App | Module | Gate Function |
|-----|--------|---------------|
| `dashboards` | `bi_dashboard` | `_check_dashboard_module()` |
| `db_manager` | `db_manager` | `_check_db_manager_module()` |
| `datasets` | `datasets` | `_check_datasets_module()` |
| `finance` | `finance` | `_check_finance_module()` |
| `llm` | `llm` | `_check_llm_module()` |

---

## 🖥️ Frontend Flow

### Login → Launcher → Module

1. **Login** (`/login`): User enters credentials → JWT token stored → Redirect to `/`
2. **Launcher** (`/`): Fetches `GET /auth/user-modules/` → Displays enabled modules as tiles
3. **Module**: User clicks a tile → Navigates to module-specific pages

### Settings Page (`/settings`)

Admin/CEO-only page with tabs:
- **Module Management**: Toggle modules on/off per company
- **Organization Structure**: Company → Division → Team hierarchy

### LLM Settings (`/settings/ai`)

System-level AI configuration:
- Add/manage LLM providers per company
- Set active provider
- Test connections
- View usage statistics
- Supports: Ollama (Gemma 4), OpenAI (GPT-4o), Gemini (Flash), Anthropic (Claude), DeepSeek

---

## 🚀 Next Steps

1. **Phase 1**: Text-to-SQL for BI Dashboard — Natural language → SQL → Results
2. **Phase 2**: Invoice OCR with LlamaIndex — Upload PDF/image → Extract data → Auto-fill forms
3. **CRM Module**: Customer relationship management features
4. **Per-module role gating**: Fine-grained role-based access within each module
5. **Audit logging**: Extend PermissionAuditLog to cover module enable/disable actions
6. **Multi-tenant isolation**: Ensure complete data isolation between companies
7. **API documentation**: Generate OpenAPI spec with drf-spectacular
8. **Frontend tests**: Add React Testing Library tests for finance and LLM pages

---

## 📝 Recent Changes (July 19, 2026)

### v0.4.0 — Test Infrastructure & Coverage

- **Shared Test Helper**: Extracted `create_test_company()` and `create_test_user()` to `accounts/tests_helpers.py` — eliminates DRY violation across all test files
- **Finance Module Tests**: 25+ tests covering CRUD, module gates, invoice confirmation, journal voucher balancing, customer/supplier search, financial summary
- **LLM Gateway Tests**: 20+ tests covering provider CRUD, API key encryption, chat sessions, usage stats, session management, module gating
- **All tests refactored** to use shared helper — single source of truth for Company fixture with enabled_modules

### v0.3.0 — Full Integration & Testing

- **Finance Module (v0.2.0)**: Complete 10-page RTL finance UI (Chart of Accounts, Invoices, Receipts, Payments, Cheques, Customers, Suppliers, Vouchers, Finance Dashboard)
- **LLM Gateway (v0.2.0)**: Unified LLM service layer supporting Ollama, OpenAI, Gemini, Anthropic; API key encryption, rate limiting, chat history cap
- **Module Management System**: Company-level `enabled_modules` JSON field, `RequireModule` DRF permission class, per-module gates on all endpoints
- **Settings Page**: Module toggle + Organization Structure management at `/settings`
- **Launcher Page**: Module tile launcher at `/` showing enabled modules per company
- **Test Fixes**: Fixed 41 backend test failures by adding Company fixtures with `enabled_modules` to all test setUp methods
- **Cleanup**: Removed legacy standalone files (Invoice_app.py, reportbro_service.py, superset_config.py, etc.)
- **All 135 backend tests passing, TypeScript typecheck clean**
