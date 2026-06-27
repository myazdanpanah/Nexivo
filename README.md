<div align="center">

# Nexivo

### نکسیوو — پلتفرم داشبورد هوشمند

**An intelligent dashboard platform for building, visualizing, and sharing business data — with full RTL (Persian/Farsi) support and role-based access control.**

[![CI](https://github.com/myazdanpanah/Nexivo/actions/workflows/tests.yml/badge.svg)](https://github.com/myazdanpanah/Nexivo/actions/workflows/tests.yml)
[![License: Pro](https://img.shields.io/badge/License-Nexivo%20Pro-purple.svg)](LICENSE)

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
- [Multi-Page Dashboards](#multi-page-dashboards)
- [Filter System](#filter-system)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [CI/CD](#cicd)
- [License](#license)

---

## What is Nexivo?

Nexivo is a self-hosted Business Intelligence platform that lets you:

1. **Upload** Excel/CSV data files — they are automatically parsed, cleaned, and stored in PostgreSQL tables.
2. **Build interactive dashboards** with a drag-and-drop grid layout, multiple pages, and charts powered by Apache ECharts.
3. **Enforce data security** with role-based access control (CEO, Finance, Sales, Admin) and PostgreSQL Row-Level Security.
4. **Visualize data** through bar, line, pie, area, scatter, table, KPI, gauge, heatmap, treemap, and more — all rendered with full RTL support for Persian/Farsi.
5. **Filter and slice data** with Looker Studio-style dashboard-level and widget-level filters (dropdown, date range, text search, checkbox, slider).

---

## Features

| Category | Details |
|---|---|
| **Data Upload** | Drag-and-drop Excel (.xlsx/.xls) and CSV file upload with automatic parsing and PostgreSQL table creation |
| **Dashboard Builder** | Drag-and-drop responsive grid layout using `react-grid-layout`; resize, reorder, and configure widgets |
| **Multi-Page Dashboards** | Create multiple pages within a single dashboard with tab navigation, drag-and-drop page reordering, page duplication, and per-page filters |
| **Charts** | Bar, Horizontal Bar, Line, Pie, Area, Scatter, Data Table, KPI Card, Gauge, Heatmap, Tree Map, Sankey, Funnel, Radar, Graph, Map — powered by Apache ECharts |
| **Chart Styling** | Background color/image, text color picker, color wheel/picker for widget backgrounds |
| **Sort & Limit** | Sort charts by max/min values, limit bar count for impressive visualizations |
| **Dark Theme** | System-wide dark/light mode toggle, persisted in localStorage |
| **RTL Support** | Full right-to-left layout for Persian/Farsi, including the Vazirmatn font and ECharts RTL configuration |
| **Dashboard-Level Filters** | Looker Studio-style filter bar with dropdown, date range, text search, checkbox, and slider controls — persisted to backend |
| **Widget-Level Filters** | Per-widget filter configuration with operators (eq, neq, contains, gt, lt, between, in, starts_with, ends_with) |
| **Dataset-Aware Filtering** | Filters automatically match by dataset — a filter on Dataset A won't affect widgets from Dataset B |
| **Cross-Chart Filtering** | Click on a chart element to filter other charts in the dashboard |
| **Drill-Down** | Table widgets support click-to-drill-down with breadcrumb navigation |
| **Data Aggregation** | Automatic GROUP BY with SUM/COUNT/COUNT_DISTINCT/AVG/MIN/MAX; date grouping by year/quarter/month/week/day/hour |
| **Role-Based Access** | Four roles — Admin, CEO, Finance, Sales — with per-dataset, per-dashboard, per-page, and per-filter access control |
| **Organization Hierarchy** | Company → Division → Team structure with org chart visualization |
| **Bulk Assignment** | Assign dashboards to entire teams, divisions, or companies at once |
| **Dashboard Templates** | Pre-built templates for Sales, Finance, Marketing, HR, Retail |
| **Notifications** | Real-time bell icon with unread count, assignment alerts |
| **Dashboard Management** | Rename, edit description, duplicate, share dashboards via context menu |
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
4. Charts fetch data from the `/query/` endpoint, which applies RLS filters, widget-level filters, dashboard-level filters, and cross-chart filters before returning results.
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
│   │   ├── datasets/             # Data upload & querying
│   │   └── dashboards/           # Dashboard, pages & widget management
│   │       ├── models.py         # Dashboard, DashboardPage, Widget models
│   │       ├── views.py          # CRUD, layout, page, widget endpoints
│   │       └── serializers.py
│   ├── nexivo/                   # Django project config
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # React SPA
│   ├── src/
│   │   ├── api/client.ts         # Axios instance with JWT interceptor
│   │   ├── components/
│   │   │   ├── ChartWidget.tsx    # ECharts rendering (all chart types)
│   │   │   ├── DashboardFilterBar.tsx  # Looker Studio-style filter controls
│   │   │   ├── PageNavBar.tsx     # Multi-page tab navigation with D&D
│   │   │   └── WidgetConfigPanel.tsx   # Widget settings panel
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardListPage.tsx
│   │   │   ├── DashboardBuilderPage.tsx  # Grid layout editor
│   │   │   └── DataUploadPage.tsx  # File upload with dropzone
│   │   ├── store/
│   │   │   ├── authStore.ts      # Zustand auth state
│   │   │   └── dashboardStore.ts # Zustand dashboard state (pages, filters)
│   │   └── utils/
│   │       ├── chartDefaults.ts
│   │       ├── kpiFormat.ts
│   │       └── rtlConfig.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── superset_config.py
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

---

## Multi-Page Dashboards

Nexivo supports multiple pages within a single dashboard:

- **Tab Navigation** — Pages appear as tabs at the top of the dashboard builder
- **Drag-and-Drop Reordering** — Drag page tabs to rearrange them (persisted to backend)
- **Page Duplication** — Duplicate a page with all its widgets and layout via the context menu
- **Rename & Delete** — Right-click a page tab to rename or delete it
- **Per-Page Filters** — Each page maintains its own independent set of filter controls
- **Per-Page Layout** — Each page has its own grid layout and widgets

---

## Filter System

Nexivo implements a comprehensive 4-layer filter pipeline (inspired by Google Looker Studio):

### Dashboard-Level Filter Controls

The filter bar at the top of the dashboard provides Looker Studio-style controls:

| Control Type | Description | Backend Operator |
|---|---|---|
| **Dropdown** | Select one value from a list (auto-populated from data) | `eq` or `in` |
| **Date Range** | Start/end date picker | `gte` / `lte` |
| **Text Search** | Free-text ILIKE search | `contains` |
| **Checkbox** | Multi-select checkboxes | `in` |
| **Slider** | Numeric range slider with min/max | `gte` / `lte` |

- Controls auto-detect type from column type (dates → date range, numeric → slider)
- Filter controls are **dataset-aware** — a filter on Dataset A won't affect widgets from Dataset B
- Controls are **persisted to the backend** per dashboard page
- Individual controls can be removed with the delete button

### Widget-Level Filters

Each widget can have its own filters configured in the widget settings panel:

| Operator | Description |
|---|---|
| `eq` | Equals |
| `neq` | Not equals |
| `contains` | Contains (ILIKE) |
| `starts_with` | Starts with |
| `ends_with` | Ends with |
| `gt` / `gte` | Greater than / Greater than or equal |
| `lt` / `lte` | Less than / Less than or equal |
| `between` | Between two values |
| `in` | In a list of values |

### Cross-Chart Filtering

Click on a chart element (bar, pie slice, etc.) to filter other charts in the same dashboard. Cross-chart filters are shown as chips in the filter bar and can be removed individually.

### Drill-Down

Table widgets support click-to-drill-down. Click a cell to filter by that value, with a breadcrumb trail showing the drill path. Click "همه" (All) to return to the root.

---

## Data Aggregation

The query engine supports automatic aggregation:

- **GROUP BY** — When multiple columns are selected, the first column becomes the dimension and numeric columns are aggregated with SUM
- **Date Grouping** — Group by year, quarter, month, week, day, or hour using `DATE_TRUNC`
- **KPI Mode** — All selected columns become metrics (no GROUP BY), perfect for summary cards
- **Column Type Validation** — SUM/AVG/MIN/MAX are only applied to numeric columns; text columns cause a clear 400 error

---

## Running Tests

### Backend Tests

```bash
cd backend
python manage.py check
python manage.py test --verbosity=2
```

### Frontend Type Checking

```bash
cd frontend
npx tsc --noEmit
```

### Using Make

```bash
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

1. **Backend Tests** — PostgreSQL 15 service container → `check` → `migrate` → `test`
2. **Frontend Typecheck** — Node.js 20 → `tsc --noEmit`

---

## Screenshots

> Screenshots will be added after the first public release. Visit [codebuff.com](https://codebuff.com) for live demos.

---

## License

This project is licensed under the **Nexivo Pro License** — see the [LICENSE](LICENSE) file for details.

Commercial use requires a separate license. Contact commercial@nexivo.dev for inquiries.

---

<div align="center">

**Built with care for the Persian-speaking business intelligence community.**

[Report Bug](https://github.com/myazdanpanah/Nexivo/issues) · [Request Feature](https://github.com/myazdanpanah/Nexivo/issues)

</div>
