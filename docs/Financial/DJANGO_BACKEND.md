# DJANGO_BACKEND.md

# Enterprise ERP Backend Architecture

Version: 1.0
Status: READY FOR IMPLEMENTATION

---

# 1. Overview

This document defines the backend architecture for the Enterprise ERP platform.

Technology Stack:

- Python 3.13+
- Django 5.x
- Django REST Framework
- PostgreSQL 16+
- Redis
- Celery
- Docker
- Nginx
- JWT Authentication

Backend Philosophy:

- Domain Driven Design
- Modular Monolith
- Service Layer Pattern
- Repository Pattern
- Event Driven Architecture
- API First
- AI Friendly Architecture

---

# 2. High Level Architecture

                    Client Applications
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    React ERP         Mobile App        External APIs
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    Django REST API
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
 Authentication      Business Services    Workflow
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  Domain Applications
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
 Accounting       Manufacturing      Trading
 Inventory         CRM               Service Sales
 Service Mgmt      HR                Reporting
                           │
                    PostgreSQL Database
                           │
                 Redis + Celery Workers

---

# 3. Design Principles

Every business rule belongs to backend.

Frontend never performs business calculations.

Frontend never creates accounting entries.

Frontend never modifies stock directly.

Backend is the single source of truth.

---

# 4. Project Structure

erp/

    config/

    apps/

    core/

    shared/

    integrations/

    workers/

    api/

    scripts/

    tests/

---

# 5. Config

config/

contains:

settings/

development.py

production.py

testing.py

base.py

urls.py

asgi.py

wsgi.py

logging.py

security.py

---

# 6. Core Layer

core/

contains reusable infrastructure.

Modules:

authentication/

permissions/

audit/

events/

exceptions/

database/

storage/

notifications/

middleware/

logging/

cache/

utils/

validators/

---

# 7. Shared Layer

Contains reusable business components.

shared/

money/

tax/

workflow/

approval/

pagination/

filters/

serializers/

responses/

enums/

constants/

---

# 8. Applications

Every ERP module is an independent Django App.

apps/

accounting/

inventory/

manufacturing/

trading/

service_sales/

service_management/

crm/

hr/

purchasing/

warehouse/

dashboard/

reporting/

workflow/

attachments/

users/

companies/

branches/

---

# 9. Standard App Structure

Each app follows exactly the same layout.

accounting/

models/

services/

repositories/

serializers/

views/

permissions/

validators/

signals/

tasks/

selectors/

api/

urls.py

admin.py

apps.py

---

# 10. Responsibility Rules

models/

Only persistence.

No business logic.

services/

Contains all business rules.

repositories/

Database access only.

serializers/

Validation and serialization.

views/

Request handling.

selectors/

Read queries.

tasks/

Background jobs.

signals/

Very limited usage.
# 11. Enterprise Organization Architecture

The ERP is designed for enterprise environments where a single installation can manage multiple legal entities, branches, warehouses, and business units.

Hierarchy:

Platform
└── Company
    ├── Branch
    │   ├── Warehouse
    │   ├── Department
    │   └── Cost Center
    └── Business Unit

Rules:

- Every record belongs to one Company.
- Most operational records belong to one Branch.
- Users may belong to multiple Companies.
- Users may have different roles in different Companies.
- Company isolation is enforced by the backend.

---

# 12. Multi-Company Architecture

Entity:

Company

Fields:

- ID (UUID)
- Company Code
- Legal Name
- Trade Name
- Registration Number
- National ID
- Economic Code
- VAT Number
- Fiscal Year
- Currency
- Timezone
- Language
- Status

Relationships:

Company

├── Branches
├── Warehouses
├── Fiscal Years
├── Chart Of Accounts
├── Users
├── Customers
├── Suppliers
└── Documents

Rules:

- Company data must never leak across companies.
- Every business service validates Company ownership.
- Accounting journals are always company-specific.

---

# 13. Multi-Branch Architecture

Branch Entity

Fields:

- Branch Code
- Name
- Address
- Phone
- Manager
- Default Warehouse
- Active Status

Rules:

