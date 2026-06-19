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

interface DashboardState {
  dashboardId: number | null
  dashboardName: string
  layout: GridItem[]
  widgets: WidgetConfig[]
  setDashboard: (id: number, name: string) => void
  setLayout: (layout: GridItem[]) => void
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
        })),
      removeWidget: (id) =>
        set((state) => ({
          widgets: state.widgets.filter((w) => w.id !== id),
          layout: state.layout.filter((l) => l.i !== id),
        })),
      reset: () =>
        set({ dashboardId: null, dashboardName: '', layout: [], widgets: [] }),
    }),
    {
      name: 'nexivo-dashboard',
    }
  )
)
