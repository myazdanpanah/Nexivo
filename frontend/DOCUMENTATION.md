# Nexivo — Intelligent Dashboard Platform

> A full-stack BI dashboard platform with role-based access, per-user data filters, organization hierarchy, and ECharts visualizations. Built with Django REST Framework + React/TypeScript.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Backend Reference](#backend-reference)
6. [Frontend Reference](#frontend-reference)
7. [Key Features](#key-features)
8. [Data Model](#data-model)
9. [API Endpoints](#api-endpoints)
10. [Role-Based Access Control (RBAC)](#role-based-access-control)
11. [Dark Theme](#dark-theme)
12. [Deployment](#deployment)
13. [Contributing](#contributing)

---

## Architecture Overview

```
┌──────────────┐     REST API (JWT)     ┌──────────────────┐
│   React SPA  │ ◄─────────────────────► │  Django Backend   │
│  (Vite+TS)   │                        │  (DRF + Celery)   │
└──────────────┘                        └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │   PostgreSQL DB   │
                                        └──────────────────┘
```

- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + ECharts
- **Backend**: Django 4.x + Django REST Framework + Celery
- **Database**: PostgreSQL (SQLite for dev)
- **Auth**: JWT tokens (stored in localStorage)
- **Charts**: ECharts (17 chart types)
- **RTL**: Full Persian/Farsi (RTL) support

---

## Tech Stack

| Layer       | Technology                                       |
|-------------|--------------------------------------------------|
| Frontend    | React 18, TypeScript, Vite, TailwindCSS 3        |
| Charts      | ECharts (bar, line, pie, scatter, gauge, map, etc.) |
| State       | Zustand (auth, dashboard, theme stores)          |
| Backend     | Django 4.x, Django REST Framework, Celery        |
| Database    | PostgreSQL (prod), SQLite (dev)                  |
| Auth        | JWT tokens, role-based permissions               |
| Icons       | Lucide React                                     |
| Grid        | react-grid-layout                                |
| Uploads     | react-dropzone                                   |
| Fonts       | Vazirmatn (Persian web font)                     |

---

## Project Structure

```
Nexivo/
├── backend/                    # Django project
│   ├── manage.py
│   ├── nexivo/                 # Django settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/           # User management, org hierarchy
│   │   │   ├── models.py       # User, Company, Division, Team
│   │   │   ├── views.py        # Auth, user CRUD, org tree
│   │   │   ├── serializers.py  # User, Company, Division, Team serializers
│   │   │   ├── urls.py
│   │   │   └── admin.py
│   │   ├── dashboards/         # Core dashboard functionality
│   │   │   ├── models.py       # Dashboard, DashboardPage, Widget, DashboardAssignment,
│   │   │   │                   #   PermissionAuditLog, Notification
│   │   │   ├── views.py        # Dashboard CRUD, pages, widgets, assignments, bulk ops,
│   │   │   │                   #   notifications, audit log, org chart
│   │   │   ├── serializers.py  # All dashboard-related serializers
│   │   │   └── urls.py
│   │   └── datasets/           # Data upload and querying
│   │       ├── models.py       # Dataset (uploaded Excel/CSV files)
│   │       ├── views.py        # Upload, query (with row-level filtering)
│   │       ├── parsers.py      # Excel/CSV parsing
│   │       └── superset.py     # Apache Superset integration
│   └── requirements.txt
│
├── frontend/                   # React + TypeScript SPA
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js      # TailwindCSS config (darkMode: 'class')
│   ├── index.html
│   ├── nginx.conf              # Production nginx config
│   ├── Dockerfile
│   └── src/
│       ├── App.tsx             # Route definitions
│       ├── main.tsx            # Entry point (theme sync)
│       ├── index.css           # Global styles, RTL, grid layout
│       ├── api/
│       │   └── client.ts       # Axios instance with JWT interceptor
│       ├── components/
│       │   ├── ChartWidget.tsx      # ECharts rendering (17 chart types)
│       │   ├── DashboardFilterBar.tsx # Looker Studio-style filter controls
│       │   ├── PageNavBar.tsx       # Page tabs with rename/duplicate/delete
│       │   ├── WidgetConfigPanel.tsx # Widget settings sidebar
│       │   ├── Toast.tsx           # Toast notification system
│       │   ├── NotificationBell.tsx # Real-time notification dropdown
│       │   └── ThemeToggle.tsx     # Dark/light mode toggle
│       ├── pages/
│       │   ├── LoginPage.tsx        # Auth page
│       │   ├── DashboardListPage.tsx # Dashboard grid with templates
│       │   ├── DashboardBuilderPage.tsx # Dashboard editor with grid layout
│       │   ├── DataUploadPage.tsx   # Excel/CSV upload
│       │   ├── AdminSettingsPage.tsx # User management + audit log
│       │   ├── DashboardAssignPage.tsx # Per-user dashboard assignments
│       │   ├── OrganizationPage.tsx  # Org hierarchy management (Company/Division/Team)
│       │   └── OrgChartPage.tsx     # Visual org chart
│       ├── store/
│       │   ├── authStore.ts        # JWT auth state
│       │   ├── dashboardStore.ts   # Dashboard/page/widget state
│       │   └── themeStore.ts       # Dark/light mode persistence
│       └── utils/
│           ├── chartDefaults.ts    # ECharts default configs
│           ├── kpiFormat.ts        # KPI number formatting
│           ├── mapRegistry.ts      # Dynamic GeoJSON map loading
│           ├── palettes.ts        # Color palettes
│           ├── resizeObserverPolyfill.ts
│           ├── roles.ts           # Role constants and labels
│           ├── rtlConfig.ts       # ECharts RTL support
│           └── themeConfig.ts     # Widget style config
│
├── docker-compose.yml          # Docker orchestration
├── Makefile                    # Build commands
├── dev.bat                     # Windows dev script
└── superset_config.py          # Apache Superset config
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or SQLite for dev)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev    # Starts Vite dev server on port 5173
```

### Docker Setup
```bash
docker-compose up --build
```

### Default Test Users
| Username | Password   | Role    |
|----------|------------|---------|
| admin    | admin12345 | admin   |
| ceo      | admin12345 | ceo     |
| sales    | admin12345 | sales   |
| finance  | admin12345 | finance |

---

## Backend Reference

### Core Models

**User** (`accounts.User`)
- Extends `AbstractUser` with: `role`, `department`, `avatar`
- Org links: `company`, `division`, `team`, `reports_to`
- Roles: `admin`, `ceo`, `finance`, `sales`

**Company → Division → Team** (Organization hierarchy)
- `Company`: Top-level organization
- `Division`: Division within a company, with optional `manager` and `parent`
- `Team`: Team within a division, with optional `manager`

**Dashboard** (`dashboards.Dashboard`)
- `name`, `description`, `owner` (FK to User)
- `allowed_roles`: JSON list of roles that can access
- `filter_controls`: Dashboard-level filter definitions
- `is_published`: Visibility flag

**DashboardPage** (`dashboards.DashboardPage`)
- FK to Dashboard, `name`, `order`
- `layout`: JSON grid positions `[{i, x, y, w, h}]`
- `filter_controls`: Page-level filter definitions
- `allowed_roles`: Page-level access control

**Widget** (`dashboards.Widget`)
- FK to Dashboard + DashboardPage
- `chart_type`: One of 17 types (bar, line, pie, kpi, table, map, etc.)
- `dataset`: FK to Dataset (data source)
- `chart_config`: ECharts option overrides (JSON)
- `query_config`: Columns, metrics, filters (JSON)
- `grid_x`, `grid_y`, `grid_w`, `grid_h`: Grid position

**DashboardAssignment** (`dashboards.DashboardAssignment`)
- FK to Dashboard + User (`assigned_to`, `assigned_by`)
- `data_filters`: Row-level data restrictions
- `visible_pages`: Which pages the user can see
- `visible_filter_controls`: Which filters the user can use
- `is_active`: Toggle without deletion

**Notification** (`dashboards.Notification`)
- FK to User (`recipient`)
- `notification_type`: `assignment_new`, `assignment_updated`, etc.
- `title`, `message`, `target_type`, `target_id`
- `is_read`: Read status

**PermissionAuditLog** (`dashboards.PermissionAuditLog`)
- Tracks all permission-related changes (shares, access updates, etc.)

---

## Frontend Reference

### State Management (Zustand)

| Store          | File                   | Purpose                              |
|----------------|------------------------|--------------------------------------|
| `authStore`    | `store/authStore.ts`   | JWT token, user profile, login/logout|
| `dashboardStore`| `store/dashboardStore.ts` | Pages, widgets, filters, layout    |
| `themeStore`   | `store/themeStore.ts`  | Dark/light mode (persisted)          |

### Chart Types (17)

| Type         | Description                    |
|--------------|--------------------------------|
| `bar`        | Bar chart (vertical)           |
| `stacked_bar`| Stacked bar chart              |
| `line`       | Line chart                     |
| `area`       | Area chart                     |
| `pie`        | Pie chart                      |
| `donut`      | Donut chart                    |
| `scatter`    | Scatter plot                   |
| `gauge`      | Gauge / speedometer            |
| `table`      | Data table with drill-down     |
| `kpi`        | KPI card (single number)       |
| `heatmap`    | Heatmap matrix                 |
| `treemap`    | Treemap (hierarchical rectangles) |
| `sankey`     | Sankey flow diagram            |
| `funnel`     | Funnel / conversion chart      |
| `radar`      | Radar / spider chart           |
| `graph`      | Network / relationship graph   |
| `map`        | Geographic map (GeoJSON)       |

### Routes

| Path                 | Component             | Auth    |
|----------------------|-----------------------|---------|
| `/login`             | LoginPage             | Public  |
| `/dashboards`        | DashboardListPage     | Private |
| `/dashboards/:id`    | DashboardBuilderPage  | Private |
| `/data/upload`       | DataUploadPage        | Private |
| `/admin/users`       | AdminSettingsPage     | Admin   |
| `/admin/assignments` | DashboardAssignPage   | Admin   |
| `/admin/org`         | OrganizationPage      | Admin   |
| `/org-chart`         | OrgChartPage          | Private |

---

## Key Features

### 1. Multi-Page Dashboards
- Create dashboards with multiple pages
- Drag-and-drop page reordering
- Page duplicate, export/import (JSON)
- Per-page access control by role

### 2. 17 Chart Types with ECharts
- Full ECharts integration with RTL support
- Rich configuration (colors, palettes, legends)
- Click-to-filter across charts
- Drill-down support in tables

### 3. Looker Studio-Style Filters
- Dashboard-level and page-level filter controls
- 5 control types: dropdown, date range, text search, checkbox, slider
- Auto-populated from dataset columns
- Per-filter role-based access control

### 4. Role-Based Access Control
- 4 roles: CEO, Admin, Finance, Sales
- Dashboard-level, page-level, and filter-level permissions
- Row-level data filtering via assignments
- Assignment system with data_filters and visible_pages

### 5. Organization Hierarchy
- Company → Division → Team structure
- Org chart visualization with expand/collapse
- Users linked to org units
- Bulk dashboard assignment by team/division
- Auto-assignment when users join org units

### 6. Notification System
- Real-time bell icon with unread count badge
- Notifications for assignment create/update
- Mark as read / mark all as read
- 30-second polling

### 7. Dark Theme
- System-wide dark mode toggle
- Persisted in localStorage
- Applied via TailwindCSS `dark:` classes
- Synced on app load

### 8. Dashboard Templates
- Pre-built templates: Sales, Finance, Marketing, HR, Retail, Blank
- One-click dashboard creation from templates
- Auto-created pages and widgets

### 9. Data Upload & Query
- Excel (.xlsx, .xls) and CSV upload
- Automatic column detection and type inference
- SQL-like query API with GROUP BY, aggregation, filters
- Row-level security via assignment data_filters

### 10. Permission Audit Log
- Tracks all permission changes (shares, access updates, filter changes)
- Viewable in admin panel with expandable details

---

## Data Model (ERD Summary)

```
User ──┬── company ──── Company
       ├── division ─── Division ── company
       ├── team ─────── Team ────── division
       ├── reports_to ── User (self)
       │
       ├── dashboards (owner) ── Dashboard
       ├── dashboard_assignments ── DashboardAssignment
       ├── managed_divisions ── Division
       ├── managed_teams ── Team
       └── notifications ── Notification

Dashboard ──┬── pages ──── DashboardPage ── widgets ── Widget
             ├── widgets ── Widget ── dataset ── Dataset
             └── assignments ── DashboardAssignment ── assigned_to → User

PermissionAuditLog ── user → User
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/login/` — Login (returns JWT)
- `POST /api/v1/auth/register/` — Register
- `GET  /api/v1/auth/profile/` — Current user profile
- `PUT  /api/v1/auth/profile/update/` — Update profile

### Users
- `GET  /api/v1/auth/users/` — List users (admin)
- `POST /api/v1/auth/users/` — Create user (admin)
- `GET  /api/v1/auth/users/:id/` — Get user
- `PUT  /api/v1/auth/users/:id/` — Update user (admin)
- `DELETE /api/v1/auth/users/:id/` — Delete user (admin)

### Organizations
- `GET/POST /api/v1/auth/companies/` — List/create companies
- `GET/PUT/DELETE /api/v1/auth/companies/:id/` — Company CRUD
- `GET/POST /api/v1/auth/divisions/` — List/create divisions
- `GET/PUT/DELETE /api/v1/auth/divisions/:id/` — Division CRUD
- `GET/POST /api/v1/auth/teams/` — List/create teams
- `GET/PUT/DELETE /api/v1/auth/teams/:id/` — Team CRUD
- `GET /api/v1/auth/org-tree/` — Full org tree (admin)

### Dashboards
- `GET/POST /api/v1/dashboards/` — List/create dashboards
- `GET/PUT/DELETE /api/v1/dashboards/:id/` — Dashboard CRUD
- `PUT /api/v1/dashboards/:id/layout/` — Update grid layout
- `PUT /api/v1/dashboards/:id/filter-controls/` — Update filter controls
- `POST /api/v1/dashboards/:id/duplicate/` — Duplicate dashboard
- `PUT /api/v1/dashboards/:id/share/` — Share with roles
- `POST /api/v1/dashboards/create-from-template/` — Create from template
- `GET /api/v1/dashboards/templates/` — List templates
- `DELETE /api/v1/dashboards/clear-all/` — Clear all (superuser)

### Pages
- `POST /api/v1/dashboards/:dash_id/pages/` — Create page
- `GET/PUT/DELETE /api/v1/dashboards/:dash_id/pages/:page_id/` — Page CRUD
- `POST /api/v1/dashboards/:dash_id/pages/:page_id/duplicate/` — Duplicate
- `PUT /api/v1/dashboards/:dash_id/pages/reorder/` — Reorder pages
- `GET /api/v1/dashboards/:dash_id/pages/:page_id/export/` — Export JSON
- `POST /api/v1/dashboards/:dash_id/pages/import/` — Import JSON

### Widgets
- `POST /api/v1/dashboards/:dash_id/widgets/` — Create widget
- `GET/PUT/DELETE /api/v1/dashboards/:dash_id/widgets/:widget_id/` — Widget CRUD

### Assignments
- `GET/POST /api/v1/dashboards/assignments/` — List/create assignments
- `GET/PUT/DELETE /api/v1/dashboards/assignments/:id/` — Assignment CRUD
- `GET /api/v1/dashboards/my-assigned/` — My assigned dashboards
- `POST /api/v1/dashboards/assignments/bulk/` — Bulk assign to team/division

### Notifications
- `GET /api/v1/dashboards/notifications/` — List notifications
- `POST /api/v1/dashboards/notifications/:id/read/` — Mark as read
- `POST /api/v1/dashboards/notifications/read-all/` — Mark all as read

### Audit Log
- `GET /api/v1/dashboards/audit-log/` — List audit entries (admin)

### Datasets
- `GET /api/v1/datasets/` — List datasets
- `POST /api/v1/datasets/upload/` — Upload Excel/CSV
- `GET /api/v1/datasets/:id/` — Dataset details
- `POST /api/v1/datasets/:id/query/` — Query data (with metrics, filters, GROUP BY)
- `DELETE /api/v1/datasets/:id/` — Delete dataset

---

## Role-Based Access Control

### Permission Matrix

| Action                    | CEO | Admin | Finance | Sales |
|---------------------------|-----|-------|---------|-------|
| View all dashboards       | ✅  | ✅    | ❌      | ❌    |
| View role-based dashboards| ✅  | ✅    | ✅      | ✅    |
| Create dashboards         | ✅  | ✅    | ✅      | ✅    |
| Delete dashboards         | ✅  | ✅    | Own     | Own   |
| Share dashboards          | ✅  | ✅    | Own     | ❌    |
| Create assignments        | ✅  | ✅    | Own     | ❌    |
| Bulk assign               | ✅  | ✅    | ❌      | ❌    |
| Manage users              | ✅  | ✅    | ❌      | ❌    |
| Manage org structure      | ✅  | ✅    | ❌      | ❌    |
| View audit log            | ✅  | ✅    | ❌      | ❌    |
| Clear all data            | ✅* | ✅*   | ❌      | ❌    |

*Superuser (is_staff) only

### Row-Level Security
- Dashboard assignments can include `data_filters` (e.g., `{col: "region", op: "eq", val: "Tehran"}`)
- Filters are enforced server-side in `dataset_query`
- Only applied when the dataset is used by a widget in the assigned dashboard

### Page-Level Access
- Each page can have `allowed_roles` restricting which roles can see it
- Empty `allowed_roles` = all roles allowed

### Filter-Level Access
- Each filter control can have `allowedRoles` restricting who can see/use it
- Server-side enforcement in `dataset_query` for filter controls with role restrictions

---

## Dark Theme

- Toggle via `ThemeToggle` component in navigation headers
- State persisted in `localStorage` via `zustand/persist`
- Applied by adding `dark` class to `<html>` element
- Uses TailwindCSS `dark:` variant for all component styling
- Chart tooltip styles adapt to dark mode

---

## Deployment

### Docker Compose
```bash
docker-compose up --build
```

### Environment Variables
```env
# Backend
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/nexivo
CELERY_BROKER_URL=redis://localhost:6379/0

# Frontend (VITE_)
VITE_API_URL=http://localhost:8000/api/v1
```

### Production Checklist
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure proper `DATABASE_URL`
- [ ] Set `DJANGO_SECRET_KEY`
- [ ] Configure CORS origins
- [ ] Set up SSL/TLS
- [ ] Configure nginx reverse proxy (see `frontend/nginx.conf`)

---

## Contributing

### Code Style
- **Backend**: Django conventions, PEP 8, type hints where practical
- **Frontend**: TypeScript strict mode, functional components, TailwindCSS utility classes
- **RTL**: All UI text in Persian (Farsi), `dir="rtl"` on root containers
- **Naming**: Backend snake_case, frontend camelCase

### Git Conventions
- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code refactoring
- `docs:` — Documentation

### Running Tests
```bash
cd backend
python manage.py test

cd frontend
npx tsc --noEmit          # Type check
npx vitest run            # Unit tests
```

---

*Built for Nexivo BI Platform — June 2026*