- Inventory belongs to a Branch.
- Cashboxes belong to a Branch.
- Production Orders belong to a Branch.
- Sales Orders belong to a Branch.
- Purchase Orders belong to a Branch.

Accounting may consolidate all branches into one Company ledger while preserving branch dimensions.

---

# 14. User Context

Every authenticated request automatically carries:

Current Company

Current Branch

Current Fiscal Year

Current User

Current Language

Current Timezone

No business service should receive these values from the frontend.

They are resolved by middleware.

Example:

request.context.company

request.context.branch

request.context.user

request.context.fiscal_year

---

# 15. Authentication

Supported methods:

- JWT Access Token
- JWT Refresh Token
- Session Authentication (Admin)
- API Token (System Integrations)

Future-ready:

- OAuth2
- OpenID Connect
- SSO
- LDAP / Active Directory

Access Token Lifetime:

15 minutes

Refresh Token:

7 days

Configurable per environment.

---

# 16. Authorization (RBAC)

Authorization uses Role-Based Access Control.

User

↓

Role

↓

Permission Set

↓

Business Action

Examples:

Accountant

Warehouse Operator

Sales Manager

Production Manager

HR Manager

Administrator

System Auditor

Permissions are evaluated in backend only.

Frontend visibility is derived from backend permissions.

---

# 17. Permission Model

Permission Format:

module.resource.action

Examples:

accounting.invoice.view

accounting.invoice.create

accounting.invoice.approve

inventory.stock.adjust

manufacturing.order.release

service_sales.booking.cancel

service_management.work_order.close

Rules:

Permissions are additive.

Explicit deny overrides allow.

Permissions may be scoped to:

- Company
- Branch
- Department
- Record Owner

---

# 18. Audit Trail

Every critical business operation creates an immutable audit record.

Audit Entity:

- User
- Company
- Branch
- Timestamp
- IP Address
- Entity Name
- Entity ID
- Action
- Old Value
- New Value

Tracked actions:

CREATE

UPDATE

DELETE

APPROVE

POST

CANCEL

LOGIN

EXPORT

Audit records cannot be edited through the application.

---

# 19. Soft Delete Policy

Business documents are never physically deleted.

Instead:

deleted_at

deleted_by

delete_reason

Records remain available for:

- Audit
- Reporting
- Legal compliance

Hard delete is reserved only for technical maintenance operations.

---

# 20. Event Bus

Business events are published internally.

Examples:

InvoiceCreated

InvoicePosted

CustomerCreated

StockReserved

StockReleased

PurchaseApproved

ProductionCompleted

TicketIssued

BookingCancelled

WarrantyActivated

Consumers:

- Notifications
- Workflow Engine
- Reporting
- AI Services
- Integrations
- Webhooks

Business modules communicate through events rather than directly whenever possible.

---

# 21. Transaction Management

Every business service executes inside a database transaction.

Rules:

- Either the entire operation succeeds.
- Or the entire operation rolls back.

Examples:

Sales Invoice

↓

Inventory Deduction

↓

Accounting Posting

↓

Commission Calculation

↓

Workflow Trigger

If any step fails:

Rollback everything.

Never allow partial business transactions.
---

# 22. Backend Layered Architecture

The backend follows a strict layered architecture.

Client

↓

APIView / ViewSet

↓

Serializer

↓

Application Service

↓

Domain Service

↓

Repository

↓

PostgreSQL

Responsibilities:

API Layer
- HTTP handling
- Authentication
- Permission checks
- Request parsing
- Response formatting

Application Service
- Business orchestration
- Transaction management
- Workflow execution
- Event publishing

Domain Service
- Core business rules
- Accounting calculations
- Inventory validation
- Tax validation
- Financial policies

Repository
- Database operations only

Model
- Persistence only

Business rules MUST NEVER exist inside Models.

---

# 23. Service Layer Pattern

Every business operation is implemented as a Service.

Examples:

CreateInvoiceService

ApproveInvoiceService

PostInvoiceService

CancelInvoiceService

CreatePurchaseOrderService

ReceiveGoodsService

ReserveInventoryService

ReleaseInventoryService

CompleteProductionService

IssueWarrantyService

CreateBookingService

CloseWorkOrderService

Rules:

