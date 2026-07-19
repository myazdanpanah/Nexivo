# AI_AGENT_IMPLEMENTATION_GUIDE.md

Enterprise ERP

AI Development Guide

Version

1.0

Status

READY FOR IMPLEMENTATION

Supported AI Agents

- OpenAI Codex
- ChatGPT (GPT-5.x)
- Claude Code
- Cursor AI
- GitHub Copilot
- Gemini Code Assist
- JetBrains AI Assistant

---

# 1. Purpose

This document defines the rules every AI development agent must follow while contributing to the ERP.

Goals

- Prevent architectural drift
- Ensure consistency
- Reduce hallucinations
- Standardize generated code
- Protect business logic
- Keep the codebase maintainable

These rules override default AI behavior whenever a conflict exists.

---

# 2. Primary Principles

Every generated change must satisfy the following principles:

Correctness

Consistency

Readability

Maintainability

Security

Scalability

Performance

Testability

Documentation

Enterprise Readiness

Never optimize for short code at the expense of clarity.

---

# 3. Source of Truth

The AI agent must treat the following documents as authoritative, in this order:

1. MASTER_ARCHITECTURE.md
2. DATABASE_SCHEMA.md
3. WORKFLOW_ENGINE.md
4. API_SPECIFICATION.md
5. DJANGO_BACKEND.md
6. REPORT_ENGINE.md
7. IMPLEMENTATION_ROADMAP.md
8. Module Documentation
9. UI_UX_GUIDELINES.md

If documentation conflicts, stop implementation and request clarification rather than inventing behavior.

---

# 4. Forbidden Behaviors

The AI agent MUST NOT:

Invent business rules

Skip validation

Ignore workflow states

Duplicate business logic

Access the database directly from the frontend

Place business logic inside React components

Bypass permission checks

Bypass audit logging

Bypass workflow approval

Ignore multi-company isolation

Ignore multi-branch isolation

Use hardcoded IDs

Create undocumented APIs

Generate hidden side effects

Assume financial calculations

Guess tax rules

Delete financial records

Generate code that contradicts project documentation

---

# 5. Required Development Order

Always implement features in this sequence:

Database Model

↓

Migration

↓

Repository / Query Layer

↓

Domain Service

↓

Workflow Integration

↓

REST API

↓

Serializer / DTO

↓

Permissions

↓

Tests

↓

Frontend

↓

Documentation

Skipping steps is prohibited.

---

# 6. Architecture Rules

Business logic belongs only inside Domain Services.

Views

Responsibilities

- Receive request
- Validate request
- Call service
- Return response

Views must never contain:

Calculations

Financial rules

Workflow logic

Inventory logic

Tax logic

Approval logic

---

# 7. Database Rules

Models

- One responsibility per model
- Soft delete where applicable
- UUID primary keys
- Audit fields on every entity
- Company isolation
- Branch isolation

Never:

Use raw SQL unless explicitly justified

Duplicate entity definitions

Store derived values unnecessarily

Break referential integrity

---

# 8. API Rules

All APIs must follow API_SPECIFICATION.md.

Requirements

RESTful

Versioned

JWT protected

Permission checked

Documented

OpenAPI compatible

Consistent error responses

Every endpoint must be idempotent where business operations require it.

---

# 9. Workflow Rules

Every business document must integrate with the Workflow Engine.

Examples

Purchase Order

Sales Invoice

Payment Voucher

Production Order

Warranty Claim

Service Ticket

The AI agent must never implement ad-hoc approval logic.

Only the Workflow Engine controls state transitions.

---

# 10. Accounting Rules

The Accounting module is authoritative.

Other modules may request accounting operations.

They must never create journal entries directly.

Only the Accounting Service may:

Post journals

Reverse journals

Close periods

Calculate balances

Financial integrity takes precedence over convenience.
---

# 11. Python Coding Standards

Target Version

Python 3.12+

General Rules

- Follow PEP 8
- Use type hints for all public functions
- Prefer dataclasses only for DTOs/value objects
- Keep functions focused on a single responsibility
- Avoid global mutable state

Naming

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

Modules

snake_case

Never abbreviate domain concepts.

Example

Good

customer_invoice_service.py

Bad

cis.py

---

# 12. Django Standards

Project Structure

apps/

common/

config/

services/

tests/

Every application contains

models.py

services.py

selectors.py

serializers.py

views.py

urls.py

permissions.py

validators.py

signals.py

tasks.py

tests/

Business rules belong in services.py.

Database queries intended for reuse belong in selectors.py.

---

# 13. React Standards

Target Stack

React

TypeScript

Vite

shadcn/ui

Tailwind CSS

TanStack Query

TanStack Table

React Hook Form

Rules

Components must be:

Small

Reusable

Typed

Composable

Presentation components must never perform business calculations.

Pages orchestrate components.

Components never call APIs directly.

All API access goes through dedicated service hooks.

---

# 14. UI Component Rules

Preferred Order

Primitive Components

↓

Shared Components

↓

Business Components

↓

Pages

Never duplicate UI components.

Favor composition over inheritance.

Use shadcn/ui as the default design system.

Custom components should extend existing primitives instead of replacing them.

---

# 15. State Management

Hierarchy

Server State

↓

TanStack Query

↓

Local UI State

↓

React State

↓

Context (only when justified)

Global state libraries should be introduced only when a clear cross-cutting requirement exists.

Business state must remain on the backend.

---

# 16. Testing Standards

Every feature requires tests.

Required Test Types

Unit Tests

Integration Tests

API Tests

Workflow Tests

Permission Tests

Regression Tests

Critical financial workflows additionally require end-to-end validation.

Tests must be deterministic.

No flaky tests.

