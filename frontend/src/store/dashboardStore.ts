import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface GridItem {
  i: string
  x: number
  y: number
  w: number
  h: number
}

export interface DashboardPageConfig {
  id: string
  name: string
  order: number
  layout: GridItem[]
  mobileLayout?: GridItem[]
  widgets: WidgetConfig[]
  filterControls?: DashboardFilterControl[]
  allowedRoles?: string[]
}

export interface WidgetConfig {
  id: string
  title: string
  chartType: string
  datasetId: number | null
  chartConfig: Record<string, unknown>
  queryConfig: Record<string, unknown>
  columnTypes?: Record<string, string>
}

export interface DashboardFilter {
  col: string
  op: 'eq' | 'neq' | 'in' | 'contains' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'starts_with' | 'ends_with'
  val: string | number | (string | number)[]
  sourceWidgetId: string
}

/** A persistent dashboard-level filter control (Looker Studio-style). */
export interface DashboardFilterControl {
  id: string
  col: string
  type: 'dropdown' | 'date_range' | 'text_search' | 'checkbox' | 'slider'
  label: string
  datasetId: number | null
  // Dropdown-specific: pre-fetched unique values
  options?: string[]
  // Slider-specific
  min?: number
  max?: number
  step?: number
  // Current active value(s)
  value: string | number | string[] | [number, number] | null
  // Multi-select for dropdown/checkbox
  multiSelect?: boolean
  // Filter-level access control: roles allowed to see/use this filter (empty = all)
  allowedRoles?: string[]
}

interface DashboardState {
  dashboardId: number | null
  dashboardName: string
  // Page support
  pages: DashboardPageConfig[]
  activePageId: string | null
  // Legacy single-page layout (for backward compat)
  layout: GridItem[]
  widgets: WidgetConfig[]
  // Cross-chart filtering (temporary, from chart clicks)
  filters: DashboardFilter[]
  // Dashboard-level filter controls (persistent, user-configured)
  filterControls: DashboardFilterControl[]
  setFilter: (filter: DashboardFilter) => void
  removeFilter: (col: string) => void
  clearFilters: () => void
  setFilterControls: (controls: DashboardFilterControl[]) => void
  addFilterControl: (control: DashboardFilterControl) => void
  updateFilterControl: (id: string, updates: Partial<DashboardFilterControl>) => void
  removeFilterControl: (id: string) => void
  setDashboard: (id: number, name: string) => void
  setLayout: (layout: GridItem[]) => void
  setWidgets: (widgets: WidgetConfig[]) => void
  addWidget: (widget: WidgetConfig) => void
  updateWidget: (id: string, updates: Partial<WidgetConfig>) => void
  removeWidget: (id: string) => void
  // Page operations
  setPages: (pages: DashboardPageConfig[]) => void
  setActivePage: (pageId: string | null) => void
  addPage: (page: DashboardPageConfig) => void
  updatePage: (id: string, updates: Partial<DashboardPageConfig>) => void
  removePage: (id: string) => void
  reset: () => void
}

export type ControlFilter = { col: string; op: string; val: string | number | (string | number)[]; datasetId?: number | null }

