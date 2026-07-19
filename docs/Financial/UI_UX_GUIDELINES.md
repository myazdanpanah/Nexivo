# UI_UX_GUIDELINES.md

Enterprise ERP

UI / UX Design Guidelines

Version

1.0

Status

READY FOR IMPLEMENTATION

Target Platform

React

TypeScript

shadcn/ui

Tailwind CSS

ECharts

TanStack Table

React Hook Form

Responsive Web

---

# 1. Purpose

This document defines the visual language, interaction patterns, layout rules, accessibility requirements, and user experience principles for the ERP.

Objectives

- Consistent user experience
- High productivity
- Low cognitive load
- Enterprise-grade usability
- Mobile responsiveness
- Accessibility compliance

---

# 2. Design Principles

The interface must be:

Simple

Predictable

Fast

Accessible

Consistent

Responsive

Keyboard Friendly

Professional

Every interaction should reduce user effort.

---

# 3. Design Philosophy

Primary inspiration

- Microsoft Dynamics 365
- SAP Fiori
- Linear
- Stripe Dashboard
- Notion
- shadcn/ui

Avoid unnecessary visual complexity.

Data clarity is more important than decoration.

---

# 4. Color System

Primary

Orange

#F16724

Secondary

Teal

#529E98

Neutral

Gray Scale

Semantic Colors

Success

Green

Warning

Amber

Danger

Red

Info

Blue

Dark mode and light mode must both be supported.

---

# 5. Typography

Primary Font

Inter

RTL Font

Vazirmatn

Fallback

System UI Fonts

Hierarchy

Display

Heading 1

Heading 2

Heading 3

Body

Caption

Mono

Typography scale must remain consistent throughout the application.

---

# 6. Layout

Desktop

Sidebar

Top Navigation

Content Area

Inspector Panel (optional)

Footer (minimal)

Mobile

Drawer Navigation

Top App Bar

Scrollable Content

Bottom Actions (when applicable)

---

# 7. Grid System

12-column responsive grid.

Spacing Scale

4 px

8 px

12 px

16 px

24 px

32 px

48 px

Avoid arbitrary spacing values.

---

# 8. Navigation

Primary

Sidebar

Secondary

Tabs

Breadcrumbs

Context Menu

Quick Search

Keyboard Palette

Navigation should never exceed three levels of depth.

---

# 9. Forms

Every form must provide:

Clear Labels

Helper Text

Inline Validation

Error Messages

Auto Save (where appropriate)

Keyboard Navigation

Required fields must be visually distinguishable.

---

# 10. Tables

Preferred Library

TanStack Table

Required Features

Sorting

Filtering

Pagination

Column Resize

Column Visibility

Sticky Header

Bulk Selection

Export

Virtualization for large datasets

Tables are the primary data interaction component.
---

# 11. Buttons

Button hierarchy communicates action importance.

Types

Primary

Secondary

Outline

Ghost

Link

Destructive

Sizes

Small

Medium

Large

Icon

Rules

- Only one Primary button per major section.
- Destructive actions require confirmation.
- Buttons must show a loading state during asynchronous operations.
- Disabled buttons should include an explanatory tooltip when appropriate.

---

# 12. Dialogs

Dialogs are used for focused tasks requiring user attention.

Types

Confirmation

Form

Information

Warning

Error

Rules

- Trap keyboard focus.
- Support Escape to close (unless unsafe).
- Close after successful completion.
- Avoid nested dialogs.

---

# 13. Drawers

Drawers are preferred for editing records without leaving context.

Use Cases

Create Record

Edit Record

Quick Details

Preview

Rules

- Width adapts to content.
- Preserve background context.
- Support keyboard navigation.
- Unsaved changes require confirmation before closing.

---

# 14. Cards

Cards group related information.

Examples

Customer Summary

Product Overview

Inventory KPI

Sales KPI

Service Ticket

Cards should have:

Header

Body

Optional Footer

