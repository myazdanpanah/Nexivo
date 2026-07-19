<div align="center">

# Nexivo

### نکسیوو — Organization Operating System

**A comprehensive, modular Organization OS that covers every aspect of a company, organization, NGO, or government workflow. Fully customizable and tailored to your organization's needs.**

[![CI](https://github.com/myazdanpanah/nexivo/actions/workflows/tests.yml/badge.svg)](https://github.com/myazdanpanah/nexivo/actions/workflows/tests.yml)
[![License: Pro](https://img.shields.io/badge/License-Nexivo%20Pro-purple.svg)](LICENSE)

</div>

---

## Table of Contents

- [What is Nexivo?](#what-is-nexivo)
- [Why Organization OS?](#why-organization-os)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Option 1 — Local Development](#option-1--local-development)
  - [Option 2 — Docker Compose (Full Stack)](#option-2--docker-compose-full-stack)
- [Default Login Credentials](#default-login-credentials)
- [API Reference](#api-reference)
- [Module System](#module-system)
- [Organization Hierarchy](#organization-hierarchy)
- [BI Dashboard](#bi-dashboard)
- [Finance Module](#finance-module)
- [Database Manager](#database-manager)
- [LLM Gateway](#llm-gateway)
- [Filter System](#filter-system)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [CI/CD](#cicd)
- [License](#license)

---

## What is Nexivo?

Nexivo is a **modular, self-hosted Organization Operating System** designed to be the single platform your organization needs. Whether you're a startup, an enterprise, an NGO, or a government agency — Nexivo adapts to your workflows, not the other way around.

Unlike traditional BI tools that only handle dashboards, or accounting software that only handle finances, Nexivo is an **integrated platform** that covers:

| Domain | What Nexivo Handles |
|---|---|
| **Business Intelligence** | Drag-and-drop dashboards, KPIs, charts, data visualization, cross-chart filtering, drill-down |
| **Finance & Accounting** | Iranian accounting standards (Kol → Moin → Tafzili), invoices, receipts, payments, cheques, journal vouchers |
| **Database Management** | Browse, edit, query, and sync external databases with a built-in SQL editor |
| **CRM & Customer Management** | Customer and supplier records, relationship tracking, contact management |
| **AI Integration** | Unified LLM gateway supporting multiple AI providers with encryption, rate limiting, and chat history |
| **Data Import & Processing** | Excel/CSV upload with automatic parsing, cleaning, and PostgreSQL table creation |
| **Organization Management** | Company → Division → Team hierarchy, org chart visualization, role-based access |
| **Module System** | Enable/disable modules per organization — only activate what you need |
| **Government Workflows** | Customizable approval chains, document management, workflow automation |

---

## Why Organization OS?

Traditional software forces organizations to adopt rigid workflows. Nexivo takes a fundamentally different approach:

1. **Modular Architecture** — Enable only the modules your organization needs. A small business might use Finance + BI, while a government agency might use Datasets + Workflows + LLM.

2. **Fully Customizable** — Every organization is unique. Nexivo's module system, role-based access, and customizable dashboards let you tailor the platform to your exact needs.

3. **Single Source of Truth** — All your data, processes, and analytics in one place. No more juggling between disconnected tools.

4. **Self-Hosted** — Keep your data under your control. Deploy on-premise or in your own cloud infrastructure.

5. **Persian/Farsi First** — Full RTL support, Iranian accounting standards, and Persian UI — built for the Iranian market from day one.

6. **AI-Powered** — Built-in LLM gateway lets you integrate AI capabilities across all modules — from data analysis to document generation.

---

## Features

### Core Platform

| Feature | Details |
|---|---|
| **Module System** | Pluggable architecture — organizations enable/disable modules (BI Dashboard, Finance, CRM, DB Manager, Data Upload, LLM, Settings) |
| **Organization Hierarchy** | Company → Division → Team structure with org chart visualization |
| **Role-Based Access** | Four roles — Admin, CEO, Finance, Sales — with per-dataset, per-dashboard, per-page, and per-filter access control |
| **JWT Authentication** | Stateless JWT authentication with automatic token refresh |
| **Dark Theme** | System-wide dark/light mode toggle, persisted in localStorage |
| **RTL Support** | Full right-to-left layout for Persian/Farsi, including the Vazirmatn font |

### BI Dashboard

| Feature | Details |
|---|---|
| **Drag-and-Drop Grid** | Responsive grid layout using `react-grid-layout` — resize, reorder, configure widgets |
| **Multi-Page Dashboards** | Create multiple pages within a single dashboard with tab navigation, duplication, and per-page filters |
| **Charts** | Bar, Horizontal Bar, Line, Pie, Area, Scatter, Data Table, KPI Card, Gauge, Heatmap, Tree Map, Sankey, Funnel, Radar, Graph, Map — powered by Apache ECharts |
| **Dashboard-Level Filters** | Looker Studio-style filter bar with dropdown, date range, text search, checkbox, and slider controls |
| **Widget-Level Filters** | Per-widget filter configuration with operators (eq, neq, contains, gt, lt, between, in, starts_with, ends_with) |
| **Cross-Chart Filtering** | Click on a chart element to filter other charts in the dashboard |
| **Drill-Down** | Table widgets support click-to-drill-down with breadcrumb navigation |
| **Data Aggregation** | Automatic GROUP BY with SUM/COUNT/COUNT_DISTINCT/AVG/MIN/MAX; date grouping by year/quarter/month/week/day/hour |
| **Row-Level Security** | PostgreSQL RLS policies combined with role-based filters |
| **Superset Integration** | Embedded Apache Superset for advanced charting with guest token generation and RLS forwarding |
| **Dashboard Templates** | Pre-built templates for Sales, Finance, Marketing, HR, Retail |
| **Bulk Assignment** | Assign dashboards to entire teams, divisions, or companies at once |
| **Notifications** | Real-time bell icon with unread count, assignment alerts |

### Finance Module

| Feature | Details |
|---|---|
| **Iranian Accounting** | Kol → Moin → Tafzili hierarchy compliant with Iranian accounting standards |
| **Invoices** | Create, manage, and track invoices with automatic numbering |
| **Receipts** | Record and manage receipts |
| **Payments** | Track payments with dates, amounts, and descriptions |
| **Cheques** | Full cheque lifecycle management |
| **Journal Vouchers** | Create balanced journal entries with debit/credit validation |
| **Customers & Suppliers** | Manage customer and supplier records |

### Database Manager

| Feature | Details |
|---|---|
| **External DB Connections** | Browse, edit, and query external databases with encryption |
| **SQL Editor** | Write and execute SQL queries (admin/CEO only) |
| **Cell Editing** | Edit database cells directly with permissions |
| **File Import** | Import Excel/CSV files to new database tables |
| **Google Sheets Sync** | Sync data from Google Sheets |

### LLM Gateway

| Feature | Details |
|---|---|
| **Multi-Provider Support** | Unified interface for Ollama, OpenAI, Gemini, and Anthropic |
| **Encrypted API Keys** | Fernet symmetric encryption for stored API keys |
| **Rate Limiting** | Configurable rate limits per provider |
| **Chat History** | Session-based chat with message history |
| **Usage Tracking** | Track token usage and costs per provider |

### Data Processing

| Feature | Details |
|---|---|
| **Data Upload** | Drag-and-drop Excel (.xlsx/.xls) and CSV file upload with automatic parsing and PostgreSQL table creation |
| **REST API** | Full REST API with OpenAPI/Swagger documentation via `drf-spectacular` |
| **Background Tasks** | Celery + Redis for asynchronous processing (dataset imports, scheduled refreshes) |
| **Superset Integration** | Embedded Apache Superset for advanced analytics |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Nexivo Organization OS                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Frontend (React + Vite)                        │  │
│  │  ┌─────────┬──────────┬──────────┬──────────┬──────────┬──────────┐  │  │
│  │  │Launcher │Dashboard │ Finance  │ DB Mgr   │ LLM      │ Settings │  │  │
│  │  │  Page   │ Builder  │ Module   │ Module   │ Gateway  │  Page    │  │  │
│  │  └────┬────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘  │  │
│  │       └─────────┴──────────┴──────────┴──────────┴──────────┘        │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ REST API                             │
│  ┌───────────────────────────────────┴───────────────────────────────────┐  │
│  │                      Backend (Django + DRF)                            │  │
│  │  ┌─────────┬──────────┬──────────┬──────────┬──────────┬──────────┐  │  │
│  │  │Accounts │Dashboards│Datasets  │Finance   │DB Manager│   LLM    │  │  │
│  │  │  Auth   │  BI      │  Upload  │Accounting│   SQL    │ Gateway  │  │  │
│  │  │  RBAC   │  Charts  │  Parse   │Invoices  │  Browse  │  AI      │  │  │
│  │  │ Modules │  Filter  │  RLS     │Payments  │  Edit    │  Chat    │  │  │
│  │  └────┬────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘  │  │
│  │       │         │          │          │          │          │         │  │
│  │  ┌────┴─────────┴──────────┴──────────┴──────────┴──────────┴─────┐  │  │
│  │  │              Module Management System                           │  │  │
│  │  │        Company.enabled_modules → RequireModule RBAC             │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴───────────────────────────────────┐  │
│  │                        Infrastructure                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │  PostgreSQL   │  │    Redis     │  │   Superset   │  │  Celery  │  │  │
│  │  │   Primary DB  │  │   Cache +    │  │   Embedded   │  │  Background│  │
│  │  │   + RLS       │  │   Broker     │  │   Analytics  │  │  Tasks   │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Request flow:**
1. The React frontend sends API requests to the Django backend (proxied via Vite in dev, Nginx in production).
2. Django authenticates via JWT, checks `RequireModule` permission (module gate), applies role-based permissions, and queries PostgreSQL.
3. Uploaded data files are parsed by pandas, and a PostgreSQL table is created automatically.
4. Charts fetch data from the `/query/` endpoint, which applies RLS filters, widget-level filters, dashboard-level filters, and cross-chart filters before returning results.
5. Finance module supports Iranian accounting (Kol → Moin → Tafzili) with automatic invoice numbering, journal voucher balancing, and balance tracking.
6. LLM Gateway routes AI requests to Ollama/OpenAI/Gemini/Anthropic with encrypted API keys, rate limiting, and usage tracking.
7. Apache Superset can be used for advanced embedded analytics with guest tokens.

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| **Python 3.11** | Runtime |
| **Django 4.2** | Web framework |
| **Django REST Framework** | REST API toolkit |
| **drf-spectacular** | OpenAPI / Swagger documentation |
| **PyJWT** | Stateless JWT authentication |
| **pandas** | Excel/CSV parsing and data processing |
| **openpyxl** | Excel file support |
| **PostgreSQL 15** | Primary database with Row-Level Security |
| **Redis 7** | Celery broker and caching |
| **Celery 5** | Background task queue |
| **Gunicorn** | WSGI HTTP server |
| **python-decouple** | Environment variable management |
| **Pillow** | Image processing (user avatars) |
| **cryptography** | API key encryption (Fernet symmetric) |

### Frontend

| Technology | Purpose |
|---|---|
| **React 18** | UI framework |
| **TypeScript 5.5** | Type safety |
| **Vite 5** | Build tool and dev server |
| **React Router 6** | Client-side routing |
| **Apache ECharts** | Interactive charting |
| **react-grid-layout** | Drag-and-drop dashboard grid |
| **Zustand** | Lightweight state management |
| **Axios** | HTTP client with JWT interceptor |
| **Tailwind CSS 3** | Utility-first styling |
| **Vazirmatn** | Persian/Farsi web font |
| **Lucide React** | Icon library |
| **react-dropzone** | File upload with drag-and-drop |

### Infrastructure

| Technology | Purpose |
|---|---|
| **Docker** | Containerization |
| **Docker Compose** | Multi-service orchestration |
| **Nginx** | Frontend reverse proxy (production) |
| **Apache Superset 3.1** | Embedded BI analytics |
| **GitHub Actions** | CI/CD pipeline |

---

## Project Structure

```
nexivo/
├── backend/                      # Django REST API
│   ├── apps/
│   │   ├── accounts/             # Auth, users, org hierarchy, module management
│   │   │   ├── models.py         # Company, Division, Team, User, CustomRole
│   │   │   ├── permissions.py    # RequireModule DRF permission class
│   │   │   ├── tests_helpers.py  # Shared test fixtures
│   │   │   └── tests.py          # Auth, register, JWT tests
│   │   ├── dashboards/           # BI Dashboard module
│   │   ├── datasets/             # Data upload & querying
│   │   ├── db_manager/           # Database management & SQL editor
│   │   ├── finance/              # Iranian accounting (Kol/Moin/Tafzili)
│   │   │   ├── models.py         # 15 models (Kol, Moin, Tafzili, Invoice, etc.)
│   │   │   └── tests.py          # CRUD, module gates, business logic tests
│   │   └── llm/                  # LLM Gateway (Ollama/OpenAI/Gemini/Anthropic)
│   │       ├── service.py        # Unified provider interface
│   │       └── tests.py          # Providers, chat, encryption tests
│   └── nexivo/                   # Django project config
├── frontend/                     # React SPA
│   └── src/
│       ├── api/                  # API clients (finance.ts, llm.ts, dbManager.ts)
│       ├── pages/
│       │   ├── finance/          # Finance module pages (10 pages)
│       │   ├── LLMSettingsPage.tsx
│       │   ├── LauncherPage.tsx  # Module tile launcher
│       │   └── SettingsPage.tsx  # Module toggle + org structure
│       └── store/                # Zustand state stores
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20+ | Frontend runtime |
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Celery broker |
| **Docker** (optional) | 24+ | For containerized deployment |

---

## Getting Started

### Option 1 — Local Development

```bash
# 1. Start PostgreSQL and Redis via Docker
make start-services

# 2. Install dependencies and set up the project
make setup

# 3. Start the backend and frontend in separate terminals
make backend   # http://localhost:8000
make frontend  # http://localhost:3000
```

### Option 2 — Docker Compose (Full Stack)

```bash
# Create a .env file in the project root
cat > .env << EOF
POSTGRES_PASSWORD=nexivo_pass
DJANGO_SECRET_KEY=your-secret-key-here
SUPERSET_SECRET_KEY=your-superset-secret-key-here
EOF

# Start everything
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| Superset | http://localhost:8088 |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |

---

## Default Login Credentials

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | Admin (superuser) |
| `ceo` | `ceo123456` | CEO |
| `finance` | `finance123` | Finance |
| `sales` | `sales12345` | Sales |

> **⚠️ These are development credentials only.**

---

## API Reference

All endpoints are prefixed with `/api/v1/`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login/` | Login and receive JWT token |
| `POST` | `/api/v1/auth/register/` | Register a new user |
| `GET` | `/api/v1/auth/profile/` | Get current user profile |

### Module Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/auth/user-modules/` | Get enabled modules for current user |
| `PUT` | `/api/v1/auth/company/modules/` | Update company enabled modules (CEO only) |

### Datasets

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/datasets/` | List accessible datasets |
| `POST` | `/api/v1/datasets/upload/` | Upload Excel/CSV |
| `POST` | `/api/v1/datasets/:id/query/` | Query data with filters & aggregation |

### Dashboards

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboards/` | List dashboards |
| `POST` | `/api/v1/dashboards/` | Create a new dashboard |
| `GET` | `/api/v1/dashboards/:id/` | Get dashboard with pages & widgets |
| `PUT` | `/api/v1/dashboards/:id/` | Update dashboard settings |
| `DELETE` | `/api/v1/dashboards/:id/` | Delete a dashboard |
| `PUT` | `/api/v1/dashboards/:id/layout/` | Update grid layout (page-aware) |
| `PUT` | `/api/v1/dashboards/:id/filter-controls/` | Persist dashboard-level filters |

### Pages

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/dashboards/:id/pages/` | Add a page |
| `PUT` | `/api/v1/dashboards/:id/pages/:pid/` | Update page (name, filters) |
| `DELETE` | `/api/v1/dashboards/:id/pages/:pid/` | Delete a page |
| `POST` | `/api/v1/dashboards/:id/pages/:pid/duplicate/` | Duplicate page with all widgets |
| `PUT` | `/api/v1/dashboards/:id/pages/reorder/` | Reorder pages |

### Widgets

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/dashboards/:id/widgets/` | Add a widget (to a page) |
| `PUT` | `/api/v1/dashboards/:id/widgets/:wid/` | Update a widget |
| `DELETE` | `/api/v1/dashboards/:id/widgets/:wid/` | Delete a widget |

### Finance

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/finance/dashboard/` | Summary KPIs |
| `GET/POST` | `/api/v1/finance/kols/` | Chart of Accounts (Kol) |
| `GET/POST` | `/api/v1/finance/moins/` | Sub-accounts (Moin) |
| `GET/POST` | `/api/v1/finance/tafzilis/` | Detail accounts (Tafzili) |
| `GET/POST` | `/api/v1/finance/bank-accounts/` | Bank accounts |
| `GET/POST` | `/api/v1/finance/fiscal-years/` | Fiscal years |
| `GET/POST` | `/api/v1/finance/vouchers/` | Journal vouchers |
| `GET/POST` | `/api/v1/finance/invoices/` | Invoices |
| `GET/POST` | `/api/v1/finance/receipts/` | Receipts |
| `GET/POST` | `/api/v1/finance/payments/` | Payments |
| `GET/POST` | `/api/v1/finance/cheques/` | Cheques |
| `GET/POST` | `/api/v1/finance/customers/` | Customers |
| `GET/POST` | `/api/v1/finance/suppliers/` | Suppliers |

### Database Manager

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/api/v1/db-manager/databases/` | List/create database connections |
| `GET` | `/api/v1/db-manager/tables/:source/` | List tables |
| `GET` | `/api/v1/db-manager/tables/:source/:table/data/` | Browse table data |
| `POST` | `/api/v1/db-manager/sql/` | Execute SQL (admin/CEO only) |
| `POST` | `/api/v1/db-manager/import/` | Import file to new table |

### LLM Gateway

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/api/v1/llm/providers/` | List/create LLM providers |
| `POST` | `/api/v1/llm/providers/:id/activate/` | Set active provider |
| `POST` | `/api/v1/llm/providers/test/` | Test provider connection |
| `POST` | `/api/v1/llm/chat/` | Send chat message |
| `GET` | `/api/v1/llm/sessions/` | List chat sessions |
| `GET` | `/api/v1/llm/sessions/:id/messages/` | Get session messages |
| `GET` | `/api/v1/llm/usage/` | Usage statistics |

---

## Module System

Nexivo uses a **pluggable module architecture**. Each organization enables/disables modules via `Company.enabled_modules`, and the backend enforces access via `RequireModule` permission gates. This means:

- **Organizations choose what they need** — No bloat, no unused features
- **Modules can be toggled live** — Enable a new module without downtime
- **Access is granular** — Each module has its own API endpoints and permissions

| Module | Endpoint Prefix | Description |
|---|---|---|
| `bi_dashboard` | `/api/v1/dashboards/` | Drag-and-drop BI dashboards with ECharts |
| `finance` | `/api/v1/finance/` | Iranian accounting (Kol/Moin/Tafzili), invoices, receipts, payments |
| `db_manager` | `/api/v1/db-manager/` | External database browsing, SQL editor, cell editing |
| `datasets` | `/api/v1/datasets/` | Excel/CSV upload and PostgreSQL table creation |
| `llm` | `/api/v1/llm/` | Unified AI gateway (Ollama/OpenAI/Gemini/Anthropic) |
| `settings` | `/api/v1/auth/company/` | Module toggle + organization hierarchy management |

---

## Organization Hierarchy

Nexivo supports a multi-level organizational structure:

```
Company
├── Division (e.g., "Sales", "Marketing", "Engineering")
│   ├── Team (e.g., "Frontend", "Backend", "DevOps")
│   │   └── User
│   └── Team
│       └── User
└── Division
    └── Team
        └── User
```

- **Org Chart Visualization** — Interactive org chart page showing the full hierarchy
- **Bulk Assignment** — Assign dashboards to entire teams, divisions, or companies at once
- **Role-Based Access** — Users inherit permissions based on their role (Admin, CEO, Finance, Sales)
- **Custom Roles** — Create custom roles with fine-grained permission sets

---

## BI Dashboard

Nexivo provides a powerful, drag-and-drop BI dashboard builder:

### Multi-Page Dashboards

- **Tab Navigation** — Pages appear as tabs at the top of the dashboard builder
- **Drag-and-Drop Reordering** — Drag page tabs to rearrange them (persisted to backend)
- **Page Duplication** — Duplicate a page with all its widgets and layout via the context menu
- **Rename & Delete** — Right-click a page tab to rename or delete it
- **Per-Page Filters** — Each page maintains its own independent set of filter controls
- **Per-Page Layout** — Each page has its own grid layout and widgets

### Charts

Bar, Horizontal Bar, Line, Pie, Area, Scatter, Data Table, KPI Card, Gauge, Heatmap, Tree Map, Sankey, Funnel, Radar, Graph, Map — all powered by Apache ECharts with full RTL support.

### Filter System

Nexivo implements a comprehensive 4-layer filter pipeline (inspired by Google Looker Studio):

| Layer | Description |
|---|---|
| **Dashboard-Level Filters** | Looker Studio-style filter bar with dropdown, date range, text search, checkbox, and slider controls |
| **Widget-Level Filters** | Per-widget filter configuration with operators (eq, neq, contains, gt, lt, between, in) |
| **Cross-Chart Filtering** | Click on a chart element to filter other charts in the dashboard |
| **Drill-Down** | Table widgets support click-to-drill-down with breadcrumb navigation |

---

## Finance Module

The Finance module implements **Iranian accounting standards** with a complete chart of accounts:

### Chart of Accounts Hierarchy

```
Account Group (e.g., "Assets", "Liabilities", "Equity", "Revenue", "Expenses")
├── Kol Account (Main account — e.g., "Cash", "Bank")
│   ├── Moin Account (Sub-account — e.g., "Bank Mellat", "Bank Saman")
│   │   ├── Tafzili Account (Detail account — e.g., specific bank account number)
```

### Features

- **Automatic Invoice Numbering** — Sequential letter numbers per customer per year
- **Journal Voucher Balancing** — Debit/credit validation ensures balanced entries
- **Balance Tracking** — Real-time balance calculation for all accounts
- **Fiscal Year Management** — Create and manage fiscal years with opening balances
- **Cheque Lifecycle** — Full cheque management from issue to clearance

---

## Database Manager

Connect to and manage external databases:

- **Multiple Database Support** — Connect to PostgreSQL, MySQL, SQL Server, and more
- **Encrypted Credentials** — Database passwords are encrypted at rest
- **SQL Editor** — Write and execute SQL queries with syntax highlighting (admin/CEO only)
- **Cell Editing** — Edit database cells directly with permission checks
- **File Import** — Import Excel/CSV files to create new tables
- **Google Sheets Sync** — Sync data from Google Sheets to your database

---

## LLM Gateway

Integrate AI capabilities across your organization:

- **Multi-Provider Support** — Switch between Ollama (local), OpenAI, Gemini, and Anthropic
- **Encrypted API Keys** — All API keys are encrypted with Fernet symmetric encryption
- **Rate Limiting** — Configurable rate limits per provider to control costs
- **Chat History** — Session-based chat with full message history
- **Usage Tracking** — Monitor token usage and costs per provider
- **Test Connection** — Verify provider connectivity before activation

---

## Testing

Nexivo has **180+ backend tests** across all modules with shared test fixtures.

### Test Architecture

- **Shared Helper** (`backend/apps/accounts/tests_helpers.py`): Provides `create_test_company()` and `create_test_user()` — eliminates duplication across all test files
- **Module Tests**: Each app has its own test file covering CRUD, permissions, module gates, and business logic
- **CI Pipeline**: GitHub Actions runs all tests on every push/PR to `main`

### Running Tests

```bash
# Backend (Django)
cd backend
python manage.py check
python manage.py test --verbosity=2

# Frontend (TypeScript)
cd frontend
npx tsc --noEmit

# Or use Make
make test-backend
make test-frontend
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-change-me-in-production` | Django secret key |
| `DEBUG` | `0` | Enable debug mode |
| `POSTGRES_DB` | `nexivo` | PostgreSQL database name |
| `POSTGRES_USER` | `nexivo_user` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `nexivo_pass` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |

### Frontend (via Vite)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API URL |

---

## CI/CD

The GitHub Actions workflow runs on every push and PR to `main`:

1. **Backend Tests** — PostgreSQL 15 service container → `check` → `migrate` → `test` (180+ tests)
2. **Frontend Typecheck** — Node.js 20 → `tsc --noEmit`

---

## Screenshots

> Screenshots will be added after the first public release.

---

## License

This project is licensed under the **Nexivo Pro License** — see the [LICENSE](LICENSE) file for details.

Commercial use requires a separate license.

---

<div align="center">

**Built with care for the Persian-speaking business community.**

[Report Bug](https://github.com/myazdanpanah/nexivo/issues) · [Request Feature](https://github.com/myazdanpanah/nexivo/issues)

</div>