/** Convert dashboard filter controls to query-ready filter objects. */
export function controlFiltersToQuery(
  controls: DashboardFilterControl[],
): ControlFilter[] {
  return controls
    .filter((c) => c.value !== null && c.value !== '' && c.value !== undefined)
    .flatMap<ControlFilter>((c) => {
      const dsId = c.datasetId
      if (c.type === 'date_range' && Array.isArray(c.value) && c.value.length === 2) {
        return [
          { col: c.col, op: 'gte', val: c.value[0], datasetId: dsId },
          { col: c.col, op: 'lte', val: c.value[1], datasetId: dsId },
        ]
      }
      if (c.type === 'dropdown' || c.type === 'checkbox') {
        if (Array.isArray(c.value)) {
          return [{ col: c.col, op: 'in', val: c.value as (string | number)[], datasetId: dsId }]
        }
        return [{ col: c.col, op: 'eq', val: String(c.value), datasetId: dsId }]
      }
      if (c.type === 'slider' && Array.isArray(c.value)) {
        return [
          { col: c.col, op: 'gte', val: c.value[0], datasetId: dsId },
          { col: c.col, op: 'lte', val: c.value[1], datasetId: dsId },
        ]
      }
      if (c.type === 'text_search' && typeof c.value === 'string' && c.value) {
        return [{ col: c.col, op: 'contains', val: c.value, datasetId: dsId }]
      }
      return []
    })
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      dashboardId: null,
      dashboardName: '',
      pages: [],
      activePageId: null,
      layout: [],
      widgets: [],
      setDashboard: (id, name) => set({ dashboardId: id, dashboardName: name }),
      setLayout: (layout) => set({ layout }),
      setWidgets: (widgets) => set({ widgets }),
      addWidget: (widget) =>
        set((state) => {
          const activePage = state.pages.find((p) => p.id === state.activePageId)
          if (activePage) {
            return {
              pages: state.pages.map((p) =>
                p.id === state.activePageId
                  ? {
                      ...p,
                      widgets: [...p.widgets, widget],
                      layout: [
                        ...p.layout,
                        { i: widget.id, x: 0, y: Infinity, w: 6, h: 4 },
                      ],
                      // Seed a stacked full-width mobile layout entry
                      mobileLayout: [
                        ...(p.mobileLayout || []),
                        { i: widget.id, x: 0, y: Infinity, w: 12, h: 4 },
                      ],
                    }
                  : p
              ),
            }
          }
          // Legacy fallback
          return {
            widgets: [...state.widgets, widget],
            layout: [
              ...state.layout,
              { i: widget.id, x: 0, y: Infinity, w: 6, h: 4 },
            ],
          }
        }),
      updateWidget: (id, updates) =>
        set((state) => ({
          pages: state.pages.map((p) => ({
            ...p,
            widgets: p.widgets.map((w) => (w.id === id ? { ...w, ...updates } : w)),
          })),
          widgets: state.widgets.map((w) => (w.id === id ? { ...w, ...updates } : w)),
        })),
      removeWidget: (id) =>
        set((state) => ({
          pages: state.pages.map((p) => ({
            ...p,
            widgets: p.widgets.filter((w) => w.id !== id),
            layout: p.layout.filter((l) => l.i !== id),
            mobileLayout: (p.mobileLayout || []).filter((l) => l.i !== id),
          })),
          widgets: state.widgets.filter((w) => w.id !== id),
          layout: state.layout.filter((l) => l.i !== id),
        })),
      filters: [],
      filterControls: [],
      setFilter: (filter) =>
        set((state) => ({
          filters: [
            ...state.filters.filter((f) => f.col !== filter.col || f.sourceWidgetId !== filter.sourceWidgetId),
            filter,
          ],
        })),
      removeFilter: (col) =>
        set((state) => ({
          filters: state.filters.filter((f) => f.col !== col),
        })),
      clearFilters: () => set({ filters: [] }),
      setFilterControls: (controls) => set({ filterControls: controls }),
      addFilterControl: (control) =>
        set((state) => ({
          filterControls: [...state.filterControls, control],
        })),
      updateFilterControl: (id, updates) =>
        set((state) => ({
          filterControls: state.filterControls.map((c) =>
            c.id === id ? { ...c, ...updates } : c
          ),
        })),
      removeFilterControl: (id) =>
        set((state) => ({
          filterControls: state.filterControls.filter((c) => c.id !== id),
        })),
      // Page operations
      setPages: (pages) => set({ pages }),
      setActivePage: (pageId) => set({ activePageId: pageId }),
      addPage: (page) =>
        set((state) => ({
          pages: [...state.pages, page],
          activePageId: page.id,
        })),
      updatePage: (id, updates) =>
        set((state) => ({
          pages: state.pages.map((p) => (p.id === id ? { ...p, ...updates } : p)),
        })),
      removePage: (id) =>
        set((state) => {
          const newPages = state.pages.filter((p) => p.id !== id)
          const newActiveId =
            state.activePageId === id
              ? newPages.length > 0
                ? newPages[0].id
                : null
              : state.activePageId
          return { pages: newPages, activePageId: newActiveId }
        }),
      reset: () =>
        set({
          dashboardId: null,
          dashboardName: '',
          pages: [],
          activePageId: null,
          layout: [],
          widgets: [],
          filters: [],
          filterControls: [],
        }),
    }),
    {
      name: 'nexivo-dashboard',
    }
  )
)