Each service performs ONE business operation.

Services may call other services.

Views never perform business logic.

---

# 24. Repository Pattern

Repositories isolate database access.

Responsibilities:

- CRUD
- Query optimization
- Bulk operations
- Locking
- Pagination

Repositories MUST NOT:

- Calculate accounting
- Validate workflows
- Execute business policies

Example:

InvoiceRepository

CustomerRepository

InventoryRepository

JournalRepository

ProductionRepository

---

# 25. Selector Pattern

Selectors are read-only query services.

Purpose:

- Dashboard queries
- Reports
- Search
- Complex filters

Examples:

InvoiceSelector

SalesDashboardSelector

InventorySelector

CustomerSelector

JournalSelector

Selectors never modify data.

---

# 26. Validation Architecture

Validation occurs in multiple layers.

Layer 1

Serializer Validation

↓

Data format

↓

Required fields

↓

Type checking

Layer 2

Business Validation

↓

Company

↓

Fiscal Year

↓

Workflow State

↓

Permissions

↓

Business Rules

Layer 3

Database Constraints

↓

Unique

↓

Foreign Keys

↓

Indexes

Validation should fail as early as possible.

---

# 27. Exception Architecture

All exceptions inherit from ERPException.

ERPException

├── ValidationException
├── BusinessException
├── PermissionException
├── WorkflowException
├── InventoryException
├── AccountingException
├── TaxException
├── IntegrationException

Every exception contains:

- Error Code
- Human Message
- Developer Message
- Suggested Resolution

The API always returns a standardized error response.

---

# 28. Transaction Policy

Critical services execute inside atomic transactions.

Examples:

Sales Invoice

↓

Inventory Reservation

↓

Accounting Posting

↓

Commission Posting

↓

Workflow Transition

↓

Notification Event

If any step fails:

ROLLBACK EVERYTHING

Partial commits are prohibited.

---

# 29. Celery Background Jobs

Long-running tasks execute asynchronously.

Supported Jobs:

Invoice PDF Generation

Excel Export

Report Generation

Email Sending

SMS Sending

Inventory Recalculation

Accounting Rebuild

MRP Planning

Large Imports

AI Processing

OCR Processing

Background jobs must be idempotent.

---

# 30. Redis Usage

Redis is used for:

- Celery Broker
- Celery Result Backend
- Distributed Cache
- Session Cache
- Rate Limiting
- Temporary Locks
- OTP Storage
- API Cache

Redis is NOT a permanent datastore.

---

# 31. File Storage

Supported Storage Providers:

Local Storage

S3 Compatible Storage

MinIO

Azure Blob Storage

Google Cloud Storage

Every uploaded file stores:

- UUID
- Original Name
- MIME Type
- Size
- SHA256 Hash
- Owner
- Company
- Upload Time

Files are never referenced directly by filesystem path.

---

# 32. Notification Engine

Notification Channels:

- In-App Notification
- Email
- SMS
- Push Notification
- Webhook

Notification Events:

Invoice Approved

Purchase Approved

Low Inventory

Production Completed

Booking Confirmed

Warranty Expiring

SLA Violation

Notifications are event-driven.

---

# 33. Integration Layer

External systems connect only through the Integration Layer.

Supported Integrations:

Payment Gateways

Iranian Tax Systems

SMS Providers

Email Providers

Accounting APIs

Shipping Providers

Flight Reservation Systems

Hotel Reservation Systems

CRM Systems

ERP-to-ERP APIs

Integration Rules:

- Retry on transient failures.
- Log all requests/responses.
- Use circuit breakers.
- Never expose internal services directly.

---

# 34. Scheduled Jobs

Periodic Tasks:

Nightly Backup

Inventory Reconciliation

Accounting Consistency Check

Expired Session Cleanup

Token Cleanup

Reminder Notifications

Warranty Expiration Scan

Deferred Revenue Recognition

Database Statistics Update

Health Monitoring

Cron schedules are centralized and configurable.
---

# 35. API Architecture

All frontend applications communicate exclusively through REST APIs.

API Versioning:

/api/v1/

/api/v2/

Rules:

