# Database Manager Module — Design Spec

**Date**: 2026-06-28
**Status**: Draft
**Scope**: New `apps/db_manager` Django app + React frontend pages for managing Nexivo datasets, external PostgreSQL databases, file imports, and Google Sheets sync.

## Overview

Add a dedicated Database Manager module to the Nexivo BI platform. This module enables:

- **Inline cell editing** of any Nexivo dataset table or external PostgreSQL table via AG Grid
- **Schema changes**: add, rename, drop columns; change data types
- **File-based updates**: import XLSX, XLS, CSV with replace/append/upsert modes
- **SQL query editor**: read/write SQL for admin/CEO users with safety guardrails
- **External PostgreSQL connections**: configure and connect to remote databases
- **Google Sheets sync**: scheduled pull from Google Sheets into PostgreSQL tables
- **Role-based access**: admins get full access; a new "updater" role gets limited access to assigned tables

## Approach

Monolithic `apps/db_manager` Django app. Single new app keeps concerns separate from the existing `datasets` app while avoiding over-splitting. Follows existing Nexivo patterns: DRF views, Celery for async tasks, session/JWT auth, dark-themed React + Tailwind frontend.

## Data Models

### `ExternalDatabase`

Stores connection credentials for external PostgreSQL databases.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField(255) | Human-readable name |
| `host` | CharField(255) | PostgreSQL host |
| `port` | IntegerField(default=5432) | PostgreSQL port |
| `database` | CharField(255) | Database name |
| `username` | EncryptedCharField | Encrypted at rest |
| `password` | EncryptedCharField | Encrypted at rest |
| `is_active` | BooleanField(default=True) | Enable/disable |
| `owner` | FK(User) | Creator |
| `created_at` | DateTimeField(auto_now_add) | Timestamp |

### `DatabasePermission`

Grants "updater" role users access to specific tables.

| Field | Type | Details |
|-------|------|---------|
| `user` | FK(User) | The updater user |
| `database_source` | CharField(100) | `"local"` or `"external_<id>"` |
| `table_name` | CharField(255) | Table name or `"*"` for all |
| `can_edit` | BooleanField(default=True) | Can modify data |
| `can_schema` | BooleanField(default=False) | Can change columns/types |
| `can_import` | BooleanField(default=True) | Can upload files |
| `created_at` | DateTimeField(auto_now_add) | Timestamp |

### `GoogleSheetsSync`

Google Sheets scheduled sync configuration.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField(255) | Human-readable name |
| `spreadsheet_id` | CharField(100) | Google Sheets spreadsheet ID |
| `sheet_name` | CharField(255) | Tab/sheet name |
| `database_source` | CharField(100) | `"local"` or `"external_<id>"` |
| `table_name` | CharField(255) | Target PG table name |
| `sync_mode` | CharField(20) | `"replace"` or `"upsert"` |
| `key_column` | CharField(255, blank=True) | For upsert mode, match column |
| `schedule` | CharField(100) | Celery cron expression |
| `is_active` | BooleanField(default=True) | Enable/disable |
| `last_sync_at` | DateTimeField(null=True) | Last successful sync |
| `last_sync_status` | CharField(20, default="pending") | `"success"`, `"error"`, `"pending"` |
| `last_error` | TextField(blank=True) | Last error message |
| `owner` | FK(User) | Who configured it |
| `credentials_json` | JSONField(encrypted) | Google Service Account credentials |

## Backend Architecture

### Directory Structure

```
apps/db_manager/
├── __init__.py
├── apps.py
├── models.py
├── urls.py
├── views.py
├── serializers.py
├── services/
│   ├── __init__.py
│   ├── connection.py       # Get DB connections (local or external)
│   ├── table_ops.py        # List tables, get schema, browse data, count rows
│   ├── cell_editor.py      # Inline cell updates (single and batch)
│   ├── schema_editor.py    # Add/rename/drop columns, change types
│   ├── file_import.py      # Import XLSX/XLS/CSV with replace/append/upsert
│   ├── sql_executor.py     # Execute raw SQL with safety checks
│   └── sheets_sync.py      # Google Sheets pull and sync logic
├── tasks.py                # Celery tasks for Google Sheets sync
└── permissions.py          # Custom DRF permissions (admin vs updater)
```