---

# 17. Performance Rules

Backend

Avoid N+1 queries.

Use

select_related()

prefetch_related()

Pagination is mandatory for list endpoints.

Large exports execute asynchronously.

Frontend

Lazy loading

Code splitting

Virtualized tables

Memoization only when justified by profiling.

Performance optimizations must be measurable.

---

# 18. Security Rules

Always validate:

Authentication

Authorization

Company Context

Branch Context

Workflow Permission

Input Data

Output Serialization

Never trust client input.

Never expose internal exceptions.

Never return stack traces.

Secrets must never be stored in source code.

---

# 19. Logging Rules

Log

Authentication Events

Permission Failures

Workflow Transitions

Accounting Posts

Inventory Adjustments

Errors

Warnings

Performance Metrics

Never log:

Passwords

Access Tokens

Refresh Tokens

Sensitive personal information

Credit card data

Logs should support troubleshooting without exposing confidential information.

---

# 20. Documentation Rules

Every implemented feature requires:

API Documentation

Code Docstrings (where appropriate)

Architecture Notes (if behavior changes)

Migration Notes (when schema changes)

Update the relevant Markdown documents when implementation changes architectural behavior.

Documentation is part of the feature—not an afterthought.
---

# 21. Git Workflow

All development follows a controlled Git workflow.

Primary Branches

main

Production-ready code.

develop

Primary integration branch.

Feature Branches

feature/<module-name>

Examples

feature/accounting

feature/workflow

feature/inventory

Bug Fixes

bugfix/<issue-name>

Hot Fixes

hotfix/<issue-name>

Direct commits to `main` are prohibited.

---

# 22. Commit Standards

Commit messages should follow a consistent format.

Format

<type>: <short description>

Examples

feat: add inventory reservation service

fix: resolve journal posting validation

refactor: simplify workflow transition engine

docs: update API specification

test: add manufacturing integration tests

Supported Types

feat

fix

refactor

docs

test

perf

build

ci

style

chore

Commits should be small and focused.

---

# 23. Pull Request Requirements

Every Pull Request must include:

- Clear description
- Related issue or task
- Architectural impact
- Database migration impact
- API impact
- Testing evidence
- Screenshots (for UI changes)

Required Checks

✓ CI passes

✓ Tests pass

✓ Documentation updated

✓ Code review completed

✓ Security review completed (when applicable)

---

# 24. AI Prompt Template

Before generating code, the AI agent should internally verify:

Context

- Target module
- Related documentation
- Existing architecture

Constraints

- Multi-company
- Multi-branch
- Workflow integration
- Audit logging
- API standards

Deliverables

- Database changes
- Services
- APIs
- Tests
- Documentation

If any required context is missing, request clarification instead of guessing.

---

# 25. Hallucination Prevention Rules

When uncertain, the AI agent must:

Stop implementation.

Identify the ambiguity.

Reference the relevant documentation.

Request clarification.

The AI must never:

Invent database fields.

Invent API endpoints.

Invent workflow states.

Invent accounting rules.

Invent tax calculations.

Invent permission models.

Correctness is always preferred over speed.

---

# 26. Code Review Checklist

Review every change for:

Architecture

Business Logic

Security

Performance

Workflow Integration

Accounting Integrity

Database Consistency

API Consistency

Documentation

Testing

No change is approved until every applicable item passes review.

---

# 27. Definition of Done

A feature is complete only when:

✓ Database migration created

✓ Models implemented

✓ Services implemented

✓ Permissions implemented

✓ Workflow integrated

✓ APIs implemented

✓ OpenAPI updated

✓ Unit tests passing

✓ Integration tests passing

✓ Documentation updated

✓ Code reviewed

✓ Ready for deployment

Partial implementation is not considered complete.

---

# 28. Quality Gates

Every module must satisfy:

Architecture Gate

Business Logic Gate

Security Gate

Performance Gate

Testing Gate

Documentation Gate

Deployment Gate

Failure in any gate blocks release.

---

# 29. Enterprise Development Principles

Every generated solution must be:

Deterministic

Predictable

Auditable

Secure

Maintainable

Reusable

Scalable

Loosely Coupled

Configuration Driven

Event Driven

The AI agent must optimize for long-term maintainability rather than minimal code size.

---

# 30. Final AI Rules

The AI agent shall:

Respect all project documentation.

Preserve architectural boundaries.

Generate readable code.

Avoid unnecessary abstractions.

Prefer explicit behavior over implicit behavior.

Write tests for every business feature.

Keep APIs consistent.

Protect financial integrity.

Protect workflow integrity.

Protect audit integrity.

Never trade correctness for convenience.

---

# Enterprise AI Readiness Checklist

Before completing any implementation:

✓ Documentation reviewed

✓ Architecture validated

✓ Dependencies identified

✓ Business rules respected

✓ Workflow integrated

✓ Accounting integration verified

✓ Permissions enforced

✓ Audit logging enabled

✓ Tests passing

✓ Documentation updated

✓ No contradictions introduced

---

# Final Statement

This ERP is designed to be developed collaboratively by humans and AI agents.

AI is an implementation assistant—not the system architect.

All architectural decisions originate from the official documentation.

When documentation and generated assumptions conflict, documentation always prevails.

---

# Document Status

Document:
AI_AGENT_IMPLEMENTATION_GUIDE.md

Version:
1.0

Status:
READY FOR IMPLEMENTATION

Target:
AI-Assisted Enterprise ERP Development

Supported AI Agents:

OpenAI Codex

ChatGPT

Claude Code

Cursor AI

GitHub Copilot

Gemini Code Assist

JetBrains AI Assistant

Compliance:

Enterprise AI Development Standard