- Never expose database models directly.
- Every endpoint validates permissions.
- Every endpoint validates company context.
- Every endpoint returns standardized responses.

Standard Response:

{
    "success": true,
    "message": "",
    "data": {},
    "errors": [],
    "meta": {}
}

---

# 36. API Design Standards

Naming Convention:

GET

/api/v1/customers/

POST

/api/v1/customers/

GET

/api/v1/customers/{id}/

PATCH

/api/v1/customers/{id}/

DELETE

/api/v1/customers/{id}/

Nested Resources:

/customers/{id}/addresses/

/customers/{id}/contacts/

/products/{id}/inventory/

/production-orders/{id}/operations/

Bulk Operations:

/bulk-create/

/bulk-update/

/bulk-delete/

/bulk-export/

---

# 37. Pagination Standard

Supported Methods:

Page Number

Limit Offset

Cursor Pagination

Default Page Size:

25

Maximum:

500

Every paginated response includes:

count

next

previous

results

---

# 38. Filtering & Search

Supported Filters:

Exact

Contains

Starts With

Ends With

Date Range

Number Range

Boolean

Status

Company

Branch

Full-text Search

Ordering:

?ordering=name

?ordering=-created_at

Search:

?search=laptop

---

# 39. Caching Strategy

Cache Levels:

Level 1

Application Cache

↓

Level 2

Redis Cache

↓

Level 3

Database

Cache Targets:

Dashboard KPIs

Permission Matrix

Configuration

Tax Rules

Exchange Rates

Lookup Tables

Reference Data

Never Cache:

Financial Transactions

Inventory Balances

Accounting Journals

Workflow State

---

# 40. Security Standards

Passwords:

Argon2

HTTPS Only

HSTS Enabled

Secure Cookies

CSRF Protection

XSS Protection

SQL Injection Protection

Rate Limiting

Request Validation

Security Headers

Sensitive fields:

Never returned by API.

Secrets are stored only in environment variables.

---

# 41. Logging Strategy

Every request generates logs.

Levels:

DEBUG

INFO

WARNING

ERROR

CRITICAL

Business Logs:

Invoice Posted

Inventory Changed

Payment Registered

Production Completed

User Login

Role Changed

Approval Granted

Technical Logs:

SQL

Performance

API

Celery

Redis

Errors

---

# 42. Monitoring

Metrics:

API Response Time

Database Latency

Redis Usage

Celery Queue

Memory Usage

CPU Usage

Failed Jobs

Active Users

Background Tasks

Health Endpoint:

/health/

Returns:

Database

Redis

Storage

Celery

Application

Version

Status

---

# 43. Performance Optimization

Database:

Indexes

Composite Indexes

Partial Indexes

Connection Pooling

Bulk Inserts

Bulk Updates

select_related()

prefetch_related()

Caching

Async Processing

Pagination

Streaming Responses

Rules:

Never execute N+1 queries.

Never load unnecessary fields.

Always paginate large datasets.

---

# 44. Testing Strategy

Testing Pyramid:

Unit Tests

↓

Service Tests

↓

Repository Tests

↓

API Tests

↓

Integration Tests

↓

End-to-End Tests

Coverage Goal:

Minimum 90%

Critical Modules:

Accounting

Inventory

Manufacturing

Workflow

Require 100% service-level coverage.

---

# 45. Docker Architecture

Containers:

nginx

↓

frontend

↓

backend

↓

celery-worker

↓

celery-beat

↓

postgres

↓

redis

↓

minio

↓

monitoring

Each container is independently deployable.

---

# 46. Environment Variables

Required Variables:

SECRET_KEY

DATABASE_URL

REDIS_URL

JWT_SECRET

EMAIL_HOST

SMS_PROVIDER

STORAGE_PROVIDER

S3_BUCKET

MINIO_ENDPOINT

LOG_LEVEL

APP_ENV

No secrets are committed to Git.

---

# 47. Deployment Pipeline

Pipeline:

Git Push

↓

CI Validation

↓

Tests

↓

Static Analysis

↓

Docker Build

↓

Security Scan

↓

Migration

↓

Deployment

↓

Health Check

↓

Release

Deployment must support:

Blue/Green

Rolling Update

Rollback