### API Endpoints

**Database Management:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/db-manager/databases/` | List Nexivo datasets + external DBs |
| POST | `/api/v1/db-manager/databases/` | Add external DB connection |
| GET | `/api/v1/db-manager/databases/<id>/` | Get connection details |
| PUT | `/api/v1/db-manager/databases/<id>/` | Update connection |
| DELETE | `/api/v1/db-manager/databases/<id>/` | Remove connection |
| POST | `/api/v1/db-manager/databases/<id>/test/` | Test connection |

**Table Operations:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/db-manager/databases/<source>/tables/` | List tables in a database |
| GET | `/api/v1/db-manager/tables/<source>/<table>/schema/` | Get column names/types |
| GET | `/api/v1/db-manager/tables/<source>/<table>/data/` | Browse rows (paginated) |
| GET | `/api/v1/db-manager/tables/<source>/<table>/count/` | Row count |

**Cell Editing:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| PATCH | `/api/v1/db-manager/tables/<source>/<table>/cell/` | Update single cell |
| PATCH | `/api/v1/db-manager/tables/<source>/<table>/batch/` | Batch update cells |
| POST | `/api/v1/db-manager/tables/<source>/<table>/rows/` | Insert row |
| DELETE | `/api/v1/db-manager/tables/<source>/<table>/rows/` | Delete rows (by filter) |

**Schema Editing:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/db-manager/tables/<source>/<table>/columns/` | Add column |
| PATCH | `/api/v1/db-manager/tables/<source>/<table>/columns/<name>/` | Rename or change type |
| DELETE | `/api/v1/db-manager/tables/<source>/<table>/columns/<name>/` | Drop column |

**File Import:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/db-manager/tables/<source>/<table>/import/` | Import file |
| POST | `/api/v1/db-manager/import/new/` | Import to new table |

**SQL Editor:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/db-manager/sql/` | Execute SQL query |

**Google Sheets Sync:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/db-manager/syncs/` | List sync configurations |
| POST | `/api/v1/db-manager/syncs/` | Create sync config |
| GET | `/api/v1/db-manager/syncs/<id>/` | Get sync details |
| PUT | `/api/v1/db-manager/syncs/<id>/` | Update sync config |
| DELETE | `/api/v1/db-manager/syncs/<id>/` | Delete sync config |
| POST | `/api/v1/db-manager/syncs/<id>/run/` | Trigger manual sync |