Optional Actions

Cards should never contain excessive scrolling.

---

# 15. Dashboard Widgets

Every widget includes:

Title

Optional Description

Refresh Action

Export Action

Fullscreen Action

Loading State

Error State

Widgets must be independently refreshable.

---

# 16. Charts

Preferred Library

ECharts

Supported Charts

Line

Bar

Area

Stacked Bar

Pie

Donut

Treemap

Heatmap

Scatter

Gauge

Funnel

Waterfall

Timeline

Charts must provide:

Legend

Tooltip

Export

Fullscreen

Drill-down (when supported)

---

# 17. Notifications

Notification Types

Success

Information

Warning

Error

Rules

- Keep messages concise.
- Avoid blocking the user's workflow.
- Critical errors may require acknowledgment.
- Notification history should be available.

---

# 18. Loading States

Every asynchronous operation requires feedback.

Preferred Patterns

Skeleton Screens

Progress Bars

Spinner (only for short operations)

Progress Indicator

Avoid blank pages during loading.

---

# 19. Empty States

Every empty screen should include:

Clear Message

Reason

Suggested Action

Optional Illustration

Example

"No purchase orders found."

Action

"Create Purchase Order"

Empty states should guide users toward the next logical action.

---

# 20. Error States

Errors should be:

Human-readable

Actionable

Consistent

Example

Unable to post the invoice because the accounting period is closed.

Actions

View Details

Retry

Contact Administrator

Never expose stack traces or internal exception details.

---

# 21. Accessibility

Target Standard

WCAG 2.1 AA

Requirements

Keyboard Navigation

Screen Reader Support

Visible Focus Indicators

Semantic HTML

Color Contrast Compliance

ARIA Labels

Forms must remain usable without a mouse.

---

# 22. Keyboard Shortcuts

Examples

Ctrl + K

Global Search

Ctrl + S

Save

Ctrl + N

Create New

Esc

Close Dialog

Ctrl + /

Show Shortcuts

Shortcuts must be configurable where practical.

---

# 23. RTL / LTR Support

The interface must support both directions.

Requirements

Mirrored Layout

Correct Text Alignment

Localized Icons (where directional)

Mixed-language Compatibility

Switching direction must not require code changes.

---

# 24. Responsive Behavior

Breakpoints

Mobile

Tablet

Laptop

Desktop

Large Desktop

Rules

- Tables adapt to available space.
- Drawers resize responsively.
- Charts remain readable.
- Navigation collapses appropriately.
- Critical actions stay accessible.

---

# 25. Design Tokens

Centralized Tokens

Colors

Typography

Spacing

Radius

Border Width

Shadow

Animation Duration

Icons

Tokens are the single source of truth for visual styling.

---

# 26. Component Standards

All shared components should support:

Light Mode

Dark Mode

RTL

Accessibility

TypeScript Types

Theme Tokens

Reusable APIs

Components should be composable and avoid embedding business logic.
# 27. Standard Page Templates

Every page should follow one of the approved layouts.

## A. List Page

Structure

Page Header

↓

Toolbar

↓

Filters

↓

Data Table

↓

Pagination

↓

Bulk Actions

Used For

- Customers
- Products
- Suppliers
- Employees
- Warehouses

---

## B. Detail Page

Structure

Header

↓

Status Banner

↓

Tabs

↓

Information Panels

↓

Timeline

↓

Attachments

↓

Audit History

Used For

- Sales Orders
- Purchase Orders
- Production Orders
- Service Tickets

---

## C. Dashboard Page

Structure

Global Filters

↓

KPIs

↓

Charts

↓

Tables

↓

Recent Activity

↓

Quick Actions

---

## D. Wizard Page

Multi-step workflow

Progress Indicator

↓

Step Content

↓

Validation

↓

Navigation Buttons

Used For

- Company Setup
- Fiscal Year Setup
- Data Import
- Manufacturing Planning

---