Zero Downtime

---

# 48. Coding Standards

Mandatory:

PEP8

Type Hints

Docstrings

Black Formatter

isort

ruff

mypy

Import Rules:

Python Standard Library

↓

Third-party Packages

↓

Internal Packages

↓

Local Modules

Magic numbers are prohibited.

Business constants belong in shared/constants.

---

# 49. Production Readiness Checklist

Authentication

Authorization

Audit Trail

Transactions

Caching

Monitoring

Logging

Backups

Health Checks

Error Handling

Rate Limiting

Data Validation

Background Jobs

Security Headers

Disaster Recovery

All items must pass before production deployment.

---

# 50. Backend Completion Criteria

The backend architecture is considered complete when:

✓ Every ERP module follows the standard app structure.

✓ All business logic exists in services.

✓ Models contain no business logic.

✓ Multi-company isolation is enforced.

✓ RBAC is fully implemented.

✓ Audit logging covers all critical actions.

✓ APIs follow a unified standard.

✓ Transactions guarantee consistency.

✓ Background jobs are asynchronous.

✓ Monitoring and logging are enabled.

✓ Security standards are enforced.

✓ Deployment supports enterprise environments.

✓ The architecture can be implemented directly by human developers or AI coding agents without architectural assumptions.

---

# 51. Domain Events

Every important business action produces a Domain Event.

A Domain Event represents something that has already happened.

Examples:

InvoiceCreated

InvoiceApproved

InvoicePosted

PaymentReceived

CustomerCreated

SupplierCreated

PurchaseOrderApproved

GoodsReceived

InventoryReserved

InventoryAdjusted

ProductionStarted

ProductionCompleted

WorkOrderClosed

BookingConfirmed

BookingCancelled

WarrantyActivated

WarrantyExpired

Events must be immutable.

Events must contain enough information for downstream consumers.

---

# 52. Event Processing

Flow:

Business Service

↓

Commit Transaction

↓

Publish Domain Event

↓

Event Bus

↓

Subscribers

Subscribers may include:

Notification Engine

Workflow Engine

Audit Service

Reporting Engine

Integration Layer

AI Engine

Analytics

Events are processed asynchronously whenever possible.

---

# 53. Outbox Pattern

To guarantee consistency between the database and asynchronous messaging, the backend uses the Outbox Pattern.

Transaction:

Business Operation

↓

Database Commit

↓

Outbox Record

↓

Background Dispatcher

↓

Event Bus

Benefits:

- Prevents lost events
- Supports retries
- Guarantees eventual consistency
- Enables reliable integrations

Outbox records include:

- Event ID
- Event Type
- Aggregate ID
- Payload
- Created At
- Published At
- Retry Count
- Status

---

# 54. Idempotency

Critical operations must be idempotent.

Examples:

Payment Callback

Invoice Posting

Inventory Reservation

Booking Confirmation

External API Webhooks

Every idempotent request contains:

Idempotency-Key

Processing Rules:

- First request executes.
- Duplicate requests return the original result.
- No duplicated business transaction is created.

---

# 55. Distributed Locking

Certain business operations require distributed locking.

Examples:

Inventory Reservation

Invoice Number Generation

Production Scheduling

Seat Reservation

Warehouse Allocation

Redis Distributed Locks are used.

Rules:

Acquire Lock

↓

Execute Operation

↓

Commit

↓

Release Lock

Locks automatically expire.

Deadlocks must be avoided.

---

# 56. Database Locking Strategy

Use Optimistic Locking for:

- Customer Updates
- Product Updates
- Configuration Records

Use Pessimistic Locking for:

- Inventory
- Accounting Posting
- Financial Closing
- Production Allocation

Version fields are required where optimistic locking is used.

---

# 57. Database Migration Strategy

All schema changes are version controlled.

Rules:

- Never modify production tables manually.
- Every schema change uses Django Migrations.
- Every migration must be reversible when possible.
- Data migrations are isolated from schema migrations.

Migration Flow:

Create Migration

↓

Review

↓

Automated Tests

↓

Deploy

↓

Run Migration

↓

Verify

---

# 58. Feature Flags

New functionality is controlled using Feature Flags.