**Permissions Management:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/db-manager/permissions/` | List all permissions (admin only) |
| POST | `/api/v1/db-manager/permissions/` | Grant permission |
| DELETE | `/api/v1/db-manager/permissions/<id>/` | Revoke permission |

### Access Control

- **Admin/CEO**: Full access to all endpoints, all databases, SQL editor (DML allowed)
- **Updater role**: Access only to tables assigned via `DatabasePermission`. Can edit cells and import files. Cannot use SQL editor. Cannot manage external DB connections.
- `source` in URLs: `"local"` for Nexivo's PG database, `"external_<id>"` for external databases.

### External DB Connections

- Credentials encrypted at rest using Django's `SECRET_KEY` (via `cryptography` library — Fernet symmetric encryption)
- Connection pooling via `psycopg2` — connections opened per-request, closed after use
- Test connection endpoint validates credentials before saving

## Frontend Architecture

### New Pages

```
frontend/src/pages/
├── DatabaseManagerPage.tsx    # Landing — list of databases + tables
├── TableEditorPage.tsx        # AG Grid spreadsheet editor
├── SchemaEditorPage.tsx       # Column management UI
├── SqlEditorPage.tsx          # SQL query editor with results
├── FileImportPage.tsx         # File upload with mode selection
├── SheetsSyncPage.tsx         # Google Sheets sync config + status
└── ExternalDbPage.tsx         # External DB connection management
```

### New Components

```
frontend/src/components/dbManager/
├── DatabaseList.tsx           # Database/table tree or list
├── AgGridEditor.tsx           # AG Grid wrapper with editing
├── SqlEditor.tsx              # CodeMirror SQL editor
├── SqlResults.tsx              # SQL results display
├── ColumnManager.tsx          # Column CRUD interface
├── FileImportWizard.tsx       # Multi-step import wizard
├── SyncConfigCard.tsx         # Google Sheets sync card
├── ConnectionForm.tsx          # External DB form
└── ConnectionTest.tsx          # Connection test indicator
```

### New Dependencies

| Package | Purpose |
|---------|---------|
| `ag-grid-react` + `ag-grid-community` | Spreadsheet data grid with inline editing |
| `@uiw/react-codemirror` + `@codemirror/lang-sql` | SQL syntax highlighting |

### Route Structure

```
/db-manager                          → DatabaseManagerPage
/db-manager/table/:source/:table     → TableEditorPage
/db-manager/table/:source/:table/schema → SchemaEditorPage
/db-manager/table/:source/:table/import → FileImportPage
/db-manager/sql                     → SqlEditorPage
/db-manager/syncs                   → SheetsSyncPage
/db-manager/connections             → ExternalDbPage
```

### User Experience

1. Admin lands on `/db-manager` → sees all Nexivo datasets + external databases
2. Clicks a table → AG Grid editor with inline editing, sorting, filtering, pagination
3. Tabs for Schema, Import accessible from table view
4. SQL editor accessible from top nav
5. Updater sees only assigned tables, no SQL editor, no connection management

## Data Flow

### File Import (Replace / Append / Upsert)

```
User uploads file
  → Frontend validates type, previews rows
  → POST /import/ with { file, mode, key_column? }
  → Backend:
    1. Parse file (pandas + openpyxl — existing pattern)
    2. Validate columns match target schema
    3. Mode:
       - REPLACE: TRUNCATE + COPY
       - APPEND: COPY new rows
       - UPSERT: Temp table → INSERT ON CONFLICT DO UPDATE
    4. Return { rows_affected, warnings }
```

### Google Sheets Sync

```
Admin configures sync (spreadsheet URL → spreadsheet_id + sheet_name)
  → Stores Google Service Account credentials encrypted
  → Celery periodic task checks active syncs
  → sheets_sync.py:
    1. Auth with Google Sheets API (service account)
    2. Read sheet → DataFrame
    3. Mode:
       - REPLACE: TRUNCATE + COPY
       - UPSERT: Temp table → ON CONFLICT DO UPDATE
    4. Update last_sync_at, last_sync_status
  → On failure: retry 3x, then mark "error" and notify owner
```

### SQL Executor Safety

```
POST /sql/ with { source, sql }
  → Admin/CEO only
  → Parse:
    - Allow: SELECT, INSERT, UPDATE, DELETE, WITH
    - Block: DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
    - Block multi-statement unless explicitly allowed
  → Execute with timeout (default 30s)
  → SELECT → return { columns, data, row_count }
  → DML → return { rows_affected }
  → Blocked → 403
```

## Error Handling

| Scenario | Backend | Frontend |
|----------|---------|----------|
| External DB unreachable | 503 with message | Show reconnect, save draft |
| SQL timeout | 504 with message | Suggest simpler query |
| Invalid file format | 400 with column mismatch | Show error details |
| Permission denied | 403 | Hide restricted UI |
| Sync failure | Update status "error" | Red indicator + error message |
| Schema conflict on import | 400 with conflict details | Show expected vs actual columns |

## New Backend Dependencies

| Package | Purpose |
|---------|---------|
| `cryptography` | Fernet encryption for credentials |
| `google-api-python-client` | Google Sheets API |
| `google-auth` | Google service account auth |

## Out of Scope

- Writing back to Google Sheets (bi-directional sync)
- Managing non-PostgreSQL databases (MySQL, SQLite, etc.)
- Database creation/deletion
- User/database-level access control for external DBs (handled at the PG level)
- Visual query builder (drag-and-drop)
