<div align="center">

# Nexivo

### نکسیوو — پلتفرم داشبورد هوشمند

**An intelligent dashboard platform for building, visualizing, and sharing business data — with full RTL (Persian/Farsi) support and role-based access control.**

[![CI](https://github.com/myazdanpanah/Nexivo/actions/workflows/tests.yml/badge.svg)](https://github.com/myazdanpanah/Nexivo/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## Table of Contents

- [What is Nexivo?](#what-is-nexivo)
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
- [Role-Based Access Control](#role-based-access-control)
- [Dataset Management](#dataset-management)
- [Dashboard Builder](#dashboard-builder)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [CI/CD](#cicd)
- [License](#license)

---

## What is Nexivo?

Nexivo is a self-hosted Business Intelligence platform that lets you:

1. **Upload** Excel/CSV data files — they are automatically parsed, cleaned, and stored in PostgreSQL tables.
2. **Build interactive dashboards** with a drag-and-drop grid layout, adding charts powered by Apache ECharts.
3. **Enforce data security** with role-based access control (CEO, Finance, Sales, Admin) and PostgreSQL Row-Level Security.
4. **Visualize data** through bar, line, pie, area, scatter, and table widgets — all rendered with full RTL support for Persian/Farsi.

The platform is designed for organizations that need a private, customizable BI tool with modern UI and robust data governance.

---

## Features

| Category | Details |
|---|---|
| **Data Upload** | Drag-and-drop Excel (.xlsx/.xls) and CSV file upload with automatic parsing and PostgreSQL table creation |
| **Dashboard Builder** | Drag-and-drop responsive grid layout using `react-grid-layout`; resize, reorder, and configure widgets |
| **Charts** | Bar, Line, Pie, Area, Scatter, Data Table, KPI Card, Gauge, Heatmap, Tree Map — powered by Apache ECharts |
| **RTL Support** | Full right-to-left layout for Persian/Farsi, including the Vazirmatn font and ECharts RTL configuration |
| **Role-Based Access** | Four roles — Admin, CEO, Finance, Sales — with per-dataset and per-dashboard access control |
| **Row-Level Security** | PostgreSQL RLS policies combined with role-based filters applied at query time |
| **JWT Authentication** | Stateless JWT authentication with automatic token refresh and 401 handling |
| **Superset Integration** | Embedded Apache Superset for advanced charting, with guest token generation and RLS forwarding |
| **REST API** | Full REST API with OpenAPI/Swagger documentation via `drf-spectacular` |
| **Background Tasks** | Celery + Redis for asynchronous processing (dataset imports, scheduled refreshes) |
| **Modern UI** | Tailwind CSS, Zustand state management, responsive design, smooth transitions |
| **CI/CD** | GitHub Actions workflow for backend tests (Django) and frontend type-checking (TypeScript) |

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│  (React +    │ API │  (Django +   │     │   Database   │
│   Vite)      │◀────│   DRF)       │◀────│              │
│   :3000      │     │   :8000      │     │   :5432      │
│              │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │              │
                     │   Superset   │
                     │   :8088      │
                     │              │
                     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │              │
                     │    Redis     │
                     │  :6379       │
                     │  (Celery)    │
                     │              │
                     └──────────────┘
```

**Request flow:**
1. The React frontend sends API requests to the Django backend (proxied via Vite in dev, Nginx in production).
2. Django authenticates via JWT, applies role-based permissions, and queries PostgreSQL.
3. Uploaded data files are parsed by pandas, and a PostgreSQL table is created automatically.
4. Charts fetch data from the `/query/` endpoint, which applies RLS filters before returning results.
5. Apache Superset can be used for advanced embedded analytics with guest tokens.

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
| **PostgreSQL 15** | Primary database |
| **Redis 7** | Celery broker and caching |
| **Celery 5** | Background task queue |
| **Gunicorn** | WSGI HTTP server |
| **python-decouple** | Environment variable management |
| **Pillow** | Image processing (user avatars) |

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
Nexivo/
├── backend/                      # Django REST API
│   ├── apps/
│   │   ├── accounts/             # User auth, roles, JWT
│   │   │   ├── authentication.py # Custom JWT auth class
│   │   │   ├── middleware.py     # Role-based RLS middleware
│   │   │   ├── models.py        # Custom User model (role, department)
│   │   │   ├── permissions.py   # IsCEO, IsFinanceOrAbove, etc.
│   │   │   ├── serializers.py   # User, Login, Register serializers
│   │   │   ├── views.py         # Login, register, profile endpoints
│   │   │   ├── urls.py
│   │   │   ├── management/commands/
│   │   │   │   └── create_dev_data.py  # Seed dev users
│   │   │   └── tests.py, tests_commands.py
│   │   ├── datasets/             # Data upload & querying
│   │   │   ├── models.py        # Dataset, DataFilter models
│   │   │   ├── parsers.py       # Excel/CSV → PostgreSQL pipeline
│   │   │   ├── superset.py      # Superset API client
│   │   │   ├── views.py         # Upload, query, CRUD endpoints
│   │   │   └── tests.py, tests_parsers.py
│   │   └── dashboards/           # Dashboard & widget management
│   │       ├── models.py        # Dashboard, Widget models
│   │       ├── views.py         # CRUD, layout, widget endpoints
│   │       └── serializers.py
│   ├── nexivo/                   # Django project config
│   │   ├── settings.py          # All configuration (DB, JWT, Superset, etc.)
│   │   ├── urls.py              # API routing
│   │   └── celery.py            # Celery setup
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # React SPA
│   ├── src/
│   │   ├── api/client.ts        # Axios instance with JWT interceptor
│   │   ├── components/
│   │   │   ├── ChartWidget.tsx   # ECharts rendering (bar/line/pie/table)
│   │   │   └── WidgetConfigPanel.tsx  # Widget settings panel
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardListPage.tsx
│   │   │   ├── DashboardBuilderPage.tsx  # Grid layout editor
│   │   │   └── DataUploadPage.tsx  # File upload with dropzone
│   │   ├── store/
│   │   │   ├── authStore.ts     # Zustand auth state (persisted)
│   │   │   └── dashboardStore.ts  # Zustand dashboard state
│   │   └── utils/
│   │       ├── chartDefaults.ts  # Default ECharts options per chart type
│   │       └── rtlConfig.ts     # RTL-aware chart configuration
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── superset_config.py            # Apache Superset configuration
├── docker-compose.yml            # Full stack orchestration
├── Makefile                      # Dev convenience commands
├── .github/workflows/tests.yml   # CI pipeline
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

Run services locally (requires PostgreSQL and Redis running — use Docker or install locally):

```bash
# 1. Start PostgreSQL and Redis via Docker
make start-services

# 2. Install dependencies and set up the project
make setup
# This will:
#   - Install Python and Node.js dependencies
#   - Copy .env.example → backend/.env (if not exists)
#   - Run database migrations
#   - Create dev superuser + sample users

# 3. Start the backend and frontend in separate terminals
make backend   # http://localhost:8000
make frontend  # http://localhost:3000
```

**Or step-by-step:**

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Create environment file
cp .env.example backend/.env

# Start PostgreSQL and Redis (Docker)
make start-services

# Run migrations
cd backend && python manage.py migrate

# Seed dev data
python manage.py create_dev_data

# Start servers (in separate terminals)
python manage.py runserver 0.0.0.0:8000    # Backend
cd ../frontend && npm run dev              # Frontend
```

### Option 2 — Docker Compose (Full Stack)

This runs all services (backend, frontend, PostgreSQL, Redis, Superset) in containers:

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

After running `make setup` or `make seed`, the following dev users are available:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | Admin (superuser) |
| `ceo` | `ceo123456` | CEO |
| `finance` | `finance123` | Finance |
| `sales` | `sales12345` | Sales |

> **⚠️ These are development credentials only. Change all passwords before any production deployment.**

---

## API Reference

All endpoints are prefixed with `/api/v1/`. Full OpenAPI documentation is available at `/api/docs/` when the server is running.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/auth/login/` | Login and receive JWT token | Public |
| `POST` | `/api/v1/auth/register/` | Register a new user | Public |
| `GET` | `/api/v1/auth/profile/` | Get current user profile | Bearer Token |
| `PUT` | `/api/v1/auth/profile/update/` | Update current user profile | Bearer Token |
| `GET` | `/api/v1/auth/users/` | List all users (admin/CEO only) | Bearer Token |

### Datasets

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/datasets/` | List datasets accessible to user's role | Bearer Token |
| `POST` | `/api/v1/datasets/upload/` | Upload Excel/CSV and create dataset | Bearer Token |
| `GET` | `/api/v1/datasets/:id/` | Get dataset details | Bearer Token |
| `PUT` | `/api/v1/datasets/:id/` | Update dataset metadata | Bearer Token |
| `DELETE` | `/api/v1/datasets/:id/` | Delete a dataset | Bearer Token |
| `POST` | `/api/v1/datasets/:id/query/` | Query dataset data with filters | Bearer Token |

### Dashboards

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/dashboards/` | List dashboards accessible to user's role | Bearer Token |
| `POST` | `/api/v1/dashboards/` | Create a new dashboard | Bearer Token |
| `GET` | `/api/v1/dashboards/:id/` | Get dashboard with widgets | Bearer Token |
| `PUT` | `/api/v1/dashboards/:id/` | Update dashboard settings | Bearer Token |
| `DELETE` | `/api/v1/dashboards/:id/` | Delete a dashboard | Bearer Token |
| `PUT` | `/api/v1/dashboards/:id/layout/` | Update grid layout (drag-and-drop) | Bearer Token |
| `POST` | `/api/v1/dashboards/:id/widgets/` | Add a widget to a dashboard | Bearer Token |
| `GET` | `/api/v1/dashboards/:id/widgets/:wid/` | Get widget details | Bearer Token |
| `PUT` | `/api/v1/dashboards/:id/widgets/:wid/` | Update a widget | Bearer Token |
| `DELETE` | `/api/v1/dashboards/:id/widgets/:wid/` | Delete a widget | Bearer Token |

### Documentation

| Endpoint | Description |
|---|---|
| `/api/docs/` | Swagger UI (interactive API explorer) |
| `/api/schema/` | OpenAPI schema (JSON) |
| `/admin/` | Django Admin panel |

---

## Role-Based Access Control

Nexivo implements a hierarchical role system with four roles:

```
Admin ─────────────────────────────────────────────┐
  │                                                 │
CEO ────────────────────────────────────────────────┤
  │                                                 │
Finance ────────────────────────────────────────────┤
  │                                                 │
Sales ──────────────────────────────────────────────┘
```

### Role Permissions

| Capability | Admin | CEO | Finance | Sales |
|---|:---:|:---:|:---:|:---:|
| See all datasets | ✅ | ✅ | ❌ | ❌ |
| See all dashboards | ✅ | ✅ | ❌ | ❌ |
| See own-role datasets | ✅ | ✅ | ✅ | ✅ |
| Upload datasets | ✅ | ✅ | ✅ | ✅ |
| Create dashboards | ✅ | ✅ | ✅ | ✅ |
| Manage users | ✅ | ✅ | ❌ | ❌ |
| Django Admin | ✅ | ❌ | ❌ | ❌ |

**How it works:**
- Each dataset and dashboard has an `allowed_roles` JSON field specifying which roles can access it.
- CEO and Admin users bypass role filters and see everything.
- The `RoleMiddleware` sets PostgreSQL session variables for Row-Level Security.
- The `/query/` endpoint applies role-based `DataFilter` records before executing queries.

---

## Dataset Management

### Upload Flow

1. User uploads an Excel (.xlsx/.xls) or CSV file via the drag-and-drop upload page.
2. The backend parses the file using **pandas**, cleaning column names (lowercase, underscored, Unicode-safe).
3. A PostgreSQL table is automatically created with the appropriate column types:
   - `int64` → `BIGINT`
   - `float64` → `DOUBLE PRECISION`
   - `object` → `TEXT`
   - `bool` → `BOOLEAN`
   - `datetime64[ns]` → `TIMESTAMP`
4. Data is inserted using PostgreSQL `COPY` for high performance.
5. The dataset is registered with metadata (row count, column names/types) and role-based access control.

### Query Flow

1. Frontend sends a query request with desired columns and optional filters.
2. The backend validates all column names against the dataset schema (prevents SQL injection).
3. Role-based `DataFilter` records are applied automatically.
4. Results are returned as `{ columns: [...], data: [...], row_count: N }`.

### DataFilter Operators

| Operator | Description | Example Value |
|---|---|---|
| `eq` | Equals | `"active"` |
| `in` | In list | `["A", "B", "C"]` |
| `contains` | Contains (ILIKE) | `"search term"` |
| `gt` | Greater than | `100` |
| `lt` | Less than | `500` |

---

## Dashboard Builder

### Creating a Dashboard

1. Click **"داشبورد جدید"** (New Dashboard) on the dashboard list page.
2. You are taken to the grid layout editor with a responsive 12-column grid.
3. Click **"افزودن نمودار"** (Add Widget) to add a new chart.

### Configuring Widgets

Click the gear icon on any widget to open the config panel:

- **Title** — Custom widget name
- **Chart Type** — Bar, Line, Pie, or Table
- **Dataset** — Select from uploaded datasets
- **Columns** — Pick which columns to display (first column = category, rest = values for charts)

### Supported Chart Types

| Type | Description | Best For |
|---|---|---|
| **Bar** (`bar`) | Vertical bar chart | Comparing categories |
| **Line** (`line`) | Line chart with markers | Trends over time |
| **Pie** (`pie`) | Donut/pie chart with percentages | Part-to-whole |
| **Area** (`area`) | Filled area chart | Cumulative trends |
| **Scatter** (`scatter`) | Scatter plot | Correlations |
| **Table** (`table`) | Scrollable data table | Raw data inspection |
The following chart types are configured in the backend and available for future frontend integration:

| Type | Description | Best For |
|---|---|---|
| **KPI** (`kpi`) | Key Performance Indicator card | Single metric display |
| **Gauge** (`gauge`) | Gauge/meter chart | Progress toward target |
| **Heatmap** (`heatmap`) | Color-coded matrix | Density/cross-tabulation |
| **Tree Map** (`treemap`) | Nested rectangles | Hierarchical proportions |

> **Note:** The widget config panel currently exposes Bar, Line, Pie, and Table. Additional chart types are backend-ready and can be wired up as needed.

### Drag and Drop

- Widgets can be **dragged** to reposition and **resized** by dragging handles.
- Layout changes are automatically persisted to the backend.
- The grid is responsive: 12 columns on large screens, 9 on medium, 6 on small.

---

## Running Tests

### Backend Tests

```bash
cd backend
python manage.py check           # Django system checks
python manage.py test --verbosity=2  # Run all tests
```

### Frontend Type Checking

```bash
cd frontend
npx tsc --noEmit                 # TypeScript type check
```

### Using Make

```bash
make test-backend   # Django checks
make test-frontend  # TypeScript type check
```

### CI Pipeline

The GitHub Actions workflow (`.github/workflows/tests.yml`) runs on every push and PR to `main`:

1. **Backend Tests** — Spins up a PostgreSQL service container, installs Python dependencies, runs `check`, `migrate`, and `test`.
2. **Frontend Typecheck** — Installs Node.js dependencies, runs `tsc --noEmit`.

---

## Environment Variables

### Backend (`backend/.env` or environment)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-change-me-in-production` | Django secret key |
| `DEBUG` | `0` | Enable debug mode |
| `POSTGRES_DB` | `nexivo` | PostgreSQL database name |
| `POSTGRES_USER` | `nexivo_user` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `nexivo_pass` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host (use `postgres` in Docker) |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `SUPERSET_API_URL` | `http://superset:8088/api/v1` | Superset API base URL |
| `SUPERSET_USERNAME` | `admin` | Superset admin username |
| `SUPERSET_PASSWORD` | `admin` | Superset admin password |
| `SUPERSET_SECRET_KEY` | (set in .env) | Superset secret key for guest tokens |

### Frontend (via Vite)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API URL |

---

## CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:     # Django check + migrate + test
  frontend-check:    # TypeScript type check
```

**Backend pipeline:**
1. PostgreSQL 15 service container with health checks
2. Python 3.11 with pip caching
3. Install dependencies → `manage.py check` → `manage.py migrate` → `manage.py test`

**Frontend pipeline:**
1. Node.js 20 with npm caching
2. Install dependencies → `tsc --noEmit`

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with care for the Persian-speaking business intelligence community.**

[Report Bug](https://github.com/myazdanpanah/Nexivo/issues) · [Request Feature](https://github.com/myazdanpanah/Nexivo/issues)

</div>
