import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface GridItem {
  i: string
  x: number
  y: number
  w: number
  h: number
}

export interface WidgetConfig {
  id: string
  title: string
  chartType: string
  datasetId: number | null
  chartConfig: Record<string, unknown>
  queryConfig: Record<string, unknown>
}

export interface DashboardFilter {
  col: string
  op: 'eq' | 'in' | 'contains' | 'gt' | 'lt'
  val: string | number | (string | number)[]
  sourceWidgetId: string
}

interface DashboardState {
  dashboardId: number | null
  dashboardName: string
  layout: GridItem[]
  widgets: WidgetConfig[]
  // Cross-chart filtering
  filters: DashboardFilter[]
  setFilter: (filter: DashboardFilter) => void
  removeFilter: (col: string) => void
  clearFilters: () => void
  setDashboard: (id: number, name: string) => void
  setLayout: (layout: GridItem[]) => void
  setWidgets: (widgets: WidgetConfig[]) => void
  addWidget: (widget: WidgetConfig) => void
  updateWidget: (id: string, updates: Partial<WidgetConfig>) => void
  removeWidget: (id: string) => void
  reset: () => void
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      dashboardId: null,
      dashboardName: '',
      layout: [],
      widgets: [],
      setDashboard: (id, name) => set({ dashboardId: id, dashboardName: name }),
      setLayout: (layout) => set({ layout }),
      setWidgets: (widgets) => set({ widgets }),
      addWidget: (widget) =>
        set((state) => ({
          widgets: [...state.widgets, widget],
          layout: [
            ...state.layout,
            { i: widget.id, x: 0, y: Infinity, w: 6, h: 4 },
          ],
        })),
      updateWidget: (id, updates) =>
        set((state) => ({
          widgets: state.widgets.map((w) =>
            w.id === id ? { ...w, ...updates } : w
          ),
        })),      removeWidget: (id) =>
        set((state) => ({
          widgets: state.widgets.filter((w) => w.id !== id),
          layout: state.layout.filter((l) => l.i !== id),
        })),
      filters: [],
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
      reset: () => set({ dashboardId: null, dashboardName: '', layout: [], widgets: [], filters: [] }),
    }),
    {
      name: 'nexivo-dashboard',
    }
  )
)