# 28. Enterprise UX Patterns

The ERP should encourage efficient workflows.

Patterns

Progressive Disclosure

Contextual Actions

Inline Editing

Bulk Operations

Quick Preview

Quick Create

Smart Defaults

Autosave (where appropriate)

Undo (where safe)

The number of required clicks should be minimized without sacrificing clarity.

---

# 29. Workflow Screen Standards

Workflow-enabled documents display:

Current Status

Workflow Timeline

Current Approver

Next Step

Previous Decisions

Approval Comments

Pending Tasks

Workflow information should remain visible throughout the document lifecycle.

---

# 30. Data Entry Optimization

Forms should optimize for speed.

Guidelines

Logical field grouping

Automatic focus progression

Keyboard-first navigation

Default values

Autocomplete

Lookup dialogs

Recently used values

Barcode scanner support

Bulk paste support (where applicable)

Data entry should minimize repetitive manual work.

---

# 31. Search Experience

Global Search

Requirements

Fast

Keyboard Accessible

Fuzzy Matching

Recent Searches

Saved Searches

Search Categories

Customers

Products

Invoices

Purchase Orders

Employees

Service Tickets

Reports

Search results should open directly to the relevant record.

---

# 32. Internationalization (i18n)

Supported Languages

English

Persian (RTL)

Architecture

Externalized translation files

Locale-aware formatting

Localized numbers

Localized dates

Localized currencies

Switching languages must not require rebuilding the application.

---

# 33. Theme System

Supported Themes

Light

Dark

System Default

Brand themes may override:

Primary Color

Accent Color

Logo

Typography (where approved)

Theme changes should apply consistently across all components.

---

# 34. Branding Rules

Configurable Elements

Company Logo

Company Name

Primary Brand Color

Secondary Brand Color

Login Screen

Favicon

Email Templates

PDF Templates

Branding must be tenant-specific in multi-company deployments.

---

# 35. User Personalization

Users may configure:

Theme

Language

Dashboard Layout

Favorite Pages

Pinned Records

Table Columns

Density

Notification Preferences

Date Format

Time Zone

Personal settings must never affect other users.

---

# 36. Design QA Checklist

Every UI implementation must verify:

✓ Responsive layout

✓ Accessibility compliance

✓ Keyboard navigation

✓ RTL compatibility

✓ Dark mode

✓ Light mode

✓ Empty state

✓ Loading state

✓ Error state

✓ Success feedback

✓ Permission-based visibility

✓ Workflow integration

---

# 37. Definition of Done (UI)

A UI feature is complete only when:

✓ Fully responsive

✓ Accessible

✓ RTL compatible

✓ Dark mode supported

✓ Light mode supported

✓ Connected to production APIs

✓ Loading states implemented

✓ Error states implemented

✓ Empty states implemented

✓ Validation implemented

✓ Tested across supported browsers

✓ Matches design tokens

---

# 38. Enterprise UI Readiness Checklist

The UI layer is production-ready when:

✓ Shared component library completed

✓ Layout system completed

✓ Dashboard framework completed

✓ Form framework completed

✓ Table framework completed

✓ Theme system completed

✓ Internationalization completed

✓ Accessibility validated

✓ Performance optimized

✓ API integration completed

✓ Design QA passed

✓ User acceptance testing completed

---

# Final UI Principles

The ERP interface must always be:

Consistent

Predictable

Fast

Accessible

Responsive

Keyboard Friendly

Workflow Aware

Enterprise Ready

The interface should prioritize productivity over visual decoration.

Every screen should help users complete tasks with the fewest possible interactions while maintaining clarity and correctness.

---

# Document Status

Document:
UI_UX_GUIDELINES.md

Version:
1.0

Status:
READY FOR IMPLEMENTATION

Target Stack:

React

TypeScript

shadcn/ui

Tailwind CSS

TanStack Table

React Hook Form

ECharts

Compliance:

Enterprise UI & UX Design Standard