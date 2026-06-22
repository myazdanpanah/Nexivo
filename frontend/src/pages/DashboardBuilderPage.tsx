import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Responsive, WidthProvider } from 'react-grid-layout'
import { useDashboardStore } from '../store/dashboardStore'
import api from '../api/client'
import ChartWidget from '../components/ChartWidget'
import WidgetConfigPanel from '../components/WidgetConfigPanel'
import { Plus, ArrowRight, Settings, Trash2 } from 'lucide-react'

import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

export default function DashboardBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const { layout, widgets, setLayout, setWidgets, addWidget, removeWidget, setDashboard } = useDashboardStore()
  const [showConfig, setShowConfig] = useState(false)
  const [editingWidget, setEditingWidget] = useState<string | null>(null)

  useEffect(() => {
    if (id) loadDashboard(parseInt(id))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadDashboard = async (dashboardId: number) => {
    try {
      const res = await api.get(`/dashboards/${dashboardId}/`)
      setDashboard(res.data.id, res.data.name)

      const serverWidgets = res.data.widgets.map((w: Record<string, unknown>) => ({
        id: String(w.id),
        title: w.title as string,
        chartType: w.chart_type as string,
        datasetId: w.dataset as number | null,
        chartConfig: (w.chart_config as Record<string, unknown>) || {},
        queryConfig: (w.query_config as Record<string, unknown>) || {},
      }))

      const serverLayout = res.data.widgets.map((w: Record<string, unknown>) => ({
        i: String(w.id),
        x: w.grid_x as number,
        y: w.grid_y as number,
        w: w.grid_w as number,
        h: w.grid_h as number,
      }))

      setWidgets(serverWidgets)
      setLayout(serverLayout)
    } catch {
      // ignore
    }
  }

  const handleLayoutChange = useCallback(
    (newLayout: Array<{ i: string; x: number; y: number; w: number; h: number }>) => {
      setLayout(newLayout)
      // Persist layout to backend
      if (id) {
        api.put(`/dashboards/${id}/layout/`, { layout: newLayout }).catch(() => {})
      }
    },
    [setLayout, id]
  )

  const addNewWidget = async () => {
    if (!id) return
    try {
      const res = await api.post(`/dashboards/${id}/widgets/`, {
        title: 'نمودار جدید',
        chart_type: 'bar',
        chart_config: {},
        query_config: {},
        grid_x: 0,
        grid_y: 0,
        grid_w: 6,
        grid_h: 4,
      })
      addWidget({
        id: String(res.data.id),
        title: res.data.title,
        chartType: res.data.chart_type,
        datasetId: res.data.dataset,
        chartConfig: res.data.chart_config,
        queryConfig: res.data.query_config,
      })
      setEditingWidget(String(res.data.id))
      setShowConfig(true)
    } catch {
      // ignore
    }
  }

  const deleteWidget = async (widgetId: string) => {
    if (!id) return
    try {
      await api.delete(`/dashboards/${id}/widgets/${widgetId}/`)
      removeWidget(widgetId)
      setShowConfig(false)
      setEditingWidget(null)
    } catch {
      // ignore
    }
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to="/dashboards"
              className="p-2 text-gray-400 hover:text-gray-600 transition"
            >
              <ArrowRight className="w-5 h-5" />
            </Link>
            <h1 className="text-lg font-bold text-gray-900">ویرایشگر داشبورد</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={addNewWidget}
              className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm"
            >
              <Plus className="w-4 h-4" />
              افزودن نمودار
            </button>
          </div>
        </div>
      </header>

      {/* Dashboard Grid */}
      <main className="p-6">
        {widgets.length === 0 ? (
          <div className="text-center py-20">
            <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              داشبورد خالی است
            </h3>
            <p className="text-gray-500 mb-6">
              اولین نمودار خود را اضافه کنید
            </p>
            <button
              onClick={addNewWidget}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-medium"
            >
              افزودن نمودار
            </button>
          </div>
        ) : (
          <ResponsiveGridLayout
            className="layout"
            layouts={{ lg: layout }}
            breakpoints={{ lg: 1200, md: 996, sm: 768 }}
            cols={{ lg: 12, md: 9, sm: 6 }}
            rowHeight={60}
            onLayoutChange={handleLayoutChange}
            isDraggable
            isResizable
          >
            {widgets.map((w) => (
              <div key={w.id} className="group">
                <div className="bg-white rounded-2xl border border-gray-200 h-full overflow-hidden shadow-sm hover:shadow-md transition">
                  <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
                    <span className="text-sm font-medium text-gray-700 truncate">
                      {w.title}
                    </span>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                      <button
                        onClick={() => {
                          setEditingWidget(w.id)
                          setShowConfig(true)
                        }}
                        className="p-1 text-gray-400 hover:text-indigo-500 transition"
                      >
                        <Settings className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => deleteWidget(w.id)}
                        className="p-1 text-gray-400 hover:text-red-500 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="p-2" style={{ height: 'calc(100% - 40px)' }}>
                    <ChartWidget widget={w} />
                  </div>
                </div>
              </div>
            ))}
          </ResponsiveGridLayout>
        )}
      </main>

      {/* Widget Config Panel */}
      {showConfig && editingWidget && (
        <WidgetConfigPanel
          widgetId={editingWidget}
          onClose={() => {
            setShowConfig(false)
            setEditingWidget(null)
          }}
        />
      )}
    </div>
  )
}