Examples:

Enable AI Assistant

Enable New Workflow

Enable Multi-Currency

Enable Beta Reports

Enable OCR

Enable Predictive Inventory

Feature Flags support:

- Global
- Company
- Branch
- User
- Percentage Rollout

This enables safe deployments without code changes.

---

# 59. Plugin Architecture

The ERP supports future plugin modules.

Plugin Requirements:

- Independent Django App
- Registered Manifest
- API Registration
- Permission Registration
- Menu Registration
- Migration Support

Plugin Manifest Example:

Name

Version

Dependencies

Permissions

Menu Items

API Routes

Plugins cannot modify Core modules directly.

All communication occurs through public services or events.

---

# 60. AI Integration Layer

AI services are isolated from business services.

Architecture:

Business Services

↓

AI Gateway

↓

LLM Provider

↓

AI Response

↓

Business Validation

↓

ERP Action

Supported AI Functions:

- Invoice Analysis
- OCR
- Financial Insights
- Inventory Forecasting
- Sales Forecasting
- Document Classification
- Report Summaries
- Workflow Suggestions

AI is advisory by default.

AI cannot directly execute financial operations without explicit authorization.

---

# 61. AI Safety Rules

The AI layer must never:

- Post accounting journals
- Delete financial records
- Modify inventory directly
- Bypass workflow approvals
- Override user permissions
- Access another company's data

Every AI-generated action must pass through the same validation pipeline as user-generated actions.

---

# 62. Internal Service Communication

Business modules communicate only through Services or Events.

Allowed:

Accounting Service
    ↓
Inventory Service

Manufacturing Service
    ↓
Workflow Service

Service Sales
    ↓
Accounting Service

Not Allowed:

Model → Model dependencies

Cross-module direct database updates

Raw SQL between modules

This preserves loose coupling.

---

# 63. Sequence Example — Sales Invoice

Customer Request

↓

API View

↓

Serializer Validation

↓

CreateInvoiceService

↓

Inventory Validation

↓

Tax Calculation

↓

Accounting Posting

↓

Workflow Initialization

↓

Audit Log

↓

Domain Event

↓

API Response

Every stage executes inside a transaction.

---

# 64. Sequence Example — Production Order

Production Request

↓

MRP Validation

↓

Capacity Check

↓

Material Reservation

↓

Production Order Creation

↓

Workflow

↓

Execution

↓

Finished Goods Receipt

↓

Accounting Posting

↓

Completion Event

---

# 65. Sequence Example — Service Booking

Customer Booking

↓

Availability Check

↓

Reservation

↓

Payment

↓

Booking Confirmation

↓

Supplier Notification

↓

Accounting Posting

↓

Revenue Recognition

↓

Completion Event

---

# 66. Code Quality Gates

Before any code is merged:

✓ Unit Tests Pass

✓ Integration Tests Pass

✓ Linting Passes

✓ Type Checking Passes

✓ Security Scan Passes

✓ Migration Review Complete

✓ API Documentation Updated

✓ Changelog Updated

Pull Requests cannot be merged if any mandatory quality gate fails.

---

# 67. Enterprise Readiness Checklist

The backend is Enterprise Ready when:

✓ Multi-Company supported

✓ Multi-Branch supported

✓ RBAC implemented

✓ Audit Trail enabled

✓ Event-Driven Architecture operational

✓ Background Workers operational

✓ Plugin System available

✓ AI Gateway integrated

✓ Monitoring enabled

✓ Health Checks operational

✓ Backup strategy documented

✓ Disaster Recovery documented

✓ API versioning enforced

✓ Production deployment automated

---

# Final Backend Principles

The ERP backend must be:

- Modular
- Predictable
- Testable
- Secure
- Event-Driven
- AI-Friendly
- Horizontally Scalable
- Maintainable
- Enterprise Ready

Every architectural decision should prioritize long-term maintainability over short-term implementation convenience.

---

# Document Status

Document:
DJANGO_BACKEND.md

Version:
1.0

Status:
READY FOR IMPLEMENTATION

Target Framework:
Django 5 + DRF + PostgreSQL + Redis + Celery

Compliance:
Enterprise ERP Architecture