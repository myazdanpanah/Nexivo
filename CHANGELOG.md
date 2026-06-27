# Changelog

All notable changes to the Nexivo platform are documented here.

## [Unreleased] — June 25, 2026

### 🎨 Chart Styling & Formatting
- **Chart background color** — Add custom background color via color picker in widget config
- **Chart background image** — Set a background image URL for any chart widget
- **Color picker** — Native HTML5 color picker for precise background color selection
- **KPI full numbers** — KPI cards now show complete numbers (e.g., `1,234,567,890`) instead of abbreviated M/B/K
- **COUNT DISTINCT** — New aggregation option for counting unique values in a column

### 📊 New Chart Types & Sorting
- **Horizontal bar chart** — New `bar_horizontal` chart type for horizontal bar visualizations
- **Sort by max/min** — Charts can now be sorted ascending or descending by value
- **Limit bar count** — Limit the number of bars/categories displayed (e.g., top 10)

### 🏢 Organization & Assignment
- **Company-level bulk assign** — Assign dashboards to all employees in a company
- **Division-level bulk assign** — Existing division-level bulk assignment
- **Team-level bulk assign** — Existing team-level bulk assignment
- **Auto-assignment** — When users join a division/team, existing dashboard assignments are replicated

### 📝 Dashboard Management
- **Dashboard rename & description edit** — Edit dashboard name and description via modal in the dashboard list
- **Dashboard context menu** — Three-dot menu on each dashboard card with edit, duplicate, share, delete options

### 🎯 Page Navigation
- **3-dot menu on all page tabs** — Context menu (rename, duplicate, delete, export, access control) now accessible on ALL page tabs via hover, not just the active tab
- **MoreVertical icon** — Replaced confusing GripVertical with proper 3-dot (⋮) menu icon

### 🔔 Notifications System
- **Notification bell** — Real-time bell icon with unread count badge in navigation header
- **Assignment notifications** — Auto-notify users when dashboards are assigned/updated
- **Mark as read** — Mark individual or all notifications as read
- **30-second polling** — Automatic notification refresh

### 🗺️ Org Chart
- **OrgChartPage** — Visual tree layout showing companies → divisions → teams → members
- **Expand/collapse** — Collapsible org chart nodes
- **Member cards** — Role badges and department info for each member

### 🌙 Dark Theme
- **System-wide dark mode** — Toggle between light and dark themes via header button
- **Persisted preference** — Theme choice saved in localStorage via Zustand
- **TailwindCSS dark classes** — Dark mode applied to LoginPage and DataUploadPage

### 📋 Filter Access Control
- **Per-filter role restriction** — Each filter control can be restricted to specific roles
- **Role picker in filter bar** — Inline role picker for filter access control
- **Server-side enforcement** — Filter restrictions enforced in the dataset query backend

### 📄 Documentation
- **Comprehensive docs** — `DOCUMENTATION.md` covering architecture, API, RBAC, dark theme, deployment
- **README update** — Updated with new features, license info, and screenshots section
- **CHANGELOG** — This file tracking all changes

### 🔐 License
- **Apache 2.0 → Nexivo Pro License** — Changed from Apache to proprietary Pro license
- **Commercial use restriction** — Commercial use requires separate license

### 🐛 Bug Fixes
- **Bulk assign notifications** — Only notify newly assigned users, not skipped ones
- **N+1 notification creation** — Fixed using `bulk_create` for bulk assignments
- **Graph chart colors** — Fixed color resolution order in graph/network chart
