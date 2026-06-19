# Contributing to Nexivo

Thank you for your interest in contributing to Nexivo! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style & Conventions](#code-style--conventions)
  - [Python / Django](#python--django)
  - [TypeScript / React](#typescript--react)
  - [Git Commit Messages](#git-commit-messages)
- [Project Architecture](#project-architecture)
- [Making Changes](#making-changes)
  - [Branch Naming](#branch-naming)
  - [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We are building a BI platform for the Persian-speaking community — we value inclusivity and collaboration.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Nexivo.git
   cd Nexivo
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/myazdanpanah/Nexivo.git
   ```
4. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker (optional, for running services)

### Quick Start (Linux/macOS)

```bash
# Start PostgreSQL and Redis
make start-services

# Install dependencies, migrate, seed
make setup

# Start backend and frontend in separate terminals
make backend   # http://localhost:8000
make frontend  # http://localhost:3000
```

### Quick Start (Windows)

```cmd
dev.bat start-services
dev.bat setup
dev.bat backend
dev.bat frontend
```

### Environment Variables

Copy `.env.example` to `backend/.env` and configure:

```bash
cp .env.example backend/.env
```

---

## Code Style & Conventions

### Python / Django

| Rule | Detail |
|---|---|
| **Formatter** | Follow PEP 8; keep lines under 100 characters |
| **Imports** | Standard library → third-party → local apps, separated by blank lines |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes |
| **Docstrings** | Use triple-double-quoted docstrings for all public functions, classes, and views |
| **Type Hints** | Use type hints where practical (function signatures, variable declarations) |
| **Models** | Always include `__str__`, `Meta.ordering`, and docstrings on model classes |
| **Serializers** | Name serializers after their model: `DatasetSerializer`, `DatasetUploadSerializer` |
| **Views** | Use function-based views with `@api_view` decorators (not class-based views) |
| **Tests** | One test method per behavior; use descriptive `test_<what>_<condition>` naming |
| **No raw SQL** | Always use parameterized queries (`%s` placeholders) — never string interpolation for SQL |

**Example:**

```python
# ✓ Good
@api_view(["POST"])
def dataset_upload(request):
    """Upload an Excel/CSV file and create a dataset."""
    serializer = DatasetUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # ...
```

```python
# ✗ Bad — no docstring, no type hints, inconsistent naming
@api_view(["POST"])
def uploadDataset(request):
    s = DatasetUploadSerializer(data=request.data)
    s.is_valid()
    # ...
```

### TypeScript / React

| Rule | Detail |
|---|---|
| **Formatting** | 2-space indentation, single quotes, no trailing commas |
| **Components** | Functional components with hooks; no class components |
| **Naming** | `PascalCase` for components, `camelCase` for functions/variables |
| **Props** | Always define TypeScript interfaces for component props |
| **State** | Use Zustand stores (`authStore.ts`, `dashboardStore.ts`) for shared state |
| **Styling** | Use Tailwind CSS utility classes; avoid inline styles except for dynamic values |
| **Imports** | Group: React → third-party → local components → local utils → types |
| **Icons** | Use `lucide-react` icons — not raw SVGs |
| **API calls** | Use the shared `api` client from `src/api/client.ts`; never hardcode URLs |
| **RTL** | The app uses `dir="rtl"`; add RTL-specific configs for charts when needed |

**Example:**

```tsx
// ✓ Good
interface ChartWidgetProps {
  widget: Widget
}

export default function ChartWidget({ widget }: ChartWidgetProps) {
  const [option, setOption] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <div className="bg-white rounded-2xl border border-gray-200">
      {/* ... */}
    </div>
  )
}
```

```tsx
// ✗ Bad — no prop types, inline styles, hardcoded URL
export default function ChartWidget({ widget }) {
  return <div style={{ backgroundColor: 'white', borderRadius: 16 }}>
    {/* ... */}
  </div>
}
```

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

**Types:**

| Type | When to Use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `test` | Adding or updating tests |
| `refactor` | Code refactoring (no feature/bug change) |
| `style` | Formatting, missing semicolons, etc. |
| `chore` | Build process, dependencies, CI config |
| `perf` | Performance improvements |

**Examples:**

```
feat: add CSV upload support to dataset parser
fix: prevent SQL injection in query endpoint
docs: add CONTRIBUTING.md and .env.example
test: add parser edge case tests for mixed types
refactor: clean up chart rendering logic
```

---

## Project Architecture

```
Nexivo/
├── backend/
│   ├── apps/
│   │   ├── accounts/    # Auth, JWT, RBAC, user management
│   │   ├── datasets/    # File upload → PostgreSQL pipeline
│   │   └── dashboards/  # Dashboard & widget CRUD
│   └── nexivo/          # Django project config
├── frontend/
│   └── src/
│       ├── api/         # Axios client with JWT interceptor
│       ├── components/  # ChartWidget, WidgetConfigPanel
│       ├── pages/       # Login, DashboardList, DashboardBuilder, DataUpload
│       ├── store/       # Zustand stores (auth, dashboard)
│       └── utils/       # Chart defaults, RTL config
├── superset_config.py   # Apache Superset configuration
└── docker-compose.yml   # Full stack orchestration
```

### Key Design Decisions

1. **Role-based access control (RBAC):** Users are assigned one of four roles (`admin`, `ceo`, `finance`, `sales`). Each dataset and dashboard has an `allowed_roles` field. CEO and Admin bypass role filters.

2. **Data upload pipeline:** Excel/CSV → pandas parsing → PostgreSQL table creation (via `COPY` for performance) → Dataset metadata stored in Django ORM.

3. **Query security:** All queries validate column names against the dataset schema before execution. Role-based `DataFilter` records are automatically applied.

4. **JWT authentication:** Stateless tokens with 24-hour expiry. The frontend Axios client attaches tokens via interceptor and handles 401 responses by logging out.

---

## Making Changes

### Branch Naming

| Prefix | Purpose | Example |
|---|---|---|
| `feat/` | New feature | `feat/csv-upload` |
| `fix/` | Bug fix | `fix/chart-loading-error` |
| `docs/` | Documentation | `docs/update-readme` |
| `test/` | Tests | `test/parser-edge-cases` |
| `refactor/` | Code cleanup | `refactor/chart-components` |

### Pull Request Process

1. **Ensure your branch is up to date** with `main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks** before submitting:
   ```bash
   make test-backend   # Django checks
   make test-frontend  # TypeScript type check
   ```

3. **Write a clear PR description** explaining:
   - What the change does and why
   - Any new dependencies added
   - Screenshots for UI changes
   - Related issue numbers (e.g., `Closes #42`)

4. **Request review** from at least one maintainer.

5. **Address feedback** promptly — push new commits to your branch, don't force-push during review.

---

## Testing

### Backend Tests

```bash
cd backend

# Run Django system checks
python manage.py check

# Run all tests
python manage.py test --verbosity=2

# Run tests for a specific app
python manage.py test apps.accounts --verbosity=2
python manage.py test apps.datasets --verbosity=2
```

**Test file locations:**

| App | Test Files |
|---|---|
| accounts | `tests.py` (login, JWT), `tests_commands.py` (create_dev_data) |
| datasets | `tests.py` (upload, query), `tests_parsers.py` (parsing, table creation) |
| dashboards | (no tests yet — contributions welcome!) |

### Frontend Type Checking

```bash
cd frontend
npx tsc --noEmit
```

### CI Pipeline

Every push and PR to `main` triggers GitHub Actions:

1. **Backend Tests** — PostgreSQL service container, Python 3.11, Django check + migrate + test
2. **Frontend Typecheck** — Node.js 20, TypeScript type checking

---

## Reporting Issues

When reporting a bug, please include:

1. **Steps to reproduce** the issue
2. **Expected behavior** vs. **actual behavior**
3. **Screenshots** if applicable
4. **Environment details** (OS, Python version, Node.js version, browser)
5. **Relevant logs** from browser console or Django server

For feature requests, describe:

1. The **problem** you're trying to solve
2. Your **proposed solution**
3. Any **alternatives** you considered

---

## Questions?

If you have questions about contributing, feel free to open a [Discussion](https://github.com/myazdanpanah/Nexivo/discussions) or reach out via the [Issues](https://github.com/myazdanpanah/Nexivo/issues) page.

Thank you for contributing to Nexivo! 🎉
